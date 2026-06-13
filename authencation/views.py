from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    
    if request.method == "POST":
        
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        
        user = authenticate(request, phone=phone, password=password)
        
        if not user:
            messages.error(request, "Telefon raqam yoki parol noto'g'ri")
            
        
        else:
            login(request, user)
            return redirect("dashboard")
            
    return render(request, "auth/login.html")

@login_required(login_url='login')
def dashboard_view(request):
    return render(request, "home/dashboard.html")


@login_required(login_url='login')
def profile_view(request):
    user = request.user

    if request.method == "POST":

        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")

        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # telefon boshqa userda band emasligini tekshirish
        if User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
            messages.error(request, "Bu telefon raqam band")
            return redirect("profile")

        # email boshqa userda band emasligini tekshirish
        if email and User.objects.filter(email=email).exclude(pk=user.pk).exists():
            messages.error(request, "Bu email band")
            return redirect("profile")

        user.full_name = full_name
        user.phone = phone
        user.email = email or None

        # rasm yuklangan bo'lsa avatarni yangilaymiz
        if request.FILES.get("avatar"):
            user.avatar = request.FILES["avatar"]

        # parolni faqat yangi parol kiritilgan bo'lsa o'zgartiramiz
        if new_password:
            if not user.check_password(old_password):
                messages.error(request, "Eski parol noto'g'ri")
                return redirect("profile")

            if new_password != confirm_password:
                messages.error(request, "Yangi parollar mos kelmadi")
                return redirect("profile")

            user.set_password(new_password)

        user.save()

        # parol o'zgargan bo'lsa user tizimdan chiqib qolmasligi uchun
        if new_password:
            update_session_auth_hash(request, user)

        messages.success(request, "Ma'lumotlar saqlandi")
        return redirect("profile")

    return render(request, "home/profile.html")


def logout_view(request):
    logout(request)
    return redirect("login")