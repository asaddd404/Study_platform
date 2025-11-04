from django.contrib.auth import logout, login # <-- 1. ДОБАВЛЕН ИМПОРТ 'login'
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test # <-- 1. ИМПОРТ
from django.contrib.auth import logout, login
from .forms import ProfileForm, CustomUserCreationForm, LessonForm # <-- 2. ИМПОРТ LessonForm
from django.utils import timezone
from .models import Course, Module, Lesson, Resource, Test, TestSubmission, TestAnswer, Progress, User
from django.http import JsonResponse, HttpResponseForbidden # <-- 3. ИМПОРТ
from django.db.models import Q #

def lesson_list_api(request):
    # (Этот код без изменений)
    module_id = request.GET.get('module_id')
    if module_id:
        lessons = Lesson.objects.filter(module_id=module_id).order_by('created_at')
        lesson_data = [{'id': lesson.id, 'title': lesson.title, 'video_url': lesson.video_url, 'content': lesson.content} for lesson in lessons]
        return JsonResponse({'lessons': lesson_data})
    return JsonResponse({'error': 'Module ID is required'}, status=400)

def index(request):
    # (Этот код без изменений)
    course = Course.objects.first()
    modules = Module.objects.filter(course=course).order_by('created_at') if course else []
    return render(request, 'core/index.html', {'course': course, 'modules': modules})

