from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q, Count, Sum, ProtectedError
from django.utils import timezone
from django.utils.dateparse import parse_time

from .models import Course, Room, Time, Group, Enrollment, Payment, SalaryPayment
from accounts.models import TeacherProfile, PupilProfile

User = get_user_model()


def _can_manage_groups(user):
    # guruh yaratish/tahrirlash faqat admin va manager uchun
    return user.role in ("admin", "manager")


def _can_view_catalog(user):
    # kurs/xona/vaqt bo'limlarini ko'rish: admin, manager, cashier, registrator
    return user.role in ("admin", "manager", "cashier", "registrator")


def _can_manage_catalog(user):
    # kurs/xona/vaqt yaratish/tahrirlash/o'chirish: faqat admin va manager
    return user.role in ("admin", "manager")


def _group_choices():
    # forma dropdownlari uchun ma'lumotlar
    return {
        "courses": Course.objects.all(),
        "teachers": TeacherProfile.objects.select_related("user").all(),
        "rooms": Room.objects.all(),
        "times": Time.objects.all(),
        "statuses": Group.Status.choices,
    }


def _read_group_form(request):
    # POST'dan guruh maydonlarini o'qish
    return {
        "name": request.POST.get("name", "").strip(),
        "course": request.POST.get("course", ""),
        "teacher": request.POST.get("teacher", ""),
        "room": request.POST.get("room", ""),
        "time": request.POST.get("time", ""),
        "price": request.POST.get("price", "").strip(),
        "status": request.POST.get("status", "active"),
    }


def _validate_group(f):
    # xato bo'lsa matn, bo'lmasa None qaytaradi
    if not f["name"]:
        return "Guruh nomini kiriting"
    if not f["course"]:
        return "Kursni tanlang"
    if not f["teacher"]:
        return "O'qituvchini tanlang"
    if not f["room"]:
        return "Xonani tanlang"
    if not f["time"]:
        return "Kun va vaqtni tanlang"
    try:
        price = Decimal(f["price"])
    except (InvalidOperation, TypeError):
        return "Narx noto'g'ri kiritilgan"
    if price < 0:
        return "Narx manfiy bo'lishi mumkin emas"
    return None


# har bir "days" qiymati qaysi hafta kunlarini qamrab olishi
# diqqat: "tu-th-sa" va "sa-su" ikkalasida ham shanba (sa) bor — ular kesishadi
DAY_TOKENS = {
    "mo-we-fr": {"mo", "we", "fr"},
    "tu-th-sa": {"tu", "th", "sa"},
    "sa-su": {"sa", "su"},
}


def _days_overlap(days_a, days_b):
    # ikki jadval kunlari umumiy kunga ega bo'lsa True
    return bool(DAY_TOKENS.get(days_a, set()) & DAY_TOKENS.get(days_b, set()))


def _find_room_conflict(room_id, time_id, exclude_pk=None):
    # shu xona+vaqtda dars qiladigan boshqa FAOL guruhni qaytaradi (bo'lmasa None)
    # nofaol guruhlar xonani band qilmaydi
    try:
        new_time = Time.objects.get(pk=time_id)
    except Time.DoesNotExist:
        return None

    qs = Group.objects.filter(room_id=room_id, status="active").select_related("time")
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)

    for group in qs:
        t = group.time
        # kunlar kesishmasa, konflikt yo'q
        if not _days_overlap(new_time.days, t.days):
            continue
        # vaqt oralig'i kesishadimi: start1 < end2 va start2 < end1
        if new_time.time_start < t.time_end and t.time_start < new_time.time_end:
            return group
    return None


