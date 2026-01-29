from django.core.management.base import BaseCommand
from learning_session.models import CodingProblem


class Command(BaseCommand):
    help = 'Seed sample coding problems for Gap 3 testing'

    def handle(self, *args, **kwargs):
        problems = [
            {
                "title": "Binary Search Implementation",
                "description": "Implement binary search algorithm that finds the position of a target value within a sorted array. Return -1 if not found.",
                "difficulty": "medium",
                "expected_algorithm": "binary_search",
                "test_cases": [
                    {"input": {"arr": [1, 3, 5, 7, 9], "target": 5}, "expected_output": 2},
                    {"input": {"arr": [1, 3, 5, 7, 9], "target": 1}, "expected_output": 0},
                    {"input": {"arr": [1, 3, 5, 7, 9], "target": 10}, "expected_output": -1},
                ],
                "starter_code": """def binary_search(arr, target):
    # Your code here
    pass""",
                "complexity": 40
            },
            {
                "title": "Two Sum Problem",
                "description": "Given an array of integers and a target sum, return indices of two numbers that add up to the target.",
                "difficulty": "easy",
                "expected_algorithm": "two_pointer",
                "test_cases": [
                    {"input": {"arr": [2, 7, 11, 15], "target": 9}, "expected_output": [0, 1]},
                    {"input": {"arr": [3, 2, 4], "target": 6}, "expected_output": [1, 2]},
                ],
                "starter_code": """def two_sum(arr, target):
    # Your code here
    pass""",
                "complexity": 30
            },
            {
                "title": "Fibonacci Sequence",
                "description": "Write a function to compute the nth Fibonacci number using dynamic programming.",
                "difficulty": "easy",
                "expected_algorithm": "dynamic_programming",
                "test_cases": [
                    {"input": {"n": 5}, "expected_output": 5},
                    {"input": {"n": 10}, "expected_output": 55},
                ],
                "starter_code": """def fibonacci(n):
    # Your code here
    pass""",
                "complexity": 35
            }
        ]

        for problem_data in problems:
            problem, created = CodingProblem.objects.get_or_create(
                title=problem_data["title"],
                defaults=problem_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {problem.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {problem.title}'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Gap 3 seed complete! {CodingProblem.objects.count()} problems total.'))
