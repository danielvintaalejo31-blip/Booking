from django.contrib import admin
from django.contrib import messages as admin_messages
from .models import Service, Package, Appointment

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'duration', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'package_price', 'original_price', 'discount_percentage', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['services']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_service_or_package', 'preferred_date', 'preferred_time', 'status', 'created_at']  # ✅ Removed 'user_notified'
    list_filter = ['status', 'preferred_date']  # ✅ Removed 'user_notified'
    search_fields = ['user__username', 'service__name', 'package__name', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('user',)
        }),
        ('Booking Details', {
            'fields': ('service', 'package', 'preferred_date', 'preferred_time', 'notes')
        }),
        ('Status', {
            'fields': ('status',),  # ✅ Temporarily removed 'user_notified'
            'description': 'Change status to "Confirmed" to accept the booking. User will be notified on next login.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_service_or_package(self, obj):
        """Display service or package name"""
        if obj.service:
            return f"Service: {obj.service.name}"
        elif obj.package:
            return f"Package: {obj.package.name}"
        return "N/A"
    get_service_or_package.short_description = 'Service/Package'
    
    def save_model(self, request, obj, form, change):
        """Handle status changes and notifications"""
        if change:
            old_obj = Appointment.objects.get(pk=obj.pk)
            
            if old_obj.status != 'confirmed' and obj.status == 'confirmed':
                obj.user_notified = False
                admin_messages.success(
                    request, 
                    f'✅ Appointment confirmed! {obj.user.username} will be notified on their next login.'
                )
        
        super().save_model(request, obj, form, change)
    
    actions = ['accept_appointments', 'cancel_appointments', 'complete_appointments']
    
    def accept_appointments(self, request, queryset):
        """Bulk action to accept multiple appointments"""
        updated = queryset.update(status='confirmed', user_notified=False)
        self.message_user(
            request, 
            f'✅ {updated} appointment(s) have been accepted. Users will be notified on next login.',
            admin_messages.SUCCESS
        )
    accept_appointments.short_description = "✅ Accept selected appointments"
    
    def cancel_appointments(self, request, queryset):
        """Bulk action to cancel multiple appointments"""
        updated = queryset.update(status='cancelled')
        self.message_user(
            request, 
            f'❌ {updated} appointment(s) have been cancelled.',
            admin_messages.WARNING
        )
    cancel_appointments.short_description = "❌ Cancel selected appointments"
    
    def complete_appointments(self, request, queryset):
        """Bulk action to mark appointments as completed"""
        updated = queryset.update(status='completed')
        self.message_user(
            request, 
            f'✅ {updated} appointment(s) marked as completed.',
            admin_messages.SUCCESS
        )
    complete_appointments.short_description = "✅ Mark as completed"