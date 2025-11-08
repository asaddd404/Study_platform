# eduplatform/core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test 
from django.contrib.auth import logout, login
# 1. ИМПОРТИРУЕМ ВСЕ НУЖНЫЕ ФОРМЫ
from .forms import (
    ProfileForm, CustomUserCreationForm, LessonForm, 
    TestForm, QuestionForm
)
from django.utils import timezone
# 2. ИМПОРТИРУЕМ TestQuestion
from .models import (
    Course, Module, Lesson, Resource, Test, TestSubmission, 
    TestAnswer, Progress, User, TestQuestion
)
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.db.models import Q, Sum  # <-- Убедись, что Sum импортирован
from django.urls import reverse

# ===================================================================
#  ИСПРАВЛЕНИЕ: Перемещаем декоратор сюда, в начало файла
# ===================================================================
def teacher_required(function):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'teacher':
            return function(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("У вас нет доступа к этой странице.")
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
# ===================================================================


def index(request):
    course = Course.objects.first()
    modules = Module.objects.filter(course=course).order_by('created_at') if course else []
    return render(request, 'core/index.html', {'course': course, 'modules': modules})

def about(request):
    return render(request, 'core/about.html')


# --- 3. ИСПРАВЛЕННАЯ ФУНКЦИЯ РЕГИСТРАЦИИ ---
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) # <-- ИСПОЛЬЗУЕМ ПРАВИЛЬНУЮ ФОРМУ
        if form.is_valid():
            user = form.save() 
            login(request, user) # АВТОМАТИЧЕСКИ ВХОДИМ В СИСТЕМУ
            return redirect('core:profile') # ПЕРЕНАПРАВЛЯЕМ В ПРОФИЛЬ
    else:
        form = CustomUserCreationForm() 

    return render(request, 'core/register.html', {'form': form})

# --- 4. VIEW СТРАНИЦЫ КУРСА ---
@login_required # <-- Добавим проверку, что пользователь вошел
def course(request):
    
    # 1. Получаем первый курс (для простоты)
    course = Course.objects.first()
    
    if not course:
        # Если курсов нет, можно показать ошибку, но пока просто отдадим пустой шаблон
        return render(request, 'core/course.html', {'error': 'Курс не найден'})

    # 2. Получаем все модули этого курса, и сразу "захватываем" связанные с ними уроки
    modules = Module.objects.filter(course=course).prefetch_related('lessons').order_by('created_at')

    # 3. Передаем курс и модули (с уроками внутри) в наш шаблон
    context = {
        'course': course,
        'modules': modules
    }
    
    return render(request, 'core/course.html', context)


# --- 6. VIEW ДЛЯ КНОПКИ "ПРОЙТИ УРОК" (БЕЗ ИЗМЕНЕНИЙ) ---
@login_required
def complete_lesson(request, lesson_id):
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id)
        progress, created = Progress.objects.get_or_create(
            student=request.user, 
            lesson=lesson
        )
        
        if not progress.passed:
            progress.passed = True
            progress.completed_at = timezone.now() # Убедись, что 'timezone' импортирован
            progress.save()
    
    return render(request, 'core/partials/_lesson_content.html', {
        'lesson': lesson,
        'progress': progress
    })


@login_required
def new_lesson_detail(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.prefetch_related('resources'),
        id=lesson_id
    )

    progress, created = Progress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )

    return render(request, 'core/partials/_lesson_content.html', {
        'lesson': lesson,
        'progress': progress
    })


