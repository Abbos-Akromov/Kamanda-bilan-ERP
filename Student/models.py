from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils import timezone


ADMIN, TEACHER, STUDENT, WAIT = ('Admin', 'Teacher', 'Student', 'wait')
NEW, CODE_VERIFY, DONE = ('new', 'code_verify', 'done')



class CustomUser(AbstractUser):
    USER_ROLE = ((ADMIN, ADMIN), (TEACHER, TEACHER), (STUDENT, STUDENT), (WAIT, WAIT))
    USER_STATUS = ((NEW, NEW), (CODE_VERIFY, CODE_VERIFY), (DONE, DONE))

    auth_role = models.CharField(choices=USER_ROLE, default=WAIT, max_length=20)
    auth_status = models.CharField(choices=USER_STATUS, default=NEW, max_length=20)
    email = models.EmailField(unique=True)
    phone = models.CharField(unique=True, max_length=13, blank=True, null=True)
    photo = models.ImageField(upload_to='user_photo/', blank=True, null=True,
                              validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg', 'heic'])])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    @property
    def is_online(self):
        return cache.get(f"last-seen-{self.id}") is not None



class TeacherProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    specialization = models.CharField(max_length=255, verbose_name="Mutaxassisligi")
    experience_years = models.IntegerField(default=0, verbose_name="Tajribasi (yil)")
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Oylik maoshi")
    bio = models.TextField(blank=True)


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True, verbose_name='Talaba ID')
    parent_name = models.CharField(max_length=200, blank=True, verbose_name='Ota-ona ismi')
    parent_phone = models.CharField(max_length=20, blank=True, verbose_name='Ota-ona telefoni')
    discount_percent = models.PositiveIntegerField(default=0, verbose_name='Chegirma (%)')

    def __str__(self):
        return f"{self.user.username} | {self.student_id}"



class Course(models.Model):
    STATUS_CHOICES = [('active', 'Faol'), ('inactive', 'Nofaol'), ('completed', 'Tugallangan')]
    name = models.CharField(max_length=200, verbose_name='Kurs nomi')
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True,
                                limit_choices_to={'auth_role': 'Teacher'}, related_name='teaching_courses')
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    duration_months = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                limit_choices_to={'auth_role': 'Student'}, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    discount = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('Student', 'course')


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField(blank=True)



class Attendance(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendances')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=10, default='absent',
                              choices=[('present', 'Keldi'), ('absent', 'Kelmadi'), ('late', 'Kechikdi')])
    marked_at = models.DateTimeField(auto_now=True)


class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='grades')
    title = models.CharField(max_length=200)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()



class Payment(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    status = models.CharField(max_length=10, default='paid')


class Expense(models.Model):
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    category = models.CharField(max_length=100)


class CodeVerify(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verify_codes')
    code = models.CharField(max_length=6)
    expiration_time = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.expiration_time:
            self.expiration_time = timezone.now() + timedelta(minutes=2)
        super().save(*args, **kwargs)