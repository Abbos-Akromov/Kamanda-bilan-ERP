from django.urls import path
from . import views, views_dashboard

app_name = 'accounts'
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views_dashboard.profile_settings, name='profile'),
    path('user/<int:user_id>/', views_dashboard.public_profile, name='public_profile'),
]
