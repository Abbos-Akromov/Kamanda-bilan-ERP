import random
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
from apps.accounts.models import User, OTPCode

def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        errors = {}
        if not email: errors['email'] = 'Email majburiy'
        if User.objects.filter(email=email).exists():
            errors['email'] = "Bu email allaqachon ro'yxatdan o'tgan"
        if len(password) < 8: errors['password'] = 'Kamida 8 belgi'
        if password != confirm: errors['confirm'] = 'Parollar mos emas'
        if errors:
            return render(request, 'accounts/register.html', {'errors': errors, 'data': request.POST})
        
        request.session['pending_register'] = {
            'email': email, 'password': password,
            'role': request.POST.get('role', 'student')
        }
        code = str(random.randint(100000, 999999))
        OTPCode.objects.filter(email=email, purpose='register', is_used=False).delete()
        OTPCode.objects.create(email=email, code=code, purpose='register')
        send_otp_email(email, code)
        return redirect('auth:verify_otp')
    return render(request, 'accounts/register.html')

def verify_otp_view(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        pending = request.session.get('pending_register')
        if not pending:
            return redirect('auth:register')
        otp = OTPCode.objects.filter(
            email=pending['email'], purpose='register', is_used=False
        ).last()
        if not otp or otp.is_expired():
            return render(request, 'accounts/verify_otp.html', {'error': "OTP muddati o'tgan, qayta urinib ko'ring"})
        if otp.attempts >= 3:
            return render(request, 'accounts/verify_otp.html', {'error': "Juda ko'p urinish. Qayta ro'yxatdan o'ting"})
        if otp.code != code:
            otp.attempts += 1; otp.save()
            return render(request, 'accounts/verify_otp.html', {'error': f"Noto'g'ri kod. {3 - otp.attempts} urinish qoldi"})
        
        user = User.objects.create_user(
            username=pending['email'], email=pending['email'],
            password=pending['password'], role=pending['role'], is_active=True
        )
        otp.is_used = True; otp.save()
        del request.session['pending_register']
        login(request, user)
        return redirect('dashboard:home')
    return render(request, 'accounts/verify_otp.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard:home')
        return render(request, 'accounts/login.html', {'error': "Email yoki parol xato"})
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('auth:login')

def send_otp_email(to_email, code):
    subject = 'LMS — Tasdiqlash kodi'
    html = f'''<div style="font-family: Arial, sans-serif; background: #fdfdfd; padding: 20px;">
      <h2 style="color: #4F46E5;">LMS Platformasi</h2>
      <p>Ro'yxatdan o'tish uchun tasdiqlash kodingiz:</p>
      <div style="font-size: 24px; font-weight: bold; background: #EEF2FF; padding: 10px; display: inline-block;">
        {code}
      </div>
      <p>Kod 10 daqiqa davomida amal qiladi. Agar siz bu so'rovni yubormagan bo'lsangiz, e'tibor bermang.</p>
    </div>'''
    try:
        from django.conf import settings
        if settings.EMAIL_HOST_USER != 'your@gmail.com': # skip sending if default user setup
            send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [to_email], html_message=html)
        else:
            print(f"MOCK EMAIL SENT TO {to_email}: {code}")
    except Exception as e:
        print("Error sending mail:", e)
