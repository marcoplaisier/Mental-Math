from django.db import models
from decimal import Decimal


class UserProfile(models.Model):
    """User profile for tracking individual progress."""
    name = models.CharField(max_length=100, unique=True)
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def update_streak(self, is_correct: bool):
        """Update streak based on answer correctness."""
        if is_correct:
            self.current_streak += 1
            if self.current_streak > self.best_streak:
                self.best_streak = self.current_streak
        else:
            self.current_streak = 0
        self.save()

    @classmethod
    def get_default_users(cls):
        """Return the list of hard-coded user names."""
        return ['Arthur', 'Lena', 'Marco', 'Susanne']

    @classmethod
    def ensure_users_exist(cls):
        """Create hard-coded users if they don't exist."""
        for name in cls.get_default_users():
            cls.objects.get_or_create(name=name)


class OperationType(models.TextChoices):
    ADDITION = 'ADD', 'Addition'
    SUBTRACTION = 'SUB', 'Subtraction'
    MULTIPLICATION = 'MUL', 'Multiplication'
    DIVISION = 'DIV', 'Division'
    PERCENTAGE = 'PCT', 'Percentage'


class DifficultyLevel(models.IntegerChoices):
    LEVEL_1 = 1, 'Multiply by 11 (2 digits)'
    LEVEL_2 = 2, 'Multiply by 11 (3 digits)'
    LEVEL_3 = 3, 'Square numbers ending in 5'
    LEVEL_4 = 4, 'Multiply numbers close to 100'
    LEVEL_5 = 5, 'Multiply 2-digit numbers'
    LEVEL_6 = 6, 'Multiply 3-digit by 1-digit'
    LEVEL_7 = 7, 'Multiply 3-digit by 2-digit'
    LEVEL_8 = 8, 'Multiply 4-digit numbers'
    LEVEL_9 = 9, 'Division (exact)'
    LEVEL_10 = 10, 'Division (with decimals)'
    LEVEL_11 = 11, 'Percentages'
    LEVEL_12 = 12, 'Addition (multi-digit)'
    LEVEL_13 = 13, 'Subtraction (multi-digit)'


class Question(models.Model):
    """Stores each question presented to the user."""
    operation = models.CharField(
        max_length=3,
        choices=OperationType.choices
    )
    difficulty_level = models.IntegerField(
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.LEVEL_1
    )
    operand1 = models.DecimalField(max_digits=20, decimal_places=10)
    operand2 = models.DecimalField(max_digits=20, decimal_places=10)
    correct_answer = models.DecimalField(max_digits=20, decimal_places=10)
    question_text = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.question_text} = {self.correct_answer}"


class Answer(models.Model):
    """Stores each answer attempt by the user."""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='answers',
        null=True,
        blank=True
    )
    user_answer = models.DecimalField(max_digits=20, decimal_places=10)
    is_correct = models.BooleanField()
    time_taken_ms = models.IntegerField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        status = "Correct" if self.is_correct else "Wrong"
        return f"{self.question.question_text}: {self.user_answer} ({status})"

    @staticmethod
    def check_answer(user_answer: Decimal, correct_answer: Decimal, tolerance_percent: Decimal = Decimal('1')) -> bool:
        """
        Check if the user's answer is correct.
        For exact integers, requires exact match.
        For decimals, allows a tolerance of 1% difference.
        """
        if correct_answer == Decimal('0'):
            return user_answer == Decimal('0')

        # Check if both are effectively integers
        if correct_answer == correct_answer.to_integral_value():
            return user_answer == correct_answer

        # For decimal answers, allow 1% tolerance
        difference = abs(user_answer - correct_answer)
        percentage_diff = (difference / abs(correct_answer)) * Decimal('100')
        return percentage_diff <= tolerance_percent
