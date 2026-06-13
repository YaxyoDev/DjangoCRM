from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q, Count, ProtectedError
from django.utils.dateparse import parse_date

from .models import (
    PupilProfile,
    TeacherProfile,
    AdminProfile,
    ManagerProfile,
    CashierProfile,
    RegisterProfile,
)
from education.models import Course, Group

User = get_user_model()


def _can_view_staff(user):
    # o'qituvchilarni ko'rish: barcha xodimlar (teacher va pupildan tashqari)
    return user.role in ("admin", "manager", "cashier", "registrator")


def _can_manage_staff(user):
    # o'qituvchi qo'shish/tahrirlash/o'chirish: faqat admin va manager
    return user.role in ("admin", "manager")


def _teacher_choices():
    return {
        "courses": Course.objects.all(),
        "statuses": TeacherProfile.Status.choices,
    }


def _read_teacher_form(request):
    return {
        "full_name": request.POST.get("full_name", "").strip(),
        "phone": request.POST.get("phone", "").strip(),
        "email": request.POST.get("email", "").strip(),
        "password": request.POST.get("password", ""),
        "salary_percent": request.POST.get("salary_percent", "").strip(),
        "status": request.POST.get("status", "active"),
        "subject": request.POST.get("subject", ""),
    }


def _validate_teacher(f, is_edit, exclude_user_pk=None):
    if not f["full_name"]:
        return "To'liq ismni kiriting"
    if not f["phone"]:
        return "Telefon raqamni kiriting"

    # telefon band emasligini tekshirish
    qs = User.objects.filter(phone=f["phone"])
    if exclude_user_pk:
        qs = qs.exclude(pk=exclude_user_pk)
    if qs.exists():
        return "Bu telefon raqam band"

    # email band emasligini tekshirish (agar kiritilgan bo'lsa)
    if f["email"]:
        qs = User.objects.filter(email=f["email"])
        if exclude_user_pk:
            qs = qs.exclude(pk=exclude_user_pk)
        if qs.exists():
            return "Bu email band"

    # yangi o'qituvchi uchun parol shart
    if not is_edit and not f["password"]:
        return "Parol kiriting"

    # oylik foizi
    try:
        sp = Decimal(f["salary_percent"]) if f["salary_percent"] else Decimal("0")
    except (InvalidOperation, TypeError):
        return "Oylik foizi noto'g'ri kiritilgan"
    if sp < 0 or sp > 100:
        return "Oylik foizi 0 va 100 orasida bo'lishi kerak"

    return None


@login_required(login_url='login')
def teacher_list_view(request):
    if not _can_view_staff(request.user):
        messages.error(request, "Sizda bu bo'limga ruxsat yo'q")
        return redirect("dashboard")

    teachers = TeacherProfile.objects.select_related("user", "subject")

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    course_id = request.GET.get("course", "")

    if q:
        teachers = teachers.filter(Q(user__full_name__icontains=q) | Q(user__phone__icontains=q))
    if status:
        teachers = teachers.filter(status=status)
    if course_id:
        teachers = teachers.filter(subject_id=course_id)

    teachers = teachers.order_by("-created_at")

    return render(request, "teachers/list.html", {
        "teachers": teachers,
        "courses": Course.objects.all(),
        "statuses": TeacherProfile.Status.choices,
        "can_manage": _can_manage_staff(request.user),
        "f": {"q": q, "status": status, "course": course_id},
    })


@login_required(login_url='login')
def teacher_create_view(request):
    if not _can_manage_staff(request.user):
        messages.error(request, "Sizda o'qituvchi qo'shishga ruxsat yo'q")
        return redirect("teacher_list")

    if request.method == "POST":
        f = _read_teacher_form(request)
        error = _validate_teacher(f, is_edit=False)

        if error:
            messages.error(request, error)
            return render(request, "teachers/form.html", {**_teacher_choices(), "f": f})

        # User + TeacherProfile birga yaratiladi (atomik)
        with transaction.atomic():
            user = User.objects.create_user(
                phone=f["phone"],
                password=f["password"],
                full_name=f["full_name"],
                email=f["email"] or None,
                role="teacher",
            )
            if request.FILES.get("avatar"):
                user.avatar = request.FILES["avatar"]
                user.save()

            TeacherProfile.objects.create(
                user=user,
                salary_percent=f["salary_percent"] or 0,
                status=f["status"],
                subject_id=f["subject"] or None,
            )

        messages.success(request, "O'qituvchi qo'shildi")
        return redirect("teacher_list")

    empty = {"full_name": "", "phone": "", "email": "", "password": "",
             "salary_percent": "", "status": "active", "subject": ""}
    return render(request, "teachers/form.html", {**_teacher_choices(), "f": empty})


