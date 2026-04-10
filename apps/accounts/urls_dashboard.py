from django.urls import path
from . import views_dashboard

app_name = 'dashboard'
urlpatterns = [
    path('', views_dashboard.dashboard_home, name='home'),
    path('student/', views_dashboard.student_dashboard, name='student'),
    path('teacher/', views_dashboard.teacher_dashboard, name='teacher'),
    path('assistant/', views_dashboard.assistant_dashboard, name='assistant'),
    path('admin/', views_dashboard.admin_dashboard, name='admin'),
    path('preview/group/<int:group_id>/', views_dashboard.group_preview, name='group_preview'),
    path('preview/user/<int:user_id>/', views_dashboard.user_preview, name='user_preview'),
    path('user/<int:user_id>/update/', views_dashboard.update_user, name='update_user'),
    path('user/<int:user_id>/delete/', views_dashboard.delete_user, name='delete_user'),
    path('enrollment/<int:enrollment_id>/remove/', views_dashboard.remove_from_group, name='remove_from_group'),
    path('enrollment/<int:enrollment_id>/change-group/', views_dashboard.change_student_group, name='change_student_group'),
    path('group/<int:group_id>/update/', views_dashboard.update_group, name='update_group'),
    path('group/<int:group_id>/delete/', views_dashboard.delete_group, name='delete_group'),
    path('group/<int:group_id>/extend-schedule/', views_dashboard.extend_lessons, name='extend_lessons'),
    path('group/<int:group_id>/update-percent/', views_dashboard.update_group_percent, name='update_group_percent'),
    path('lesson/<int:lesson_id>/update/', views_dashboard.update_lesson, name='update_lesson'),
]

