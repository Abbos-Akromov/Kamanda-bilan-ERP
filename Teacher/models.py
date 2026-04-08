from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TeacherProfile(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    specialization   = models.CharField(max_length=200, blank=True, verbose_name='Mutaxassislik')
    experience_years = models.PositiveIntegerField(default=0, verbose_name='Tajriba (yil)')
    bio              = models.TextField(blank=True, verbose_name='Haqida')
    salary           = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Maosh')

    class Meta:
        verbose_name = "O'qituvchi profili"
        verbose_name_plural = "O'qituvchi profillari"

    def __str__(self):
        return f"{self.user.get_full_name()} profili"


class Course(models.Model):
    STATUS_CHOICES = [
        ('active',    'Faol'),
        ('inactive',  'Nofaol'),
        ('completed', 'Tugallangan'),
    ]
    name            = models.CharField(max_length=200, verbose_name='Kurs nomi')
    description     = models.TextField(blank=True, verbose_name='Tavsif')
    teacher         = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        limit_choices_to={'auth_role': 'Teacher'},
        related_name='teaching_courses',
        verbose_name="O'qituvchi"
    )
    price           = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Narx (so\'m)')
    duration_months = models.PositiveIntegerField(default=1, verbose_name='Davomiylik (oy)')
    schedule        = models.CharField(max_length=200, blank=True, verbose_name='Dars jadvali')
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    max_students    = models.PositiveIntegerField(default=20, verbose_name='Maks. talabalar')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Kurs'
        verbose_name_plural = 'Kurslar'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def student_count(self):
        return self.enrollments.filter(is_active=True).count()


class Enrollment(models.Model):
    student      = models.ForeignKey(
        User, on_delete=models.CASCADE,
        limit_choices_to={'auth_role': 'Student'},
        related_name='enrollments',
        verbose_name='Talaba'
    )
    course       = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Kurs'
    )
    enrolled_date = models.DateField(auto_now_add=True, verbose_name='Yozilgan sana')
    end_date      = models.DateField(null=True, blank=True, verbose_name='Tugash sanasi')
    is_active     = models.BooleanField(default=True)
    discount      = models.PositiveIntegerField(default=0, verbose_name='Chegirma (%)')

    class Meta:
        verbose_name = 'Yozilish'
        verbose_name_plural = 'Yozilishlar'
        unique_together = ('Student', 'course')

    def __str__(self):
        return f"{self.student.get_full_name()} → {self.course.name}"

    @property
    def monthly_payment(self):
        return self.course.price * (100 - self.discount) / 100


class Lesson(models.Model):
    course      = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title       = models.CharField(max_length=200, verbose_name='Mavzu')
    date        = models.DateField(verbose_name='Sana')
    description = models.TextField(blank=True, verbose_name='Qo\'shimcha')

    class Meta:
        verbose_name = 'Dars'
        verbose_name_plural = 'Darslar'
        ordering = ['date']

    def __str__(self):
        return f"{self.course.name} — {self.title} ({self.date})"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Keldi'),
        ('absent',  'Kelmadi'),
        ('late',    'Kech keldi'),
        ('excused', 'Uzrli'),
    ]
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Yozilish'
    )
    lesson     = models.ForeignKey(
        Lesson, on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Dars'
    )
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')
    marked_by  = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='marked_attendances',
        verbose_name="O'qituvchi"
    )
    note       = models.CharField(max_length=200, blank=True, verbose_name='Izoh')
    marked_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Davomat'
        verbose_name_plural = 'Davomatlar'
        unique_together = ('enrollment', 'lesson')

    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} | {self.lesson} | {self.get_status_display()}"


class Grade(models.Model):
    TYPE_CHOICES = [
        ('homework', 'Uy vazifasi'),
        ('quiz',     'Test'),
        ('exam',     'Imtihon'),
        ('project',  'Loyiha'),
        ('monthly',  'Oylik baho'),
    ]
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE,
        related_name='grades',
        verbose_name='Yozilish'
    )
    grade_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='Turi')
    title      = models.CharField(max_length=200, verbose_name='Sarlavha')
    score      = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Ball')
    max_score  = models.DecimalField(max_digits=5, decimal_places=2, default=100, verbose_name='Maks. ball')
    date       = models.DateField(verbose_name='Sana')
    given_by   = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='given_grades',
        verbose_name="O'qituvchi"
    )
    comment    = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Baho'
        verbose_name_plural = 'Baholar'
        ordering = ['-date']

    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} — {self.title}: {self.score}/{self.max_score}"

    @property
    def percentage(self):
        return round(float(self.score) / float(self.max_score) * 100, 1) if self.max_score else 0

    @property
    def letter_grade(self):
        p = self.percentage
        if p >= 90: return 'A'
        if p >= 80: return 'B'
        if p >= 70: return 'C'
        if p >= 60: return 'D'
        return 'F'