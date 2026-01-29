# appointments/models.py

from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    """Individual services offered by the salon"""
    
    # Service categories
    CATEGORY_CHOICES = [
        ('HAIR', 'Hair Services'),
        ('NAIL', 'Nail Services'),
        ('FACIAL', 'Facial Services'),
        ('MASSAGE', 'Massage Services'),
        ('WAXING', 'Waxing Services'),
        ('MAKEUP', 'Makeup Services'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in minutes")
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} - ₱{self.price}"


class Package(models.Model):
    """Service packages (bundles of services at discounted price)"""
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    services = models.ManyToManyField(Service, related_name='packages')
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    package_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def savings(self):
        """Calculate how much customer saves"""
        return self.original_price - self.package_price
    
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.original_price > 0:
            return int((self.savings() / self.original_price) * 100)
        return 0

class Appointment(models.Model):
    """Customer appointment bookings"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # User (optional - for logged-in bookings)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='appointments',
        null=True,  # ✅ ADDED: Allow null for public bookings
        blank=True  # ✅ ADDED: Allow blank for public bookings
    )
    
    # Service/Package
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True)
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Appointment details
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    # ✅ NEW: Customer contact info (for public bookings)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
    
    def __str__(self):
        # Determine who made the booking
        if self.user:
            customer = self.user.username
        elif self.customer_name:
            customer = self.customer_name
        else:
            customer = "Unknown"
        
        # Determine what was booked
        if self.service:
            service_name = self.service.name
        elif self.package:
            service_name = f"Package: {self.package.name}"
        else:
            service_name = "No service/package"
        
        return f"{customer} - {service_name} on {self.preferred_date}"
    
    def get_status_display_color(self):
        """Return Bootstrap color class for status"""
        colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'completed': 'success',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')
    
    def get_customer_display(self):
        """Return customer name for display"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.customer_name or "Guest"
    
    def get_customer_email(self):
        """Return customer email"""
        if self.user:
            return self.user.email
        return self.customer_email
    
    def get_customer_phone(self):
        """Return customer phone"""
        return self.customer_phone if self.customer_phone else "Not provided"