@login_required(login_url='login')
def group_list_view(request):
    user = request.user

    # pupil bu bo'limni ko'ra olmaydi
    if user.role == "pupil":
        messages.error(request, "Sizda bu bo'limga ruxsat yo'q")
        return redirect("dashboard")

    groups = Group.objects.select_related(
        "course", "teacher__user", "room", "time"
    ).annotate(pupils_count=Count("enrollments"))

    # teacher faqat o'z guruhlarini ko'radi
    if user.role == "teacher":
        groups = groups.filter(teacher__user=user)

    # --- filtrlar ---
    q = request.GET.get("q", "").strip()
    course_id = request.GET.get("course", "")
    teacher_id = request.GET.get("teacher", "")
    room_id = request.GET.get("room", "")
    day = request.GET.get("day", "")
    status = request.GET.get("status", "")

    if q:
        groups = groups.filter(name__icontains=q)
    if course_id:
        groups = groups.filter(course_id=course_id)
    if teacher_id and user.role != "teacher":
        groups = groups.filter(teacher_id=teacher_id)
    if room_id:
        groups = groups.filter(room_id=room_id)
    if day:
        groups = groups.filter(time__days=day)
    if status:
        groups = groups.filter(status=status)

    groups = groups.order_by("-created_at")

    context = {
        "groups": groups,
        "courses": Course.objects.all(),
        "teachers": TeacherProfile.objects.select_related("user").all(),
        "rooms": Room.objects.all(),
        "days": Time.Days.choices,
        "statuses": Group.Status.choices,
        "can_manage": _can_manage_groups(user),
        # tanlangan filtr qiymatlarini formada saqlash uchun
        "f": {
            "q": q,
            "course": course_id,
            "teacher": teacher_id,
            "room": room_id,
            "day": day,
            "status": status,
        },
    }
    return render(request, "groups/list.html", context)


@login_required(login_url='login')
def group_create_view(request):
    if not _can_manage_groups(request.user):
        messages.error(request, "Sizda guruh yaratishga ruxsat yo'q")
        return redirect("group_list")

    if request.method == "POST":
        f = _read_group_form(request)
        error = _validate_group(f)

        # xona band emasligini tekshirish — faqat yangi guruh faol bo'lsa
        if not error and f["status"] == "active":
            conflict = _find_room_conflict(f["room"], f["time"])
            if conflict:
                error = f"Bu xona band: «{conflict.name}» guruhi shu vaqtda dars qiladi ({conflict.time})"

        if error:
            messages.error(request, error)
        else:
            Group.objects.create(
                name=f["name"],
                course_id=f["course"],
                teacher_id=f["teacher"],
                room_id=f["room"],
                time_id=f["time"],
                price=f["price"],
                status=f["status"],
            )
            messages.success(request, "Guruh yaratildi")
            return redirect("group_list")

        # xato bo'lsa kiritilgan qiymatlar bilan qayta ko'rsatamiz
        return render(request, "groups/form.html", {**_group_choices(), "f": f})

    # bo'sh forma (status default "active")
    f = {"name": "", "course": "", "teacher": "", "room": "", "time": "", "price": "", "status": "active"}
    return render(request, "groups/form.html", {**_group_choices(), "f": f})


@login_required(login_url='login')
def group_edit_view(request, pk):
    if not _can_manage_groups(request.user):
        messages.error(request, "Sizda guruhni tahrirlashga ruxsat yo'q")
        return redirect("group_list")

    group = get_object_or_404(Group, pk=pk)

    if request.method == "POST":
        f = _read_group_form(request)
        error = _validate_group(f)

        # xona band emasligini tekshirish — faqat guruh faol bo'lsa (o'zidan tashqari)
        if not error and f["status"] == "active":
            conflict = _find_room_conflict(f["room"], f["time"], exclude_pk=group.pk)
            if conflict:
                error = f"Bu xona band: «{conflict.name}» guruhi shu vaqtda dars qiladi ({conflict.time})"

        if error:
            messages.error(request, error)
            return render(request, "groups/form.html", {**_group_choices(), "f": f, "is_edit": True, "group_id": group.pk})

        group.name = f["name"]
        group.course_id = f["course"]
        group.teacher_id = f["teacher"]
        group.room_id = f["room"]
        group.time_id = f["time"]
        group.price = f["price"]
        group.status = f["status"]
        group.save()
        messages.success(request, "Guruh yangilandi")
        return redirect("group_list")

    # mavjud guruh qiymatlari bilan forma
    f = {
        "name": group.name,
        "course": str(group.course_id),
        "teacher": str(group.teacher_id),
        "room": str(group.room_id),
        "time": str(group.time_id),
        "price": group.price,
        "status": group.status,
    }
    return render(request, "groups/form.html", {**_group_choices(), "f": f, "is_edit": True, "group_id": group.pk})


