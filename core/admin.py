from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Module, Lesson, Resource, Test, TestQuestion, TestSubmission, TestAnswer, Progress

@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_teacher_approved', 'is_active')
    list_filter = ('role', 'is_teacher_approved', 'is_active')
    search_fields = ('username', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'avatar', 'bio', 'phone')}),
        ('Permissions', {'fields': ('role', 'is_teacher_approved', 'is_active', 'is_staff', 'is_superuser')}),
    )

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1
    show_change_link = True
    fields = ('title', 'content', 'video_url', 'is_free_preview')

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_at')
    search_fields = ('title', 'description')
    inlines = [LessonInline]
    readonly_fields = ('created_at',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'created_at')
    list_filter = ('module', 'is_free_preview')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at',)

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'file', 'url', 'created_at')
    search_fields = ('title',)
    readonly_fields = ('created_at',)

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)

@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'max_score')
    search_fields = ('text',)
    list_filter = ('test',)

@admin.register(TestSubmission)
class TestSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'score', 'passed', 'submitted_at')
    list_filter = ('passed', 'test')
    search_fields = ('student__username', 'test__title')
    readonly_fields = ('submitted_at',)

@admin.register(TestAnswer)
class TestAnswerAdmin(admin.ModelAdmin):
    list_display = ('submission', 'question', 'answer_text')
    search_fields = ('answer_text',)
    list_filter = ('submission',)

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'passed', 'completed_at')
    list_filter = ('passed', 'lesson')
    search_fields = ('student__username', 'lesson__title')
    readonly_fields = ('completed_at',)