from django.contrib import admin
from django.urls import path, include
from appointments import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing_page, name='landing'),  # Public landing page
    path('', include('appointments.urls')),  # All appointment URLs including auth
]