@login_required(login_url='login')
def teacher_edit_view(request, pk):
    if not _can_manage_staff(request.user):
        messages.error(request, "Sizda o'qituvchini tahrirlashga ruxsat yo'q")
        return redirect("teacher_list")

    profile = get_object_or_404(TeacherProfile.objects.select_related("user"), pk=pk)
    user = profile.user

    if request.method == "POST":
        f = _read_teacher_form(request)
        error = _validate_teacher(f, is_edit=True, exclude_user_pk=user.pk)

        if error:
            messages.error(request, error)
            return render(request, "teachers/form.html", {**_teacher_choices(), "f": f, "is_edit": True, "obj_id": profile.pk, "avatar_url": user.avatar_url, "has_avatar": bool(user.avatar)})

        with transaction.atomic():
            user.full_name = f["full_name"]
            user.phone = f["phone"]
            user.email = f["email"] or None
            # yangi rasm yuklansa almashtiramiz, "o'chirish" belgilansa olib tashlaymiz
            if request.FILES.get("avatar"):
                user.avatar = request.FILES["avatar"]
            elif request.POST.get("remove_avatar") and user.avatar:
                user.avatar.delete(save=False)
            # parolni faqat admin o'zgartira oladi
            if f["password"] and request.user.role == "admin":
                user.set_password(f["password"])
            user.save()

            profile.salary_percent = f["salary_percent"] or 0
            profile.status = f["status"]
            profile.subject_id = f["subject"] or None
            profile.save()

        messages.success(request, "O'qituvchi yangilandi")
        return redirect("teacher_list")

    f = {
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email or "",
        "password": "",
        "salary_percent": profile.salary_percent,
        "status": profile.status,
        "subject": str(profile.subject_id) if profile.subject_id else "",
    }
    return render(request, "teachers/form.html", {**_teacher_choices(), "f": f, "is_edit": True, "obj_id": profile.pk, "avatar_url": user.avatar_url, "has_avatar": bool(user.avatar)})


@login_required(login_url='login')
def teacher_delete_view(request, pk):
    if not _can_manage_staff(request.user):
        messages.error(request, "Sizda o'qituvchini o'chirishga ruxsat yo'q")
        return redirect("teacher_list")

    profile = get_object_or_404(TeacherProfile.objects.select_related("user"), pk=pk)

    if request.method == "POST":
        user = profile.user  # user o'chsa, profil ham CASCADE bilan o'chadi
        try:
            user.delete()
            messages.success(request, "O'qituvchi o'chirildi")
        except ProtectedError:
            messages.error(request, "Bu o'qituvchini o'chirib bo'lmaydi — unga bog'liq guruhlar yoki to'lovlar bor")
        return redirect("teacher_list")

    return redirect("teacher_edit", pk=pk)


# ==================== XODIMLAR ====================

# har bir xodim roli -> o'z profil modeli
ROLE_PROFILE = {
    "admin": AdminProfile,
    "manager": ManagerProfile,
    "cashier": CashierProfile,
    "registrator": RegisterProfile,
}

# rol -> User dagi teskari OneToOne nomi
ROLE_PROFILE_ATTR = {
    "admin": "admin_profile",
    "manager": "manager_profile",
    "cashier": "cashier_profile",
    "registrator": "register_profile",
}

STAFF_STATUS_CHOICES = [("active", "Faol"), ("inactive", "Nofaol")]


def _staff_role_choices(actor=None):
    # xodim rollari (teacher/pupil emas)
    roles = [
        (User.Role.ADMIN.value, User.Role.ADMIN.label),
        (User.Role.MANAGER.value, User.Role.MANAGER.label),
        (User.Role.CASHIER.value, User.Role.CASHIER.label),
        (User.Role.REGISTER.value, User.Role.REGISTER.label),
    ]
    # manager admin rolini tanlay olmaydi
    if actor is not None and actor.role != "admin":
        roles = [r for r in roles if r[0] != User.Role.ADMIN.value]
    return roles


