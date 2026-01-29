from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Auth URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Services and Packages
    path('services/', views.services_page, name='services'),
    path('packages/', views.packages_page, name='packages'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    
    # API Endpoints
    path('api/services-and-packages/', views.get_services_and_packages, name='get_services_and_packages'),
    path('api/book/', views.book_appointment, name='book_appointment'),
    path('api/quick-edit/<int:appointment_id>/', views.quick_edit_appointment, name='quick_edit_appointment'),
    path('api/quick-delete/<int:appointment_id>/', views.quick_delete_appointment, name='quick_delete_appointment'),
    
    # Public booking
    path('public-book/', views.public_book_appointment, name='public_book_appointment'),
    
    # My Appointments
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('guest-appointments/', views.guest_appointments, name='guest_appointments'),
    
    # Appointment Management
    path('edit/<int:appointment_id>/', views.edit_appointment, name='edit_appointment'),
    path('delete/<int:appointment_id>/', views.delete_appointment, name='delete_appointment'),
    path('booking-confirmation/<int:appointment_id>/', views.booking_confirmation, name='booking_confirmation'),
    # Admin Dashboard (add this section)
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/update-status/<int:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),
]