from django.contrib import admin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["avatar_tag", "full_name", "phone", "role", "is_active", "date_joined"]
    list_display_links = ["avatar_tag", "full_name"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["full_name", "phone", "email"]
    list_per_page = 20
    ordering = ["-date_joined"]

    fields = ["avatar", "full_name", "phone", "email", "role", "is_active", "is_staff"]

    @admin.display(description="Avatar")
    def avatar_tag(self, obj):
        # ro'yxatda kichik dumaloq avatar ko'rsatish
        return format_html(
            '<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;">',
            obj.avatar_url,
        )