def _can_view_employees(user):
    # xodimlar ro'yxatini ko'rish: admin, manager, cashier, registrator
    return user.role in ("admin", "manager", "cashier", "registrator")


def _can_manage_employees(user):
    # xodim qo'shish/tahrirlash/o'chirish: admin va manager
    return user.role in ("admin", "manager")


def _can_view_employee_detail(user):
    # batafsil ko'rish (ko'zcha icon): faqat admin va manager
    return user.role in ("admin", "manager")


def _can_manage_target_role(actor, target_role):
    # admin hamma rolni boshqaradi, manager admin'dan boshqasini boshqaradi
    if actor.role == "admin":
        return True
    return target_role != "admin"


def _profile_of(user):
    # userning roliga mos profilini qaytaradi (bo'lmasa None)
    attr = ROLE_PROFILE_ATTR.get(user.role)
    if not attr:
        return None
    try:
        return getattr(user, attr)
    except ObjectDoesNotExist:
        return None


def _read_staff_form(request):
    return {
        "full_name": request.POST.get("full_name", "").strip(),
        "phone": request.POST.get("phone", "").strip(),
        "email": request.POST.get("email", "").strip(),
        "password": request.POST.get("password", ""),
        "role": request.POST.get("role", ""),
        "salary": request.POST.get("salary", "").strip(),
        "status": request.POST.get("status", "active"),
    }


def _validate_staff(f, is_edit, exclude_user_pk=None):
    if not f["full_name"]:
        return "To'liq ismni kiriting"
    if not f["phone"]:
        return "Telefon raqamni kiriting"

    qs = User.objects.filter(phone=f["phone"])
    if exclude_user_pk:
        qs = qs.exclude(pk=exclude_user_pk)
    if qs.exists():
        return "Bu telefon raqam band"

    if f["email"]:
        qs = User.objects.filter(email=f["email"])
        if exclude_user_pk:
            qs = qs.exclude(pk=exclude_user_pk)
        if qs.exists():
            return "Bu email band"

    if f["role"] not in ROLE_PROFILE:
        return "Rolni tanlang"

    if not is_edit and not f["password"]:
        return "Parol kiriting"

    try:
        salary = Decimal(f["salary"]) if f["salary"] else Decimal("0")
    except (InvalidOperation, TypeError):
        return "Oylik noto'g'ri kiritilgan"
    if salary < 0:
        return "Oylik manfiy bo'lishi mumkin emas"

    return None


def _staff_form_ctx(f, is_edit=False, obj_id=None, avatar_url=None, has_avatar=False, actor=None):
    return {
        "f": f,
        "roles": _staff_role_choices(actor),
        "statuses": STAFF_STATUS_CHOICES,
        "is_edit": is_edit,
        "obj_id": obj_id,
        "avatar_url": avatar_url,
        "has_avatar": has_avatar,
    }


@login_required(login_url='login')
def staff_list_view(request):
    if not _can_view_employees(request.user):
        messages.error(request, "Sizda bu bo'limga ruxsat yo'q")
        return redirect("dashboard")

    users = User.objects.filter(role__in=ROLE_PROFILE.keys()).select_related(
        "admin_profile", "manager_profile", "cashier_profile", "register_profile"
    )

    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "")
    if q:
        users = users.filter(Q(full_name__icontains=q) | Q(phone__icontains=q))
    if role:
        users = users.filter(role=role)
    users = users.order_by("-date_joined")

    can_manage_all = _can_manage_employees(request.user)

    # har bir user uchun roliga mos profil + uni boshqarish mumkinmi
    staff = [
        {
            "user": u,
            "profile": _profile_of(u),
            "can_manage": can_manage_all and _can_manage_target_role(request.user, u.role),
        }
        for u in users
    ]

    return render(request, "staff/list.html", {
        "staff": staff,
        "roles": _staff_role_choices(),
        "can_manage": can_manage_all,
        "can_view_detail": _can_view_employee_detail(request.user),
        "f": {"q": q, "role": role},
    })


