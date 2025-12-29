from django.contrib import admin
from .models import Question, Answer, LeitnerCard, UserProfile


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'operation', 'difficulty_level', 'correct_answer', 'created_at')
    list_filter = ('operation', 'difficulty_level', 'created_at')
    search_fields = ('question_text',)
    ordering = ('-created_at',)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'user_answer', 'is_correct', 'time_taken_ms', 'answered_at', 'session_id')
    list_filter = ('is_correct', 'answered_at', 'question__operation', 'question__difficulty_level')
    search_fields = ('question__question_text',)
    ordering = ('-answered_at',)
    raw_id_fields = ('question',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_streak', 'best_streak', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(LeitnerCard)
class LeitnerCardAdmin(admin.ModelAdmin):
    list_display = ('user', 'difficulty_level', 'operation', 'box_number', 'next_review', 'times_correct', 'times_incorrect', 'accuracy')
    list_filter = ('box_number', 'user', 'difficulty_level', 'operation')
    search_fields = ('user__name',)
    ordering = ('user', 'box_number', 'next_review')
    readonly_fields = ('created_at', 'updated_at')

    def accuracy(self, obj):
        return f"{obj.accuracy}%"
    accuracy.short_description = 'Accuracy'
