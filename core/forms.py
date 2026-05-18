from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import StudyMaterial, Question


class UserRegistrationForm(UserCreationForm):
    """Form for user registration."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email


class StudyMaterialForm(forms.ModelForm):
    """Form for uploading study materials."""
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 10,
            'placeholder': 'Enter your study notes here...',
            'class': 'form-control'
        }),
        required=False,
        label="Study Content"
    )
    file_upload = forms.FileField(
        required=False,
        label="Or Upload a File",
        help_text="Supported formats: .txt, .pdf, .docx, .pptx, .ppt",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.txt,.pdf,.docx,.pptx,.ppt'
        })
    )
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = ['.txt', '.pdf', '.docx', '.pptx', '.ppt']
    
    class Meta:
        model = StudyMaterial
        fields = ['title', 'content', 'file_upload']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter a title for your study material',
                'class': 'form-control'
            }),
        }
    
    def clean_file_upload(self):
        """Validate uploaded file extension."""
        file = self.cleaned_data.get('file_upload')
        if file:
            # Get file extension
            name = file.name.lower()
            if not any(name.endswith(ext) for ext in self.ALLOWED_EXTENSIONS):
                raise forms.ValidationError(
                    f"Unsupported file format. Allowed formats: {', '.join(self.ALLOWED_EXTENSIONS)}"
                )
            # Check file size (max 20MB)
            if file.size > 20 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 20MB.")
        return file
    
    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        file_upload = cleaned_data.get('file_upload')
        
        if not content and not file_upload:
            raise forms.ValidationError(
                "Please either enter content or upload a file."
            )
        
        return cleaned_data


class QuizSettingsForm(forms.Form):
    """Form for configuring quiz generation settings."""
    num_questions = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=5,
        label="Number of Questions",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    question_types = forms.MultipleChoiceField(
        choices=Question.QUESTION_TYPES,
        initial=['MCQ'],
        label="Question Types",
        widget=forms.CheckboxSelectMultiple()
    )
    difficulty = forms.ChoiceField(
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        initial='medium',
        label="Difficulty Level",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class QuizAnswerForm(forms.Form):
    """Dynamic form for quiz answers."""
    def __init__(self, questions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for question in questions:
            if question.question_type == 'MCQ':
                choices = [(opt, opt) for opt in question.get_options_list()]
                self.fields[f'question_{question.id}'] = forms.ChoiceField(
                    choices=choices,
                    label=question.question_text,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                    required=True
                )
            elif question.question_type == 'TF':
                self.fields[f'question_{question.id}'] = forms.ChoiceField(
                    choices=[('True', 'True'), ('False', 'False')],
                    label=question.question_text,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                    required=True
                )
            else:
                self.fields[f'question_{question.id}'] = forms.CharField(
                    label=question.question_text,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'Your answer...'
                    }),
                    required=True
                )


class ContactForm(forms.Form):
    """Form for contact page."""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your Message'
        })
    )
