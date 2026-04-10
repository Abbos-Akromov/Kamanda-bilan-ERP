from django.shortcuts import render, redirect
from django.contrib import messages
from apps.accounts.decorators import role_required
from .utils import generate_certificate
from apps.accounts.models import User
from apps.courses.models import Course

@role_required('admin')
def issue_certificate(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_id = request.POST.get('course_id')
        student = User.objects.get(id=student_id)
        course = Course.objects.get(id=course_id)
        generate_certificate(student, course)
        messages.success(request, 'Sertifikat yaratildi')
        return redirect('dashboard:admin')
    students = User.objects.filter(role='student')
    courses = Course.objects.filter(is_active=True)
    return render(request, 'certificates/issue.html', {'students': students, 'courses': courses})
