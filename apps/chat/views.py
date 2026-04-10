from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages

from apps.courses.models import Group, Enrollment
from apps.accounts.models import User
from .models import Message

def get_chat_context(user):
    """Helper to get sidebar groups and contacts based on user role"""
    # Previously limited, now everyone can message everyone
    if user.role == 'student':
        groups = Group.objects.filter(enrollment__student=user, enrollment__status='approved')
    elif user.role == 'teacher':
        groups = Group.objects.filter(teacher=user)
    elif user.role == 'assistant':
        groups = Group.objects.filter(assistant=user)
    else: # Admin
        groups = Group.objects.all()

    # All users can see all other users
    contacts = User.objects.exclude(id=user.id).order_by('role', 'username')
    return groups, contacts

@login_required
def chat_list(request):
    groups, contacts = get_chat_context(request.user)
    return render(request, 'chat/room.html', {
        'groups': groups,
        'contacts': contacts,
        'mode': 'list'
    })

@login_required
def chat_direct(request, user_id):
    me = request.user
    other = get_object_or_404(User, id=user_id)
    
    # History
    history = Message.objects.filter(
        Q(sender=me, receiver=other) | Q(sender=other, receiver=me),
        msg_type='direct'
    ).order_by('created_at')
    
    groups, contacts = get_chat_context(me)

    return render(request, 'chat/room.html', {
        'groups': groups,
        'contacts': contacts,
        'chat_partner': other,
        'history': history,
        'mode': 'direct'
    })

@login_required
def chat_group(request, group_id):
    me = request.user
    group = get_object_or_404(Group, id=group_id)
    
    # Security check
    can_access = False
    if me.role == 'admin': can_access = True
    elif me.role == 'teacher' and group.teacher == me: can_access = True
    elif me.role == 'assistant' and group.assistant == me: can_access = True
    elif me.role == 'student' and Enrollment.objects.filter(group=group, student=me, status='approved').exists(): can_access = True
    
    if not can_access:
        messages.error(request, "Kirish cheklangan.")
        return redirect('chat:list')

    history = Message.objects.filter(group=group, msg_type='group').order_by('created_at')
    groups, contacts = get_chat_context(me)

    return render(request, 'chat/room.html', {
        'groups': groups,
        'contacts': contacts,
        'chat_group': group,
        'history': history,
        'mode': 'group'
    })
