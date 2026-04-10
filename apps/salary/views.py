from django.shortcuts import render, redirect
from django.contrib import messages
from apps.accounts.decorators import role_required
from .models import Salary
from apps.accounts.models import User
from apps.courses.models import Course, Group, Enrollment
from datetime import datetime
from decimal import Decimal

@role_required('admin')
def salary_list(request):
    salaries = Salary.objects.all().order_by('-month')
    return render(request, 'salary/list.html', {'salaries': salaries})

@role_required('admin')
def calculate_monthly_salary(request):
    if request.method == 'POST':
        month_str = request.POST.get('month')
        if not month_str:
            messages.error(request, 'Oyni tanlang')
            return redirect('salary:list')
        month = datetime.strptime(month_str, '%Y-%m').date().replace(day=1)
        teachers = User.objects.filter(role='teacher')
        assistants = User.objects.filter(role='assistant')
        
        for teacher in teachers:
            count = Enrollment.objects.filter(group__teacher=teacher, status='approved').count()
            groups = Group.objects.filter(teacher=teacher)
            base = sum(g.course.price * Enrollment.objects.filter(group=g, status='approved').count() for g in groups)
            total = base * Decimal('0.50')
            Salary.objects.update_or_create(
                user=teacher, month=month,
                defaults={'students_count': count, 'percent': 50, 'base_amount': base, 'total_amount': total}
            )
        
        for assistant in assistants:
            groups = Group.objects.filter(assistant=assistant)
            base = sum(g.course.price * Enrollment.objects.filter(group=g, status='approved').count() for g in groups)
            total = base * Decimal('0.20')
            Salary.objects.update_or_create(
                user=assistant, month=month,
                defaults={'students_count': 0, 'percent': 20, 'base_amount': base, 'total_amount': total}
            )
        messages.success(request, 'Oylik hisoblandi')
        return redirect('salary:list')
    return redirect('salary:list')

@role_required('admin')
def export_salary_excel(request, month):
    import openpyxl
    from django.http import HttpResponse
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Oylik maosh'
    ws.append(['Ism', 'Rol', 'Studentlar', 'Foiz', 'Summa', 'Oy'])
    for s in Salary.objects.filter(month=month).select_related('user'):
        ws.append([s.user.email, s.user.role, s.students_count, f"{s.percent}%", float(s.total_amount), str(s.month)])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=salary_{month}.xlsx'
    wb.save(response)
    return response
