from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from datetime import timedelta
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
        return f"{self.username} ({self.auth_role})"


class TeacherProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    specialization = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bio = models.TextField(blank=True)


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    parent_phone = models.CharField(max_length=20, blank=True)


class Course(models.Model):
    name = models.CharField(max_length=200)
    teacher = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='courses')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, default='active')

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)


# MANA SHU MODEL SIZDA YETISHMAYOTGAN EDI:
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.course.name} - {self.title}"


class Attendance(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendances')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=10, default='absent')  # present, absent, late
    marked_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    marked_at = models.DateTimeField(auto_now=True)


class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='grades')
    title = models.CharField(max_length=200)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    grade_type = models.CharField(max_length=20)  # homework, exam
    date = models.DateField()
    given_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)


class Payment(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    status = models.CharField(max_length=20, default='paid')


class CodeVerify(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expiration_time = models.DateTimeField()