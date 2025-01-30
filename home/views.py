from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
import g4f
import json
from .models import Quiz, Question , Score
from django.http import JsonResponse

# Create your views here.
def main_page(request):
    return render(request,"home/index.html")

def register_page(request):
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register_page')
        
        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register_page')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already taken.")
            return redirect('register_page')
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        login(request, user)
        
        messages.success(request, "Registration successful!")
        return redirect('dashboard_page')  # Update to your home page or dashboard URL

    return render(request, 'home/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Log in the user
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('dashboard_page')  # Change this to the home or dashboard page
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login_page')  # Redirect back to the login page
    
    return render(request, 'home/login.html')

@login_required(login_url='/login/')
def dashboard(request):
    return render(request, 'home/dashboard.html')


def create_quiz(quiz_topic, quiz_description):
    prompt = f"""
    You are a specialist Nepali Lok-Sewa Exam Helper. You know most of the question formats and what types of questions commonly appear in the Lok Sewa exams for various topics. 
    Please help me create quiz questions for a specific topic. Ensure the questions are effective and likely to appear in the exam.
    The topic for the quiz is: {quiz_topic}
    The description of the quiz is: {quiz_description}
    quiz description might be blank too if it is then ignore else make questions according to quiz description.
    Respond with JSON only, like this:

    {{
        "quiz_name": "General Knowledge Quiz",
        "topic": "General Knowledge",
        "description": "A quiz to test your general knowledge.",
        "questions": [
            {{
                "question": "What is the capital of France?",
                "options": ["Berlin", "Madrid", "Paris", "Rome"],
                "correct_option": 3
            }},
            {{
                "question": "Who wrote 'Romeo and Juliet'?",
                "options": ["Shakespeare", "Dickens", "Hemingway", "Twain"],
                "correct_option": 1
            }}
        ]
    }}

    If the description or topic provided is incorrect, reply with: "Error Occurred: Bad Quiz Description or Topic".
    Do not include any other content, only the JSON response. Only reply in English. Give at least 10 questions. Just reply me with JSON format only not even this ```json too.
    if the quiz_topic and quiz_description is non-sense or out of topic please reply with that error.Always make sure that correct option should be from 1 to 4 (not starting from 0).
    Generate that type of questions that might come in Nepal's lok sewa exam. Recheck before giving me the questions and answers make sure every answers of the questions are correct.Give most of the questions for past Lok Sewa Exams questions please.
    """

    response = g4f.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        web_search=True,
    )

    quiz_details = ""
    for message in response:
        # Since message is a string, append it directly to trip_plan
        quiz_details += message

    if quiz_details:
        return quiz_details  # Return the full aggregated response
    return False

@login_required(login_url='/login/')
def quiz_page(request):
    if request.method == 'POST':
        quiz_topic = request.POST.get('quiz-topic')
        quiz_description = request.POST.get('quiz-description')

        if not quiz_topic or not quiz_description:
            messages.error(request, "Both quiz topic and description are required.")
            return redirect('quiz_page')
        
        # Generate the quiz using AI
        quiz_data = create_quiz(quiz_topic, quiz_description)
        print(quiz_data)
        if quiz_data:
            print("Got the quiz data!!!!!!!!!")
            try:
                quiz_data = json.loads(quiz_data)

                # Check if the response contains valid keys before accessing them
                if 'quiz_name' in quiz_data and 'topic' in quiz_data and 'questions' in quiz_data:
                    # Save Quiz Data
                    quiz = Quiz.objects.create(
                        user = request.user,
                        name=quiz_data['quiz_name'],
                        topic=quiz_data['topic'],
                        description=quiz_data['description']
                    )

                    # Save Questions Data
                    for question_data in quiz_data['questions']:
                        Question.objects.create(
                            quiz=quiz,
                            question_text=question_data.get('question', ''),
                            option_1=question_data.get('options', [])[0],
                            option_2=question_data.get('options', [])[1],
                            option_3=question_data.get('options', [])[2],
                            option_4=question_data.get('options', [])[3],
                            correct_option=question_data.get('correct_option', 1)
                        )

                    messages.success(request, "Quiz created successfully!")
                    return JsonResponse({'success': True, 'message': 'Quiz created successfully!'})  # Redirect to view quiz page
                else:
                    messages.error(request, "Invalid quiz data format received.")
                    return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)

            except json.JSONDecodeError:
                messages.error(request, "Error occurred while parsing the quiz data.")
                return redirect('quiz_page')
        else:
            messages.error(request, "Error occurred while generating the quiz.")
            return redirect('quiz_page')
    latest_quizzes = Quiz.objects.filter(user=request.user).order_by('-created_at')[:3]
    return render(request, 'home/makequiz.html', {'latest_quizzes': latest_quizzes})