@login_required(login_url='login')
def group_delete_view(request, pk):
    if not _can_manage_groups(request.user):
        messages.error(request, "Sizda guruhni o'chirishga ruxsat yo'q")
        return redirect("group_list")

    group = get_object_or_404(Group, pk=pk)

    if request.method == "POST":
        group.delete()
        messages.success(request, "Guruh o'chirildi")
        return redirect("group_list")

    # to'g'ridan-to'g'ri ochilsa, tahrirlash sahifasiga qaytaramiz
    return redirect("group_edit", pk=pk)


# ==================== KURSLAR ====================

@login_required(login_url='login')
def course_list_view(request):
    if not _can_view_catalog(request.user):
        messages.error(request, "Sizda bu bo'limga ruxsat yo'q")
        return redirect("dashboard")

    courses = Course.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        courses = courses.filter(name__icontains=q)
    courses = courses.order_by("-created_at")

    return render(request, "courses/list.html", {
        "courses": courses,
        "can_manage": _can_manage_catalog(request.user),
        "f": {"q": q},
    })


@login_required(login_url='login')
def course_create_view(request):
    if not _can_manage_catalog(request.user):
        messages.error(request, "Sizda kurs yaratishga ruxsat yo'q")
        return redirect("course_list")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Kurs nomini kiriting")
            return render(request, "courses/form.html", {"f": {"name": name}})
        Course.objects.create(name=name)
        messages.success(request, "Kurs yaratildi")
        return redirect("course_list")

    return render(request, "courses/form.html", {"f": {"name": ""}})


@login_required(login_url='login')
def course_edit_view(request, pk):
    if not _can_manage_catalog(request.user):
        messages.error(request, "Sizda kursni tahrirlashga ruxsat yo'q")
        return redirect("course_list")

    course = get_object_or_404(Course, pk=pk)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Kurs nomini kiriting")
            return render(request, "courses/form.html", {"f": {"name": name}, "is_edit": True, "obj_id": course.pk})
        course.name = name
        course.save()
        messages.success(request, "Kurs yangilandi")
        return redirect("course_list")

    return render(request, "courses/form.html", {"f": {"name": course.name}, "is_edit": True, "obj_id": course.pk})


@login_required(login_url='login')
def course_delete_view(request, pk):
    if not _can_manage_catalog(request.user):
        messages.error(request, "Sizda kursni o'chirishga ruxsat yo'q")
        return redirect("course_list")

    course = get_object_or_404(Course, pk=pk)

    if request.method == "POST":
        try:
            course.delete()
            messages.success(request, "Kurs o'chirildi")
        except ProtectedError:
            messages.error(request, "Bu kursni o'chirib bo'lmaydi — unga bog'liq guruhlar bor")
        return redirect("course_list")

    return redirect("course_edit", pk=pk)


# ==================== XONALAR ====================

@login_required(login_url='login')
def room_list_view(request):
    if not _can_view_catalog(request.user):
        messages.error(request, "Sizda bu bo'limga ruxsat yo'q")
        return redirect("dashboard")

    rooms = Room.objects.all()
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if q:
        rooms = rooms.filter(name__icontains=q)
    if status:
        rooms = rooms.filter(status=status)
    rooms = rooms.order_by("-created_at")

    return render(request, "rooms/list.html", {
        "rooms": rooms,
        "statuses": Room.Status.choices,
        "can_manage": _can_manage_catalog(request.user),
        "f": {"q": q, "status": status},
    })


@login_required(login_url='login')
def room_create_view(request):
    if not _can_manage_catalog(request.user):
        messages.error(request, "Sizda xona yaratishga ruxsat yo'q")
        return redirect("room_list")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        status = request.POST.get("status", "active")
        if not name:
            messages.error(request, "Xona nomini kiriting")
            return render(request, "rooms/form.html", {"f": {"name": name, "status": status}, "statuses": Room.Status.choices})
        Room.objects.create(name=name, status=status)
        messages.success(request, "Xona yaratildi")
        return redirect("room_list")

    return render(request, "rooms/form.html", {"f": {"name": "", "status": "active"}, "statuses": Room.Status.choices})


