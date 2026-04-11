from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import role_required
from apps.accounts.models import User
from .models import Notification

@login_required
@role_required('admin')
def notification_admin_dashboard(request):
    notifications = Notification.objects.all().order_by('-created_at')[:100]
    users_count = User.objects.count()
    
    return render(request, 'notifications/admin_dashboard.html', {
        'notifications': notifications,
        'users_count': users_count,
    })

@login_required
@role_required('admin')
def send_broadcast(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('body')
        target = request.POST.get('target', 'all')
        
        if not title or not body:
            messages.error(request, "Iltimos, barcha maydonlarni to'ldiring.")
            return redirect('notifications:admin_dashboard')
            
        users = User.objects.all()
        if target == 'teachers':
            users = users.filter(role='teacher')
        elif target == 'students':
            users = users.filter(role='student')
        elif target == 'assistants':
            users = users.filter(role='assistant')
            
        count = 0
        for u in users:
            Notification.objects.create(
                user=u,
                title=title,
                body=body,
                notif_type='announcement'
            )
            count += 1
            
        messages.success(request, f"{count} ta foydalanuvchiga xabarnoma muvaffaqiyatli yuborildi.")
        return redirect('notifications:admin_dashboard')
    
    return redirect('notifications:admin_dashboard')

@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, id=pk, user=request.user)
    notif.is_read = True
    notif.save()
    
    # If the notification has a link (e.g., to a chat room), redirect there
    if notif.link:
        return redirect(notif.link)
        
    return redirect(request.META.get('HTTP_REFERER', '/'))
