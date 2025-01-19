from django.contrib import admin
from django.urls import path , include
from home import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("register/",views.register_page, name="register_page"),
    path('login/', views.login_view, name='login_page'),
    path('dashboard/', views.dashboard, name='dashboard_page'),
    path("makequiz/",views.quiz_page,name="quiz_page"),
    path('quiz/<int:quiz_id>/', views.play_quiz, name='play_quiz'),
    path('quiz/<int:quiz_id>/result/', views.quiz_results, name='quiz_results'),
    path('check_answer/', views.check_answer, name='check_answer'),
    path('leaderboard/',views.leaderboard, name='leaderboard_page'),
    path('quizzes/', views.my_quizzes, name='quizzes_page'),
    path('quiz/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('profile/', views.profile, name='profile'),    
    path('profile/update/', views.update_username, name='update_profile'),
    path('materials/', views.study_materials, name='materials'),
    path('logout/', views.logout_view, name='logout'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