@login_required(login_url='login')
def room_edit_view(request, pk):
    if not _can_manage_catalog(request.user):
        messages.error(request, "Sizda xonani tahrirlashga ruxsat yo'q")
        return redirect("room_list")

    room = get_object_or_404(Room, pk=pk)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        status = request.POST.get("status", "active")
        if not name:
            messages.error(request, "Xona nomini kiriting")
            return render(request, "rooms/form.html", {"f": {"name": name, "status": status}, "statuses": Room.Status.choices, "is_edit": True, "obj_id": room.pk})
        room.name = name
        room.status = status
        room.save()
        messages.success(request, "Xona yangilandi")
        return redirect("room_list")

    return render(request, "rooms/form.html", {"f": {"name": room.name, "status": room.status}, "statuses": Room.Status.choices, "is_edit": True, "obj_id": room.pk})


@login_required(login_url='login')
def room_delete_view(request, pk):
    if not _can_manage_catalog(request.user):
        messages.error(request, "Sizda xonani o'chirishga ruxsat yo'q")
        return redirect("room_list")

    room = get_object_or_404(Room, pk=pk)

    if request.method == "POST":
        try:
            room.delete()
            messages.success(request, "Xona o'chirildi")
        except ProtectedError:
            messages.error(request, "Bu xonani o'chirib bo'lmaydi — unga bog'liq guruhlar bor")
        return redirect("room_list")

    return redirect("room_edit", pk=pk)


# ==================== VAQTLAR ====================

def _validate_time_form(f):
    # xato bo'lsa matn, bo'lmasa None qaytaradi
    valid_days = [c[0] for c in Time.Days.choices]
    if f["days"] not in valid_days:
        return "Kunni tanlang"
    start_t = parse_time(f["time_start"]) if f["time_start"] else None
    end_t = parse_time(f["time_end"]) if f["time_end"] else None
    if not start_t or not end_t:
        return "Vaqtni to'g'ri kiriting"
    if start_t >= end_t:
        return "Boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak"
    return None


def _time_duplicate_exists(f, exclude_pk=None):
    # xuddi shu kun + vaqt allaqachon bormi
    qs = Time.objects.filter(days=f["days"], time_start=f["time_start"], time_end=f["time_end"])
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


@login_required(login_url='login')
def time_list_view(request):
    if not _can_view_catalog(request.user):
        messages.error(request, "Sizda bu bo'limga ruxsat yo'q")
        return redirect("dashboard")

    times = Time.objects.all()
    day = request.GET.get("day", "")
    if day:
        times = times.filter(days=day)
    times = times.order_by("days", "time_start")

    return render(request, "times/list.html", {
        "times": times,
        "days": Time.Days.choices,
        "can_manage": _can_manage_catalog(request.user),
        "f": {"day": day},
    })


@login_required(login_url='login')
def time_create_view(request):
    if not _can_manage_catalog(request.user):
        messages.error(request, "Sizda vaqt yaratishga ruxsat yo'q")
        return redirect("time_list")

    if request.method == "POST":
        f = {
            "days": request.POST.get("days", ""),
            "time_start": request.POST.get("time_start", ""),
            "time_end": request.POST.get("time_end", ""),
        }
        error = _validate_time_form(f)
        if not error and _time_duplicate_exists(f):
            error = "Bunday vaqt allaqachon mavjud"
        if error:
            messages.error(request, error)
            return render(request, "times/form.html", {"f": f, "days_choices": Time.Days.choices})
        Time.objects.create(days=f["days"], time_start=f["time_start"], time_end=f["time_end"])
        messages.success(request, "Vaqt yaratildi")
        return redirect("time_list")

    return render(request, "times/form.html", {
        "f": {"days": "", "time_start": "", "time_end": ""}, "days_choices": Time.Days.choices,
    })


