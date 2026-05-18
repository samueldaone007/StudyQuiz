from django.db import models
from django.contrib.auth.models import User
import json


class StudyMaterial(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_materials')
    title = models.CharField(max_length=255)
    content = models.TextField()
    upload_date = models.DateTimeField(auto_now_add=True)
    file_upload = models.FileField(upload_to='study_materials/', blank=True, null=True)
    
    class Meta:
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def get_content(self):
        """Get content from file or text field."""
        if self.file_upload:
            try:
                # Import here to avoid circular imports
                from .utils import parse_uploaded_file
                return parse_uploaded_file(self.file_upload.path)
            except Exception as e:
                # Fallback to stored content if parsing fails
                print(f"Error parsing file: {e}")
                return self.content
        return self.content


class Summary(models.Model):
    """Model for storing generated summaries of study materials."""
    study_material = models.OneToOneField(StudyMaterial, on_delete=models.CASCADE, related_name='summary')
    summarized_text = models.TextField()
    key_concepts = models.TextField(help_text="JSON array of key concepts/keywords")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Summaries"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Summary of {self.study_material.title}"
    
    def get_key_concepts_list(self):
        """Return key concepts as a Python list."""
        try:
            return json.loads(self.key_concepts)
        except:
            return []


class Quiz(models.Model):
    """Model for storing quizzes generated from study materials."""
    study_material = models.ForeignKey(StudyMaterial, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ['-date_created']
    
    def __str__(self):
        return f"{self.title} - {self.study_material.title}"
    
    def get_question_count(self):
        """Return the number of questions in this quiz."""
        return self.questions.count()
    
    def get_total_score(self):
        """Return total possible score for this quiz."""
        return self.get_question_count()


class Question(models.Model):
    """Model for storing individual quiz questions."""
    QUESTION_TYPES = [
        ('MCQ', 'Multiple Choice'),
        ('TF', 'True/False'),
        ('SHORT', 'Short Answer'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='MCQ')
    options = models.TextField(help_text="JSON array of options for MCQ")
    correct_answer = models.CharField(max_length=255)
    explanation = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."
    
    def get_options_list(self):
        """Return options as a Python list."""
        try:
            return json.loads(self.options)
        except:
            return []
    
    def is_correct(self, answer):
        """Check if the given answer is correct."""
        return answer.strip().lower() == self.correct_answer.strip().lower()


class QuizAttempt(models.Model):
    """Model for storing quiz attempts by users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    answers = models.TextField(help_text="JSON object with question_id: answer pairs")
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}/{self.total_questions}"
    
    def get_percentage(self):
        """Calculate percentage score."""
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100, 2)
    
    def get_answers_dict(self):
        """Return answers as a Python dictionary."""
        try:
            return json.loads(self.answers)
        except:
            return {}
