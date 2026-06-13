from django.urls import path
from .views import (
    group_list_view,
    group_create_view,
    group_edit_view,
    group_delete_view,
    course_list_view,
    course_create_view,
    course_edit_view,
    course_delete_view,
    room_list_view,
    room_create_view,
    room_edit_view,
    room_delete_view,
    time_list_view,
    time_create_view,
    time_edit_view,
    time_delete_view,
    statistics_view,
    group_detail_view,
    enrollment_create_view,
    enrollment_delete_view,
)

urlpatterns = [
    # Guruhlar
    path("groups/", group_list_view, name="group_list"),
    path("groups/create/", group_create_view, name="group_create"),
    path("groups/<int:pk>/", group_detail_view, name="group_detail"),
    path("groups/<int:pk>/edit/", group_edit_view, name="group_edit"),
    path("groups/<int:pk>/delete/", group_delete_view, name="group_delete"),

    # O'quvchini guruhga biriktirish
    path("enrollments/create/", enrollment_create_view, name="enrollment_create"),
    path("enrollments/<int:pk>/delete/", enrollment_delete_view, name="enrollment_delete"),

    # Kurslar
    path("courses/", course_list_view, name="course_list"),
    path("courses/create/", course_create_view, name="course_create"),
    path("courses/<int:pk>/edit/", course_edit_view, name="course_edit"),
    path("courses/<int:pk>/delete/", course_delete_view, name="course_delete"),

    # Xonalar
    path("rooms/", room_list_view, name="room_list"),
    path("rooms/create/", room_create_view, name="room_create"),
    path("rooms/<int:pk>/edit/", room_edit_view, name="room_edit"),
    path("rooms/<int:pk>/delete/", room_delete_view, name="room_delete"),

    # Vaqtlar
    path("times/", time_list_view, name="time_list"),
    path("times/create/", time_create_view, name="time_create"),
    path("times/<int:pk>/edit/", time_edit_view, name="time_edit"),
    path("times/<int:pk>/delete/", time_delete_view, name="time_delete"),

    # Statistika / Kassa
    path("statistics/", statistics_view, name="statistics"),
]
