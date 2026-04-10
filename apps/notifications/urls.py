from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('admin/', views.notification_admin_dashboard, name='admin_dashboard'),
    path('send-broadcast/', views.send_broadcast, name='send_broadcast'),
    path('mark-read/<int:pk>/', views.mark_notification_read, name='mark_read'),
]