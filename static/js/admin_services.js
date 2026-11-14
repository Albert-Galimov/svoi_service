/**
 * Автоподстановка названия и цены из услуги справочника.
 *
 * Используем ТОЛЬКО события пользователя от Select2:
 *   - select2:select — пользователь выбрал услугу;
 *   - select2:clear  — пользователь очистил выбор крестиком.
 *
 * При инициализации Select2 эти события НЕ бросает, поэтому сохранённые
 * name и client_price в старом заказе не затираются.
 *
 * Никакого polling, никаких нативных change — только чистые действия
 * пользователя.
 */

document.addEventListener("DOMContentLoaded", function () {
    console.log("JS для услуг загружен");

    const $ = (window.django && window.django.jQuery) || window.jQuery || null;
    console.log("jQuery доступен:", !!$);

    if (!$) {
        console.error(
            "jQuery не найден — Select2-события не будут перехвачены. " +
            "Проверь, инициализирован ли Select2 для поля service."
        );
        return;
    }

    function applyServiceData(select) {
        const row = select.closest("tr");
        if (!row) return;

        const serviceId = select.value;
        if (!serviceId) return;

        const nameInput = row.querySelector('input[name$="-name"]');
        const priceInput = row.querySelector('input[name$="-client_price"]');

        console.log("Запрос услуги id:", serviceId);

        fetch(`/crm/api/service-lookup/?id=${encodeURIComponent(serviceId)}`)
            .then(function (r) {
                if (!r.ok) throw new Error("HTTP " + r.status);
                return r.json();
            })
            .then(function (data) {
                console.log("Ответ API услуги:", data);

                // Пока запрос летел, могли выбрать другую услугу
                if (select.value !== serviceId) return;

                if (nameInput) {
                    nameInput.value = data.name || "";
                    nameInput.dispatchEvent(new Event("input", { bubbles: true }));
                }
                if (priceInput) {
                    priceInput.value = data.price || "";
                    priceInput.dispatchEvent(new Event("input", { bubbles: true }));
                }
            })
            .catch(function (err) {
                console.error("Ошибка получения услуги:", err);
            });
    }

    function clearFields(select) {
        const row = select.closest("tr");
        if (!row) return;

        ["-name", "-client_price"].forEach(function (suffix) {
            const f = row.querySelector(`input[name$="${suffix}"]`);
            if (f && f.value !== "") {
                f.value = "";
                f.dispatchEvent(new Event("input", { bubbles: true }));
            }
        });
    }

    // Пользователь ВЫБРАЛ услугу
    $(document).on("select2:select", 'select[name$="-service"]', function () {
        applyServiceData(this);
    });

    // Пользователь ОЧИСТИЛ выбор крестиком
    $(document).on("select2:clear", 'select[name$="-service"]', function () {
        clearFields(this);
    });
});