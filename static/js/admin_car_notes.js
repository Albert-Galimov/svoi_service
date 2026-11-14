/**
 * При выборе автомобиля в заказ-наряде:
 *   - показывает прошлые рекомендации мастера;
 *   - показывает VIN и госномер авто (read-only, клик = копирование).
 */

document.addEventListener("DOMContentLoaded", function () {
    console.log("JS для заметок и VIN загружен");
    const apiUrl = "/crm/api/car-notes/";

    function getExcludeId() {
        const m = window.location.pathname.match(/workorder\/(\d+)\/change/);
        return m ? m[1] : "";
    }

    // ---------- копирование в буфер ----------

    function showToast(message) {
        const toast = document.createElement("div");
        toast.textContent = message;
        toast.style.cssText =
            "position:fixed;bottom:20px;right:20px;background:#10b981;color:#fff;" +
            "padding:10px 18px;border-radius:6px;font-size:14px;z-index:99999;" +
            "box-shadow:0 4px 12px rgba(0,0,0,.15);opacity:0;transition:opacity .2s;";
        document.body.appendChild(toast);
        requestAnimationFrame(function () { toast.style.opacity = "1"; });
        setTimeout(function () {
            toast.style.opacity = "0";
            setTimeout(function () { toast.remove(); }, 250);
        }, 1500);
    }

    function fallbackCopy(text, done) {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        try {
            document.execCommand("copy");
            done();
        } catch (err) {
            console.error("fallback copy error:", err);
        } finally {
            document.body.removeChild(ta);
        }
    }

    function copyToClipboard(text, label) {
        function done() { showToast(label + " скопирован"); }
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(done).catch(function (err) {
                console.error("clipboard error:", err);
                fallbackCopy(text, done);
            });
        } else {
            fallbackCopy(text, done);
        }
    }

    // ---------- отображение VIN и номера ----------

    function buildCopyLine(label, value) {
        const wrap = document.createElement("span");
        wrap.style.display = "inline-block";
        wrap.style.marginRight = "24px"; // Отступ между VIN и Госномером
        wrap.style.marginBottom = "4px";

        const strong = document.createElement("strong");
        strong.textContent = label + ": ";
        wrap.appendChild(strong);

        const link = document.createElement("span");
        link.textContent = value;
        link.style.cssText =
            "cursor:pointer;color:#e87722;text-decoration:underline;" +
            "font-family:monospace;font-size:14px;font-weight:600;";
        link.title = "Нажмите, чтобы скопировать";
        link.addEventListener("click", function () {
            copyToClipboard(value, label);
        });
        wrap.appendChild(link);

        return wrap;
    }

    function renderCarInfo(carSelect, data) {
        if (!carSelect) return;

        let container = document.getElementById("car-info-block");
        if (!container) {
            container = document.createElement("div");
            container.id = "car-info-block";
            container.style.marginTop = "8px";
            container.style.fontSize = "14px";
            container.style.display = "block";
            container.style.width = "100%";
            
            // Вставляем блок СТРОГО ПОД выпадающим списком Select2
            const widgetWrapper = carSelect.closest(".related-widget-wrapper") || carSelect.parentNode;
            if (widgetWrapper && widgetWrapper.parentNode) {
                widgetWrapper.parentNode.insertBefore(container, widgetWrapper.nextSibling);
            }
        }

        container.innerHTML = "";

        if (!data.vin && !data.plate) {
            container.style.display = "none";
            return;
        }
        container.style.display = "block";

        if (data.vin) {
            container.appendChild(buildCopyLine("VIN", data.vin));
        }
        if (data.plate) {
            container.appendChild(buildCopyLine("Госномер", data.plate));
        }
    }

    // ---------- загрузка данных авто ----------

    function fetchCarData(carId) {
        const container = document.getElementById("previous-notes-container");
        const carSelect = document.getElementById("id_car");

        if (!carId) {
            if (container) container.innerHTML = "";
            renderCarInfo(carSelect, { vin: "", plate: "" });
            return;
        }

        const excludeId = getExcludeId();

        fetch(`${apiUrl}?car_id=${carId}&exclude_id=${excludeId}`)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                // 1. Заметки
                if (container) container.innerHTML = data.html || "";

                // 2. VIN и госномер
                renderCarInfo(carSelect, data);
            })
            .catch(function (err) { console.error("ОШИБКА:", err); });
    }

    // ---------- инициализация ----------

    // Контейнер для заметок
    let notesContainer = document.getElementById("previous-notes-container");
    if (!notesContainer) {
        notesContainer = document.createElement("div");
        notesContainer.id = "previous-notes-container";
        notesContainer.style.marginBottom = "20px";
        
        const form =
            document.getElementById("workorder_form") ||
            document.querySelector("form.change-form") ||
            document.querySelector("#content form") ||
            document.querySelector("form");
        if (form) form.insertBefore(notesContainer, form.firstChild);
    }

    const carSelect = document.getElementById("id_car");
    if (carSelect) {
        // Нативный change
        carSelect.addEventListener("change", function () {
            fetchCarData(this.value);
        });

        // Select2
        const $ = (window.django && window.django.jQuery) || window.jQuery;
        if ($) {
            $(carSelect).on("select2:select select2:unselect", function () {
                fetchCarData(this.value);
            });
        }

        // Страховка: polling
        let lastValue = carSelect.value;
        setInterval(function () {
            if (carSelect.value !== lastValue) {
                lastValue = carSelect.value;
                fetchCarData(carSelect.value);
            }
        }, 500);

        // Если заказ открыт на редактирование — сразу грузим данные
        if (carSelect.value) {
            fetchCarData(carSelect.value);
        }
    }
});