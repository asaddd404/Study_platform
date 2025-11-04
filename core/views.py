from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test 
from django.contrib.auth import logout, login
# --- 1. ИМПОРТИРУЕМ НОВЫЕ ФОРМЫ ---
from .forms import (
    ProfileForm, CustomUserCreationForm, LessonForm, 
    TestForm, QuestionForm
)
from django.utils import timezone
from .models import Course, Module, Lesson, Resource, Test, TestSubmission, TestAnswer, Progress, User, TestQuestion
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.db.models import Q 
from django.urls import reverse


# <-- 5. ДЕКОРАТОР ПЕРЕМЕЩЕН СЮДА, В НАЧАЛО ФАЙЛА -->
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
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), id=lesson_id)
    course = lesson.module.course
    lessons = Lesson.objects.filter(module__course=course).order_by('module__created_at', 'created_at')
    current_index = list(lessons).index(lesson)
    
    # Проверка на прохождение предыдущего урока
    if current_index > 0:
        prev_lesson = lessons[current_index - 1]
        if not Progress.objects.filter(student=request.user, lesson=prev_lesson, passed=True).exists() and not lesson.is_free_preview:
            return render(request, 'core/locked.html', {'lesson': lesson, 'message': 'Пройдите предыдущее занятие.'})
            
    # --- 2. ЛОГИКА АВТО-ЗАВЕРШЕНИЯ УДАЛЕНА ---
    # (Мы больше не ставим 'passed=True' просто за просмотр)
    progress, created = Progress.objects.get_or_create(student=request.user, lesson=lesson)
        
    return render(request, 'core/lesson.html', {
        'lesson': lesson, 
        'assignment': lesson.assignment,
        'progress': progress, # <-- Передаем прогресс в шаблон
        'resources': lesson.resources.all() # <-- Передаем ресурсы
    })
@login_required
def complete_lesson(request, lesson_id):
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id)
        progress, created = Progress.objects.get_or_create(student=request.user, lesson=lesson)
        
        if not progress.passed:
            progress.passed = True
            progress.completed_at = timezone.now()
            progress.save()
            
    # Возвращаем пользователя обратно на урок
    return redirect('core:lesson', lesson_id=lesson_id)
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
    # --- 6. Получаем ID модуля из URL (для кнопки "Добавить урок" в модуле) ---
    module_id = request.GET.get('module_id')
    initial_data = {}
    if module_id:
        if Module.objects.filter(id=module_id, teachers=request.user).exists():
             initial_data['module'] = module_id

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, user=request.user) # <-- Добавлен request.FILES
        if form.is_valid():
            lesson = form.save(commit=False) 
            lesson.author = request.user     
            lesson.save()                    
            return redirect('core:profile') 
    else:
        form = LessonForm(user=request.user, initial=initial_data) # <-- Передаем initial_data
        
    return render(request, 'core/teacher/lesson_form.html', {
        'form': form,
        'form_title': 'Добавить новый урок'
    })



# <-- ОПРЕДЕЛЕНИЕ ДЕКОРАТОРА ОТСЮДА УДАЛЕНО -->

@login_required
def profile(request):
    # ... (логика 'profile_form' без изменений) ...
    profile_form = ProfileForm(instance=request.user)
    if request.method == 'POST' and 'username' in request.POST: 
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if profile_form.is_valid():
            profile_form.save()
            return redirect('core:profile')
            
    context = {
        'form': profile_form,
    }

    if request.user.role == 'student':
        # ... (логика 'student' без изменений) ...
        pass

    if request.user.role == 'teacher':
        # --- 4. ОБНОВЛЕННАЯ ЛОГИКА ДЛЯ ГРУППИРОВКИ ---
        # Получаем модули и сразу все связанные с ними уроки и тесты
        teacher_modules = request.user.taught_modules.all().prefetch_related(
            'lessons', 'tests'
        )
        
        context['teacher_modules'] = teacher_modules # <-- Передаем модули
        
        # ... (логика поиска студентов 'students_queryset' без изменений) ...
        student_ids = Progress.objects.filter(
            lesson__module__in=teacher_modules
        ).values_list('student_id', flat=True).distinct()
        students_queryset = User.objects.filter(id__in=student_ids, role='student')
        query = request.GET.get('q', '')
        if query:
            students_queryset = students_queryset.filter(
                Q(username__icontains=query) | Q(email__icontains=query)
            )
        context['students_list'] = students_queryset.order_by('username')
        context['search_query'] = query

    return render(request, 'core/profile.html', context)


#

# <-- ВТОРОЕ (ЛИШНЕЕ) ОПРЕДЕЛЕНИЕ ДЕКОРАТОРА УДАЛЕНО ОТСЮДА -->

