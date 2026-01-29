from django.urls import path
from . import views

app_name = 'security_management'  # important!

urlpatterns = [
    path('home/', views.client_homepage, name='client_homepage'),
]
