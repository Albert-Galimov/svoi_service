/**
 * Ссылки на поставщиков + проверка остатков на складе.
 *
 * Работает через делегирование событий на document — поэтому
 * автоматически подхватывает и существующие строки, и новые,
 * добавленные кнопкой «Добавить ещё одну запчасть».
 */

document.addEventListener("DOMContentLoaded", function () {
    console.log("JS для запчастей загружен (делегирование)");

    // Хранилище дебаунсеров по каждому input, чтобы не срабатывал на каждую букву
    const debounceTimers = new WeakMap();

    function ensureLinkContainer(input) {
        // Ищем контейнер в той же ячейке/строке, где лежит инпут.
        // Сначала ищем уже созданный (при повторном вводе не дублируем).
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
        if (!data.suppliers || data.suppliers.length === 0) {
            container.innerHTML = "";
            return;
        }

        const wrapper = document.createElement("div");
        wrapper.className = "part-supplier-links__row";

        // Плашка склада
        const stockBadge = document.createElement("span");
        const stockCount = data.stock !== undefined ? data.stock : 0;
        if (stockCount > 0) {
            stockBadge.style.cssText = "background-color: #10b981; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;";
            stockBadge.textContent = `Склад: остаток ${stockCount}`;
        } else {
            stockBadge.style.cssText = "background-color: #ef4444; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;";
            stockBadge.textContent = "Склад: остаток 0";
        }
        wrapper.appendChild(stockBadge);

        // Ссылки на поставщиков
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

    // Один слушатель на весь документ
    document.addEventListener("input", function (e) {
        const input = e.target;
        if (!input || !input.name) return;
        if (!input.name.endsWith("-article")) return;

        const container = ensureLinkContainer(input);
        if (!container) return;

        const article = input.value.trim().toUpperCase();

        // Пользователь стёр артикул — очищаем ссылки
        if (!article) {
            container.innerHTML = "";
            return;
        }

        // Дебаунс на 400 мс — чтобы не дёргать сервер на каждую букву
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
                    renderLinks(container, data);
                })
                .catch(function (err) {
                    console.error("Ошибка получения ссылок:", err);
                });
        }, 400);

        debounceTimers.set(input, t);
    });
});