@login_required(login_url='login')
def staff_create_view(request):
    if not _can_manage_employees(request.user):
        messages.error(request, "Sizda xodim qo'shishga ruxsat yo'q")
        return redirect("staff_list")

    if request.method == "POST":
        f = _read_staff_form(request)
        error = _validate_staff(f, is_edit=False)

        # manager admin rolidagi xodim qo'sha olmaydi
        if not error and not _can_manage_target_role(request.user, f["role"]):
            error = "Sizda admin rolidagi xodim qo'shishga ruxsat yo'q"

        if error:
            messages.error(request, error)
            return render(request, "staff/form.html", _staff_form_ctx(f, actor=request.user))

        with transaction.atomic():
            user = User.objects.create_user(
                phone=f["phone"], password=f["password"],
                full_name=f["full_name"], email=f["email"] or None, role=f["role"],
            )
            if request.FILES.get("avatar"):
                user.avatar = request.FILES["avatar"]
                user.save()
            ROLE_PROFILE[f["role"]].objects.create(
                user=user, salary=f["salary"] or 0, status=f["status"],
            )

        messages.success(request, "Xodim qo'shildi")
        return redirect("staff_list")

    empty = {"full_name": "", "phone": "", "email": "", "password": "",
             "role": "", "salary": "", "status": "active"}
    return render(request, "staff/form.html", _staff_form_ctx(empty, actor=request.user))


@login_required(login_url='login')
def staff_edit_view(request, pk):
    if not _can_manage_employees(request.user):
        messages.error(request, "Sizda xodimni tahrirlashga ruxsat yo'q")
        return redirect("staff_list")

    user = get_object_or_404(User, pk=pk, role__in=ROLE_PROFILE.keys())

    # manager admin rolidagi xodimni tahrirlay olmaydi
    if not _can_manage_target_role(request.user, user.role):
        messages.error(request, "Sizda admin rolidagi xodimni tahrirlashga ruxsat yo'q")
        return redirect("staff_list")

    if request.method == "POST":
        f = _read_staff_form(request)
        error = _validate_staff(f, is_edit=True, exclude_user_pk=user.pk)

        # o'z rolini o'zgartira olmaydi (o'zini qulflab qo'ymasligi uchun)
        if not error and user.pk == request.user.pk and f["role"] != user.role:
            error = "O'zingizning rolingizni o'zgartira olmaysiz"

        # manager rolni admin'ga ko'tara olmaydi
        if not error and not _can_manage_target_role(request.user, f["role"]):
            error = "Sizda admin roli berishga ruxsat yo'q"

        if error:
            messages.error(request, error)
            return render(request, "staff/form.html",
                          _staff_form_ctx(f, is_edit=True, obj_id=user.pk,
                                          avatar_url=user.avatar_url, has_avatar=bool(user.avatar),
                                          actor=request.user))

        with transaction.atomic():
            old_role = user.role
            new_role = f["role"]

            user.full_name = f["full_name"]
            user.phone = f["phone"]
            user.email = f["email"] or None
            if request.FILES.get("avatar"):
                user.avatar = request.FILES["avatar"]
            elif request.POST.get("remove_avatar") and user.avatar:
                user.avatar.delete(save=False)
            if f["password"]:
                user.set_password(f["password"])
            user.role = new_role
            user.save()

            if old_role == new_role:
                profile = _profile_of(user)
                if profile:
                    profile.salary = f["salary"] or 0
                    profile.status = f["status"]
                    profile.save()
                else:
                    ROLE_PROFILE[new_role].objects.create(user=user, salary=f["salary"] or 0, status=f["status"])
            else:
                # rol o'zgargan: eski profilni o'chirib, yangisini yaratamiz
                old_profile = ROLE_PROFILE[old_role].objects.filter(user=user).first()
                if old_profile:
                    old_profile.delete()
                ROLE_PROFILE[new_role].objects.create(user=user, salary=f["salary"] or 0, status=f["status"])

        messages.success(request, "Xodim yangilandi")
        return redirect("staff_list")

    profile = _profile_of(user)
    f = {
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email or "",
        "password": "",
        "role": user.role,
        "salary": profile.salary if profile else "",
        "status": profile.status if profile else "active",
    }
    return render(request, "staff/form.html",
                  _staff_form_ctx(f, is_edit=True, obj_id=user.pk,
                                  avatar_url=user.avatar_url, has_avatar=bool(user.avatar),
                                  actor=request.user))


