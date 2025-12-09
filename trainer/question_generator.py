"""
Question generator for mental math training.
Based on techniques from "Thinking Like a Maths Genius" book.
"""
import random
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple

from .models import Question, OperationType, DifficultyLevel


class QuestionGenerator:
    """Generates math questions at various difficulty levels."""

    @staticmethod
    def generate(difficulty_level: int = None, operation: str = None) -> Question:
        """
        Generate a new question based on difficulty level or operation type.
        If neither is specified, picks a random difficulty level.
        """
        if difficulty_level is None and operation is None:
            difficulty_level = random.choice(list(DifficultyLevel.values))

        generators = {
            DifficultyLevel.LEVEL_1: QuestionGenerator._multiply_by_11_2digit,
            DifficultyLevel.LEVEL_2: QuestionGenerator._multiply_by_11_3digit,
            DifficultyLevel.LEVEL_3: QuestionGenerator._square_ending_in_5,
            DifficultyLevel.LEVEL_4: QuestionGenerator._multiply_close_to_100,
            DifficultyLevel.LEVEL_5: QuestionGenerator._multiply_2digit,
            DifficultyLevel.LEVEL_6: QuestionGenerator._multiply_3digit_by_1digit,
            DifficultyLevel.LEVEL_7: QuestionGenerator._multiply_3digit_by_2digit,
            DifficultyLevel.LEVEL_8: QuestionGenerator._multiply_4digit,
            DifficultyLevel.LEVEL_9: QuestionGenerator._division_exact,
            DifficultyLevel.LEVEL_10: QuestionGenerator._division_decimal,
            DifficultyLevel.LEVEL_11: QuestionGenerator._percentages,
            DifficultyLevel.LEVEL_12: QuestionGenerator._addition_multi,
            DifficultyLevel.LEVEL_13: QuestionGenerator._subtraction_multi,
        }

        if difficulty_level is not None:
            generator_func = generators.get(difficulty_level)
            if generator_func:
                return generator_func()

        # Generate based on operation type
        operation_generators = {
            OperationType.ADDITION: QuestionGenerator._addition_multi,
            OperationType.SUBTRACTION: QuestionGenerator._subtraction_multi,
            OperationType.MULTIPLICATION: QuestionGenerator._multiply_2digit,
            OperationType.DIVISION: QuestionGenerator._division_exact,
            OperationType.PERCENTAGE: QuestionGenerator._percentages,
        }

        generator_func = operation_generators.get(operation, QuestionGenerator._multiply_by_11_2digit)
        return generator_func()

    @staticmethod
    def _create_question(
        op1: int | Decimal,
        op2: int | Decimal,
        operation: str,
        difficulty: int,
        question_text: str
    ) -> Question:
        """Helper to create a Question object."""
        op1_decimal = Decimal(str(op1))
        op2_decimal = Decimal(str(op2))

        if operation == OperationType.ADDITION:
            answer = op1_decimal + op2_decimal
        elif operation == OperationType.SUBTRACTION:
            answer = op1_decimal - op2_decimal
        elif operation == OperationType.MULTIPLICATION:
            answer = op1_decimal * op2_decimal
        elif operation == OperationType.DIVISION:
            answer = (op1_decimal / op2_decimal).quantize(Decimal('0.0000000001'), rounding=ROUND_HALF_UP)
        elif operation == OperationType.PERCENTAGE:
            answer = (op1_decimal * op2_decimal / Decimal('100')).quantize(Decimal('0.0000000001'), rounding=ROUND_HALF_UP)
        else:
            answer = Decimal('0')

        return Question(
            operation=operation,
            difficulty_level=difficulty,
            operand1=op1_decimal,
            operand2=op2_decimal,
            correct_answer=answer,
            question_text=question_text
        )

    @staticmethod
    def _multiply_by_11_2digit() -> Question:
        """Level 1: Multiply 2-digit numbers by 11."""
        num = random.randint(10, 99)
        return QuestionGenerator._create_question(
            num, 11, OperationType.MULTIPLICATION,
            DifficultyLevel.LEVEL_1,
            f"{num} × 11"
        )

    @staticmethod
    def _multiply_by_11_3digit() -> Question:
        """Level 2: Multiply 3-digit numbers by 11."""
        num = random.randint(100, 999)
        return QuestionGenerator._create_question(
            num, 11, OperationType.MULTIPLICATION,
            DifficultyLevel.LEVEL_2,
            f"{num} × 11"
        )

    @staticmethod
    def _square_ending_in_5() -> Question:
        """Level 3: Square numbers ending in 5 (15, 25, 35, etc.)."""
        base = random.choice([15, 25, 35, 45, 55, 65, 75, 85, 95])
        return QuestionGenerator._create_question(
            base, base, OperationType.MULTIPLICATION,
            DifficultyLevel.LEVEL_3,
            f"{base}²"
        )

    @staticmethod
    def _multiply_close_to_100() -> Question:
        """Level 4: Multiply numbers close to 100."""
        num1 = random.randint(91, 109)
        num2 = random.randint(91, 109)
        return QuestionGenerator._create_question(
            num1, num2, OperationType.MULTIPLICATION,
            DifficultyLevel.LEVEL_4,
            f"{num1} × {num2}"
        )

    @staticmethod
    def _multiply_2digit() -> Question:
        """Level 5: Multiply any 2-digit numbers."""
        num1 = random.randint(10, 99)
        num2 = random.randint(10, 99)
        return QuestionGenerator._create_question(
            num1, num2, OperationType.MULTIPLICATION,
            DifficultyLevel.LEVEL_5,
            f"{num1} × {num2}"
        )

    @staticmethod
    def _multiply_3digit_by_1digit() -> Question:
        """Level 6: Multiply 3-digit by 1-digit numbers."""
        num1 = random.randint(100, 999)
        num2 = random.randint(2, 9)
        return QuestionGenerator._create_question(
            num1, num2, OperationType.MULTIPLICATION,
            DifficultyLevel.LEVEL_6,
            f"{num1} × {num2}"
        )

    @staticmethod
    def _multiply_3digit_by_2digit() -> Question:
        """Level 7: Multiply 3-digit by 2-digit numbers."""
        num1 = random.randint(100, 999)
        num2 = random.randint(10, 99)
        return QuestionGenerator._create_question(
            num1, num2, OperationType.MULTIPLICATION,
            DifficultyLevel.LEVEL_7,
            f"{num1} × {num2}"
        )

    @staticmethod
    def _multiply_4digit() -> Question:
        """Level 8: Multiply 4-digit numbers."""
        num1 = random.randint(1000, 9999)
        num2 = random.randint(10, 99)
        return QuestionGenerator._create_question(
            num1, num2, OperationType.MULTIPLICATION,
            DifficultyLevel.LEVEL_8,
            f"{num1} × {num2}"
        )

    @staticmethod
    def _division_exact() -> Question:
        """Level 9: Division with exact integer results."""
        divisor = random.randint(2, 12)
        quotient = random.randint(10, 100)
        dividend = divisor * quotient
        return QuestionGenerator._create_question(
            dividend, divisor, OperationType.DIVISION,
            DifficultyLevel.LEVEL_9,
            f"{dividend} ÷ {divisor}"
        )

    @staticmethod
    def _division_decimal() -> Question:
        """Level 10: Division with decimal results."""
        divisor = random.randint(3, 9)
        dividend = random.randint(100, 999)
        return QuestionGenerator._create_question(
            dividend, divisor, OperationType.DIVISION,
            DifficultyLevel.LEVEL_10,
            f"{dividend} ÷ {divisor}"
        )

    @staticmethod
    def _percentages() -> Question:
        """Level 11: Calculate percentages."""
        percentage = random.choice([5, 10, 15, 20, 25, 30, 40, 50, 75])
        value = random.randint(20, 500)
        return QuestionGenerator._create_question(
            percentage, value, OperationType.PERCENTAGE,
            DifficultyLevel.LEVEL_11,
            f"{percentage}% of {value}"
        )

    @staticmethod
    def _addition_multi() -> Question:
        """Level 12: Multi-digit addition."""
        num1 = random.randint(100, 9999)
        num2 = random.randint(100, 9999)
        return QuestionGenerator._create_question(
            num1, num2, OperationType.ADDITION,
            DifficultyLevel.LEVEL_12,
            f"{num1} + {num2}"
        )

    @staticmethod
    def _subtraction_multi() -> Question:
        """Level 13: Multi-digit subtraction."""
        num1 = random.randint(500, 9999)
        num2 = random.randint(100, num1 - 1)
        return QuestionGenerator._create_question(
            num1, num2, OperationType.SUBTRACTION,
            DifficultyLevel.LEVEL_13,
            f"{num1} − {num2}"
        )
