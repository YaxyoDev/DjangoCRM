from django.urls import path
from .views import (
    teacher_list_view,
    teacher_create_view,
    teacher_edit_view,
    teacher_delete_view,
    staff_list_view,
    staff_create_view,
    staff_edit_view,
    staff_delete_view,
    staff_detail_view,
    pupil_list_view,
    pupil_create_view,
    pupil_edit_view,
    pupil_delete_view,
)

urlpatterns = [
    # O'qituvchilar
    path("teachers/", teacher_list_view, name="teacher_list"),
    path("teachers/create/", teacher_create_view, name="teacher_create"),
    path("teachers/<int:pk>/edit/", teacher_edit_view, name="teacher_edit"),
    path("teachers/<int:pk>/delete/", teacher_delete_view, name="teacher_delete"),

    # Xodimlar
    path("staff/", staff_list_view, name="staff_list"),
    path("staff/create/", staff_create_view, name="staff_create"),
    path("staff/<int:pk>/", staff_detail_view, name="staff_detail"),
    path("staff/<int:pk>/edit/", staff_edit_view, name="staff_edit"),
    path("staff/<int:pk>/delete/", staff_delete_view, name="staff_delete"),

    # O'quvchilar
    path("pupils/", pupil_list_view, name="pupil_list"),
    path("pupils/create/", pupil_create_view, name="pupil_create"),
    path("pupils/<int:pk>/edit/", pupil_edit_view, name="pupil_edit"),
    path("pupils/<int:pk>/delete/", pupil_delete_view, name="pupil_delete"),
]