@login_required(login_url='login')
def staff_delete_view(request, pk):
    if not _can_manage_employees(request.user):
        messages.error(request, "Sizda xodimni o'chirishga ruxsat yo'q")
        return redirect("staff_list")

    user = get_object_or_404(User, pk=pk, role__in=ROLE_PROFILE.keys())

    # manager admin rolidagi xodimni o'chira olmaydi
    if not _can_manage_target_role(request.user, user.role):
        messages.error(request, "Sizda admin rolidagi xodimni o'chirishga ruxsat yo'q")
        return redirect("staff_list")

    if request.method == "POST":
        # o'zini o'chira olmasin
        if user.pk == request.user.pk:
            messages.error(request, "O'zingizni o'chira olmaysiz")
            return redirect("staff_list")
        try:
            user.delete()
            messages.success(request, "Xodim o'chirildi")
        except ProtectedError:
            messages.error(request, "Bu xodimni o'chirib bo'lmaydi — unga bog'liq to'lovlar bor")
        return redirect("staff_list")

    return redirect("staff_edit", pk=pk)


@login_required(login_url='login')
def staff_detail_view(request, pk):
    # batafsil ko'rish: faqat admin va manager
    if not _can_view_employee_detail(request.user):
        messages.error(request, "Sizda batafsil ko'rishga ruxsat yo'q")
        return redirect("staff_list")

    user = get_object_or_404(User, pk=pk, role__in=ROLE_PROFILE.keys())
    profile = _profile_of(user)

    return render(request, "staff/detail.html", {
        "obj": user,
        "profile": profile,
        "can_manage": _can_manage_employees(request.user) and _can_manage_target_role(request.user, user.role),
    })


# ==================== O'QUVCHILAR ====================


def _can_view_pupils(user):
    # o'quvchilarni ko'rish: barcha xodim (teacher emas)
    return user.role in ("admin", "manager", "cashier", "registrator")


def _can_manage_pupils(user):
    # o'quvchi qo'shish/tahrirlash/o'chirish: faqat admin va registrator
    return user.role in ("admin", "registrator")


def _read_pupil_form(request):
    return {
        "full_name": request.POST.get("full_name", "").strip(),
        "phone": request.POST.get("phone", "").strip(),
        "email": request.POST.get("email", "").strip(),
        "password": request.POST.get("password", ""),
        "parent_phone_number": request.POST.get("parent_phone_number", "").strip(),
        "birth_date": request.POST.get("birth_date", "").strip(),
        "status": request.POST.get("status", "active"),
    }


def _validate_pupil(f, is_edit, exclude_user_pk=None):
    if not f["full_name"]:
        return "To'liq ismni kiriting"
    if not f["phone"]:
        return "Telefon raqamni kiriting"

    qs = User.objects.filter(phone=f["phone"])
    if exclude_user_pk:
        qs = qs.exclude(pk=exclude_user_pk)
    if qs.exists():
        return "Bu telefon raqam band"

    if f["email"]:
        qs = User.objects.filter(email=f["email"])
        if exclude_user_pk:
            qs = qs.exclude(pk=exclude_user_pk)
        if qs.exists():
            return "Bu email band"

    if not is_edit and not f["password"]:
        return "Parol kiriting"

    # tug'ilgan sana (ixtiyoriy, lekin kiritilsa to'g'ri bo'lsin)
    if f["birth_date"] and parse_date(f["birth_date"]) is None:
        return "Tug'ilgan sana noto'g'ri kiritilgan"

    return None


def _pupil_form_ctx(f, is_edit=False, obj_id=None, avatar_url=None,
                    has_avatar=False, balance=None, enrollments=None, available_groups=None):
    return {
        "f": f,
        "statuses": PupilProfile.Status.choices,
        "is_edit": is_edit,
        "obj_id": obj_id,
        "avatar_url": avatar_url,
        "has_avatar": has_avatar,
        "balance": balance,
        "enrollments": enrollments,
        "available_groups": available_groups,
    }


@login_required(login_url='login')
def pupil_list_view(request):
    if not _can_view_pupils(request.user):
        messages.error(request, "Sizda bu bo'limga ruxsat yo'q")
        return redirect("dashboard")

    pupils = PupilProfile.objects.select_related("user").annotate(
        course_count=Count("enrollments", filter=Q(enrollments__status="active"), distinct=True)
    )

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if q:
        pupils = pupils.filter(Q(user__full_name__icontains=q) | Q(user__phone__icontains=q))
    if status:
        pupils = pupils.filter(status=status)
    pupils = pupils.order_by("-created_at")

    return render(request, "pupils/list.html", {
        "pupils": pupils,
        "statuses": PupilProfile.Status.choices,
        "can_manage": _can_manage_pupils(request.user),
        "f": {"q": q, "status": status},
    })


