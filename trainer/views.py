from decimal import Decimal, InvalidOperation
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate

from .models import Question, Answer, DifficultyLevel, OperationType, UserProfile
from .question_generator import QuestionGenerator


def get_current_user(request):
    """Get the current user from session, or None if not selected."""
    user_id = request.session.get('user_id')
    if user_id:
        try:
            return UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            pass
    return None


def select_user(request):
    """User selection page."""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            try:
                user = UserProfile.objects.get(id=user_id)
                request.session['user_id'] = user.id
                return redirect('trainer:index')
            except UserProfile.DoesNotExist:
                pass

    # Ensure default users exist
    UserProfile.ensure_users_exist()
    users = UserProfile.objects.all().order_by('name')

    return render(request, 'trainer/select_user.html', {'users': users})


def switch_user(request):
    """Clear the current user and redirect to selection."""
    if 'user_id' in request.session:
        del request.session['user_id']
    return redirect('trainer:select_user')


def index(request):
    """Main quiz page."""
    # Require user selection
    current_user = get_current_user(request)
    if not current_user:
        return redirect('trainer:select_user')

    difficulty = request.GET.get('difficulty')
    operation = request.GET.get('operation')

    # Generate a new question
    if difficulty:
        try:
            difficulty = int(difficulty)
        except ValueError:
            difficulty = None

    question = QuestionGenerator.generate(
        difficulty_level=difficulty,
        operation=operation
    )
    question.save()

    # Get session ID for tracking
    if not request.session.session_key:
        request.session.create()

    context = {
        'question': question,
        'difficulty_levels': DifficultyLevel.choices,
        'operation_types': OperationType.choices,
        'selected_difficulty': difficulty,
        'selected_operation': operation,
        'current_user': current_user,
    }
    return render(request, 'trainer/index.html', context)


@require_http_methods(["POST"])
def check_answer(request):
    """Check the user's answer and return result."""
    # Get current user
    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'error': 'No user selected'}, status=401)

    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        user_answer_str = data.get('answer', '').strip()
        time_taken = data.get('time_taken_ms')

        if not question_id or not user_answer_str:
            return JsonResponse({
                'error': 'Missing question_id or answer'
            }, status=400)

        # Parse user answer using Decimal for precision
        try:
            user_answer = Decimal(user_answer_str)
        except InvalidOperation:
            return JsonResponse({
                'error': 'Invalid number format'
            }, status=400)

        # Get the question
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return JsonResponse({
                'error': 'Question not found'
            }, status=404)

        # Check if answer is correct
        is_correct = Answer.check_answer(user_answer, question.correct_answer)

        # Store the answer with user association
        session_id = request.session.session_key or ''
        answer = Answer.objects.create(
            question=question,
            user=current_user,
            user_answer=user_answer,
            is_correct=is_correct,
            time_taken_ms=time_taken,
            session_id=session_id
        )

        # Update user's streak
        current_user.update_streak(is_correct)

        # Format the correct answer for display
        correct_answer = question.correct_answer
        if correct_answer == correct_answer.to_integral_value():
            correct_answer_display = str(int(correct_answer))
        else:
            correct_answer_display = str(correct_answer.normalize())

        return JsonResponse({
            'correct': is_correct,
            'correct_answer': correct_answer_display,
            'user_answer': str(user_answer),
            'question_text': question.question_text,
            'current_streak': current_user.current_streak,
            'best_streak': current_user.best_streak,
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON'
        }, status=400)


def statistics(request):
    """Show statistics and analysis of past performance."""
    # Require user selection
    current_user = get_current_user(request)
    if not current_user:
        return redirect('trainer:select_user')

    # Overall stats - filter by user
    total_answers = Answer.objects.filter(user=current_user).count()
    correct_answers = Answer.objects.filter(user=current_user, is_correct=True).count()
    accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0

    # Stats by difficulty level
    difficulty_stats = []
    for level_value, level_name in DifficultyLevel.choices:
        level_answers = Answer.objects.filter(
            user=current_user,
            question__difficulty_level=level_value
        )
        level_total = level_answers.count()
        level_correct = level_answers.filter(is_correct=True).count()
        level_accuracy = (level_correct / level_total * 100) if level_total > 0 else 0
        avg_time = level_answers.aggregate(avg_time=Avg('time_taken_ms'))['avg_time']

        if level_total > 0:
            difficulty_stats.append({
                'level': level_value,
                'name': level_name,
                'total': level_total,
                'correct': level_correct,
                'accuracy': round(level_accuracy, 1),
                'avg_time': round(avg_time / 1000, 2) if avg_time else None,
            })

    # Stats by operation type
    operation_stats = []
    for op_value, op_name in OperationType.choices:
        op_answers = Answer.objects.filter(
            user=current_user,
            question__operation=op_value
        )
        op_total = op_answers.count()
        op_correct = op_answers.filter(is_correct=True).count()
        op_accuracy = (op_correct / op_total * 100) if op_total > 0 else 0

        if op_total > 0:
            operation_stats.append({
                'operation': op_name,
                'total': op_total,
                'correct': op_correct,
                'accuracy': round(op_accuracy, 1),
            })

    # Recent answers
    recent_answers = Answer.objects.filter(
        user=current_user
    ).select_related('question').order_by('-answered_at')[:20]

    context = {
        'total_answers': total_answers,
        'correct_answers': correct_answers,
        'accuracy': round(accuracy, 1),
        'difficulty_stats': difficulty_stats,
        'operation_stats': operation_stats,
        'recent_answers': recent_answers,
        'current_user': current_user,
    }
    return render(request, 'trainer/statistics.html', context)
