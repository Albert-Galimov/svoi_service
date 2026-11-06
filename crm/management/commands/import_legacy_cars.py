"""Импорт старой базы брата (merged.txt) в CRM.

Стратегия:
  - каждая машина получает СВОЕГО клиента;
  - если в старых данных был телефон — клиент реальный (phone = телефон);
  - если телефона нет — клиент «виртуальный» с фиктивным номером
    +7000XXXXXXX и понятным именем вида "Opel Mokka (архив)"
    или "Рафаилыч (архив)";
  - вся история ремонта остаётся текстом в Car.notes;
  - повторный запуск не создаёт дублей: если машина с таким же
    VIN/госномером уже есть — перевешиваем её на актуального клиента.
"""

import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from crm.models import Car, Client


FILE_MARKER_RE = re.compile(
    r"^###\s+ФАЙЛ:\s+(.+?)\.txt\s+\(.*?\)\s*$", re.MULTILINE,
)
VIN_RE = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")
PLATE_RE = re.compile(
    r"[АВЕКМНОРСТУХавекмнорстух]\d{3}[АВЕКМНОРСТУХавекмнорстух]{2}\d{2,3}"
)
PHONE_RE = re.compile(
    r"(?:\+7|8|7)[\s\-\.\(\)]*\d{3}[\s\-\.\(\)]*\d{3}[\s\-\.]*\d{2}[\s\-\.]*\d{2}"
)

FAKE_PREFIX = "+7000"
FAKE_NOTE = (
    "Клиент восстановлен из старой базы брата. "
    "Реальный телефон неизвестен — при первом звонке обновите поле "
    "«Телефон». Если такой человек уже есть отдельной карточкой — "
    "перенесите к нему машины и удалите эту запись."
)

_NOT_NAMES = {
    "тел", "телефон", "моб", "смс", "звонить", "звонок", "номер", "контакт",
    "мастер", "клиент", "клиента", "заказ", "заявка", "авто", "автосервис",
    "оплата", "предоплата", "долг", "остаток", "скидка", "итого",
    "работа", "работы", "запчасти", "масло", "акпп", "кпп", "мкпп",
    "двигатель", "ремонт", "пробег", "адрес", "вацап", "вотсап", "ватсап",
    "whatsapp", "telegram", "телеграм",
}


# ---------- парсинг ----------

def parse_filename(name: str):
    """Возвращает (brand, model, plate, tail).

    Логика:
      - есть госномер → brand + model + plate, после него — tail;
      - нет госномера, но есть пробел → brand + model (может быть, «Audi A4»);
      - нет ни госномера, ни пробела → скорее всего, это имя человека
        («Рафаилыч.txt») — тогда brand=«Неизвестно», model=«Неизвестно»,
        tail=имя. Машину с таким файлом создадим только если в теле
        нашёлся VIN.
    """
    name = name.strip()

    m = PLATE_RE.search(name)
    if m:
        plate = m.group(0).upper()
        before = name[: m.start()].strip(" -—,")
        after = name[m.end():].strip(" -—,")
        parts = before.split(None, 1)
        brand = parts[0] if parts else "Неизвестно"
        model = parts[1] if len(parts) > 1 else "—"
        return brand, model, plate, after

    if " " not in name:
        # единственное слово без номера — вероятно имя человека
        return "Неизвестно", "Неизвестно", "", name

    parts = name.split(None, 1)
    return parts[0], parts[1], "", ""


def extract_vin(text: str) -> str:
    m = VIN_RE.search(text)
    return m.group(1) if m else ""


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits[0] in "78":
        return "+7" + digits[1:]
    if len(digits) == 10:
        return "+7" + digits
    return ""


def extract_phone(text: str) -> str:
    for m in PHONE_RE.finditer(text):
        phone = normalize_phone(m.group(0))
        if not phone or len(phone) != 12:
            continue
        tail = phone[2:]
        if tail == "0" * 10 or len(set(tail)) <= 2:
            continue
        return phone
    return ""


