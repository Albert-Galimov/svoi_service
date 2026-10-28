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
});