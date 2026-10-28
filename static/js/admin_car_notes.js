document.addEventListener("DOMContentLoaded", function () {
    // 1. ПРОВЕРКА: Работаем только на странице СОЗДАНИЯ заказа
    // Если в URL есть '/change/', значит мы редактируем — выходим.
    if (window.location.pathname.includes('/change/')) {
        console.log("Режим редактирования. Плашка с прошлыми заметками отключена.");
        return;
    }

    console.log("JS для заметок мастера успешно загружен! (Режим создания)");
    const apiUrl = "/crm/api/car-notes/";

    function fetchNotes(carId) {
        if (!carId) {
            const container = document.getElementById("previous-notes-container");
            if (container) container.innerHTML = "";
            return;
        }

        // На странице создания excludeId всегда пустой (текущего заказа еще нет)
        fetch(`${apiUrl}?car_id=${carId}`)
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById("previous-notes-container");
                if (container) {
                    container.innerHTML = data.html;
                    container.style.display = "block";
                    console.log("Заметки вставлены.");
                }
            })
            .catch(err => console.error("ОШИБКА при запросе:", err));
    }

    const carSelect = document.getElementById("id_car");

    if (carSelect) {
        // Создаем контейнер и вставляем его над полем "Автомобиль"
        let container = document.getElementById("previous-notes-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "previous-notes-container";
            container.style.marginBottom = "20px";
            container.style.display = "block";

            const formRow = carSelect.closest('.form-row') || carSelect.closest('div');
            if (formRow && formRow.parentNode) {
                formRow.parentNode.insertBefore(container, formRow);
            }
        }

        // Слушатели
        carSelect.addEventListener("change", function () {
            fetchNotes(this.value);
        });

        if (window.jQuery) {
            jQuery(carSelect).on("select2:select select2:unselect", function () {
                fetchNotes(this.value);
            });
        }

        // Таймер-страховка
        let lastValue = carSelect.value;
        setInterval(function () {
            if (carSelect.value !== lastValue) {
                lastValue = carSelect.value;
                fetchNotes(carSelect.value);
            }
        }, 500);
    }
});