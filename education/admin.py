from django.contrib import admin
from .models import Course, Room, Time, Group, Enrollment, Payment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]
    list_per_page = 20
    ordering = ["-created_at"]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["name"]
    list_per_page = 20
    ordering = ["-created_at"]


@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    list_display = ["days", "time_start", "time_end"]
    list_filter = ["days"]
    list_per_page = 20


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["name", "course", "teacher", "room", "time", "price", "status", "created_at"]
    list_filter = ["status", "course"]
    search_fields = ["name"]
    list_per_page = 20
    ordering = ["-created_at"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["pupil", "group", "status", "joined_at"]
    list_filter = ["status", "group"]
    search_fields = ["pupil__user__full_name", "group__name"]
    list_per_page = 20
    ordering = ["-joined_at"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["pupil", "group", "amount", "cashier", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["pupil__user__full_name", "cashier__full_name"]
    list_per_page = 20
    ordering = ["-created_at"]