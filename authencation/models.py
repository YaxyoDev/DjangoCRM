from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Telefon raqam kiritilishi shart")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        UNKNOWN = 'unknown', 'Belgilanmagan'
        TEACHER = "teacher", "O'qituvchi" 
        PUPIL = "pupil", "O'quvchi"
        ADMIN = "admin", "Admin" # barcha huquqga ega superadmin
        MANAGER = "manager", "Menejer" # 1) o'qituvchilar va o'quvchilar ni register qiladi. 2) guruhlar yaratadi 3) kurslar yaratadi. 4) Xona nazorati 
        CASHIER = "cashier", "Kassir" # faqat oylik tulovlar bilan ishlaydi
        REGISTER = "registrator", "Registrator" # faqat o'quvchilarni register qiladi

    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True, unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.UNKNOWN,
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_pupil(self):
        return self.role == self.Role.PUPIL
    
    @property
    def is_teacher(self):
        return self.role == self.Role.PUPIL
    
    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER
    
    @property
    def is_cashier(self):
        return self.role == self.Role.CASHIER
    
    @property
    def is_registrator(self):
        return self.role == self.Role.REGISTER
    
    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.full_name