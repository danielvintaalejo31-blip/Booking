from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import SimpleRegistrationForm
from django.shortcuts import redirect

def login_view(request):
    if request.method == 'POST':
       
        if user is not None:
            login(request, user)
            return redirect('client_homepage')  

def register_view(request):
    """Simple registration view - accepts any username/password"""
    if request.method == 'POST':
        form = SimpleRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('appointment_list')
    else:
        form = SimpleRegistrationForm()
    
    return render(request, 'pages/register.html', {'form': form})


def home_view(request):  # Fixed indentation - moved this out
    """Homepage after login"""
    return render(request, 'pages/home.html')


def login_view(request):
    """Login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirect immediately after successful login
            return redirect('appointment_list')
        # If form is invalid, it will fall through and re-render with errors
    else:
        form = AuthenticationForm()
    
    return render(request, 'pages/login.html', {'form': form})


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')