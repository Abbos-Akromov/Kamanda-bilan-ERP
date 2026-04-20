from django.urls import path
from . import views

app_name = 'certificates'
urlpatterns = [
    path('issue/', views.issue_certificate, name='issue'),
    path('verify/<str:code>/', views.verify_certificate, name='verify'),
    path('admin-list/', views.admin_certificate_list, name='admin_list'),
    path('revoke/<int:pk>/', views.revoke_certificate, name='revoke'),
]

