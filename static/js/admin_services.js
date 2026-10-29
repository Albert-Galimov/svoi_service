document.addEventListener("DOMContentLoaded", function () {
    console.log("JS для услуг загружен");

    document.addEventListener("change", function (e) {
        if (e.target && e.target.name && e.target.name.endsWith("-service")) {
            const serviceCode = e.target.value;
            const row = e.target.closest("tr");

            if (!serviceCode) return;

            fetch(`/crm/api/service-lookup/?code=${serviceCode}`)
                .then(response => response.json())
                .then(data => {
                    const nameInput = row.querySelector('input[name$="-name"]');
                    const priceInput = row.querySelector('input[name$="-client_price"]');

                    if (serviceCode === "custom_work") {
                        // Если это "Доп. услуга", очищаем поля, чтобы брат вписал свои
                        if (nameInput) {
                            nameInput.value = "";
                            nameInput.focus();
                        }
                        if (priceInput) priceInput.value = "";
                    } else {
                        // Обычная услуга — подставляем название и цену
                        if (nameInput) nameInput.value = data.name;
                        if (priceInput) priceInput.value = data.price;
                    }
                })
                .catch(err => console.error("Ошибка при получении услуги:", err));
        }
    });

        // --- АВТОПОДСТАНОВКА МАСТЕРА ---
    function syncMasters() {
        const mainMasterSelect = document.getElementById("id_master");
        if (!mainMasterSelect) return;
        
        const mainMasterValue = mainMasterSelect.value;
        if (!mainMasterValue) return;

        // Ищем все селекты мастеров в блоке услуг (они заканчиваются на -master)
        // Исключаем главное поле id_master
        const inlineMasterSelects = document.querySelectorAll('select[name$="-master"]:not(#id_master)');

        inlineMasterSelects.forEach(select => {
            // Если в строке услуги мастер еще не выбран, подставляем главного
            if (!select.value) {
                select.value = mainMasterValue;
                // Вызываем событие, чтобы Select2 (красивый выпадающий список) обновился
                if (window.jQuery) {
                    jQuery(select).trigger('change.select2');
                }
            }
        });
    }

    // 1. Подставляем при изменении главного мастера в заказе
    const mainMaster = document.getElementById("id_master");
    if (mainMaster) {
        mainMaster.addEventListener("change", syncMasters);
        if (window.jQuery) {
            jQuery(mainMaster).on("select2:select", syncMasters);
        }
    }

    // 2. Подставляем, когда нажимают "Добавить еще одну услугу"
    // (Django генерирует событие formset:added)
    if (window.jQuery) {
        jQuery(document).on('formset:added', function(event, $row, formsetName) {
            if (formsetName === 'items' || formsetName === 'work') {
                setTimeout(syncMasters, 100);
            }
        });
    }
});