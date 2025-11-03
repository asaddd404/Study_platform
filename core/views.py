from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
#
# ИСПРАВЛЕНИЕ:
#
# from django.contrib.auth.forms import UserCreationForm # <-- УДАЛЕНО
from .forms import ProfileForm, CustomUserCreationForm # <-- ИМПОРТИРУЕМ НАШУ ФОРМУ
#
from django.utils import timezone
from .models import Course, Module, Lesson, Resource, Test, TestSubmission, TestAnswer, Progress, User
from django.http import JsonResponse
from .forms import RegisterForm

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
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()  # ← Без request.POST!

    return render(request, 'register.html', {'form': form})

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
    # (Этот код без изменений, но я добавлю проверку на наличие теста)
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

@login_required
def profile(request):
    # (Этот код без изменений)
    progress = None
    submissions = None
    if request.user.role == 'student':
        progress = Progress.objects.filter(student=request.user).select_related('lesson', 'lesson__module').order_by('lesson__created_at')
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('core:profile')
    else:
        form = ProfileForm(instance=request.user)
        
    return render(request, 'core/profile.html', {
        'form': form,
        'progress': progress,
        'submissions': submissions
    })

def custom_logout(request):
    logout(request)
    return render(request, 'core/logged_out.html')