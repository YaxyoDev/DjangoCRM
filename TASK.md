# DjangoCRM — O'quv Markazi Boshqaruv Tizimi

Academia O'quv Markazi uchun ichki CRM panel. Django + Templates (1-bosqich).

---

## TEXNIK STACK

- **Backend:** Django
- **Auth:** Custom User model (`phone` orqali login), session-based auth (HTML uchun) + JWT (API uchun, keyin)
- **DB:** SQLite (hozircha)
- **Frontend (1-bosqich):** Django Templates + Bootstrap (hal qilinmoqda)
- **Admin panel:** Jazzmin (o'rnatilgan, ishlayapti)

---

## QABUL QILINGAN ASOSIY QARORLAR

1. **User modeli markaziy.** Har rol uchun alohida profil modeli `OneToOneField` orqali User'ga bog'lanadi (mustaqil modellar EMAS — login buzilmasligi uchun).
2. **`full_name`, `phone` faqat User'da.** Profillarda takrorlanmaydi — `user` orqali olinadi.
3. **Barcha pul maydonlari `DecimalField`** (`FloatField` emas).
4. **Profil faqat rolga xos maydon bo'lsa qilinadi.** Hozir hammasida `salary`/`status` bor, shuning uchun hammasiga profil qilindi.
5. **`on_delete` siyosati:** Group bog'lanishlarida `PROTECT`, Enrollment'da `CASCADE`, Payment'da `PROTECT`/`SET_NULL` (moliyaviy tarix saqlanadi).
6. **Bosqichli reja:**
   - 1-bosqich (HOZIR): Django Templates + oddiy view'lar. To'liq ishlaydigan panel.
   - 2-bosqich: DRF API qatlami (foydalanuvchi buni yaxshi biladi).
   - 3-bosqich: React/Vue frontend (shoshilmasdan, keyin o'rganiladi).
7. **Biznes-mantiqni** (balans yangilash, to'lov qabul qilish) iloji boricha view'dan tashqarida (funksiya/model metod) yozish — keyin API'da qayta ishlatish uchun.

---

## APP TUZILMASI

```
authencation/   -> User
accounts/       -> PupilProfile, TeacherProfile, AdminProfile,
                   ManagerProfile, CashierProfile, RegisterProfile
education/      -> Course, Room, Time, Group, Enrollment, Payment
```

**Holat:** Modellar yozilgan, migration o'tgan, admin panelda hammasi ko'rinadi va ishlayapti.

---

## TEMPLATE PAPKA TUZILMASI (hozirgi)

```
templates/
├── admin/
├── auth/
├── cashier/
├── home/
├── includes/
│   ├── 404.html
│   ├── footer.html
│   └── navbar.html
├── manager/
├── pupil/
├── register/
├── teacher/
└── base.html
```

**OCHIQ SAVOL:** Papkani rol bo'yicha (hozirgi: `manager/pupils.html`) yoki bo'lim bo'yicha (`pupils/list.html`) tashkillashtirish? Tavsiya: bo'lim bo'yicha — takrorni kamaytiradi.

---

## HAL QILINMAGAN SAVOLLAR (keyingi suhbatda hal qilinadi)

1. **CSS:** Bootstrap (tavsiya) yoki o'zimiz yozgan CSS?
2. **Rang/uslub:** oddiy oq fon + ko'k aksent professional panelmi?
3. **Menyu:** bitta panel, rolga qarab menyu bo'limlari ko'rinadi/yashiriladi?
4. **Papka mantiqi:** rol bo'yicha yoki bo'lim bo'yicha?

---

## BAJARILADIGAN ISHLAR (tartib bilan)

### 1. Asos (base + includes)
- [ ] `base.html` — umumiy karkas (header, sidebar, content, messages bloki)
- [ ] `includes/navbar.html` — tepa header
- [ ] `includes/sidebar.html` — chap menyu (rolga qarab bo'limlar)
- [ ] `includes/messages.html` — xato/muvaffaqiyat xabarlari
- [ ] `includes/footer.html`, `includes/404.html` — bor, base'ga ulash

### 2. Authencation
- [ ] Login sahifasini base dizayniga moslash (hozir oddiy ishlaydi)
- [ ] Logout
- [ ] Login'dan keyin rolga qarab to'g'ri dashboard'ga yo'naltirish

### 3. Dashboard (bosh sahifa)
- [ ] Statistika kartalari (o'quvchilar soni, guruhlar, bugungi to'lovlar)
- [ ] Rolga qarab ko'rinish farqi

### 4. Bo'limlar (har biri to'liq CRUD: list + add + edit + detail)
**Eslatma:** Bitta bo'limni TO'LIQ tugatib, keyin keyingisiga o'tish. Yarim-yarim qilmaslik.
- [ ] **Pupils (O'quvchilar)** — birinchi, andoza sifatida to'liq qilinadi
  - [ ] Ro'yxat (HTML → view)
  - [ ] Qo'shish formasi — User + PupilProfile birga, `transaction.atomic()` bilan
  - [ ] Tahrirlash
  - [ ] Ko'rish (detail)
- [ ] **Teachers (O'qituvchilar)** — Pupils andozasida
- [ ] **Groups (Guruhlar)**
- [ ] **Course / Room / Time** — oddiy, tez ketadi
- [ ] **Payments (To'lovlar)** — to'lov qabul qilish + balansni yangilash mantiqi
- [ ] **Staff (Admin/Manager/Cashier/Register)** — eng oxirida (kam ishlatiladi)

---

## MUHIM ESLATMALAR

- **Imlo:** App nomi `authencation` (to'g'risi `authentication`) — hozir tegmaymiz, yangi loyihada e'tibor.
- **Django Group vs education Group:** admin'da ikki "Groups" bor. Biri Django ruxsatlari, biri o'quv guruhi. Chalkashmaslik kerak.
- **O'quvchi qo'shish jarayoni:** bitta formada User maydonlari + profil maydonlari, view ichida avval User (role bilan), keyin Profil — `transaction.atomic()` ichida.
- **Profil yaratish:** asosiy yo'l — view ichida qo'lda (signal emas), chunki profil maydonlari formadan keladi.

---

## KEYINGI SUHBATDA BIRINCHI QADAM

Foydalanuvchi database structure'ini tashlaydi. Shundan keyin:
1. Hal qilinmagan 4 ta savolga javob olinadi (CSS, rang, menyu, papka).
2. `base.html` + includes quriladi.
3. Keyin Authencation → Dashboard → Pupils tartibida davom.
