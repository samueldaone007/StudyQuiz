# StudyQuiz - Personalized Study and Quiz Web Application

A Django-based web application that helps students study more effectively by providing AI-powered text summarization and automated quiz generation from study materials.

## Features

- **User Authentication**: Register, login, and manage your account
- **Study Material Upload**: Upload or type your study notes
- **AI-Powered Summarization**: Automatically generate concise summaries of your materials
- **Key Concept Extraction**: Identify important terms and concepts
- **Automated Quiz Generation**: Create personalized quizzes from your study materials
- **Quiz Taking**: Take quizzes with multiple choice, true/false, and short answer questions
- **Progress Tracking**: View your quiz results and track your learning progress

## Technology Stack

- **Backend**: Django 4.2, Python 3.8+
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Database**: SQLite (default)
- **NLP**: Hugging Face Transformers (optional) or Extractive Summarization (built-in)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional)

### Step 1: Clone or Download the Project

```bash
cd /mnt/okcomputer/output/studyquiz
```

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```

### Step 3: Activate the Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

Copy the example environment file and update it:

```bash
cp .env.example .env
```

Edit `.env` and set your values:
```
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
HUGGINGFACE_API_TOKEN=your-huggingface-token-here  # Optional
```

To get a Hugging Face API token (optional but recommended for better summarization):
1. Visit https://huggingface.co/settings/tokens
2. Create a new token
3. Copy it to your `.env` file

### Step 6: Run Migrations

```bash
python manage.py migrate
```

### Step 7: Create a Superuser (Admin)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### Step 8: Run the Development Server

```bash
python manage.py runserver
```

The application will be available at: http://127.0.0.1:8000/

### Step 9: Access the Admin Panel (Optional)

Visit http://127.0.0.1:8000/admin/ and log in with your superuser credentials.

## Usage

### For Students

1. **Register an Account**: Create a new account or login
2. **Upload Study Materials**: Go to Dashboard → Upload Material
3. **View Summary**: After uploading, view the AI-generated summary and key concepts
4. **Generate Quiz**: Click "Generate Quiz" to create a quiz from your material
5. **Take Quiz**: Answer the questions and submit
6. **View Results**: See your score and review correct answers

### For Administrators

Access the admin panel at `/admin/` to:
- Manage users
- View all study materials
- Monitor quiz attempts
- Manage questions and quizzes

## Project Structure

```
studyquiz/
├── core/                   # Main application
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── forms.py           # Form classes
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin configuration
│   └── utils.py           # Utility functions (NLP, quiz generation)
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   └── core/              # App templates
├── static/                # Static files
│   ├── css/               # Stylesheets
│   └── js/                # JavaScript files
├── studyquiz/             # Project settings
│   ├── settings.py        # Django settings
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI configuration
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Database Schema

The application uses the following models:

- **User**: Django's built-in user model
- **StudyMaterial**: Stores uploaded study materials
- **Summary**: Stores AI-generated summaries
- **Quiz**: Stores generated quizzes
- **Question**: Stores individual quiz questions
- **QuizAttempt**: Stores user's quiz attempts and scores

## API Endpoints

### Web Routes

| URL | Description |
|-----|-------------|
| `/` | Home page |
| `/register/` | User registration |
| `/login/` | User login |
| `/logout/` | User logout |
| `/dashboard/` | User dashboard |
| `/materials/upload/` | Upload study material |
| `/materials/` | List user's materials |
| `/materials/<id>/` | View material and summary |
| `/materials/<id>/generate-quiz/` | Generate quiz from material |
| `/quizzes/` | List user's quizzes |
| `/quizzes/<id>/take/` | Take a quiz |
| `/results/` | View all results |
| `/results/<id>/` | View specific result |

### API Endpoints

| URL | Method | Description |
|-----|--------|-------------|
| `/api/materials/<id>/regenerate-summary/` | POST | Regenerate material summary |

## Customization

### Changing the Theme

Edit `static/css/style.css` to customize the appearance.

### Modifying Quiz Generation

Edit `core/utils.py` to customize:
- Summarization algorithm
- Key concept extraction
- Question generation logic

### Adding New Question Types

1. Update `Question.QUESTION_TYPES` in `core/models.py`
2. Update quiz generation logic in `core/utils.py`
3. Update templates to display new question types

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError` when running server
**Solution**: Make sure virtual environment is activated and dependencies are installed

**Issue**: Static files not loading
**Solution**: Run `python manage.py collectstatic` in production

**Issue**: Database errors
**Solution**: Delete `db.sqlite3` and run migrations again

**Issue**: Summarization not working
**Solution**: The app uses built-in extractive summarization if Hugging Face API is not configured

## Development

### Running Tests

```bash
python manage.py test
```

### Adding New Features

1. Create models in `core/models.py`
2. Create views in `core/views.py`
3. Add URL patterns in `core/urls.py`
4. Create templates in `templates/core/`
5. Update admin in `core/admin.py`

## Production Deployment

Before deploying to production:

1. Set `DEBUG=False` in `.env`
2. Generate a new secret key
3. Configure allowed hosts
4. Set up a production database (PostgreSQL recommended)
5. Configure static files serving (WhiteNoise or CDN)
6. Set up HTTPS

## License

This project is developed as an academic project for Bingham University, Nigeria.

## Credits

**Developer**: Afolayan Samuel Bolutife  
**Matric Number**: BHU/22/04/05/0007  
**Department**: Computer Science  
**Institution**: Bingham University, Karu, Nigeria

## Acknowledgments

- Supervisor: Mr. Barka Fori
- HOD: Dr. Adamu S. Usman
- Faculty of Computing, Bingham University