def _is_name_word(word: str) -> bool:
    if len(word) < 2:
        return False
    if word.lower() in _NOT_NAMES:
        return False
    return True


def extract_name(text: str, phone: str) -> str:
    if not phone:
        return ""
    tail7 = phone[-7:]
    for line in text.splitlines():
        digits = re.sub(r"\D", "", line)
        if tail7 in digits:
            words = re.findall(r"[А-ЯЁ][а-яё\-]+", line)
            picked = [w for w in words if _is_name_word(w)]
            if picked:
                return " ".join(picked[:3])
    return ""


def name_from_tail(tail: str) -> str:
    if not tail:
        return ""
    tail = re.sub(
        r"^(от|у|для|клиент[а-я]*|мастер[а-я]*)\s+", "", tail, flags=re.I,
    )
    words = re.findall(r"[А-ЯЁ][а-яё\-]+", tail)
    picked = [w for w in words if _is_name_word(w)]
    return " ".join(picked[:3])


def strip_decorative_noise(body: str) -> str:
    body = body.strip()
    body = re.sub(r"^[=\-]{3,}\s*$", "", body, flags=re.MULTILINE)
    return body.strip()


# ---------- клиенты ----------

def _next_fake_phone() -> str:
    used = Client.objects.filter(
        phone__startswith=FAKE_PREFIX
    ).values_list("phone", flat=True)

    max_n = 0
    for p in used:
        try:
            n = int(p[len(FAKE_PREFIX):])
        except (ValueError, TypeError):
            continue
        if n > max_n:
            max_n = n

    while True:
        max_n += 1
        candidate = f"{FAKE_PREFIX}{max_n:07d}"
        if not Client.objects.filter(phone=candidate).exists():
            return candidate


def _fake_client_name(brand, model, base_name) -> str:
    """Красивое имя виртуального клиента.

    Приоритет:
      1. Если знаем имя человека — "<Имя> (архив)".
      2. Если знаем машину  — "<Марка Модель> (архив)".
      3. Совсем без данных — "Неизвестный клиент (архив)".
    Ни VIN, ни госномер в имя не попадают: они и так есть в карточке Car
    и ищутся через раздел «Автомобили».
    """
    if base_name:
        return f"{base_name} (архив)"

    if brand and brand != "Неизвестно":
        if model and model not in ("—", "Неизвестно"):
            return f"{brand} {model} (архив)"
        return f"{brand} (архив)"

    return "Неизвестный клиент (архив)"


def _make_fake_client(brand, model, base_name) -> Client:
    return Client.objects.create(
        phone=_next_fake_phone(),
        name=_fake_client_name(brand, model, base_name),
        notes=FAKE_NOTE,
    )


# ---------- команда ----------

