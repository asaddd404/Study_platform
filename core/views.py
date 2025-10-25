from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import Course, Module, Lesson, Resource, Test, TestSubmission, TestAnswer, Progress, User
from .forms import ProfileForm
from django.http import JsonResponse

def lesson_list_api(request):
    module_id = request.GET.get('module_id')
    if module_id:
        lessons = Lesson.objects.filter(module_id=module_id).order_by('created_at')
        lesson_data = [{'id': lesson.id, 'title': lesson.title, 'video_url': lesson.video_url, 'content': lesson.content} for lesson in lessons]
        return JsonResponse({'lessons': lesson_data})
    return JsonResponse({'error': 'Module ID is required'}, status=400)

def index(request):
    course = Course.objects.first()
    modules = Module.objects.filter(course=course).order_by('created_at') if course else []
    return render(request, 'core/index.html', {'course': course, 'modules': modules})

def about(request):
    return render(request, 'core/about.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'
            user.save()
            login(request, user)
            return redirect('core:profile')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def course(request):
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
    print(f"Передано модулей: {modules.count()}, уроков: {lessons.count()}")  # Отладка
    for module in modules:
        lesson_count = lessons.filter(module=module).count()
        print(f"Модуль {module.title} имеет {lesson_count} уроков")
    return render(request, 'core/course.html', context)

@login_required
def lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    lessons = Lesson.objects.filter(module__course=course).order_by('module__created_at', 'created_at')
    current_index = list(lessons).index(lesson)
    if current_index > 0:
        prev_lesson = lessons[current_index - 1]
        if not Progress.objects.filter(student=request.user, lesson=prev_lesson, passed=True).exists() and not lesson.is_free_preview:
            return render(request, 'core/locked.html', {'lesson': lesson, 'message': 'Пройдите предыдущее занятие.'})
    progress, created = Progress.objects.get_or_create(student=request.user, lesson=lesson)
    if not progress.completed_at:
        progress.completed_at = timezone.now()
        progress.passed = True
        progress.save()
    return render(request, 'core/lesson.html', {'lesson': lesson, 'assignment': lesson.assignment})

@login_required
def lesson_description(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'core/lesson_description.html', {'lesson': lesson})

@login_required
def lesson_resources(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    resources = lesson.resources.all()
    return render(request, 'core/lesson_resources.html', {'lesson': lesson, 'resources': resources})

@login_required
def test_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    test = get_object_or_404(Test, module=module)
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
        if submission.passed:
            next_module = Module.objects.filter(course=module.course, created_at__gt=module.created_at).order_by('created_at').first()
            if next_module:
                next_lessons = Lesson.objects.filter(module=next_module)
                for lesson in next_lessons:
                    Progress.objects.get_or_create(student=request.user, lesson=lesson)
        return redirect('core:course')
    return render(request, 'core/test_module.html', {'test': test, 'module': module})

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('core:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'core/profile.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect('core:index')