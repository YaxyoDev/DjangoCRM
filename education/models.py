from django.db import models
from django.conf import settings


class Course(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        INACTIVE = "inactive", "Nofaol"

    name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Time(models.Model):
    class Days(models.TextChoices):
        MWF = "mo-we-fr", "Du-Cho-Ju"
        TTS = "tu-th-sa", "Se-Pay-Sha"
        WEEKEND = "sa-su", "Sha-Yak"

    days = models.CharField(max_length=10, choices=Days.choices)
    time_start = models.TimeField()
    time_end = models.TimeField()

    def __str__(self):
        return f"{self.get_days_display()} ({self.time_start} - {self.time_end})"


class Group(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        INACTIVE = "inactive", "Nofaol"

    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="groups")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    teacher = models.ForeignKey("accounts.TeacherProfile", on_delete=models.PROTECT, related_name="groups")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="groups")
    time = models.ForeignKey(Time, on_delete=models.PROTECT, related_name="groups")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Faol"
        FROZEN = "frozen", "Muzlatilgan"
        LEFT = "left", "Chiqib ketgan"

    pupil = models.ForeignKey("accounts.PupilProfile", on_delete=models.CASCADE, related_name="enrollments")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["pupil", "group"]

    def __str__(self):
        return f"{self.pupil.user.full_name} -> {self.group.name}"


class Payment(models.Model):
    pupil = models.ForeignKey("accounts.PupilProfile", on_delete=models.PROTECT, related_name="payments")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="received_payments")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pupil.user.full_name} - {self.amount}"