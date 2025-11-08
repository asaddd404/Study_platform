from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone # <-- Убедитесь, что этот импорт есть
import uuid
import re

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

    teachers = models.ManyToManyField(
        User,
        related_name="taught_modules", 
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


class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons", verbose_name=_("Модуль"))
    title = models.CharField(max_length=200, verbose_name=_("Название занятия"))
    content = models.TextField(blank=True, verbose_name=_("Содержание"))
    
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
    passing_score = models.PositiveIntegerField(
        default=70, 
        validators=[MinValueValidator(0)], 
        verbose_name=_("Проходной балл (в %)")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))

    class Meta:
        verbose_name = _("Тест")
        verbose_name_plural = _("Тесты")

    def __str__(self):
        return self.title
        
    def get_max_score(self):
        # <--- НОВЫЙ МЕТОД: Поможет нам быстро посчитать макс. балл за тест
        return self.questions.all().aggregate(models.Sum('max_score'))['max_score__sum'] or 0


class TestQuestion(models.Model):
    # 1. <--- ИЗМЕНЕНЫ ТИПЫ ВОПРОСОВ
    QUESTION_TYPE_CHOICES = (
        ('choice', 'Выбор из вариантов'),
        ('open_ended', 'Развернутый ответ (проверяется учителем)'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions", verbose_name=_("Тест"))
    text = models.TextField(verbose_name=_("Текст вопроса"))
    
    # 2. ПОЛЕ ДЛЯ ВЫБОРА ТИПА
    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPE_CHOICES,
        default='choice', # <-- Изменим стандартный на 'choice'
        verbose_name="Тип вопроса"
    )

    # 3. ПОЛЯ ДЛЯ ВАРИАНТОВ ОТВЕТА (только для 'choice')
    option_a = models.CharField(max_length=255, blank=True, null=True, verbose_name="Вариант А")
    option_b = models.CharField(max_length=255, blank=True, null=True, verbose_name="Вариант Б")
    option_c = models.CharField(max_length=255, blank=True, null=True, verbose_name="Вариант В")
    option_d = models.CharField(max_length=255, blank=True, null=True, verbose_name="Вариант Г")

    # 4. ПРАВИЛЬНЫЙ ОТВЕТ (только для 'choice')
    # <--- ИЗМЕНЕНО: Сделаем необязательным
    correct_answer = models.CharField(
        max_length=255, 
        blank=True, null=True, 
        verbose_name="Правильный ответ (для 'Выбора из вариантов')"
    )
    
    # 5. БАЛЛ ЗА ВОПРОС (для всех типов)
    max_score = models.PositiveIntegerField(default=1, verbose_name="Макс. балл за этот вопрос")
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_("Дата создания"))

    class Meta:
        verbose_name = _("Вопрос теста")
        verbose_name_plural = _("Вопросы теста")

    def __str__(self):
        return self.text[:50]


class TestSubmission(models.Model):
    # <--- НОВОЕ: Статусы проверки
    STATUS_PENDING = 'pending'
    STATUS_GRADED = 'graded'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'На проверке'),
        (STATUS_GRADED, 'Проверено'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="submissions", verbose_name=_("Тест"))
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="test_submissions", verbose_name=_("Студент"))
    score = models.FloatField(default=0, verbose_name=_("Итоговый балл (%)")) 
    passed = models.BooleanField(default=False, verbose_name=_("Пройден"))
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата отправки"))
    
    # <--- НОВОЕ: Поле статуса
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="Статус проверки"
    )

    class Meta:
        verbose_name = _("Попытка теста")
        verbose_name_plural = _("Попытки тестов")

    def __str__(self):
        return f"{self.student.username} - {self.test.title}"

    # <--- 1. ПЕРЕИМЕНОВАННЫЙ И ИЗМЕНЕННЫЙ МЕТОД (бывший calculate_score)
    def auto_grade(self):
        """
        Автоматически оценивает ответы типа 'choice' 
        и обновляет статус попытки.
        """
        has_open_ended_questions = False
        
        for answer in self.answers.all().select_related('question'):
            question = answer.question
            
            if question.question_type == 'choice':
                student_text = (answer.answer_text or "").strip().lower()
                correct_text = (question.correct_answer or "").strip().lower()
                
                if student_text == correct_text:
                    answer.score = question.max_score
                else:
                    answer.score = 0
                answer.save() # <-- Сохраняем балл в самом ответе
            
            elif question.question_type == 'open_ended':
                has_open_ended_questions = True
        
        # Если были вопросы с ручной проверкой, ставим "На проверке"
        if has_open_ended_questions:
            self.status = self.STATUS_PENDING
        else:
            # Если все вопросы были 'choice', можно сразу считать итог
            self.status = self.STATUS_GRADED
            self.update_final_score() # <-- Сразу вызываем расчет итога

        self.save()

    # <--- 2. НОВЫЙ МЕТОД: Расчет итогового балла
    def update_final_score(self):
        """
        Считает итоговый балл (в %) на основе баллов из TestAnswer.
        Вызывается либо после auto_grade (если нет ручных), 
        либо учителем после ручной проверки.
        """
        
        # Суммируем все баллы, которые стоят в ответах (TestAnswer)
        total_score = self.answers.all().aggregate(
            models.Sum('score')
        )['score__sum'] or 0
        
        # Получаем макс. возможный балл за тест
        max_possible_score = self.test.get_max_score()

        self.score = (total_score / max_possible_score) * 100 if max_possible_score else 0
        self.passed = self.score >= self.test.passing_score
        self.status = self.STATUS_GRADED # <--- Ставим статус "Проверено"
        self.save()
        
        return self.score


class TestAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(TestSubmission, on_delete=models.CASCADE, related_name="answers", verbose_name=_("Попытка теста"))
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name="answers", verbose_name=_("Вопрос"))
    answer_text = models.TextField(blank=True, verbose_name=_("Ответ студента")) # <-- Изменил на TextField для развернутых ответов
    
    # <--- НОВОЕ ПОЛЕ: Сюда пишется балл за этот конкретный ответ
    score = models.PositiveIntegerField(default=0, verbose_name="Балл за ответ")

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