@login_required(login_url='login')
def time_edit_view(request, pk):
    if not _can_manage_catalog(request.user):
        messages.error(request, "Sizda vaqtni tahrirlashga ruxsat yo'q")
        return redirect("time_list")

    time_obj = get_object_or_404(Time, pk=pk)

    if request.method == "POST":
        f = {
            "days": request.POST.get("days", ""),
            "time_start": request.POST.get("time_start", ""),
            "time_end": request.POST.get("time_end", ""),
        }
        error = _validate_time_form(f)
        if not error and _time_duplicate_exists(f, exclude_pk=time_obj.pk):
            error = "Bunday vaqt allaqachon mavjud"
        if error:
            messages.error(request, error)
            return render(request, "times/form.html", {"f": f, "days_choices": Time.Days.choices, "is_edit": True, "obj_id": time_obj.pk})
        time_obj.days = f["days"]
        time_obj.time_start = f["time_start"]
        time_obj.time_end = f["time_end"]
        time_obj.save()
        messages.success(request, "Vaqt yangilandi")
        return redirect("time_list")

    f = {
        "days": time_obj.days,
        "time_start": time_obj.time_start.strftime("%H:%M"),
        "time_end": time_obj.time_end.strftime("%H:%M"),
    }
    return render(request, "times/form.html", {"f": f, "days_choices": Time.Days.choices, "is_edit": True, "obj_id": time_obj.pk})


@login_required(login_url='login')
def time_delete_view(request, pk):
    if not _can_manage_catalog(request.user):
        messages.error(request, "Sizda vaqtni o'chirishga ruxsat yo'q")
        return redirect("time_list")

    time_obj = get_object_or_404(Time, pk=pk)

    if request.method == "POST":
        try:
            time_obj.delete()
            messages.success(request, "Vaqt o'chirildi")
        except ProtectedError:
            messages.error(request, "Bu vaqtni o'chirib bo'lmaydi — unga bog'liq guruhlar bor")
        return redirect("time_list")


# ==================== STATISTIKA / KASSA ====================

# har bir xodim roli -> User dagi balansli profil nomi
EMPLOYEE_PROFILE_ATTR = {
    "teacher": "teacher_profile",
    "admin": "admin_profile",
    "manager": "manager_profile",
    "cashier": "cashier_profile",
    "registrator": "register_profile",
}


def _can_view_statistics(user):
    # statistika bo'limi: admin va cashier
    return user.role in ("admin", "cashier")


def _employee_profile(user):
    # userning roliga mos, balansi bor profilini qaytaradi (bo'lmasa None)
    attr = EMPLOYEE_PROFILE_ATTR.get(user.role)
    if not attr:
        return None
    try:
        return getattr(user, attr)
    except ObjectDoesNotExist:
        return None


def _sum(qs):
    return qs.aggregate(s=Sum("amount"))["s"] or Decimal("0")


@login_required(login_url='login')
def statistics_view(request):
    if not _can_view_statistics(request.user):
        messages.error(request, "Sizda statistika bo'limiga ruxsat yo'q")
        return redirect("dashboard")

    # ---- oylik to'lov (minus) qabul qilish ----
    if request.method == "POST":
        employee_id = request.POST.get("employee", "")
        amount_raw = request.POST.get("amount", "").strip()
        note = request.POST.get("note", "").strip()

        error = None
        employee = User.objects.filter(
            pk=employee_id, role__in=EMPLOYEE_PROFILE_ATTR.keys()
        ).first()
        if not employee:
            error = "Xodimni tanlang"

        amount = None
        if not error:
            try:
                amount = Decimal(amount_raw) if amount_raw else Decimal("0")
            except InvalidOperation:
                error = "Summa noto'g'ri kiritilgan"
        if not error and amount <= 0:
            error = "Summa 0 dan katta bo'lishi kerak"
        if not error and not note:
            error = "Izoh kiriting"

        profile = _employee_profile(employee) if employee else None
        if not error and profile is None:
            error = "Bu xodimning profili topilmadi"

        if error:
            messages.error(request, error)
            return redirect("statistics")

        with transaction.atomic():
            SalaryPayment.objects.create(
                employee=employee, amount=amount, note=note, paid_by=request.user,
            )
            profile.balance = (profile.balance or Decimal("0")) - amount
            profile.save(update_fields=["balance"])

        messages.success(request, f"{employee.full_name}ga {amount} oylik berildi")
        return redirect("statistics")

    # ---- statistikani hisoblash ----
    total_income = _sum(Payment.objects)
    total_salary = _sum(SalaryPayment.objects)
    total_balance = total_income - total_salary

    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_income = _sum(Payment.objects.filter(created_at__gte=month_start))
    month_salary = _sum(SalaryPayment.objects.filter(created_at__gte=month_start))

    # o'qituvchilar balansi
    teachers = TeacherProfile.objects.select_related("user").order_by("user__full_name")

    # oylik to'lash uchun xodimlar ro'yxati (o'qituvchi + xodimlar)
    employees = User.objects.filter(
        role__in=EMPLOYEE_PROFILE_ATTR.keys()
    ).order_by("full_name")

    # so'nggi oylik to'lovlari
    recent = SalaryPayment.objects.select_related("employee", "paid_by")[:50]

    return render(request, "statistics/index.html", {
        "total_balance": total_balance,
        "total_income": total_income,
        "total_salary": total_salary,
        "month_income": month_income,
        "month_salary": month_salary,
        "teachers": teachers,
        "employees": employees,
        "recent": recent,
    })


