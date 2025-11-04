from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Ученик'),
        ('teacher', 'Учитель'),
        ('manager', 'Менеджер'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name=_("Роль"))
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name=_("Аватар"))
    bio = models.TextField(blank=True, verbose_name=_("О себе"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Телефон"))
    is_teacher_approved = models.BooleanField(default=False, verbose_name=_("Учитель подтверждён"))
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_groups',
        blank=True,
        verbose_name=_("Группы"),
        help_text=_("Группы, к которым принадлежит пользователь."),
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_permissions',
        blank=True,
        verbose_name=_("Разрешения пользователя"),
        help_text=_("Индивидуальные разрешения пользователя."),
    )

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")

    def __str__(self):
        return self.username

class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, default="Культура речи и стилистика", verbose_name=_("Название курса"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    cover_image = models.ImageField(upload_to='course_covers/', blank=True, null=True, verbose_name=_("Обложка"))
    published = models.BooleanField(default=False, verbose_name=_("Опубликован"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    
    # <-- НОВОЕ ПОЛЕ: СВЯЗЬ С УЧИТЕЛЯМИ -->
    teachers = models.ManyToManyField(
        User, 
        related_name="taught_courses", 
        limit_choices_to={'role': 'teacher'}, 
        blank=True,
        verbose_name=_("Преподаватели")
    )

    class Meta:
        verbose_name = _("Курс")
        verbose_name_plural = _("Курсы")

    def __str__(self):
        return self.title

class Module(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules", verbose_name=_("Курс"))
    title = models.CharField(max_length=200, verbose_name=_("Название модуля"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))

    # <-- 1. НОВОЕ ПОЛЕ: УЧИТЕЛЯ, ОТВЕТСТВЕННЫЕ ЗА МОДУЛЬ -->
    teachers = models.ManyToManyField(
        User,
        related_name="taught_modules", # Новое связанное имя
        limit_choices_to={'role': 'teacher'},
        blank=True,
        verbose_name=_("Преподаватели модуля")
    )

    class Meta:
        verbose_name = _("Модуль")
        verbose_name_plural = _("Модули")
        ordering = ['created_at']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


pass

class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons", verbose_name=_("Модуль"))
    title = models.CharField(max_length=200, verbose_name=_("Название занятия"))
    content = models.TextField(blank=True, verbose_name=_("Содержание"))
    
    # --- 1. ИЗМЕНЕНИЯ ЗДЕСЬ ---
    video_url = models.URLField(blank=True, null=True, verbose_name=_("URL видео (Youtube/Vimeo)"))
    
    video_file = models.FileField(
        upload_to='lesson_videos/', blank=True, null=True, 
        verbose_name=_("Видео-файл (MP4, AVI)")
    )
    image_file = models.ImageField(
        upload_to='lesson_images/', blank=True, null=True, 
        verbose_name=_("Изображение (JPG, PNG)")
    )
    pdf_file = models.FileField(
        upload_to='lesson_pdfs/', blank=True, null=True, 
        verbose_name=_("PDF-файл")
    )
    # --- (Конец изменений) ---
    
    is_free_preview = models.BooleanField(default=False, verbose_name=_("Бесплатный предпросмотр"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    assignment = models.TextField(blank=True, verbose_name=_("Задание"))
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name="authored_lessons",
        limit_choices_to={'role': 'teacher'},
        verbose_name=_("Автор урока")
    )

    class Meta:
        verbose_name = _("Занятие")
        verbose_name_plural = _("Занятия")
        ordering = ['created_at']

    def __str__(self):
        return f"{self.module.title} - {self.title}"

class Resource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name="resources", null=True, verbose_name=_("Занятие"))
    title = models.CharField(max_length=200, verbose_name=_("Название материала"))
    file = models.FileField(upload_to='resources/', blank=True, null=True, verbose_name=_("Файл"))
    url = models.URLField(blank=True, null=True, verbose_name=_("Ссылка"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата добавления"))

    class Meta:
        verbose_name = _("Материал")
        verbose_name_plural = _("Материалы")

    def __str__(self):
        return self.title

class Test(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="tests", verbose_name=_("Модуль"))
    title = models.CharField(max_length=200, verbose_name=_("Название теста"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))

    class Meta:
        verbose_name = _("Тест")
        verbose_name_plural = _("Тесты")

    def __str__(self):
        return self.title

class TestQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions", verbose_name=_("Тест"))
    text = models.TextField(verbose_name=_("Текст вопроса"))
    correct_answer = models.CharField(max_length=200, blank=True, verbose_name=_("Правильный ответ"))
    max_score = models.PositiveIntegerField(default=10, verbose_name=_("Максимальный балл"))

    class Meta:
        verbose_name = _("Вопрос теста")
        verbose_name_plural = _("Вопросы теста")

    def __str__(self):
        return self.text[:50]

class TestSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="submissions", verbose_name=_("Тест"))
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="test_submissions", verbose_name=_("Студент"))
    score = models.FloatField(default=0, verbose_name=_("Балл"))
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата отправки"))
    passed = models.BooleanField(default=False, verbose_name=_("Пройден"))

    class Meta:
        verbose_name = _("Ответ на тест")
        verbose_name_plural = _("Ответы на тесты")

    def __str__(self):
        return f"{self.student.username} - {self.test.title}"

    def calculate_score(self):
        answers = self.answers.all()
        total_score = 0
        max_possible_score = sum(question.max_score for question in self.test.questions.all())
        for answer in answers:
            if answer.answer_text.lower() == answer.question.correct_answer.lower():
                total_score += answer.question.max_score
        self.score = total_score
        self.passed = self.score >= (max_possible_score * 0.7)
        self.save()
        return self.score

class TestAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(TestSubmission, on_delete=models.CASCADE, related_name="answers", verbose_name=_("Ответ на тест"))
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name="answers", verbose_name=_("Вопрос"))
    answer_text = models.CharField(max_length=200, blank=True, verbose_name=_("Ответ студента"))

    class Meta:
        verbose_name = _("Ответ на вопрос теста")
        verbose_name_plural = _("Ответы на вопросы теста")

    def __str__(self):
        return self.answer_text[:50]

class Progress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="progress", verbose_name=_("Студент"))
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress", verbose_name=_("Занятие"))
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Дата завершения"))
    passed = models.BooleanField(default=False, verbose_name=_("Пройдено"))

    class Meta:
        verbose_name = _("Прогресс")
        verbose_name_plural = _("Прогресс")
        unique_together = ['student', 'lesson']

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"