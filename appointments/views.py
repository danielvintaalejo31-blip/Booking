import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Service, Package, Appointment
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import AppointmentForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Count
from datetime import date, timedelta

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard for managing appointments"""
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    date_filter = request.GET.get('date', 'all')
    search_query = request.GET.get('search', '')
    
    # Base query
    appointments = Appointment.objects.all()
    
    # Apply status filter
    if status_filter != 'all':
        appointments = appointments.filter(status=status_filter)
    
    # Apply date filter
    today = date.today()
    if date_filter == 'today':
        appointments = appointments.filter(preferred_date=today)
    elif date_filter == 'tomorrow':
        appointments = appointments.filter(preferred_date=today + timedelta(days=1))
    elif date_filter == 'week':
        week_end = today + timedelta(days=7)
        appointments = appointments.filter(preferred_date__range=[today, week_end])
    elif date_filter == 'month':
        month_end = today + timedelta(days=30)
        appointments = appointments.filter(preferred_date__range=[today, month_end])
    
    # Apply search filter
    if search_query:
        appointments = appointments.filter(
            Q(customer_name__icontains=search_query) |
            Q(customer_email__icontains=search_query) |
            Q(customer_phone__icontains=search_query)
        )
    
    # Order by date and time
    appointments = appointments.order_by('-preferred_date', '-preferred_time')
    
    # Get statistics
    stats = {
        'total': Appointment.objects.count(),
        'pending': Appointment.objects.filter(status='pending').count(),
        'confirmed': Appointment.objects.filter(status='confirmed').count(),
        'completed': Appointment.objects.filter(status='completed').count(),
        'cancelled': Appointment.objects.filter(status='cancelled').count(),
        'today': Appointment.objects.filter(preferred_date=today).count(),
    }
    
    context = {
        'appointments': appointments,
        'stats': stats,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search_query': search_query,
    }
    
    return render(request, 'appointments/admin_dashboard.html', context)


@staff_member_required
@require_http_methods(["POST"])
def update_appointment_status(request, appointment_id):
    """Update appointment status (approve/reject)"""
    try:
        data = json.loads(request.body)
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        new_status = data.get('status')
        if new_status not in ['pending', 'confirmed', 'completed', 'cancelled']:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        appointment.status = new_status
        appointment.save()
        
        return JsonResponse({
            'message': f'Appointment {new_status} successfully',
            'status': new_status
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)





@require_http_methods(["GET"])
def get_services_and_packages(request):
    """
    API endpoint to get all active services and packages
    """
    try:
        services = Service.objects.filter(is_active=True)
        packages = Package.objects.filter(is_active=True)
        
        # Organize services by category
        services_by_category = {}
        for service in services:
            category = service.get_category_display()
            if category not in services_by_category:
                services_by_category[category] = []
            services_by_category[category].append({
                'id': service.id,
                'name': service.name,
                'price': str(service.price),
            })
        
        # Get packages
        packages_list = []
        for package in packages:
            packages_list.append({
                'id': package.id,
                'name': package.name,
                'price': str(package.total_price),
            })
        
        return JsonResponse({
            'success': True,
            'services_by_category': services_by_category,
            'packages': packages_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def public_book_appointment(request):
    """
    Handle public appointment booking from landing page (no login required)
    """
    try:
        data = json.loads(request.body)
        
        service_id = data.get('service_id')
        appointment_date = data.get('date')
        appointment_time = data.get('time')
        customer_name = data.get('customer_name')
        customer_email = data.get('customer_email')
        customer_phone = data.get('customer_phone')
        notes = data.get('notes', '')
        
        if not all([service_id, appointment_date, appointment_time, customer_name, customer_email, customer_phone]):
            return JsonResponse({
                'success': False,
                'error': 'All fields are required'
            }, status=400)
        
        try:
            service = Service.objects.get(id=service_id, is_active=True)
        except Service.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Service not found'
            }, status=404)
        
        appointment = Appointment.objects.create(
            user=None,
            service=service,
            preferred_date=appointment_date,
            preferred_time=appointment_time,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            notes=notes,
            status='pending'
        )
        
        # Store appointment ID in session for guest users
        if not request.user.is_authenticated:
            if 'guest_appointments' not in request.session:
                request.session['guest_appointments'] = []
            request.session['guest_appointments'].append(appointment.id)
            request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': 'Appointment booked successfully! We will contact you soon.',
            'appointment_id': appointment.id,
            'appointment_details': {
                'service': service.name,
                'date': appointment_date,
                'time': appointment_time,
                'customer': customer_name
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
        
    except Exception as e:
        print(f"Error booking appointment: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


def guest_appointments(request):
    """
    Show appointments for guest users (stored in session)
    """
    guest_appointment_ids = request.session.get('guest_appointments', [])
    appointments = Appointment.objects.filter(id__in=guest_appointment_ids).order_by('-created_at')
    
    context = {
        'appointments': appointments,
        'is_guest': True
    }
    
    return render(request, 'pages/my_appointments.html', context)


@login_required(login_url='/login/')
def my_appointments(request):
    """
    Show all appointments for the logged-in user
    """
    appointments = Appointment.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'appointments': appointments,
        'is_guest': False
    }
    
    return render(request, 'pages/my_appointments.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def quick_edit_appointment(request, appointment_id):
    """
    Quick edit appointment details via AJAX
    """
    try:
        # For guest users, check session
        if not request.user.is_authenticated:
            guest_appointment_ids = request.session.get('guest_appointments', [])
            appointment = get_object_or_404(Appointment, id=appointment_id, id__in=guest_appointment_ids)
        else:
            appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
        
        data = json.loads(request.body)
        
        # Update appointment fields
        if 'date' in data:
            appointment.preferred_date = data['date']
        if 'time' in data:
            appointment.preferred_time = data['time']
        if 'notes' in data:
            appointment.notes = data['notes']
        
        appointment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Appointment updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def quick_delete_appointment(request, appointment_id):
    """
    Delete appointment via AJAX
    """
    try:
        # For guest users, check session
        if not request.user.is_authenticated:
            guest_appointment_ids = request.session.get('guest_appointments', [])
            appointment = get_object_or_404(Appointment, id=appointment_id, id__in=guest_appointment_ids)
            # Remove from session
            guest_appointment_ids.remove(appointment_id)
            request.session['guest_appointments'] = guest_appointment_ids
            request.session.modified = True
        else:
            appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
        
        appointment.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Appointment deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('appointments:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'security_management/pages/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created successfully! Please login with your credentials.')
            return redirect('appointments:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    return render(request, 'security_management/pages/register.html', {'form': form})


@login_required(login_url='/login/')
def dashboard(request):
    services = Service.objects.filter(is_active=True)
    packages = Package.objects.filter(is_active=True)
    appointments = Appointment.objects.filter(user=request.user).order_by('-preferred_date', '-preferred_time')
    
    context = {
        'services': services,
        'packages': packages,
        'appointments': appointments,
        'user': request.user,
    }
    
    return render(request, 'pages/dashboard.html', context)


@login_required(login_url='/login/')
def landing_page(request):
    """
    Redirect to login page
    """
    return redirect('/login/')
    
    # Get featured services and packages for public display
    services = Service.objects.filter(is_active=True)[:6]  # Show 6 featured services
    packages = Package.objects.filter(is_active=True)[:3]  # Show 3 packages
    
    # Organize services by category for better display
    services_by_category = {}
    for service in services:
        category = service.get_category_display()
        if category not in services_by_category:
            services_by_category[category] = []
        services_by_category[category].append(service)
    
    context = {
        'services': services,
        'services_by_category': services_by_category,
        'packages': packages,
    }
    
    return render(request, 'pages/landing.html', context)


def custom_logout(request):
    if request.method == "POST":
        logout(request)
        return redirect('/login/')
    
    return render(request, 'security_management/pages/logout.html')


def services_page(request):
    category = request.GET.get('category', None)
    services = Service.objects.filter(is_active=True)
    
    if category:
        services = services.filter(category=category)
    
    categories = Service.CATEGORY_CHOICES
    
    context = {
        'services': services,
        'categories': categories,
        'selected_category': category,
    }
    
    return render(request, 'pages/service_page.html', context)


def packages_page(request):
    packages = Package.objects.filter(is_active=True)
    
    context = {
        'packages': packages,
    }
    
    return render(request, 'pages/packages_page.html', context)


def service_detail(request, service_id):
    service = get_object_or_404(Service, id=service_id, is_active=True)
    
    related_services = Service.objects.filter(
        category=service.category,
        is_active=True
    ).exclude(id=service_id)[:3]
    
    context = {
        'service': service,
        'related_services': related_services,
    }
    
    return render(request, 'pages/service_detail.html', context)


@login_required(login_url='/login/')
@csrf_exempt
@login_required(login_url='/login/')
def book_appointment(request):
    """
    Handle appointment booking via AJAX (POST request only)
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            service_id = data.get('service_id')
            package_id = data.get('package_id')
            
            # Must have either service or package
            if not service_id and not package_id:
                return JsonResponse({'success': False, 'error': 'Service or Package is required'}, status=400)
            
            # Get service or package
            service = None
            package = None
            
            if service_id:
                try:
                    service_id = int(service_id)
                    service = Service.objects.get(id=service_id, is_active=True)
                except (ValueError, TypeError, Service.DoesNotExist):
                    return JsonResponse({'success': False, 'error': 'Invalid service'}, status=404)
            
            if package_id:
                try:
                    package_id = int(package_id)
                    package = Package.objects.get(id=package_id, is_active=True)
                except (ValueError, TypeError, Package.DoesNotExist):
                    return JsonResponse({'success': False, 'error': 'Invalid package'}, status=404)
            
            date = data.get('date')
            time = data.get('time')
            notes = data.get('notes', '')
            
            if not date or not time:
                return JsonResponse({'success': False, 'error': 'Date and time are required'}, status=400)
            
            # Create appointment
            appointment = Appointment.objects.create(
                user=request.user,
                service=service,
                package=package,
                preferred_date=date,
                preferred_time=time,
                notes=notes,
                status='pending'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Appointment booked successfully!',
                'appointment_id': appointment.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required(login_url='/login/')
def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Appointment updated successfully!')
            return redirect('appointments:my_appointments')
        else:
            messages.error(request, '⚠️ Please correct the errors below.')
    else:
        form = AppointmentForm(instance=appointment)
    
    context = {
        'form': form,
        'appointment': appointment,
        'editing': True,
        'services': Service.objects.filter(is_active=True),
        'packages': Package.objects.filter(is_active=True),
    }
    
    return render(request, 'pages/appointment_form.html', context)


@login_required(login_url='/login/')
def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, '🗑️ Appointment deleted successfully!')
        return redirect('appointments:my_appointments')
    
    context = {'appointment': appointment}
    return render(request, 'pages/confirm_delete.html', context)


@login_required(login_url='/login/')
def booking_confirmation(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    
    # Get all user appointments for display
    all_appointments = Appointment.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'appointment': appointment,
        'all_appointments': all_appointments
    }
    
    return render(request, 'pages/booking_confirmation.html', context)