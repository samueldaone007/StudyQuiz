from django.contrib import admin
from .models import StudyMaterial, Summary, Quiz, Question, QuizAttempt


@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'upload_date']
    list_filter = ['upload_date', 'user']
    search_fields = ['title', 'content']
    date_hierarchy = 'upload_date'


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ['study_material', 'created_at']
    list_filter = ['created_at']
    search_fields = ['study_material__title', 'summarized_text']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'study_material', 'date_created', 'is_active', 'get_question_count']
    list_filter = ['is_active', 'date_created']
    search_fields = ['title', 'study_material__title']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'question_text', 'question_type', 'order']
    list_filter = ['question_type', 'quiz']
    search_fields = ['question_text', 'quiz__title']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'total_questions', 'completed', 'started_at']
    list_filter = ['completed', 'started_at']
    search_fields = ['user__username', 'quiz__title']
    date_hierarchy = 'started_at'
