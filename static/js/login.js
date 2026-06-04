/* ============================================================
   GrandStudy — Login JS
   ============================================================ */
(function () {
    "use strict";

    const phone = document.getElementById("phone");
    const pass = document.getElementById("password");
    const toggle = document.getElementById("togglePass");

    /* --- floating label uchun: bo'sh placeholder kerak (CSS :not(:placeholder-shown)) --- */
    document.querySelectorAll(".field__input").forEach((el) => {
        el.setAttribute("placeholder", " ");
    });

    /* ============================================================
       TELEFON FORMATLASH
       Format:  94 214 05-51   (9 ta raqam, +998 dan keyin)
       Bloklar: [2] [3] [2]-[2]
       ============================================================ */
    function formatPhone(digits) {
        // faqat raqamlar, maksimum 9 ta
        digits = digits.replace(/\D/g, "").slice(0, 9);

        let out = "";
        if (digits.length > 0) out += digits.slice(0, 2);           // 94
        if (digits.length > 2) out += " " + digits.slice(2, 5);     // 214
        if (digits.length > 5) out += " " + digits.slice(5, 7);     // 05
        if (digits.length > 7) out += "-" + digits.slice(7, 9);     // -51
        return out;
    }

    if (phone) {
        // foydalanuvchi +998 ni yozmaydi — JS faqat keyingi qismni formatlaydi
        phone.addEventListener("input", function () {
            const caretFromEnd = this.value.length - this.selectionStart;
            this.value = formatPhone(this.value);
            // kursorni oxirga yaqin tutib turish
            const pos = this.value.length - caretFromEnd;
            this.setSelectionRange(pos, pos);
            markFilled(this);
        });

        // raqam bo'lmagan tugmalarni bloklamaymiz (navigatsiya uchun), faqat input'da tozalaymiz
        phone.addEventListener("keydown", function (e) {
            const allowed = ["Backspace", "Delete", "ArrowLeft", "ArrowRight", "Tab", "Home", "End"];
            if (allowed.includes(e.key) || e.ctrlKey || e.metaKey) return;
            if (!/[0-9]/.test(e.key)) e.preventDefault();
        });

        // paste'ni ham tozalash
        phone.addEventListener("paste", function (e) {
            e.preventDefault();
            const text = (e.clipboardData || window.clipboardData).getData("text");
            // agar +998 bilan kelsa, uni olib tashlaymiz
            const cleaned = text.replace(/^\+?998/, "");
            this.value = formatPhone(cleaned);
            markFilled(this);
        });
    }

    /* ============================================================
       FLOATING LABEL — is-filled holatini boshqarish
       (autofill yoki dasturiy o'zgarishlar uchun)
       ============================================================ */
    function markFilled(el) {
        const field = el.closest(".field");
        if (!field) return;
        if (el.value.trim() !== "") field.classList.add("is-filled");
        else field.classList.remove("is-filled");
    }

    document.querySelectorAll(".field__input").forEach((el) => {
        markFilled(el);
        el.addEventListener("blur", () => markFilled(el));
        el.addEventListener("change", () => markFilled(el));
    });

    /* ============================================================
       PAROL KO'RSATISH / YASHIRISH
       ============================================================ */
    if (toggle && pass) {
        toggle.addEventListener("click", function () {
            const show = pass.type === "password";
            pass.type = show ? "text" : "password";
            this.classList.toggle("is-shown", show);
            this.setAttribute("aria-label", show ? "Parolni yashirish" : "Parolni ko'rsatish");
            pass.focus();
        });
    }

    /* ============================================================
       SUBMIT — input ko'rinishi O'ZGARMAYDI (94 214 05-51 qoladi).
       Backendga to'liq qiymat yashirin "phone" maydoni orqali boradi.
       Ko'rinadigan input name'i "phone_display" — backend uni o'qimaydi.
       ============================================================ */
    const form = document.querySelector(".form");
    if (form && phone) {
        // ko'rinadigan input backendga ketmasin
        phone.setAttribute("name", "phone_display");

        // yashirin "phone" maydoni — view shuni oladi
        let hidden = form.querySelector('input[name="phone"]');
        if (!hidden) {
            hidden = document.createElement("input");
            hidden.type = "hidden";
            hidden.name = "phone";
            form.appendChild(hidden);
        }

        form.addEventListener("submit", function () {
            const digits = phone.value.replace(/\D/g, "");
            hidden.value = "+998" + digits;   // input o'zi o'zgarmaydi
        });
    }
})();