class Command(BaseCommand):
    help = "Импорт старых записей из merged.txt (каждая машина = свой клиент)"

    def add_arguments(self, parser):
        parser.add_argument("file", help="Путь к merged.txt")
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Только показать план, без записи в БД",
        )

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.exists():
            self.stderr.write(self.style.ERROR(f"Файл не найден: {path}"))
            return

        text = path.read_text(encoding="utf-8")
        matches = list(FILE_MARKER_RE.finditer(text))
        if not matches:
            self.stderr.write(self.style.ERROR(
                "Не найдено блоков «### ФАЙЛ:». Проверь, что это merged.txt."
            ))
            return

        dry = options["dry_run"]

        rows = []
        skipped_no_id = []

        for i, m in enumerate(matches):
            file_name = m.group(1).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = strip_decorative_noise(text[start:end])

            brand, model, plate, tail = parse_filename(file_name)
            vin = extract_vin(body)

            if not vin and not plate:
                skipped_no_id.append(file_name)
                continue

            phone = extract_phone(body)
            name = extract_name(body, phone) if phone else ""
            if not name:
                name = name_from_tail(tail)

            rows.append({
                "file_name": file_name,
                "brand": brand, "model": model,
                "plate": plate, "vin": vin,
                "phone": phone, "name": name,
                "body": body,
            })

        with_phone = [r for r in rows if r["phone"]]
        with_name_only = [r for r in rows if not r["phone"] and r["name"]]
        without_any = [r for r in rows if not r["phone"] and not r["name"]]

        self.stdout.write(
            f"Машин: {len(rows)}. "
            f"С реальным телефоном: {len(with_phone)}. "
            f"С именем без телефона: {len(with_name_only)}. "
            f"Без клиентских данных: {len(without_any)}. "
            f"Пропущено (нет ни VIN, ни номера): {len(skipped_no_id)}."
        )

        if dry:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(
                f"=== РЕАЛЬНЫЕ КЛИЕНТЫ (первые 20 из {len(with_phone)}) ==="
            ))
            for r in with_phone[:20]:
                self.stdout.write(
                    f"  · {r['phone']:<13} {r['name'] or '(без имени)':<38} "
                    f"← {r['file_name']}"
                )
            if len(with_phone) > 20:
                self.stdout.write(f"  … и ещё {len(with_phone) - 20}")

            self.stdout.write("")
            self.stdout.write(self.style.WARNING(
                f"=== АРХИВНЫЕ С ИМЕНЕМ (первые 20 из {len(with_name_only)}) ==="
            ))
            for r in with_name_only[:20]:
                display = _fake_client_name(r["brand"], r["model"], r["name"])
                self.stdout.write(f"  · {display:<50} ← {r['file_name']}")
            if len(with_name_only) > 20:
                self.stdout.write(f"  … и ещё {len(with_name_only) - 20}")

            self.stdout.write("")
            self.stdout.write(self.style.WARNING(
                f"=== АРХИВНЫЕ БЕЗ ИМЕНИ (первые 10 из {len(without_any)}) ==="
            ))
            for r in without_any[:10]:
                display = _fake_client_name(r["brand"], r["model"], "")
                self.stdout.write(f"  · {display:<50} ← {r['file_name']}")
            if len(without_any) > 10:
                self.stdout.write(f"  … и ещё {len(without_any) - 10}")

            if skipped_no_id:
                self.stdout.write("")
                self.stdout.write(self.style.WARNING(
                    f"=== ПРОПУЩЕНО ({len(skipped_no_id)} файлов) ==="
                ))
                for n in skipped_no_id:
                    self.stdout.write(f"  · {n}")
            return

        # ---------- реальный импорт ----------

        clients_real_created = 0
        clients_real_reused = 0
        clients_fake_created = 0
        cars_created = 0
        cars_updated = 0

        with transaction.atomic():
            for r in rows:
                # ---- 1. Клиент ----
                if r["phone"]:
                    client, created = Client.objects.get_or_create(
                        phone=r["phone"],
                        defaults={
                            "name": r["name"] or "Клиент из старой базы",
                        },
                    )
                    if created:
                        clients_real_created += 1
                    else:
                        clients_real_reused += 1
                else:
                    client = _make_fake_client(
                        r["brand"], r["model"], r["name"],
                    )
                    clients_fake_created += 1

                # ---- 2. Машина: создать или обновить владельца ----
                qs = Car.objects.filter(brand=r["brand"], model=r["model"])
                if r["plate"]:
                    qs = qs.filter(plate=r["plate"])
                if r["vin"]:
                    qs = qs.filter(vin=r["vin"])

                car = qs.first() if (r["plate"] or r["vin"]) else None

                if car:
                    if car.client_id != client.pk:
                        car.client = client
                        car.save(update_fields=["client"])
                    cars_updated += 1
                else:
                    notes = f"Исходный файл: {r['file_name']}.txt\n\n{r['body']}"
                    Car.objects.create(
                        client=client,
                        brand=r["brand"], model=r["model"],
                        plate=r["plate"], vin=r["vin"],
                        mileage=0, notes=notes,
                    )
                    cars_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Готово. "
            f"Реальных клиентов создано: {clients_real_created}, "
            f"привязано к существующим: {clients_real_reused}. "
            f"Архивных клиентов создано: {clients_fake_created}. "
            f"Машин создано: {cars_created}, обновлено: {cars_updated}."
        ))