from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import TeacherProfile, CashierProfile, ManagerProfile

User = get_user_model()


class TeacherModuleTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            phone="+998901112233", password="pass12345", full_name="Admin", role="admin",
        )
        self.cashier = User.objects.create_user(
            phone="+998904445566", password="pass12345", full_name="Cashier", role="cashier",
        )

    def test_admin_creates_teacher(self):
        # admin o'qituvchi qo'shadi -> User(role=teacher) + TeacherProfile yaratiladi
        self.client.force_login(self.admin)
        self.client.post(reverse("teacher_create"), {
            "full_name": "Ali Valiyev", "phone": "+998901234567", "email": "",
            "password": "teachpass1", "salary_percent": "50", "status": "active",
        })
        user = User.objects.filter(phone="+998901234567").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, "teacher")
        self.assertTrue(TeacherProfile.objects.filter(user=user).exists())

    def test_cashier_cannot_create_teacher(self):
        # cashier faqat ko'ra oladi, qo'sha olmaydi
        self.client.force_login(self.cashier)
        self.client.post(reverse("teacher_create"), {
            "full_name": "X", "phone": "+998900000099", "password": "x12345678",
            "salary_percent": "10", "status": "active",
        })
        self.assertFalse(User.objects.filter(phone="+998900000099").exists())

    def test_cashier_can_view_teacher_list(self):
        self.client.force_login(self.cashier)
        response = self.client.get(reverse("teacher_list"))
        self.assertEqual(response.status_code, 200)

    def test_teacher_role_cannot_view_list(self):
        # teacher uchun bu bo'lim umuman yo'q -> dashboard'ga yo'naltiriladi
        teacher = User.objects.create_user(
            phone="+998905556677", password="pass12345", full_name="T", role="teacher",
        )
        self.client.force_login(teacher)
        response = self.client.get(reverse("teacher_list"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_duplicate_phone_rejected(self):
        # band telefon bilan o'qituvchi yaratilmaydi
        self.client.force_login(self.admin)
        self.client.post(reverse("teacher_create"), {
            "full_name": "Dup", "phone": "+998901112233", "password": "pass12345",
            "salary_percent": "10", "status": "active",
        })
        self.assertFalse(TeacherProfile.objects.filter(user__phone="+998901112233").exists())


class TeacherPasswordPermissionTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            phone="+998901112200", password="pass12345", full_name="Admin", role="admin",
        )
        self.manager = User.objects.create_user(
            phone="+998901112201", password="pass12345", full_name="Manager", role="manager",
        )
        # tahrirlanadigan o'qituvchi (boshlang'ich parol: oldpass123)
        self.teacher_user = User.objects.create_user(
            phone="+998901112202", password="oldpass123", full_name="Teacher", role="teacher",
        )
        self.profile = TeacherProfile.objects.create(user=self.teacher_user, status="active")

    def _edit_payload(self, password):
        return {
            "full_name": "Teacher", "phone": "+998901112202", "email": "",
            "password": password, "salary_percent": "10", "status": "active", "subject": "",
        }

    def test_manager_cannot_change_password(self):
        # manager tahrirlaydi, parol yuboradi -> parol o'zgarmaydi
        self.client.force_login(self.manager)
        self.client.post(reverse("teacher_edit", args=[self.profile.pk]), self._edit_payload("newpass999"))
        self.teacher_user.refresh_from_db()
        self.assertTrue(self.teacher_user.check_password("oldpass123"))
        self.assertFalse(self.teacher_user.check_password("newpass999"))

    def test_admin_can_change_password(self):
        # admin parolni o'zgartira oladi
        self.client.force_login(self.admin)
        self.client.post(reverse("teacher_edit", args=[self.profile.pk]), self._edit_payload("newpass999"))
        self.teacher_user.refresh_from_db()
        self.assertTrue(self.teacher_user.check_password("newpass999"))


class StaffModuleTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            phone="+998930000001", password="pass12345", full_name="Admin", role="admin",
        )
        self.manager = User.objects.create_user(
            phone="+998930000002", password="pass12345", full_name="Manager", role="manager",
        )
        self.registrator = User.objects.create_user(
            phone="+998930000003", password="pass12345", full_name="Reg", role="registrator",
        )

    def test_admin_creates_cashier(self):
        # admin kassir qo'shadi -> User(role=cashier) + CashierProfile
        self.client.force_login(self.admin)
        self.client.post(reverse("staff_create"), {
            "full_name": "Kassir K", "phone": "+998930000010", "email": "",
            "password": "cashpass1", "role": "cashier", "salary": "2000000", "status": "active",
        })
        user = User.objects.filter(phone="+998930000010").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, "cashier")
        self.assertTrue(CashierProfile.objects.filter(user=user).exists())

    def test_manager_cannot_create_staff(self):
        # manager faqat ko'ra oladi, qo'sha olmaydi
        self.client.force_login(self.manager)
        self.client.post(reverse("staff_create"), {
            "full_name": "X", "phone": "+998930000011", "password": "x12345678",
            "role": "cashier", "salary": "1", "status": "active",
        })
        self.assertFalse(User.objects.filter(phone="+998930000011").exists())

    def test_manager_can_view_staff_list(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("staff_list"))
        self.assertEqual(response.status_code, 200)

    def test_registrator_cannot_view_staff_list(self):
        # registrator uchun bo'lim umuman yo'q -> dashboard'ga
        self.client.force_login(self.registrator)
        response = self.client.get(reverse("staff_list"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_role_change_swaps_profile(self):
        # kassirni menejerga o'zgartirsa: CashierProfile o'chadi, ManagerProfile yaratiladi
        cashier = User.objects.create_user(
            phone="+998930000020", password="pass12345", full_name="C", role="cashier",
        )
        CashierProfile.objects.create(user=cashier, salary=1000000, status="active")

        self.client.force_login(self.admin)
        self.client.post(reverse("staff_edit", args=[cashier.pk]), {
            "full_name": "C", "phone": "+998930000020", "email": "",
            "password": "", "role": "manager", "salary": "1500000", "status": "active",
        })
        cashier.refresh_from_db()
        self.assertEqual(cashier.role, "manager")
        self.assertFalse(CashierProfile.objects.filter(user=cashier).exists())
        self.assertTrue(ManagerProfile.objects.filter(user=cashier).exists())

    def test_admin_cannot_delete_self(self):
        # admin o'zini o'chira olmaydi
        self.client.force_login(self.admin)
        self.client.post(reverse("staff_delete", args=[self.admin.pk]))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