def about(request):
    # (Этот код без изменений)
    return render(request, 'core/about.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) # <-- 3. ИСПОЛЬЗУЕМ ПРАВИЛЬНУЮ ФОРМУ
        if form.is_valid():
            user = form.save() # <-- 4. СОХРАНЯЕМ ПОЛЬЗОВАТЕЛЯ В ПЕРЕМЕННУЮ
            login(request, user) # <-- 5. АВТОМАТИЧЕСКИ ВХОДИМ В СИСТЕМU
            return redirect('core:profile') # <-- 6. ПЕРЕНАПРАВЛЯЕМ В ПРОФИЛЬ
    else:
        form = CustomUserCreationForm()  # <-- 7. ИСПОЛЬЗУЕМ ПРАВИЛЬНУЮ ФОРМУ

    return render(request, 'core/register.html', {'form': form})

@login_required
def course(request):
    # (Этот код без изменений)
    course = Course.objects.first()
    if not course:
        return render(request, 'core/course.html', {'error': 'Курс не найден'})
    modules = Module.objects.filter(course=course).order_by('created_at')
    lessons = Lesson.objects.filter(module__course=course).order_by('module__created_at', 'created_at')
    progress = Progress.objects.filter(student=request.user, lesson__module__course=course)
    completed_lessons = set(progress.filter(passed=True).values_list('lesson_id', flat=True))
    context = {
        'course': course,
        'modules': modules,
        'lessons': lessons,
        'completed_lessons': completed_lessons,
        'progress_percentage': (len(completed_lessons) / lessons.count() * 100) if lessons.count() else 0,
    }
    return render(request, 'core/course.html', context)

@login_required
def lesson(request, lesson_id):
    # (Этот код без изменений)
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    lessons = Lesson.objects.filter(module__course=course).order_by('module__created_at', 'created_at')
    current_index = list(lessons).index(lesson)
    
    if current_index > 0:
        prev_lesson = lessons[current_index - 1]
        if not Progress.objects.filter(student=request.user, lesson=prev_lesson, passed=True).exists() and not lesson.is_free_preview:
            return render(request, 'core/locked.html', {'lesson': lesson, 'message': 'Пройдите предыдущее занятие.'})
            
    progress, created = Progress.objects.get_or_create(student=request.user, lesson=lesson)
    if not progress.passed: 
        progress.completed_at = timezone.now()
        progress.passed = True
        progress.save()
        
    return render(request, 'core/lesson.html', {
        'lesson': lesson, 
        'assignment': lesson.assignment
    })

# Эти views больше не нужны, но пусть остаются, чтобы ничего не сломать
@login_required
def lesson_description(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'core/partials/lesson_description.html', {'lesson': lesson})
@login_required
def lesson_resources(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    resources = lesson.resources.all()
    return render(request, 'core/partials/lesson_resources.html', {'lesson': lesson, 'resources': resources})

@login_required
def test_module(request, module_id):
    # (Этот код без изменений)
    module = get_object_or_404(Module, id=module_id)
    try:
        test = Test.objects.get(module=module)
    except Test.DoesNotExist:
        return render(request, 'core/locked.html', {'lesson': None, 'message': 'Тест для этого модуля еще не создан.'})
        
    lessons = Lesson.objects.filter(module=module)
    
    if not all(Progress.objects.filter(student=request.user, lesson=lesson, passed=True).exists() for lesson in lessons):
        return render(request, 'core/locked.html', {'lesson': None, 'message': 'Пройдите все уроки модуля перед тестированием.'})
        
    if request.method == 'POST':
        submission = TestSubmission(test=test, student=request.user)
        submission.save()
        for question in test.questions.all():
            answer_text = request.POST.get(f'answer_{question.id}', '')
            TestAnswer(submission=submission, question=question, answer_text=answer_text).save()
        submission.calculate_score()
        
        # (Создай файл 'core/templates/core/partials/test_result.html', если хочешь)
        # return render(request, 'core/partials/test_result.html', {'submission': submission, 'test': test})
        return redirect('core:course') # <-- Пока просто перекинем на курс
        
    return render(request, 'core/test_module.html', {'test': test, 'module': module})




# ... (lesson_list_api, index, about, register, course, lesson, ... test_module - БЕЗ ИЗМЕНЕНИЙ) ...
# ...
# ...
@login_required
@teacher_required
def teacher_lesson_create(request):
    if request.method == 'POST':
        form = LessonForm(request.POST, user=request.user) 
        if form.is_valid():
            #
            # <-- 3. НАЗНАЧАЕМ АВТОРА ПРИ СОЗДАНИИ -->
            #
            lesson = form.save(commit=False) # Не сохраняем в БД сразу
            lesson.author = request.user     # Назначаем автором текущего юзера
            lesson.save()                    # Теперь сохраняем
            
            return redirect('core:profile') 
    else:
        form = LessonForm(user=request.user)
        
    return render(request, 'core/teacher/lesson_form.html', {
        'form': form,
        'form_title': 'Добавить новый урок'
    })
# <-- 5. НОВЫЙ ДЕКОРАТОР ДЛЯ ПРОВЕРКИ РОЛИ "УЧИТЕЛЬ" -->
def teacher_required(function):
    # ... (декоратор без изменений) ...
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'teacher':
            return function(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("У вас нет доступа к этой странице.")
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

@login_required
def profile(request):
    
    # ... (Общая логика 'profile_form' без изменений) ...
    profile_form = ProfileForm(instance=request.user)
    if request.method == 'POST' and 'avatar' in request.FILES: # Проверяем, что это форма профиля
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if profile_form.is_valid():
            profile_form.save()
            return redirect('core:profile')
            
    context = {
        'form': profile_form,
    }

    # ... (Логика 'student' без изменений) ...
    if request.user.role == 'student':
        progress = Progress.objects.filter(student=request.user).select_related('lesson', 'lesson__module').order_by('lesson__created_at')
        context['progress'] = progress

    #
    # <-- ИЗМЕНЕННАЯ ЛОГИКА ДЛЯ УЧИТЕЛЯ -->
    #
    if request.user.role == 'teacher':
        # Вкладка "Мои Уроки": Получаем модули, назначенные учителю
        teacher_modules = request.user.taught_modules.all() # <-- 1. ПОЛУЧАЕМ МОДУЛИ
        
        # Получаем уроки ИЗ ЭТИХ модулей
        teacher_lessons = Lesson.objects.filter(
            module__in=teacher_modules
        ).select_related('module', 'module__course', 'author').order_by('-created_at')
        
        context['teacher_lessons'] = teacher_lessons
        context['teacher_modules'] = teacher_modules # Передаем модули (вдруг пригодится)
        
        # Вкладка "Мои Ученики": Поиск и список
        # Находим всех студентов, у которых есть прогресс В ЭТИХ МОДУЛЯХ
        student_ids = Progress.objects.filter(
            lesson__module__in=teacher_modules # <-- 2. ФИЛЬТРУЕМ ПО МОДУЛЯМ
        ).values_list('student_id', flat=True).distinct()
        
        students_queryset = User.objects.filter(
            id__in=student_ids, role='student'
        )

        # ... (Логика поиска 'query' без изменений) ...
        query = request.GET.get('q', '')
        if query:
            students_queryset = students_queryset.filter(
                Q(username__icontains=query) | Q(email__icontains=query)
            )
        
        context['students_list'] = students_queryset.order_by('username')
        context['search_query'] = query


    return render(request, 'core/profile.html', context)

@login_required
def teacher_required(function):
    # ... (декоратор без изменений) ...
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'teacher':
            return function(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("У вас нет доступа к этой странице.")
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
@login_required
@teacher_required
def teacher_lesson_update(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    #
    # <-- 4. НОВАЯ ПРОВЕРКА ДОСТУПА -->
    #
    # Проверка, что учитель редактирует урок из модуля, к которому он привязан
    if request.user not in lesson.module.teachers.all():
         return HttpResponseForbidden("Вы не можете редактировать уроки в этом модуле.")
         
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('core:profile')
    else:
        form = LessonForm(instance=lesson, user=request.user)
        
    return render(request, 'core/teacher/lesson_form.html', {
        'form': form,
        'form_title': f'Редактировать урок: {lesson.title}'
    })

@login_required
@teacher_required
def teacher_lesson_delete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    #
    # <-- 5. НОВАЯ ПРОВЕРКА ДОСТУПА -->
    #
    if request.user not in lesson.module.teachers.all():
         return HttpResponseForbidden("Вы не можете удалять уроки в этом модуле.")
         
    if request.method == 'POST':
        lesson.delete()
        return redirect('core:profile')
        
    return render(request, 'core/teacher/confirm_delete.html', {
        'object_name': f'урок "{lesson.title}"'
    })

# <-- 8. НОВЫЕ VIEWS ДЛЯ ПРОСМОТРА УЧЕНИКОВ -->
# (Список учеников теперь находится во view 'profile')

@login_required
@teacher_required
def teacher_student_list(request):
    # Эта логика была перенесена в 'profile', 
    # но можно оставить и отдельную страницу, если хотите.
    # Для простоты - перенаправим в профиль на нужную вкладку.
    return redirect('core:profile') # В `profile.html` мы сделаем переход на якорь #students

@login_required
@teacher_required
def teacher_student_detail(request, student_id):
    student = get_object_or_404(User, id=student_id, role='student')
    
    # Получаем курсы, которые ведет учитель
    teacher_courses = request.user.taught_courses.all()
    
    # Получаем прогресс студента ТОЛЬКО по курсам этого учителя
    progress = Progress.objects.filter(
        student=student,
        lesson__module__course__in=teacher_courses
    ).select_related('lesson', 'lesson__module').order_by('lesson__created_at')
    
    # Получаем сдачи тестов студента ТОЛЬКО по курсам этого учителя
    submissions = TestSubmission.objects.filter(
        student=student,
        test__module__course__in=teacher_courses
    ).select_related('test', 'test__module').order_by('-submitted_at')
    
    return render(request, 'core/teacher/student_detail.html', {
        'student': student,
        'progress': progress,
        'submissions': submissions
    })


def custom_logout(request):
    logout(request)
    return render(request, 'core/logged_out.html')

# <-- УДАЛЕНА ЛИШНЯЯ СКОБКА (как в прошлый раз)