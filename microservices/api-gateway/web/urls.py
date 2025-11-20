"""
URL Configuration for Web Interface
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/step1/', views.signup_step1_view, name='signup_step1'),
    path('signup/step2/', views.signup_step2_view, name='signup_step2'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),

    # Doctor pages
    path('doctor/home/', views.doctor_home_view, name='doctor_home'),
    path('doctor/hours/', views.doctor_hours_view, name='doctor_hours'),
    path('doctor/availability/', views.doctor_availability_view, name='doctor_availability'),

    # Patient pages
    path('patient/home/', views.patient_home_view, name='patient_home'),
    path('patient/search/', views.patient_search_doctors_view, name='patient_search'),
    path('patient/doctor-availability/', views.view_doctor_availability_view, name='view_doctor_availability'),

    # Pharmacy pages
    path('pharmacy/home/', views.pharmacy_home_view, name='pharmacy_home'),
    path('pharmacy/settings/', views.pharmacy_settings_view, name='pharmacy_settings'),
    path('pharmacy/staff/<int:staff_id>/delete/', views.delete_staff_view, name='delete_pharmacist'),
    path('pharmacy/medicine/add/', views.add_medicine_view, name='add_medicine'),
    path('pharmacy/stock/update/', views.update_stock_view, name='update_stock'),
    path('pharmacy/inventory/', views.view_inventory_view, name='view_inventory'),

    # Utility
    path('error/', views.error_view, name='error'),
]
