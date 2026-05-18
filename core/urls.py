from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Study Materials
    path('materials/upload/', views.upload_material, name='upload_material'),
    path('materials/', views.my_materials, name='my_materials'),
    path('materials/<int:material_id>/', views.view_material, name='view_material'),
    path('materials/<int:material_id>/delete/', views.delete_material, name='delete_material'),
    
    # Quizzes
    path('materials/<int:material_id>/generate-quiz/', views.generate_quiz, name='generate_quiz'),
    path('quizzes/', views.my_quizzes, name='my_quizzes'),
    path('quizzes/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('quizzes/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    
    # Results
    path('results/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    path('results/', views.my_results, name='my_results'),
    
    # API
    path('api/materials/<int:material_id>/regenerate-summary/', 
         views.api_regenerate_summary, name='api_regenerate_summary'),
]
