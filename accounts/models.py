from django.db import models
from django.conf import settings


class PupilProfile(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        FROZEN = "frozen", "Muzlatilgan"
        ARCHIVED = "archived", "Arxivlangan"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pupil_profile",
    )
    parent_phone_number = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.full_name


class TeacherProfile(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        ARCHIVED = "archived", "Arxivlangan"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
    )
    salary_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subjects = models.ManyToManyField("education.Course", related_name="teachers", blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.full_name


class AdminProfile(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        INACTIVE = "inactive", "Nofaol"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_profile",
    )
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.full_name


class ManagerProfile(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        INACTIVE = "inactive", "Nofaol"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="manager_profile",
    )
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.full_name


class CashierProfile(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        INACTIVE = "inactive", "Nofaol"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cashier_profile",
    )
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.full_name


class RegisterProfile(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        INACTIVE = "inactive", "Nofaol"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="register_profile",
    )
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.full_name