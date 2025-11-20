"""
Web Interface Views for API Gateway
These views render HTML templates and make API calls to microservices
"""

import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_http_methods
import json


# ============================================================================
# Helper Functions
# ============================================================================

def get_auth_headers(request):
    """Get authentication headers from session"""
    token = request.session.get('access_token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}


def is_authenticated(request):
    """Check if user is authenticated"""
    return 'access_token' in request.session and 'user' in request.session


def get_current_user(request):
    """Get current user from session"""
    return request.session.get('user', {})


# ============================================================================
# Authentication Views
# ============================================================================

@require_http_methods(["GET", "POST"])
def login_view(request):
    """Login page - renders form and handles authentication"""
    if request.method == 'GET':
        # If already logged in, redirect to appropriate home
        if is_authenticated(request):
            user = get_current_user(request)
            role = user.get('role', 'patient')
            if role == 'doctor':
                return redirect('doctor_home')
            elif role == 'pharmacy':
                return redirect('pharmacy_home')
            else:
                return redirect('patient_home')

        return render(request, 'accounts/login.html')

    # POST - handle login
    username = request.POST.get('username')
    password = request.POST.get('password')

    try:
        # Call auth service
        response = requests.post(
            f'{settings.AUTH_SERVICE_URL}/api/auth/login/',
            json={'username': username, 'password': password},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()

            # Store tokens in session
            request.session['access_token'] = data['access']
            request.session['refresh_token'] = data['refresh']

            # Get user profile
            profile_response = requests.get(
                f'{settings.AUTH_SERVICE_URL}/api/auth/profile/',
                headers={'Authorization': f"Bearer {data['access']}"},
                timeout=5
            )

            if profile_response.status_code == 200:
                user_data = profile_response.json()
                request.session['user'] = user_data

                # Redirect based on role
                role = user_data.get('role', 'patient')
                if role == 'doctor':
                    return redirect('doctor_home')
                elif role == 'pharmacy':
                    return redirect('pharmacy_home')
                else:
                    return redirect('patient_home')
            else:
                messages.error(request, 'Login successful but could not fetch profile')
                return redirect('login')
        else:
            error_data = response.json()
            messages.error(request, error_data.get('detail', 'Invalid credentials'))
            return render(request, 'accounts/login.html')

    except requests.exceptions.RequestException as e:
        messages.error(request, f'Unable to connect to authentication service: {str(e)}')
        return render(request, 'accounts/login.html')


@require_http_methods(["GET"])
def logout_view(request):
    """Logout - clear session"""
    request.session.flush()
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')


@require_http_methods(["GET", "POST"])
def signup_step1_view(request):
    """Signup step 1 - choose role"""
    if request.method == 'GET':
        return render(request, 'accounts/signup_step1.html')

    # POST - store role and go to step 2
    user_type = request.POST.get('user_type')
    if user_type in ['patient', 'doctor', 'pharmacy']:
        request.session['signup_role'] = user_type
        return redirect('signup_step2')
    else:
        messages.error(request, 'Please select a valid account type')
        return render(request, 'accounts/signup_step1.html')


@require_http_methods(["GET", "POST"])
def signup_step2_view(request):
    """Signup step 2 - enter details"""
    role = request.session.get('signup_role')
    if not role:
        return redirect('signup_step1')

    if request.method == 'GET':
        return render(request, 'accounts/signup_step2.html', {'role': role})

    # POST - create account
    data = {
        'username': request.POST.get('username'),
        'email': request.POST.get('email'),
        'password': request.POST.get('password'),
        'password2': request.POST.get('password2'),
        'first_name': request.POST.get('first_name'),
        'last_name': request.POST.get('last_name'),
        'role': role
    }

    try:
        response = requests.post(
            f'{settings.AUTH_SERVICE_URL}/api/auth/register/',
            json=data,
            timeout=5
        )

        if response.status_code == 201:
            del request.session['signup_role']
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
        else:
            error_data = response.json()
            for field, errors in error_data.items():
                if isinstance(errors, list):
                    messages.error(request, f'{field}: {errors[0]}')
                else:
                    messages.error(request, f'{field}: {errors}')
            return render(request, 'accounts/signup_step2.html', {'role': role})

    except requests.exceptions.RequestException as e:
        messages.error(request, f'Unable to connect to service: {str(e)}')
        return render(request, 'accounts/signup_step2.html', {'role': role})


# ============================================================================
# Doctor Views
# ============================================================================

@require_http_methods(["GET"])
def doctor_home_view(request):
    """Doctor home page - shows appointments and overview"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied: Doctor account required')
        return redirect('login')

    # Get doctor profile
    doctor_data = None
    try:
        doctor_response = requests.get(
            f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{user["id"]}/',
            headers=get_auth_headers(request),
            timeout=5
        )
        if doctor_response.status_code == 200:
            doctor_data = doctor_response.json()
    except:
        pass

    context = {
        'user': user,
        'doctor': doctor_data,
        'upcoming_appointments': [],  # TODO: Get from scheduling service
        'today_appointments': [],  # TODO: Get from scheduling service
    }

    return render(request, 'accounts/doctor_home.html', context)


@require_http_methods(["GET", "POST"])
def doctor_hours_view(request):
    """Doctor working hours management"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    if request.method == 'GET':
        # Get existing working hours
        working_hours = []
        try:
            response = requests.get(
                f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{user["id"]}/working-hours/',
                headers=get_auth_headers(request),
                timeout=5
            )
            if response.status_code == 200:
                working_hours = response.json()
        except:
            pass

        context = {
            'user': user,
            'working_hours': working_hours,
            'days': [
                {'value': 1, 'name': 'Monday'},
                {'value': 2, 'name': 'Tuesday'},
                {'value': 3, 'name': 'Wednesday'},
                {'value': 4, 'name': 'Thursday'},
                {'value': 5, 'name': 'Friday'},
                {'value': 6, 'name': 'Saturday'},
                {'value': 7, 'name': 'Sunday'},
            ]
        }
        return render(request, 'accounts/doctor_hours.html', context)

    # POST - add/update working hours
    day_of_week = request.POST.get('day_of_week')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')

    try:
        response = requests.post(
            f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{user["id"]}/working-hours/',
            json={
                'day_of_week': int(day_of_week),
                'start_time': start_time,
                'end_time': end_time
            },
            headers=get_auth_headers(request),
            timeout=5
        )

        if response.status_code == 201:
            messages.success(request, 'Working hours added successfully')
        else:
            error_data = response.json()
            messages.error(request, f'Error: {error_data}')

    except requests.exceptions.RequestException as e:
        messages.error(request, f'Unable to save working hours: {str(e)}')

    return redirect('doctor_hours')


@require_http_methods(["GET"])
def doctor_availability_view(request):
    """View doctor availability"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'doctor':
        messages.error(request, 'Access denied')
        return redirect('login')

    # Get date and duration from query params
    date = request.GET.get('date')
    duration = request.GET.get('duration', '30')

    availability_data = None
    if date:
        try:
            response = requests.get(
                f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{user["id"]}/availability/',
                params={'date': date, 'duration': duration},
                headers=get_auth_headers(request),
                timeout=5
            )
            if response.status_code == 200:
                availability_data = response.json()
        except:
            pass

    context = {
        'user': user,
        'date': date,
        'duration': duration,
        'availability': availability_data
    }

    return render(request, 'accounts/doctor_availability.html', context)


@require_http_methods(["GET"])
def view_doctor_availability_view(request):
    """View availability for a specific doctor (patient view)"""
    doctor_id = request.GET.get('doctor_id')
    date = request.GET.get('date')
    duration = request.GET.get('duration', '30')

    availability_data = None
    doctor_data = None

    if doctor_id and date:
        try:
            # Get doctor info
            doctor_response = requests.get(
                f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{doctor_id}/',
                headers=get_auth_headers(request),
                timeout=5
            )
            if doctor_response.status_code == 200:
                doctor_data = doctor_response.json()

            # Get availability
            avail_response = requests.get(
                f'{settings.DOCTOR_SERVICE_URL}/api/doctors/{doctor_id}/availability/',
                params={'date': date, 'duration': duration},
                headers=get_auth_headers(request),
                timeout=5
            )
            if avail_response.status_code == 200:
                availability_data = avail_response.json()
        except:
            pass

    context = {
        'doctor': doctor_data,
        'date': date,
        'duration': duration,
        'availability': availability_data
    }

    return render(request, 'accounts/view_doctor_availability.html', context)


# ============================================================================
# Patient Views
# ============================================================================

@require_http_methods(["GET"])
def patient_home_view(request):
    """Patient home page"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'patient':
        messages.error(request, 'Access denied: Patient account required')
        return redirect('login')

    context = {
        'user': user,
        'appointments': [],  # TODO: Get from scheduling service
        'prescriptions': [],  # TODO: Get from patient service
    }

    return render(request, 'accounts/patient_home.html', context)


@require_http_methods(["GET"])
def patient_search_doctors_view(request):
    """Search for doctors"""
    if not is_authenticated(request):
        return redirect('login')

    specialty = request.GET.get('specialty', '')
    doctors = []

    if specialty:
        try:
            response = requests.get(
                f'{settings.DOCTOR_SERVICE_URL}/api/doctors/search/',
                params={'specialty': specialty},
                headers=get_auth_headers(request),
                timeout=5
            )
            if response.status_code == 200:
                doctors = response.json()
        except:
            pass
    else:
        # Get all doctors if no search
        try:
            response = requests.get(
                f'{settings.DOCTOR_SERVICE_URL}/api/doctors/',
                headers=get_auth_headers(request),
                timeout=5
            )
            if response.status_code == 200:
                doctors = response.json()
        except:
            pass

    context = {
        'user': get_current_user(request),
        'specialty': specialty,
        'doctors': doctors
    }

    return render(request, 'accounts/patient_search.html', context)


# ============================================================================
# Pharmacy Views
# ============================================================================

@require_http_methods(["GET"])
def pharmacy_home_view(request):
    """Pharmacy home page"""
    if not is_authenticated(request):
        return redirect('login')

    user = get_current_user(request)
    if user.get('role') != 'pharmacy':
        messages.error(request, 'Access denied: Pharmacy account required')
        return redirect('login')

    context = {
        'user': user,
        'pending_orders': [],  # TODO: Get from pharmacy service
        'inventory_low': [],  # TODO: Get from inventory service
    }

    return render(request, 'accounts/pharmacy_home.html', context)


# ============================================================================
# Utility Views
# ============================================================================

@require_http_methods(["GET"])
def forgot_password_view(request):
    """Forgot password page"""
    return render(request, 'accounts/forgot_password.html')


@require_http_methods(["GET"])
def error_view(request):
    """Generic error page"""
    return render(request, 'accounts/error.html')
