from django.contrib import admin
from django.urls import path , include
from home import views

urlpatterns = [
    path("register/",views.register_page, name="register_page"),
    path('login/', views.login_view, name='login_page'),
    path('dashboard/', views.dashboard, name='dashboard_page'),
    path("makequiz/",views.quiz_page,name="quiz_page"),
    path('quiz/<int:quiz_id>/', views.play_quiz, name='play_quiz'),
    path('quiz/<int:quiz_id>/result/', views.quiz_results, name='quiz_results'),
    path('check_answer/', views.check_answer, name='check_answer'),
]
