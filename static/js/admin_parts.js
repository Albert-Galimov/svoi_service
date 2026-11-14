/**
 * Ссылки на поставщиков + проверка остатков на складе +
 * автоподстановка названия и закупочной цены из складской карточки.
 *
 * Работает через делегирование событий на document — подхватывает
 * и существующие строки, и новые после «Добавить ещё одну запчасть».
 *
 * Поведение:
 *  - при вводе артикула — запрос к API; если на складе есть данные,
 *    подставляются название и (при остатке > 0) закупочная цена;
 *    существующие значения в этих полях ЗАМЕНЯЮТСЯ;
 *  - при полной очистке артикула — контейнер со ссылками, название,
 *    закупочная цена и цена для клиента в этой строке очищаются.
 */

document.addEventListener("DOMContentLoaded", function () {
    console.log("JS для запчастей загружен (делегирование)");

    const debounceTimers = new WeakMap();

    // ---- Утилиты ----

    function ensureLinkContainer(input) {
        const row = input.closest("tr");
        if (!row) return null;

        let container = row.querySelector(".part-supplier-links");
        if (container) return container;

        container = document.createElement("div");
        container.className = "part-supplier-links";

        const td = input.closest("td");
        if (td) {
            td.appendChild(container);
        } else {
            input.parentNode.appendChild(container);
        }
        return container;
    }

    function renderLinks(container, data) {
        if (!data || !data.suppliers || data.suppliers.length === 0) {
            container.innerHTML = "";
            return;
        }

        const wrapper = document.createElement("div");
        wrapper.className = "part-supplier-links__row";

        const stockBadge = document.createElement("span");
        const stockCount = data.stock !== undefined ? data.stock : 0;
        if (stockCount > 0) {
            stockBadge.style.cssText =
                "background-color: #10b981; color: white; " +
                "padding: 3px 8px; border-radius: 4px; " +
                "font-size: 11px; font-weight: bold;";
            stockBadge.textContent = `Склад: остаток ${stockCount}`;
        } else {
            stockBadge.style.cssText =
                "background-color: #ef4444; color: white; " +
                "padding: 3px 8px; border-radius: 4px; " +
                "font-size: 11px; font-weight: bold;";
            stockBadge.textContent = "Склад: остаток 0";
        }
        wrapper.appendChild(stockBadge);

        data.suppliers.forEach(function (supplier) {
            const link = document.createElement("a");
            link.href = supplier.url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.className = "part-link";
            link.textContent = supplier.name;
            wrapper.appendChild(link);
        });

        container.innerHTML = "";
        container.appendChild(wrapper);
    }

    /** Подставляет название и закупочную цену, ЗАМЕНЯЯ существующие значения. */
    function applyWarehouseData(input, data) {
        const row = input.closest("tr");
        if (!row) return;

        const nameInput = row.querySelector('input[name$="-name"]');
        const purchaseInput = row.querySelector('input[name$="-purchase_price"]');

        // Название — заменяем при каждом успешном автозаполнении.
        if (nameInput && data.name) {
            nameInput.value = data.name;
            nameInput.dispatchEvent(new Event("input", { bubbles: true }));
            console.log("Название заменено из склада:", data.name);
        }

        // Закупочная цена — заменяем, если есть остаток на складе.
        if (purchaseInput && data.purchase_price && data.stock > 0) {
            purchaseInput.value = data.purchase_price;
            // admin_markup.js посчитает «Цену для клиента» +30%
            purchaseInput.dispatchEvent(new Event("input", { bubbles: true }));
            console.log("Закупочная цена заменена из склада:", data.purchase_price);
        }
    }

    /** Полностью очищает в строке название, закупочную и цену клиента. */
    function clearRowFields(row) {
        ["-name", "-purchase_price", "-client_price"].forEach(function (suffix) {
            const f = row.querySelector(`input[name$="${suffix}"]`);
            if (!f) return;
            if (f.value !== "") {
                f.value = "";
                f.dispatchEvent(new Event("input", { bubbles: true }));
            }
        });
    }

    // ---- Основной обработчик ----

    function handleArticleChange(e) {
        const input = e.target;
        if (!input || !input.name) return;
        if (!input.name.endsWith("-article")) return;

        const container = ensureLinkContainer(input);
        if (!container) return;

        const article = input.value.trim().toUpperCase();

        // ---- Артикул стёрт: чистим всё в строке ----
        if (!article) {
            if (debounceTimers.has(input)) {
                clearTimeout(debounceTimers.get(input));
                debounceTimers.delete(input);
            }
            container.innerHTML = "";

            const row = input.closest("tr");
            if (row) clearRowFields(row);
            return;
        }

        // ---- Артикул непустой: дебаунс и запрос ----
        if (debounceTimers.has(input)) {
            clearTimeout(debounceTimers.get(input));
        }

        const t = setTimeout(function () {
            console.log("Запрос ссылок для артикула:", article);

            fetch(`/crm/api/part-lookup/?article=${encodeURIComponent(article)}`)
                .then(function (response) {
                    if (!response.ok) throw new Error("HTTP " + response.status);
                    return response.json();
                })
                .then(function (data) {
                    // Защита от гонки: пока запрос был в полёте, пользователь мог
                    // стереть поле или ввести другой артикул.
                    const current = input.value.trim().toUpperCase();
                    if (current !== article) return;

                    renderLinks(container, data);
                    applyWarehouseData(input, data);
                })
                .catch(function (err) {
                    console.error("Ошибка получения ссылок:", err);
                });
        }, 400);

        debounceTimers.set(input, t);
    }

    document.addEventListener("input", handleArticleChange);
    document.addEventListener("change", handleArticleChange);
});