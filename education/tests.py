from datetime import time

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import TeacherProfile
from education.models import Course, Room, Time, Group

User = get_user_model()


class RoomConflictTest(TestCase):
    def setUp(self):
        # admin (guruh yaratish huquqiga ega)
        self.admin = User.objects.create_user(
            phone="+998900000000", password="pass12345", full_name="Admin", role="admin",
        )
        self.client.force_login(self.admin)

        teacher_user = User.objects.create_user(
            phone="+998911111111", password="pass12345", full_name="Teacher", role="teacher",
        )
        self.teacher = TeacherProfile.objects.create(user=teacher_user)

        self.course = Course.objects.create(name="Ingliz tili")
        self.room = Room.objects.create(name="1-xona")
        # bir xil kunlar, vaqtlari kesishadi: 10:00-11:00 va 10:50-11:50
        self.time1 = Time.objects.create(days="mo-we-fr", time_start=time(10, 0), time_end=time(11, 0))
        self.time2 = Time.objects.create(days="mo-we-fr", time_start=time(10, 50), time_end=time(11, 50))

        # mavjud faol guruh (1-xona, 10:00-11:00)
        self.existing = Group.objects.create(
            name="Ingliz A", course=self.course, price=100,
            teacher=self.teacher, room=self.room, time=self.time1, status="active",
        )

    def _create_group(self, time_obj, status="active"):
        return self.client.post(reverse("group_create"), {
            "name": "Rus B", "course": self.course.id, "teacher": self.teacher.id,
            "room": self.room.id, "time": time_obj.id, "price": "100", "status": status,
        })

    def test_overlapping_active_group_rejected(self):
        # faol guruh, vaqti kesishadi -> rad etiladi
        self._create_group(self.time2, status="active")
        self.assertFalse(Group.objects.filter(name="Rus B").exists())

    def test_overlapping_inactive_group_allowed(self):
        # nofaol guruh xonani band qilmaydi -> yaratiladi
        self._create_group(self.time2, status="inactive")
        self.assertTrue(Group.objects.filter(name="Rus B").exists())

    def test_inactive_existing_does_not_block(self):
        # mavjud guruh nofaol bo'lsa, xona bo'sh -> yangi faol guruh yaratiladi
        self.existing.status = "inactive"
        self.existing.save()
        self._create_group(self.time2, status="active")
        self.assertTrue(Group.objects.filter(name="Rus B").exists())

    def test_delete_group(self):
        # guruhni o'chirish ishlaydi
        self.client.post(reverse("group_delete", args=[self.existing.pk]))
        self.assertFalse(Group.objects.filter(pk=self.existing.pk).exists())

    def test_activating_into_occupied_slot_rejected(self):
        # nofaol guruhni faollashtirishda xona band bo'lsa -> rad etiladi
        other = Group.objects.create(
            name="Rus B", course=self.course, price=100,
            teacher=self.teacher, room=self.room, time=self.time2, status="inactive",
        )
        self.client.post(reverse("group_edit", args=[other.pk]), {
            "name": "Rus B", "course": self.course.id, "teacher": self.teacher.id,
            "room": self.room.id, "time": self.time2.id, "price": "100", "status": "active",
        })
        other.refresh_from_db()
        # faollasha olmaydi, nofaol qoladi
        self.assertEqual(other.status, "inactive")


class CatalogPermissionTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            phone="+998900000001", password="pass12345", full_name="Admin", role="admin",
        )
        self.cashier = User.objects.create_user(
            phone="+998900000002", password="pass12345", full_name="Cashier", role="cashier",
        )
        self.teacher = User.objects.create_user(
            phone="+998900000003", password="pass12345", full_name="Teacher", role="teacher",
        )

    def test_admin_can_create_course(self):
        # admin to'liq huquqli
        self.client.force_login(self.admin)
        self.client.post(reverse("course_create"), {"name": "Matematika"})
        self.assertTrue(Course.objects.filter(name="Matematika").exists())

    def test_cashier_cannot_create_course(self):
        # cashier faqat ko'ra oladi, yarata olmaydi
        self.client.force_login(self.cashier)
        self.client.post(reverse("course_create"), {"name": "Fizika"})
        self.assertFalse(Course.objects.filter(name="Fizika").exists())

    def test_cashier_can_view_course_list(self):
        # cashier ro'yxatni ko'ra oladi
        self.client.force_login(self.cashier)
        response = self.client.get(reverse("course_list"))
        self.assertEqual(response.status_code, 200)

    def test_teacher_cannot_view_course_list(self):
        # teacher uchun bu bo'lim umuman yo'q -> dashboard'ga yo'naltiriladi
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("course_list"))
        self.assertRedirects(response, reverse("dashboard"))


class TimeDuplicateTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            phone="+998900000004", password="pass12345", full_name="Admin", role="admin",
        )
        self.client.force_login(self.admin)
        Time.objects.create(days="mo-we-fr", time_start="10:00", time_end="11:00")

    def test_duplicate_time_rejected(self):
        # xuddi shu kun + vaqt qayta yaratilmaydi
        self.client.post(reverse("time_create"), {
            "days": "mo-we-fr", "time_start": "10:00", "time_end": "11:00",
        })
        self.assertEqual(Time.objects.filter(days="mo-we-fr", time_start="10:00", time_end="11:00").count(), 1)

    def test_different_time_allowed(self):
        # boshqa vaqt yaratilaveradi
        self.client.post(reverse("time_create"), {
            "days": "mo-we-fr", "time_start": "11:00", "time_end": "12:00",
        })
        self.assertTrue(Time.objects.filter(days="mo-we-fr", time_start="11:00", time_end="12:00").exists())
