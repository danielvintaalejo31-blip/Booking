# security_management/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages


def register(request):
    """
    Handles user registration.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'security_management/pages/register.html', {'form': form})


@login_required
def client_homepage(request):
    """
    Homepage for logged-in clients.
    """
    return render(request, 'security_management/pages/client_homepage.html')


@login_required
def home(request):
    """
    Alias for client_homepage.
    """
    return render(request, 'security_management/pages/client_homepage.html')


def custom_logout(request):
    """
    Logs out the user and displays a custom logout page.
    """
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return render(request, 'security_management/pages/logout.html')