# ==================== GURUH DETAIL / BIRIKTIRISH ====================


def _can_manage_enrollment(user):
    # o'quvchini guruhga biriktirish/chiqarish: admin va registrator
    return user.role in ("admin", "registrator")


def _safe_redirect(request, default="group_list"):
    # POST'dagi 'next' xavfsiz ichki URL bo'lsa o'shanga, aks holda default'ga
    nxt = request.POST.get("next", "")
    if nxt.startswith("/"):
        return redirect(nxt)
    return redirect(default)


@login_required(login_url='login')
def group_detail_view(request, pk):
    user = request.user
    if user.role == "pupil":
        messages.error(request, "Sizda bu bo'limga ruxsat yo'q")
        return redirect("dashboard")

    group = get_object_or_404(
        Group.objects.select_related("course", "teacher__user", "room", "time"), pk=pk
    )

    # teacher faqat o'z guruhini ko'radi
    if user.role == "teacher" and group.teacher.user_id != user.id:
        messages.error(request, "Bu guruh sizga tegishli emas")
        return redirect("group_list")

    enrollments = group.enrollments.select_related("pupil__user").order_by("pupil__user__full_name")
    enrolled_ids = list(enrollments.values_list("pupil_id", flat=True))

    # o'quvchini ism/telefon orqali qidirish (dropdown emas — 1000 o'quvchi uchun)
    q = request.GET.get("q", "").strip()
    candidates = None
    if q:
        candidates = (
            PupilProfile.objects.select_related("user")
            .exclude(id__in=enrolled_ids)
            .filter(Q(user__full_name__icontains=q) | Q(user__phone__icontains=q))
            .order_by("user__full_name")[:20]
        )

    return render(request, "groups/detail.html", {
        "group": group,
        "enrollments": enrollments,
        "candidates": candidates,
        "q": q,
        "can_manage": _can_manage_enrollment(user),
    })


@login_required(login_url='login')
def enrollment_create_view(request):
    if not _can_manage_enrollment(request.user):
        messages.error(request, "Sizda o'quvchini guruhga biriktirishga ruxsat yo'q")
        return redirect("group_list")

    if request.method == "POST":
        group = Group.objects.filter(pk=request.POST.get("group")).first()
        pupil = PupilProfile.objects.filter(pk=request.POST.get("pupil")).first()

        if not group or not pupil:
            messages.error(request, "Guruh yoki o'quvchi topilmadi")
        else:
            _, created = Enrollment.objects.get_or_create(group=group, pupil=pupil)
            if created:
                messages.success(request, f"{pupil.user.full_name} guruhga qo'shildi")
            else:
                messages.info(request, "Bu o'quvchi allaqachon shu guruhda")

    return _safe_redirect(request)


@login_required(login_url='login')
def enrollment_delete_view(request, pk):
    if not _can_manage_enrollment(request.user):
        messages.error(request, "Sizda o'quvchini guruhdan chiqarishga ruxsat yo'q")
        return redirect("group_list")

    enrollment = get_object_or_404(
        Enrollment.objects.select_related("pupil__user"), pk=pk
    )

    if request.method == "POST":
        name = enrollment.pupil.user.full_name
        enrollment.delete()
        messages.success(request, f"{name} guruhdan chiqarildi")

    return _safe_redirect(request)
