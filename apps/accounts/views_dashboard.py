from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from apps.courses.models import Course, Enrollment

@login_required
def dashboard_home(request):
    user = request.user
    if user.role == 'student': return redirect('dashboard:student')
    elif user.role == 'teacher': return redirect('dashboard:teacher')
    elif user.role == 'assistant': return redirect('dashboard:assistant')
    elif user.role == 'admin': return redirect('dashboard:admin')
    return redirect('auth:login')

@login_required
@role_required('student')
def student_dashboard(request):
    enrollments = Enrollment.objects.filter(student=request.user)
    return render(request, 'dashboard/student.html', {'enrollments': enrollments})

@login_required
@role_required('teacher')
def teacher_dashboard(request):
    courses = Course.objects.filter(teacher=request.user)
    return render(request, 'dashboard/teacher.html', {'courses': courses})

@login_required
@role_required('assistant')
def assistant_dashboard(request):
    return render(request, 'dashboard/assistant.html')

@login_required
@role_required('admin')
def admin_dashboard(request):
    return render(request, 'dashboard/admin.html')
