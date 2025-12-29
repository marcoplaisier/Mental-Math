from django.db import models
from django.utils import timezone
from datetime import timedelta
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


class LeitnerCard(models.Model):
    """
    Tracks Leitner box progression for each user per question type.

    The Leitner system is a spaced repetition learning method:
    - Box 1: New/failed cards - review immediately
    - Box 2: Review after 1 day
    - Box 3: Review after 3 days
    - Box 4: Review after 7 days
    - Box 5: Mastered - review after 14 days

    Cards move up a box on correct answers, back to Box 1 on incorrect.
    """

    # Box intervals in days
    BOX_INTERVALS = {
        1: 0,    # Review immediately
        2: 1,    # Review after 1 day
        3: 3,    # Review after 3 days
        4: 7,    # Review after 7 days
        5: 14,   # Review after 14 days
    }

    MAX_BOX = 5

    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='leitner_cards'
    )
    difficulty_level = models.IntegerField(
        choices=DifficultyLevel.choices
    )
    operation = models.CharField(
        max_length=3,
        choices=OperationType.choices
    )
    box_number = models.IntegerField(default=1)
    next_review = models.DateTimeField(default=timezone.now)
    last_reviewed = models.DateTimeField(null=True, blank=True)
    times_correct = models.IntegerField(default=0)
    times_incorrect = models.IntegerField(default=0)
    consecutive_correct = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'difficulty_level', 'operation']
        ordering = ['next_review', 'box_number']

    def __str__(self):
        return f"{self.user.name} - Level {self.difficulty_level} {self.operation} - Box {self.box_number}"

    @property
    def is_due(self):
        """Check if this card is due for review."""
        return self.next_review <= timezone.now()

    @property
    def accuracy(self):
        """Calculate accuracy percentage for this card."""
        total = self.times_correct + self.times_incorrect
        if total == 0:
            return 0
        return round((self.times_correct / total) * 100, 1)

    def record_answer(self, is_correct: bool):
        """
        Record an answer and update the box position.

        Correct: Move to next box (max Box 5)
        Incorrect: Move back to Box 1
        """
        self.last_reviewed = timezone.now()

        if is_correct:
            self.times_correct += 1
            self.consecutive_correct += 1
            # Move to next box, max is Box 5
            if self.box_number < self.MAX_BOX:
                self.box_number += 1
        else:
            self.times_incorrect += 1
            self.consecutive_correct = 0
            # Move back to Box 1
            self.box_number = 1

        # Set next review date based on new box
        interval_days = self.BOX_INTERVALS.get(self.box_number, 0)
        self.next_review = timezone.now() + timedelta(days=interval_days)
        self.save()

        return self.box_number

    @classmethod
    def get_or_create_card(cls, user, difficulty_level, operation):
        """Get existing card or create a new one for the user and question type."""
        card, created = cls.objects.get_or_create(
            user=user,
            difficulty_level=difficulty_level,
            operation=operation,
            defaults={
                'box_number': 1,
                'next_review': timezone.now(),
            }
        )
        return card

    @classmethod
    def get_due_cards(cls, user, limit=None):
        """Get all cards due for review for a user, prioritizing lower boxes."""
        queryset = cls.objects.filter(
            user=user,
            next_review__lte=timezone.now()
        ).order_by('box_number', 'next_review')

        if limit:
            queryset = queryset[:limit]

        return queryset

    @classmethod
    def get_next_card_to_review(cls, user):
        """
        Get the next card that should be reviewed.
        Returns the most urgent due card, or None if no cards are due.
        """
        return cls.objects.filter(
            user=user,
            next_review__lte=timezone.now()
        ).order_by('box_number', 'next_review').first()

    @classmethod
    def get_box_distribution(cls, user):
        """Get count of cards in each box for a user."""
        from django.db.models import Count

        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        counts = cls.objects.filter(user=user).values('box_number').annotate(
            count=Count('id')
        )

        for item in counts:
            distribution[item['box_number']] = item['count']

        return distribution

    @classmethod
    def get_due_count(cls, user):
        """Get count of cards due for review."""
        return cls.objects.filter(
            user=user,
            next_review__lte=timezone.now()
        ).count()
