
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .models import User,Course,Lesson
from .forms import UserSignupForm,UserLoginForm,InstructorLoginForm,InstructorSignupForm,CourseCreationForm,LessonCreationForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib.auth import update_session_auth_hash


# Create your views here.
def home(request):
    return render(request,'ArtiQuityapp/home.html')
def about(request):
    return HttpResponse("Welcome to ArtiQuity")


def custom_authenticate(username, password):
    try:
        user = User.objects.get(username=username)
        if user and password==user.password_hash:
            user.is_authenticated = True
            user.last_login = timezone.now()
            user.save()
            return user
    except User.DoesNotExist:
        return None
    return None
@login_required
def instructor_dashboard(request):

    print(f"User logged in: {request.user.username}")  # Print the logged-in user
    print(f"User role: {request.user.role}")
    if request.user.role != 'instructor':
        messages.error(request, "Access denied! Only instructors can access this page.")
        return redirect('home')

    # Get courses created by the instructor
    courses = Course.objects.filter(instructor=request.user)

    return render(request, 'ArtiQuityapp/instructor_dashboard.html', {'courses': courses})
@login_required
def student_dashboard(request):

    print(f"User logged in: {request.user.username}")  # Print the logged-in user
    print(f"User role: {request.user.role}")
    if request.user.role != 'student':
        messages.error(request, "Access denied! Only instructors can access this page.")
        return redirect('home')

    # Get courses created by the instructor
    print("hello")
    courses = Course.objects.all()
    print(courses)


    return render(request, 'ArtiQuityapp/student_dashboard.html', {'courses': courses})


@login_required
def create_course(request):
    if request.user.role != 'instructor':
        messages.error(request, "Access denied! Only instructors can create courses.")
        return redirect('instructor_dashboard')

    if request.method == 'POST':
        form = CourseCreationForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user  # Set the instructor as the logged-in user
            course.save()
            messages.success(request, 'Course created successfully!')
            return redirect('instructor_dashboard')
    else:
        form = CourseCreationForm()
    
    return render(request, 'ArtiQuityapp/create_course.html', {'form': form})

@login_required
def create_lesson(request, course_id):
    try:
        course = Course.objects.get(id=course_id, instructor=request.user)
    except Course.DoesNotExist:
        messages.error(request, "Course not found or you do not have permission to add lessons to this course.")
        return redirect('instructor_dashboard')

    if request.method == 'POST':
        form = LessonCreationForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, 'Lesson added successfully!')
            return redirect('instructor_dashboard')
    else:
        form = LessonCreationForm()
    
    return render(request, 'ArtiQuityapp/create_lesson.html', {'form': form, 'course': course})




def user_signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            # Hash the password before saving it
            user.password_hash = form.cleaned_data['password']
            user.save()
            return redirect('home')  # Redirect to home page after successful signup
    else:
        form = UserSignupForm()
    return render(request, 'ArtiQuityapp/signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST, request.FILES)
        if form.is_valid():
                  
            username = request.POST['username']
            password = request.POST['password']
            print (username)
            print(password)

            try:
                user_obj = User.objects.get(username=username)
                print(user_obj.last_name)
            except User.DoesNotExist:
                messages.error(request, "User does not exist. Please sign up first.")
                return redirect('user_signup')
            

            # Authenticate the user
            user = custom_authenticate(username,password)
            print (user.password_hash)
            if user is not None:
                request.session['user_id'] = user.id
                request.session['user_role'] = user.role
                request.session['username'] = user.username
                    

                print(f"User {user.username} is logged in: {user.is_authenticated}")  # Should print True
             
               
                print(f"Session Data: {request.session.items()}")
                update_session_auth_hash(request, user)
                print(f"Session Data: {request.session.items()}")
                return redirect('student_dashboard')
                
    else:
        form = UserLoginForm()

    return render(request, 'ArtiQuityapp/login.html', {'form': form})

def instructor_signup(request):
    if request.method == 'POST':
        form = InstructorSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            # Hash the password before saving it
            user.password_hash = form.cleaned_data['password']
            user.save()
            return redirect('home')  # Redirect to home page after successful signup
    else:
        form = InstructorSignupForm()
    return render(request, 'ArtiQuityapp/instructor_signup.html', {'form': form})

def instructor_login(request):
    if request.method == 'POST':
        form = InstructorLoginForm(request.POST, request.FILES)
        if form.is_valid():
                  
            username = request.POST['username']
            password = request.POST['password']
            print (username)
            print(password)

            try:
                user_obj = User.objects.get(username=username)
                print(user_obj.last_name)
            except User.DoesNotExist:
                messages.error(request, "User does not exist. Please sign up first.")
                return redirect('instructor_signup')
            
            # Authenticate the user
            user = custom_authenticate(username,password)
            print (user.password_hash)
            if user is not None:
                request.session['user_id'] = user.id
                request.session['user_role'] = user.role
                request.session['username'] = user.username
                    

                print(f"User {user.username} is logged in: {user.is_authenticated}")  # Should print True
             
               
                print(f"Session Data: {request.session.items()}")
                update_session_auth_hash(request, user)
                print(f"Session Data: {request.session.items()}")
                return redirect('instructor_dashboard')
                
    
                
                 # Redirect to the home page after successful login
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = InstructorLoginForm()

    return render(request, 'ArtiQuityapp/instructor_login.html', {'form': form})
from django.shortcuts import get_object_or_404

# Edit a Course
@login_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == 'POST':
        form = CourseCreationForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('instructor_dashboard')
    else:
        form = CourseCreationForm(instance=course)
    
    return render(request, 'ArtiQuityapp/edit_course.html', {'form': form, 'course': course})


# Delete a Course
@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return redirect('instructor_dashboard')
    
    return render(request, 'ArtiQuityapp/confirm_delete.html', {'course': course})


# Edit a Lesson
@login_required
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    if request.method == 'POST':
        form = LessonCreationForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lesson updated successfully!')
            return redirect('instructor_dashboard')
    else:
        form = LessonCreationForm(instance=lesson)
    
    return render(request, 'ArtiQuityapp/edit_lesson.html', {'form': form, 'lesson': lesson})


# Delete a Lesson
@login_required
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Lesson deleted successfully!')
        return redirect('instructor_dashboard')
    
    return render(request, 'ArtiQuityapp/confirm_delete.html', {'lesson': lesson})