@login_required(login_url='login')
def pupil_create_view(request):
    if not _can_manage_pupils(request.user):
        messages.error(request, "Sizda o'quvchi qo'shishga ruxsat yo'q")
        return redirect("pupil_list")

    if request.method == "POST":
        f = _read_pupil_form(request)
        error = _validate_pupil(f, is_edit=False)
        if error:
            messages.error(request, error)
            return render(request, "pupils/form.html", _pupil_form_ctx(f))

        with transaction.atomic():
            user = User.objects.create_user(
                phone=f["phone"], password=f["password"],
                full_name=f["full_name"], email=f["email"] or None, role="pupil",
            )
            if request.FILES.get("avatar"):
                user.avatar = request.FILES["avatar"]
                user.save()
            PupilProfile.objects.create(
                user=user,
                parent_phone_number=f["parent_phone_number"],
                birth_date=parse_date(f["birth_date"]) if f["birth_date"] else None,
                status=f["status"],
            )

        messages.success(request, "O'quvchi qo'shildi")
        return redirect("pupil_list")

    empty = {"full_name": "", "phone": "", "email": "", "password": "",
             "parent_phone_number": "", "birth_date": "", "status": "active"}
    return render(request, "pupils/form.html", _pupil_form_ctx(empty))


@login_required(login_url='login')
def pupil_edit_view(request, pk):
    if not _can_manage_pupils(request.user):
        messages.error(request, "Sizda o'quvchini tahrirlashga ruxsat yo'q")
        return redirect("pupil_list")

    profile = get_object_or_404(PupilProfile.objects.select_related("user"), pk=pk)
    user = profile.user
    enrollments = profile.enrollments.select_related("group", "group__course")
    enrolled_group_ids = enrollments.values_list("group_id", flat=True)
    available_groups = (
        Group.objects.select_related("course")
        .exclude(id__in=enrolled_group_ids)
        .order_by("name")
    )

    if request.method == "POST":
        f = _read_pupil_form(request)
        error = _validate_pupil(f, is_edit=True, exclude_user_pk=user.pk)
        if error:
            messages.error(request, error)
            return render(request, "pupils/form.html",
                          _pupil_form_ctx(f, is_edit=True, obj_id=profile.pk,
                                          avatar_url=user.avatar_url, has_avatar=bool(user.avatar),
                                          balance=profile.balance, enrollments=enrollments,
                                          available_groups=available_groups))

        with transaction.atomic():
            user.full_name = f["full_name"]
            user.phone = f["phone"]
            user.email = f["email"] or None
            if request.FILES.get("avatar"):
                user.avatar = request.FILES["avatar"]
            elif request.POST.get("remove_avatar") and user.avatar:
                user.avatar.delete(save=False)
            # parolni faqat admin o'zgartira oladi
            if f["password"] and request.user.role == "admin":
                user.set_password(f["password"])
            user.save()

            profile.parent_phone_number = f["parent_phone_number"]
            profile.birth_date = parse_date(f["birth_date"]) if f["birth_date"] else None
            profile.status = f["status"]
            profile.save()

        messages.success(request, "O'quvchi yangilandi")
        return redirect("pupil_list")

    f = {
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email or "",
        "password": "",
        "parent_phone_number": profile.parent_phone_number,
        "birth_date": profile.birth_date.isoformat() if profile.birth_date else "",
        "status": profile.status,
    }
    return render(request, "pupils/form.html",
                  _pupil_form_ctx(f, is_edit=True, obj_id=profile.pk,
                                  avatar_url=user.avatar_url, has_avatar=bool(user.avatar),
                                  balance=profile.balance, enrollments=enrollments,
                                  available_groups=available_groups))


@login_required(login_url='login')
def pupil_delete_view(request, pk):
    if not _can_manage_pupils(request.user):
        messages.error(request, "Sizda o'quvchini o'chirishga ruxsat yo'q")
        return redirect("pupil_list")

    profile = get_object_or_404(PupilProfile.objects.select_related("user"), pk=pk)

    if request.method == "POST":
        user = profile.user  # user o'chsa, profil CASCADE bilan o'chadi
        try:
            user.delete()
            messages.success(request, "O'quvchi o'chirildi")
        except ProtectedError:
            messages.error(request, "Bu o'quvchini o'chirib bo'lmaydi — unga bog'liq to'lovlar bor")
        return redirect("pupil_list")

    return redirect("pupil_edit", pk=pk)