@login_required(login_url='/login/')
def play_quiz(request, quiz_id):
    # Fetch the quiz using the ID
    quiz = get_object_or_404(Quiz, pk=quiz_id)

    # Fetch the related questions using the foreign key relationship
    questions = Question.objects.filter(quiz=quiz)

    # Initialize the session score if not already set
    if 'score' not in request.session:
        request.session['score'] = 0

    # Keep track of the current question
    current_question_index = int(request.GET.get('q', 0))  # Default to the first question

    # Get the current question
    current_question = questions[current_question_index]

    # Store user answers if the form is submitted
    if request.method == "POST":
        selected_option = request.POST.get(f'question_{current_question.id}')
        if selected_option:
            # Save the user's answer (you could store this in a session or model)
            # For simplicity, we're not persisting it in this example.
            pass

        # Redirect to the next question
        if current_question_index + 1 < len(questions):
            return redirect(f'/quiz/{quiz_id}/?q={current_question_index + 1}')
        else:
            # All questions are answered, show results
            return redirect(f'/quiz/{quiz_id}/result')

    # Return the current question and options
    context = {
        'quiz': quiz,
        'question': current_question,
        'question_index': current_question_index,
        'total_questions': len(questions),
    }
    return render(request, 'home/play_quiz.html', context)

@login_required(login_url='/login/')
def quiz_results(request, quiz_id):
    # Fetch the quiz details
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Fetch score and total_questions from session
    session_score = request.session.pop('score', 0)  # Default to 0 if not found
    correct_answers = session_score 
    incorrect_answers = 10 - correct_answers

    # Update the user's score in the database
    db_score, created = Score.objects.get_or_create(user=request.user)
    db_score.score += session_score
    db_score.save()
    total_score = db_score.score
    return render(request, 'home/quiz_results.html', {
        'quiz': quiz,
        'score': session_score,
        'total_questions': 10,
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
        'total_score':total_score,
    })


def check_answer(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question_id = data.get('question_id')
        selected_option = int(data.get('selected_option', -1))  # Default to invalid if missing

        # Initialize score in session if not already set
        if 'score' not in request.session:
            request.session['score'] = 0

        # Ensure the selected option is valid (1-4)
        if selected_option not in [1, 2, 3, 4]:
            return JsonResponse({'error': 'Invalid option selected'}, status=400)

        # Get the question object
        try:
            question = Question.objects.get(id=question_id)
            correct_option = question.correct_option
            is_correct = selected_option == correct_option

            # Update score in session
            if is_correct:
                request.session['score'] += 1  # Increment score for correct answer

            response_data = {
                'is_correct': is_correct,
                'correct_option_text': getattr(question, f'option_{correct_option}'),
                'score': request.session['score'],  # Send the current score back to frontend
            }

            return JsonResponse(response_data)
        except Question.DoesNotExist:
            return JsonResponse({'error': 'Question not found'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required(login_url='/login/')
def leaderboard(request):
    # Fetch all scorers ordered by score
    scores = Score.objects.select_related('user').order_by('-score')

    # Fetch top 3 scorers
    top_scorers = scores[:3]

    # Fetch other scorers (excluding top 3, limit to 20)
    other_scorers = scores[3:23]

    # Find the requested user's rank
    user_rank = None
    user_score = None
    for index, score in enumerate(scores, start=1):
        if score.user == request.user:
            user_rank = index
            user_score = score.score
            break

    return render(request, 'home/leaderboard.html', {
        'top_scorers': top_scorers,
        'other_scorers': other_scorers,
        'user_rank': user_rank,
        'user_score': user_score,
    })

@login_required(login_url='/login/')
def my_quizzes(request):
    # Fetch all quizzes created by the logged-in user
    user_quizzes = Quiz.objects.filter(user=request.user).order_by('-created_at')

    # Handle quiz deletion
    if request.method == 'POST' and 'delete_quiz' in request.POST:
        quiz_id = request.POST.get('quiz_id')
        quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
        quiz.delete()
        messages.success(request, "Quiz deleted successfully.")
        return redirect('my_quizzes')

    return render(request, 'home/quizzes.html', {
        'latest_quizzes': user_quizzes,  # Pass quizzes as `latest_quizzes`
    })
@login_required(login_url='/login/')
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz.delete()
    messages.success(request, "Quiz deleted successfully!")
    return redirect('quizzes_page')

@login_required(login_url='/login/')
def profile(request):
    # Use get_or_create to either fetch the existing score or create a new one if it doesn't exist
    score, created = Score.objects.get_or_create(user=request.user)
    
    # If a new score is created, you may want to set a default value, for example:
    if created:
        score.value = 0  # assuming 'value' is the field that stores the score, adjust accordingly
        score.save()
    
    return render(request, 'home/profile.html', {'score': score})

@login_required(login_url='/login/')
def update_username(request):
    if request.method == 'POST':
        new_username = request.POST.get('username')
        if new_username:
            request.user.username = new_username
            request.user.save()
            messages.success(request, 'Your username has been updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Username cannot be empty!')
            return redirect('profile')
        

from .models import StudyMaterial

def study_materials(request):
    materials = StudyMaterial.objects.all().order_by('-uploaded_at')
    return render(request, 'home/study_materials.html', {'materials': materials})

from django.contrib.auth import logout
@login_required(login_url='/login/')
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('login_page')

def custom_404(request, exception):
    return render(request, 'home/404.html', status=404)
