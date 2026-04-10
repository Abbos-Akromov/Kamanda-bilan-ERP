from django.urls import path
from . import views_dashboard

app_name = 'dashboard'
urlpatterns = [
    path('', views_dashboard.dashboard_home, name='home'),
    path('student/', views_dashboard.student_dashboard, name='student'),
    path('teacher/', views_dashboard.teacher_dashboard, name='teacher'),
    path('assistant/', views_dashboard.assistant_dashboard, name='assistant'),
    path('admin/', views_dashboard.admin_dashboard, name='admin'),
]
