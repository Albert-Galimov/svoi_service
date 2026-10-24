/**
 * Подгружает ссылки на поставщиков запчастей, когда брат вводит артикул
 * в inline-таблице позиций заказ-наряда.
 *
 * Как работает:
 *   - находим все поля артикула (name оканчивается на "-article");
 *   - при вводе ждём 500 мс (debounce), чтобы не дёргать сервер на каждую букву;
 *   - отправляем GET на /crm/api/part-lookup/?article=...;
 *   - рисуем под полем кнопки-ссылки.
 */

document.addEventListener("DOMContentLoaded", function () {
    const articleInputs = document.querySelectorAll('input[name$="-article"]');

    articleInputs.forEach(function (input) {
        // Создаём контейнер под ссылки и ставим его сразу после поля
        const linkContainer = document.createElement("div");
        linkContainer.className = "part-supplier-links";
        input.parentNode.appendChild(linkContainer);

        let debounceTimer = null;

        input.addEventListener("input", function () {
            clearTimeout(debounceTimer);

            const article = input.value.trim().toUpperCase();
            if (!article) {
                linkContainer.innerHTML = "";
                return;
            }

            debounceTimer = setTimeout(function () {
                fetch(`/crm/api/part-lookup/?article=${encodeURIComponent(article)}`)
                    .then(function (response) {
                        if (!response.ok) throw new Error("HTTP " + response.status);
                        return response.json();
                    })
                    .then(function (data) {
                        if (!data.suppliers || data.suppliers.length === 0) {
                            linkContainer.innerHTML = "";
                            return;
                        }

                        // Строим строку с кнопками через DOM, а не через innerHTML
                        // с сырым вводом пользователя — так безопаснее и чище.
                        const wrapper = document.createElement("div");
                        wrapper.className = "part-supplier-links__row";

                        data.suppliers.forEach(function (supplier) {
                            const link = document.createElement("a");
                            link.href = supplier.url;
                            link.target = "_blank";
                            link.rel = "noopener noreferrer";
                            link.className = "part-link";
                            link.textContent = supplier.name;
                            wrapper.appendChild(link);
                        });

                        linkContainer.innerHTML = "";
                        linkContainer.appendChild(wrapper);
                    })
                    .catch(function (err) {
                        console.error("Ошибка получения ссылок на поставщиков:", err);
                    });
            }, 500);
        });

        // Если поле очистили — сразу убираем ссылки
        input.addEventListener("blur", function () {
            if (!input.value.trim()) {
                linkContainer.innerHTML = "";
            }
        });
    });
});