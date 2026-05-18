import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg
from django.db import OperationalError
from django.conf import settings

from .models import StudyMaterial, Summary, Quiz, Question, QuizAttempt
from .forms import (
    UserRegistrationForm, 
    StudyMaterialForm, 
    QuizSettingsForm,
    QuizAnswerForm,
    ContactForm
)
from .utils import process_study_material
from .ai_question_generator import generate_ai_questions, APINotConfiguredError, APIGenerationError


def home(request):
    """Home page view."""
    try:
        context = {
            'total_users': StudyMaterial.objects.values('user').distinct().count(),
            'total_materials': StudyMaterial.objects.count(),
            'total_quizzes': Quiz.objects.count(),
        }
    except OperationalError:
        # Database tables don't exist yet (migrations not run)
        context = {
            'total_users': 0,
            'total_materials': 0,
            'total_quizzes': 0,
        }
    return render(request, 'core/home.html', context)


def about(request):
    """About page view."""
    return render(request, 'core/about.html')


def contact(request):
    """Contact page view."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form})


def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'core/register.html', {'form': form})


def user_login(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'core/login.html')


@login_required
def user_logout(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def dashboard(request):
    """User dashboard view."""
    user_materials = StudyMaterial.objects.filter(user=request.user)[:5]
    user_quizzes = Quiz.objects.filter(study_material__user=request.user)[:5]
    recent_attempts = QuizAttempt.objects.filter(user=request.user, completed=True)[:5]
    
    # Statistics
    total_materials = StudyMaterial.objects.filter(user=request.user).count()
    total_quizzes = Quiz.objects.filter(study_material__user=request.user).count()
    total_attempts = QuizAttempt.objects.filter(user=request.user, completed=True).count()
    
    avg_score = 0
    if total_attempts > 0:
        avg = QuizAttempt.objects.filter(user=request.user, completed=True).aggregate(
            avg_score=Avg('score')
        )
        avg_score = avg['avg_score'] or 0
    
    context = {
        'user_materials': user_materials,
        'user_quizzes': user_quizzes,
        'recent_attempts': recent_attempts,
        'total_materials': total_materials,
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 2),
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def upload_material(request):
    """View for uploading study materials."""
    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.user = request.user
            
            # Save first to write the file to disk
            material.save()
            
            # If a file was uploaded, extract its content
            if material.file_upload:
                try:
                    from .utils import parse_uploaded_file
                    extracted_content = parse_uploaded_file(material.file_upload.path)
                    material.content = extracted_content
                    material.save()  # Save again with extracted content
                except Exception as e:
                    messages.warning(request, f'File uploaded but content extraction failed: {str(e)}')
            
            messages.success(request, 'Study material uploaded successfully!')
            return redirect('view_material', material_id=material.id)
    else:
        form = StudyMaterialForm()
    
    return render(request, 'core/upload_material.html', {'form': form})


@login_required
def view_material(request, material_id):
    """View for displaying a study material and its summary."""
    material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)
    
    # Get or create summary
    summary = None
    summary_word_count = 0
    try:
        summary = material.summary
        if summary:
            summary_word_count = len(summary.summarized_text.split())
    except Summary.DoesNotExist:
        # Generate summary
        content = material.get_content()
        if content:
            try:
                summary_text, key_concepts = process_study_material(content)
                summary = Summary.objects.create(
                    study_material=material,
                    summarized_text=summary_text,
                    key_concepts=json.dumps(key_concepts)
                )
                summary_word_count = len(summary_text.split())
                messages.success(request, 'Summary generated successfully!')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'An unexpected error occurred while generating the summary: {e}')
    
    context = {
        'material': material,
        'summary': summary,
        'key_concepts': summary.get_key_concepts_list() if summary else [],
        'summary_word_count': summary_word_count,
    }
    return render(request, 'core/view_material.html', context)


@login_required
def my_materials(request):
    """View for listing all user's study materials."""
    materials = StudyMaterial.objects.filter(user=request.user)
    return render(request, 'core/my_materials.html', {'materials': materials})


@login_required
def delete_material(request, material_id):
    """View for deleting a study material."""
    material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)
    
    if request.method == 'POST':
        material.delete()
        messages.success(request, 'Study material deleted successfully!')
        return redirect('my_materials')
    
    return render(request, 'core/confirm_delete.html', {'material': material, 'type': 'material'})


