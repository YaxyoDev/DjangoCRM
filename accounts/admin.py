from django.contrib import admin
from .models import (
    PupilProfile,
    TeacherProfile,
    AdminProfile,
    ManagerProfile,
    CashierProfile,
    RegisterProfile,
)


@admin.register(PupilProfile)
class PupilProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "parent_phone_number", "balance", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__full_name", "user__phone", "parent_phone_number"]
    list_per_page = 20
    ordering = ["-created_at"]


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "subject", "salary_percent", "balance", "status", "created_at"]
    list_filter = ["status", "subject"]
    search_fields = ["user__full_name", "user__phone"]
    list_per_page = 20
    ordering = ["-created_at"]


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "salary", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__full_name", "user__phone"]
    list_per_page = 20
    ordering = ["-created_at"]


@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "salary", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__full_name", "user__phone"]
    list_per_page = 20
    ordering = ["-created_at"]


@admin.register(CashierProfile)
class CashierProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "salary", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__full_name", "user__phone"]
    list_per_page = 20
    ordering = ["-created_at"]


@admin.register(RegisterProfile)
class RegisterProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "salary", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__full_name", "user__phone"]
    list_per_page = 20
    ordering = ["-created_at"]