@login_required
def new_test_detail(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    
    # 1. Пытаемся найти тест
    try:
        test = Test.objects.prefetch_related('questions').get(module=module)
    except Test.DoesNotExist:
        # Если теста нет, отдаем шаблон-заглушку
        return render(request, 'core/partials/_content_locked.html', {
            'message': 'Тест для этого модуля еще не создан.'
        })

    # 2. Проверяем, пройдены ли все уроки в этом модуле
    lessons = Lesson.objects.filter(module=module)
    all_lessons_passed = all(
        Progress.objects.filter(student=request.user, lesson=lesson, passed=True).exists() 
        for lesson in lessons
    )
    
    if not all_lessons_passed:
        # Если уроки не пройдены, отдаем шаблон-заглушку
        return render(request, 'core/partials/_content_locked.html', {
            'message': 'Пройдите все уроки в этом модуле, прежде чем начать тест.'
        })

    # 3. Если все проверки пройдены, отдаем partial-шаблон с тестом
    return render(request, 'core/partials/_test_content.html', {
        'test': test,
        'module': module
    })


# --- ИЗМЕНЕННАЯ VIEW ДЛЯ ОТПРАВКИ ТЕСТА ---
@login_required
def new_test_submit(request, test_id):
    
    # Мы принимаем только POST-запросы
    if request.method != 'POST':
        return HttpResponse("Что-то пошло не так (нужен POST)", status=400)

    test = get_object_or_404(Test.objects.prefetch_related('questions'), id=test_id)
    student = request.user

    # 1. Создаем "Попытку прохождения" (Submission)
    submission = TestSubmission.objects.create(test=test, student=student)

    # 2. Собираем все вопросы этого теста
    all_questions = test.questions.all()

    # 3. Пробегаемся по вопросам и сохраняем ответы студента
    for question in all_questions:
        answer_text = request.POST.get(f'answer_{question.id}', '')
        
        TestAnswer.objects.create(
            submission=submission,
            question=question,
            answer_text=answer_text
        )

    # 4. ВАЖНО: Вызываем твой метод из models.py, который проверит 'choice'
    #
    submission.auto_grade() 

    # 5. Отдаем HTMX-фрагмент с результатами
    # (шаблон _test_result_content.html сам решит, что показать: балл или "На проверке")
    return render(request, 'core/partials/_test_result_content.html', {
        'submission': submission,
        'test': test
    })


# --- (ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ) ---

@login_required
def profile(request):
    
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
        progress = Progress.objects.filter(student=request.user).select_related('lesson', 'lesson__module').order_by('lesson__created_at')
        context['progress'] = progress

    if request.user.role == 'teacher':
        teacher_modules = request.user.taught_modules.all().prefetch_related(
            'lessons', 'tests'
        )
        context['teacher_modules'] = teacher_modules
        
        student_ids = Progress.objects.filter(
            lesson__module__in=teacher_modules
        ).values_list('student_id', flat=True).distinct()
        
        students_queryset = User.objects.filter(
            id__in=student_ids, role='student'
        )

        query = request.GET.get('q', '')
        if query:
            students_queryset = students_queryset.filter(
                Q(username__icontains=query) | Q(email__icontains=query)
            )
        
        context['students_list'] = students_queryset.order_by('username')
        context['search_query'] = query

    return render(request, 'core/profile.html', context)

@login_required
@teacher_required
def teacher_lesson_create(request):
    module_id = request.GET.get('module_id')
    initial_data = {}
    if module_id:
        if Module.objects.filter(id=module_id, teachers=request.user).exists():
             initial_data['module'] = module_id

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            lesson = form.save(commit=False) 
            lesson.author = request.user     
            lesson.save()                    
            return redirect('core:profile') 
    else:
        form = LessonForm(user=request.user, initial=initial_data)
        
    return render(request, 'core/teacher/lesson_form.html', {
        'form': form,
        'form_title': 'Добавить новый урок'
    })

@login_required
@teacher_required
def teacher_lesson_update(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if request.user not in lesson.module.teachers.all():
         return HttpResponseForbidden("Вы не можете редактировать уроки в этом модуле.")
         
    if request.method == 'POST':
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
    
    if request.user not in lesson.module.teachers.all():
         return HttpResponseForbidden("Вы не можете удалить этот урок.")
         
    if request.method == 'POST':
        lesson.delete()
        return redirect('core:profile')
        
    return render(request, 'core/teacher/confirm_delete.html', {
        'object_name': f'урок "{lesson.title}"'
    })

@login_required
@teacher_required
def teacher_test_create(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    
    if request.user not in module.teachers.all():
        return HttpResponseForbidden("Вы не можете добавлять тесты в этот модуль.")
        
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.module = module
            test.save()
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
    
    if request.user not in test.module.teachers.all():
        return HttpResponseForbidden("Вы не можете редактировать этот тест.")
        
    if 'submit_test_form' in request.POST:
        test_form = TestForm(request.POST, instance=test)
        if test_form.is_valid():
            test_form.save()
            return redirect('core:teacher_test_update', test_id=test.id)
    else:
        test_form = TestForm(instance=test)
        
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
        'questions': test.questions.all()
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

@login_required
@teacher_required
def teacher_student_list(request):
    return redirect('core:profile')

@login_required
@teacher_required
def teacher_student_detail(request, student_id):
    student = get_object_or_404(User, id=student_id, role='student')
    
    teacher_modules = request.user.taught_modules.all()
    
    progress = Progress.objects.filter(
        student=student,
        lesson__module__in=teacher_modules
    ).select_related('lesson', 'lesson__module').order_by('lesson__created_at')
    
    submissions = TestSubmission.objects.filter(
        student=student,
        test__module__in=teacher_modules
    ).select_related('test', 'test__module').order_by('-submitted_at')
    
    return render(request, 'core/teacher/student_detail.html', {
        'student': student,
        'progress': progress,
        'submissions': submissions
    })

@login_required
@teacher_required
def teacher_remove_student(request, student_id):
    student = get_object_or_404(User, id=student_id, role='student')
    
    if request.method == 'POST':
        teacher_modules = request.user.taught_modules.all()
        
        Progress.objects.filter(
            student=student, 
            lesson__module__in=teacher_modules
        ).delete()
        
        TestSubmission.objects.filter(
            student=student, 
            test__module__in=teacher_modules
        ).delete()
        
        return redirect(reverse('core:profile') + '#my-students')
    
    return render(request, 'core/teacher/confirm_delete.html', {
        'object_name': f'весь прогресс ученика {student.username}'
    })

def custom_logout(request):
    logout(request)
    return render(request, 'core/logged_out.html')


# --- НОВАЯ VIEW ДЛЯ РУЧНОЙ ПРОВЕРКИ ---
@login_required
@teacher_required
def teacher_grade_submission(request, submission_id):
    # 1. Получаем попытку и связанные с ней ответы и вопросы
    submission = get_object_or_404(
        TestSubmission.objects.prefetch_related(
            'answers', 'answers__question'
        ), 
        id=submission_id
    )
    
    # 2. Убедимся, что учитель имеет право проверять этот тест
    if request.user not in submission.test.module.teachers.all():
         return HttpResponseForbidden("Вы не можете проверять эту работу.")

    if request.method == 'POST':
        # 3. Обрабатываем POST-запрос (сохраняем оценки)
        
        # Проходимся по всем ответам в этой попытке
        for answer in submission.answers.all():
            # Нас интересуют только "open_ended", т.к. 'choice' уже оценены
            if answer.question.question_type == 'open_ended':
                
                # Получаем балл из формы
                score_str = request.POST.get(f'score_{answer.id}')
                
                try:
                    score = int(score_str)
                    max_score = answer.question.max_score
                    
                    # Ставим балл, но не больше максимального
                    answer.score = max(0, min(score, max_score)) 
                    
                except (ValueError, TypeError):
                    answer.score = 0 # Если пришло что-то не то, ставим 0
                
                answer.save() # Сохраняем балл за этот ответ
        
        # 4. ВАЖНО: Вызываем твой метод из models.py
        # Он посчитает ИТОГОВЫЙ % (сложив авто-баллы и ручные) 
        # и поменяет статус на 'graded'
        submission.update_final_score()
        
        # 5. Возвращаем учителя на страницу ученика
        return redirect('core:teacher_student_detail', student_id=submission.student.id)

    # 6. Обрабатываем GET-запрос (показываем форму)
    context = {
        'submission': submission,
        'answers': submission.answers.all().order_by('question__created_at')
    }
    # Используем новый шаблон, который создали
    return render(request, 'core/teacher/grade_submission.html', context)