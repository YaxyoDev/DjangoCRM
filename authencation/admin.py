from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["full_name", "phone", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["full_name", "phone", "email"]
    list_per_page = 20
    ordering = ["-date_joined"]

    fields = ["full_name", "phone", "email", "role", "is_active", "is_staff"]
