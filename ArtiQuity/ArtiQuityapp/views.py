
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .models import User,Course,Lesson
from .forms import UserSignupForm,UserLoginForm,InstructorLoginForm,InstructorSignupForm,CourseCreationForm,LessonCreationForm,AdminLoginForm,ForgotPasswordForm,SetNewPasswordForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import logout
import os
from .models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.urls import reverse

# Create your views here.
def home(request):
    if(request.user):
        print("User:")
        print(request.user)
    else:
        print("User is not logged in")
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
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(title__icontains=search_query)

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
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(title__icontains=search_query)
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



def admin_login(request):
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']

            try:
                user_obj = User.objects.get(username=username)
            except User.DoesNotExist:
                messages.error(request, "Admin does not exist.")
                return redirect('admin_login')
            
            user = custom_authenticate(username, password)
            if user and user.role == 'admin':
                # Set session data for the admin
                request.session['user_id'] = user.id
                request.session['user_role'] = user.role
                request.session['username'] = user.username

                return redirect('admin_dashboard')
            else:
                messages.error(request, "Invalid admin credentials.")
        else:
            messages.error(request, "Invalid form input.")
    else:
        form = AdminLoginForm()

    return render(request, 'ArtiQuityapp/admin_login.html', {'form': form})


def admin_dashboard(request):
    # Check if the logged-in user has the role of 'admin'
    if request.session.get('user_role') != 'admin':
        messages.error(request, "Access denied! Only admins can access this page.")
        return redirect('home')

    # If the user is an admin, render the custom admin dashboard
    users=User.objects.all()
    user_count=users.count()
    courses = Course.objects.all()
    active_courses=Course.objects.filter(status='approved').count()
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(title__icontains=search_query)
    print(courses)


    return render(request, 'ArtiQuityapp/admin_dashboard.html', {'courses': courses,'users':users,'user_count':user_count,'active_courses':active_courses})





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
    old_image_path = course.thumbnail.path if course.thumbnail else None
    if request.method == 'POST':
        form = CourseCreationForm(request.POST, request.FILES, instance=course)

        if 'thumbnail' in request.FILES and old_image_path:
            if os.path.isfile(old_image_path):
                os.remove(old_image_path)
                print("INFO | Old Image deleted")


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
    old_image_path = course.thumbnail.path if course.thumbnail else None
   
    if request.method == 'POST':
        if 'thumbnail' in request.FILES and old_image_path:
                if os.path.isfile(old_image_path):
                    os.remove(old_image_path)  # Remove the old image file
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

def user_logout(request):
    logout(request)
    request.session.flush()
    print("User is logged out")
    return redirect('home')

@login_required
def send_course_for_approval(request, course_id):
    """
    View for instructors to send a course for admin approval.
    """
    course = get_object_or_404(Course, id=course_id, instructor=request.user)

    if course.status == 'draft' or course.status=='rejected':
        course.send_for_approval()
        messages.success(request, f'Course "{course.title}" has been sent for admin approval.')
    else:
        messages.error(request, 'Only draft courses can be sent for approval.')

    return redirect('instructor_dashboard')

@login_required
def approve_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Ensure only admin can approve courses
    if request.user.role == 'admin':
        course.status = 'approved' 
         # Change course status to 'approved'
        course.save()
        messages.success(request, f'Course "{course.title}" has been approved successfully.')
    else:
        messages.error(request, 'You do not have permission to perform this action.')
    
    return redirect('admin_dashboard')

# View to reject a course
@login_required
def reject_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Ensure only admin can reject courses
    if request.user.role == 'admin':
        if request.method == 'POST':
            rejection_reason = request.POST.get('rejection_reason')  # Fetch rejection reason from form
            course.status = 'rejected'  # Change course status to 'rejected'
            course.rejection_reason = rejection_reason  # Save the rejection reason
            course.save()
            messages.success(request, f'Course "{course.title}" has been rejected.')
            return redirect('admin_dashboard')
        
        # Render a template to ask for rejection reason
        return render(request, 'ArtiQuityapp/reject_course.html', {'course': course})
    else:
        messages.error(request, 'You do not have permission to perform this action.')
    
    return redirect('admin_dashboard')

def course_detail_view(request, course_id):
    role=request.user.role
    print(role)
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()  # Retrieve all lessons for the course
    context = {
        'course': course,
        'lessons': lessons,
        'role':role
    }
    return render(request, 'ArtiQuityapp/course_detail.html', context)

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST, request.FILES)
        if form.is_valid():
                  
            email=request.POST['email']
           
            print(email)

            try:
                user_obj = User.objects.get(email=email)
                print(user_obj.last_name)
                token = generate_token()
                user_obj.reset_password_token = token  # Save the token in the user table
                user_obj.save()
                if user_obj is not None:
                 # Save the token in the user table
                    reset_link = request.build_absolute_uri(reverse('reset_password') + f"?token={token}")
                    send_mail(
                        'Reset Your Password',
                        f'Click the link to reset your password: {reset_link}',
                        'tapasyasangrai700@gmail.com',  # Change to your email
                        [email],
                        fail_silently=False,
                        )
                    messages.success(request, 'A password reset link has been sent to your email.')
                    return redirect('forgot_password')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
                return redirect('forgot_password')
                
    else:
        form = ForgotPasswordForm()

    return render(request, 'ArtiQuityapp/forgot_password.html', {'form': form})

def generate_token():
    return get_random_string(64)

def reset_password(request):
    token = request.GET.get('token')

    if not token:
        messages.error(request, 'Invalid or expired token.')
        return redirect('forgot_password')

    try:
        user = User.objects.get(reset_password_token=token)
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired token.')
        return redirect('forgot_password')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.password_hash=(new_password)  # Update the user's password
            user.reset_password_token = None  # Clear the token after reset
            user.save()
            messages.success(request, 'Your password has been reset successfully.')
            return redirect('user_login')
    else:
        form = SetNewPasswordForm()

    return render(request, 'ArtiQuityapp/reset_password.html', {'form': form})
