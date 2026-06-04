from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


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


def logout_view(request):
    logout(request)
    return redirect("login")