document.addEventListener("DOMContentLoaded", function () {
    const articleInputs = document.querySelectorAll('input[name$="-article"]');

    articleInputs.forEach(function (input) {
        // Создаем контейнер под ссылки и плашки
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

            // Ждем полсекунды после последнего нажатия клавиши
            debounceTimer = setTimeout(function () {
                fetch(`/crm/api/part-lookup/?article=${encodeURIComponent(article)}`)
                    .then(function (response) {
                        if (!response.ok) throw new Error("HTTP " + response.status);
                        return response.json();
                    })
                    .then(function (data) {
                        if (!data.suppliers) {
                            linkContainer.innerHTML = "";
                            return;
                        }

                        const wrapper = document.createElement("div");
                        wrapper.className = "part-supplier-links__row";
                        // Стили для строки, чтобы всё было в одну линию
                        wrapper.style.display = "flex";
                        wrapper.style.flexWrap = "wrap";
                        wrapper.style.gap = "6px";
                        wrapper.style.marginTop = "6px";
                        wrapper.style.alignItems = "center";

                        // --- БЛОК СКЛАДА ---
                        const stockBadge = document.createElement("span");
                        if (data.stock > 0) {
                            // Зеленый, если есть на складе
                            stockBadge.style.cssText = "background-color: #10b981; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;";
                            stockBadge.textContent = `Склад: остаток ${data.stock}`;
                        } else {
                            // Красный, если нет
                            stockBadge.style.cssText = "background-color: #ef4444; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;";
                            stockBadge.textContent = `Склад: остаток 0`;
                        }
                        wrapper.appendChild(stockBadge);

                        // --- ССЫЛКИ НА ПОСТАВЩИКОВ ---
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
                        console.error("Ошибка получения данных:", err);
                    });
            }, 500);
        });

        // Очистка при удалении артикула
        input.addEventListener("blur", function () {
            if (!input.value.trim()) {
                linkContainer.innerHTML = "";
            }
        });
    });
});