from django.db import models
from apps.accounts.models import User

class Notification(models.Model):
    TYPES = [('lesson_added','Lesson'),('test_started','Test'),
             ('payment_reminder','Payment'),('announcement','Announcement'),
             ('lesson_reminder', 'Dars Eslatmasi'),
             ('chat_message', 'Chat Xabari')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()
    notif_type = models.CharField(max_length=30, choices=TYPES)
    link = models.CharField(max_length=500, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