@login_required
@teacher_required
def teacher_lesson_update(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if request.user not in lesson.module.teachers.all():
         return HttpResponseForbidden("Вы не можете редактировать уроки в этом модуле.")
         
    if request.method == 'POST':
        # <-- Добавлен request.FILES для загрузки файлов -->
        form = LessonForm(request.POST, request.FILES, instance=lesson, user=request.user)
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
def teacher_test_create(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    
    # Проверка, что учитель привязан к этому модулю
    if request.user not in module.teachers.all():
        return HttpResponseForbidden("Вы не можете добавлять тесты в этот модуль.")
        
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.module = module
            test.save()
            # Перенаправляем на страницу редактирования теста для добавления вопросов
            return redirect('core:teacher_test_update', test_id=test.id)
    else:
        form = TestForm()
        
    return render(request, 'core/teacher/test_form.html', {
        'form': form,
        'form_title': f'Новый тест для модуля: {module.title}'
    })

@login_required
@teacher_required
def teacher_test_update(request, test_id):
    test = get_object_or_404(Test.objects.prefetch_related('questions'), id=test_id)
    
    # Проверка, что учитель привязан к модулю этого теста
    if request.user not in test.module.teachers.all():
        return HttpResponseForbidden("Вы не можете редактировать этот тест.")
        
    # Форма для редактирования самого теста
    if 'submit_test_form' in request.POST:
        test_form = TestForm(request.POST, instance=test)
        if test_form.is_valid():
            test_form.save()
            return redirect('core:teacher_test_update', test_id=test.id)
    else:
        test_form = TestForm(instance=test)
        
    # Форма для добавления НОВОГО вопроса
    if 'submit_question_form' in request.POST:
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.test = test
            question.save()
            return redirect('core:teacher_test_update', test_id=test.id)
    else:
        question_form = QuestionForm()

    return render(request, 'core/teacher/test_update_form.html', {
        'test': test,
        'test_form': test_form,
        'question_form': question_form,
        'questions': test.questions.all() # Передаем список вопросов
    })

@login_required
@teacher_required
def teacher_test_delete(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    if request.user not in test.module.teachers.all():
         return HttpResponseForbidden("Вы не можете удалить этот тест.")
         
    if request.method == 'POST':
        test.delete()
        return redirect('core:profile')
    
    return render(request, 'core/teacher/confirm_delete.html', {
        'object_name': f'тест "{test.title}"'
    })

@login_required
@teacher_required
def teacher_question_update(request, question_id):
    question = get_object_or_404(TestQuestion.objects.select_related('test__module'), id=question_id)
    test = question.test
    
    if request.user not in test.module.teachers.all():
         return HttpResponseForbidden("Вы не можете редактировать этот вопрос.")
         
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            # Возвращаемся на страницу редактирования теста
            return redirect('core:teacher_test_update', test_id=test.id)
    else:
        form = QuestionForm(instance=question)
        
    return render(request, 'core/teacher/question_form.html', {
        'form': form,
        'form_title': 'Редактировать вопрос'
    })

@login_required
@teacher_required
def teacher_question_delete(request, question_id):
    question = get_object_or_404(TestQuestion.objects.select_related('test'), id=question_id)
    test_id = question.test.id
    
    if request.user not in question.test.module.teachers.all():
         return HttpResponseForbidden("Вы не можете удалить этот вопрос.")
         
    if request.method == 'POST':
        question.delete()
        return redirect('core:teacher_test_update', test_id=test_id)
    
    return render(request, 'core/teacher/confirm_delete.html', {
        'object_name': f'вопрос "{question.text[:50]}..."'
    })

# ... (teacher_student_list, teacher_student_detail - без изменений) ...
# ...

# --- 8. НОВАЯ VIEW ДЛЯ УДАЛЕНИЯ ПРОГРЕССА УЧЕНИКА ---
@login_required
@teacher_required
def teacher_remove_student(request, student_id):
    student = get_object_or_404(User, id=student_id, role='student')
    
    if request.method == 'POST':
        # Находим все модули, которые ведет этот учитель
        teacher_modules = request.user.taught_modules.all()
        
        # Удаляем прогресс по урокам в этих модулях
        Progress.objects.filter(
            student=student, 
            lesson__module__in=teacher_modules
        ).delete()
        
        # Удаляем ответы на тесты в этих модулях
        TestSubmission.objects.filter(
            student=student, 
            test__module__in=teacher_modules
        ).delete()
        
        # Возвращаемся в профиль (вкладка "Мои ученики")
        return redirect(reverse('core:profile') + '#my-students')
    
    return render(request, 'core/teacher/confirm_delete.html', {
        'object_name': f'весь прогресс ученика {student.username}'
    })
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