@login_required
def generate_quiz(request, material_id):
    """View for generating a quiz from study material."""
    material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)
    
    if request.method == 'POST':
        form = QuizSettingsForm(request.POST)
        if form.is_valid():
            num_questions = form.cleaned_data['num_questions']
            question_types = form.cleaned_data['question_types']
            
            # Get summary and key concepts
            try:
                summary = material.summary
                key_concepts = summary.get_key_concepts_list()
            except Summary.DoesNotExist:
                content = material.get_content()
                try:
                    summary_text, key_concepts = process_study_material(content)
                    summary = Summary.objects.create(
                        study_material=material,
                        summarized_text=summary_text,
                        key_concepts=json.dumps(key_concepts)
                    )
                except ValueError as e:
                    messages.error(request, str(e))
                except Exception as e:
                    messages.error(request, f'An unexpected error occurred while generating the summary: {e}')
            
            if not key_concepts:
                messages.error(request, 'Could not extract enough key concepts to generate a quiz.')
                return redirect('view_material', material_id=material.id)
            
            # Generate questions exclusively via the AI API
            content = material.get_content()

            try:
                questions_data = generate_ai_questions(
                    content,
                    num_questions=num_questions,
                    question_types=question_types,
                )
            except APINotConfiguredError:
                messages.error(
                    request,
                    'No AI API key is configured. Please add OPENAI_API_KEY or '
                    'HUGGINGFACE_API_TOKEN to your .env file and restart the server.'
                )
                return redirect('view_material', material_id=material.id)
            except APIGenerationError as exc:
                messages.error(
                    request,
                    f'The AI API could not generate questions: {exc}. '
                    'Please check your API key and try again.'
                )
                return redirect('view_material', material_id=material.id)

            if not questions_data:
                messages.error(
                    request,
                    'The AI API returned no questions. Try again or check your API key.'
                )
                return redirect('view_material', material_id=material.id)

            # Save quiz and questions
            quiz = Quiz.objects.create(
                study_material=material,
                title=f"Quiz on {material.title}",
            )

            for q_data in questions_data:
                Question.objects.create(
                    quiz=quiz,
                    question_text=q_data['question_text'],
                    question_type=q_data['question_type'],
                    options=q_data['options'],
                    correct_answer=q_data['correct_answer'],
                    explanation=q_data['explanation'],
                    order=q_data['order'],
                )

            messages.success(
                request,
                f'Quiz generated with {len(questions_data)} questions using Hugging Face AI!'
            )
            return redirect('take_quiz', quiz_id=quiz.id)
    else:
        form = QuizSettingsForm()
    
    context = {
        'form': form,
        'material': material,
        'has_ai_api': bool(settings.HUGGINGFACE_API_TOKEN),
        'ai_provider': 'Hugging Face (Flan-T5 + RoBERTa, free)',
    }
    return render(request, 'core/generate_quiz.html', context)


@login_required
def take_quiz(request, quiz_id):
    """View for taking a quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id, study_material__user=request.user)
    questions = quiz.questions.all()
    
    if request.method == 'POST':
        form = QuizAnswerForm(questions, request.POST)
        if form.is_valid():
            # Calculate score
            score = 0
            answers = {}
            
            for question in questions:
                answer = form.cleaned_data.get(f'question_{question.id}', '')
                answers[str(question.id)] = answer
                
                if question.is_correct(answer):
                    score += 1
            
            # Save attempt
            attempt = QuizAttempt.objects.create(
                user=request.user,
                quiz=quiz,
                score=score,
                total_questions=len(questions),
                answers=json.dumps(answers),
                completed=True,
                completed_at=timezone.now()
            )
            
            messages.success(request, f'Quiz completed! Your score: {score}/{len(questions)}')
            return redirect('quiz_result', attempt_id=attempt.id)
    else:
        form = QuizAnswerForm(questions)
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'form': form,
        'question_count': len(questions),
    }
    return render(request, 'core/take_quiz.html', context)


@login_required
def quiz_result(request, attempt_id):
    """View for displaying quiz results."""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    quiz = attempt.quiz
    questions = quiz.questions.all()
    answers = attempt.get_answers_dict()
    
    # Prepare results with correct/incorrect status
    results = []
    for question in questions:
        user_answer = answers.get(str(question.id), '')
        is_correct = question.is_correct(user_answer)
        results.append({
            'question': question,
            'user_answer': user_answer,
            'is_correct': is_correct,
        })
    
    context = {
        'attempt': attempt,
        'quiz': quiz,
        'results': results,
        'percentage': attempt.get_percentage(),
    }
    return render(request, 'core/quiz_result.html', context)


@login_required
def my_quizzes(request):
    """View for listing all user's quizzes."""
    quizzes = Quiz.objects.filter(study_material__user=request.user)
    return render(request, 'core/my_quizzes.html', {'quizzes': quizzes})


@login_required
def delete_quiz(request, quiz_id):
    """View for deleting a quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id, study_material__user=request.user)
    
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Quiz deleted successfully!')
        return redirect('my_quizzes')
    
    return render(request, 'core/confirm_delete.html', {'quiz': quiz, 'type': 'quiz'})


@login_required
def my_results(request):
    """View for displaying all quiz results."""
    attempts = QuizAttempt.objects.filter(user=request.user, completed=True)
    
    # Calculate statistics
    total_attempts = attempts.count()
    avg_score = attempts.aggregate(avg=Avg('score'))['avg'] or 0
    total_questions = sum(a.total_questions for a in attempts)
    total_correct = sum(a.score for a in attempts)
    overall_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
    
    context = {
        'attempts': attempts,
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 2),
        'overall_percentage': round(overall_percentage, 2),
    }
    return render(request, 'core/my_results.html', context)


# API Views
@login_required
def api_regenerate_summary(request, material_id):
    """API endpoint to regenerate summary."""
    if request.method == 'POST':
        material = get_object_or_404(StudyMaterial, id=material_id, user=request.user)
        
        content = material.get_content()
        if content:
            summary_text, key_concepts = process_study_material(content)
            
            # Update or create summary
            summary, created = Summary.objects.update_or_create(
                study_material=material,
                defaults={
                    'summarized_text': summary_text,
                    'key_concepts': json.dumps(key_concepts)
                }
            )
            
            return JsonResponse({
                'success': True,
                'summary': summary_text,
                'key_concepts': key_concepts,
            })
        
        return JsonResponse({'success': False, 'error': 'No content found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
