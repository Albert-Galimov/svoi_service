/**
 * Автозаполнение «Цена для клиента» на основе «Закупочной цены» +30%.
 * Только для запчастей (признак — поле «Артикул» в строке).
 *
 * Особенности:
 *  - при фокусе на поле с "0" / "0.00" — очищаем, чтобы не получать
 *    "022" и "0.0022" при наборе;
 *  - метка "ручная цена" ставится только если введено значение,
 *    отличное от 0 / пусто / 0.00. Просто клик или ноль — не считаются
 *    ручным вводом.
 */

(function () {
    "use strict";

    const MARKUP = 0.30;

    function toNumber(raw) {
        if (!raw) return NaN;
        const cleaned = String(raw).replace(/\s+/g, "").replace(",", ".");
        return parseFloat(cleaned);
    }

    function isZeroOrEmpty(value) {
        if (value === null || value === undefined) return true;
        const s = String(value).trim();
        if (s === "") return true;
        const n = parseFloat(s.replace(",", "."));
        return isNaN(n) || n === 0;
    }

    // ---- 1. При фокусе очищаем "0" / "0.00" ----
    document.addEventListener("focusin", function (e) {
        const t = e.target;
        if (!t || !t.name) return;
        if (!t.name.endsWith("-purchase_price") && !t.name.endsWith("-client_price")) return;
        if (isZeroOrEmpty(t.value)) {
            t.value = "";
        }
    });

    // ---- 2. Пересчёт при вводе ----
    document.addEventListener("input", function (e) {
        const target = e.target;
        if (!target || !target.name) return;

        const row = target.closest("tr");
        if (!row) return;

        // Только строки запчастей (у услуг нет поля article)
        if (!row.querySelector('input[name$="-article"]')) return;

        // --- Пользователь правит client_price ---
        if (target.name.endsWith("-client_price")) {
            if (isZeroOrEmpty(target.value)) {
                // пусто/0 — снимаем метку "ручная", возвращаем в авто-режим
                delete row.dataset.manualClientPrice;
            } else {
                // осмысленное значение — помечаем как ручное
                row.dataset.manualClientPrice = "1";
            }
            return;
        }

        // --- Пользователь правит purchase_price ---
        if (!target.name.endsWith("-purchase_price")) return;

        // В этой сессии client_price уже правили вручную — не трогаем
        if (row.dataset.manualClientPrice === "1") return;

        const clientInput = row.querySelector('input[name$="-client_price"]');
        if (!clientInput) return;

        const purchase = toNumber(target.value);
        if (isNaN(purchase) || purchase <= 0) {
            // purchase пустой или 0 — обнуляем client
            if (!isZeroOrEmpty(clientInput.value)) {
                clientInput.value = "";
                clientInput.dispatchEvent(new Event("change", { bubbles: true }));
            }
            return;
        }

        clientInput.value = Math.round(purchase * (1 + MARKUP));
        clientInput.dispatchEvent(new Event("change", { bubbles: true }));
    });
})();