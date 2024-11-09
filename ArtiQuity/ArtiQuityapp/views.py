
import json
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
from .models import User,Cart,Payment,Enrollment
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
import stripe
from ArtiQuityapp.models import Cart 
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from .models import Course, Lesson, Enrollment, Progress, Review,Certificate
from .forms import ReviewForm
from django.contrib import messages
# views.py
from django.db.models import Avg
from django.shortcuts import render, get_object_or_404, redirect
from .models import Course, Lesson, Enrollment, Progress, Review
from .forms import ReviewForm
from django.contrib import messages

from django.shortcuts import get_object_or_404, redirect
from django.db.models import Avg
from django.contrib import messages

from django.shortcuts import get_object_or_404, redirect
from django.db.models import Avg
from django.contrib import messages
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
        if user and check_password(password,user.password_hash):
            user.is_authenticated = True
            user.last_login = timezone.now()
            user.save()
            return user
    except User.DoesNotExist:
        return None
    return None
@login_required


@login_required
def instructor_dashboard(request):
    # Debug information for the logged-in user
    print(f"User logged in: {request.user.username}")  # Print the logged-in user
    print(f"User role: {request.user.role}")

    # Check if the user has the role of 'instructor'
    if request.user.role != 'instructor':
        messages.error(request, "Access denied! Only instructors can access this page.")
        return redirect('home')

    # Retrieve all courses created by the instructor
    course_data = []
    all_courses = Course.objects.filter(instructor=request.user)
    approved_courses = all_courses.filter(status='approved')
    rejected_courses = all_courses.filter(status='rejected')
    
    

    # Apply search filter if a query is provided
    search_query = request.GET.get('search', '')
    if search_query:
        all_courses = all_courses.filter(title__icontains=search_query)
        approved_courses = approved_courses.filter(title__icontains=search_query)
        rejected_courses = rejected_courses.filter(title__icontains=search_query)
    for course in all_courses:
        first_lesson = course.lessons.first()  # Get the first lesson, if it exists
        course_data.append({
            'course': course,
            'first_lesson_id': first_lesson.id if first_lesson else None,
        })  


    # Render the dashboard template with the filtered courses
    return render(request, 'ArtiQuityapp/instructor_dashboard.html', {
        'all_courses': all_courses,
        'approved_courses': approved_courses,
        'rejected_courses': rejected_courses,
        'search_query': search_query,  # Pass the search query to maintain it in the template if needed
        'course_data': course_data,
    })


@login_required


def student_dashboard(request):
    # Verify if the user is a student
    print(f"User logged in: {request.user.username}")  # Print the logged-in user
    print(f"User role: {request.user.role}")
    if request.user.role != 'student':
        messages.error(request, "Access denied! Only students can access this page.")
        return redirect('home')
    
    # Retrieve all courses or filter by search query
    courses = Course.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(title__icontains=search_query)

    # Process each course to calculate average rating and get the first lesson ID
    course_data = []
    for course in courses:
        avg_rating = course.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        course.average_rating = round(avg_rating, 1)
        first_lesson = course.lessons.first()  # Get the first lesson, if it exists

        course_data.append({
            'course': course,
            'first_lesson_id': first_lesson.id if first_lesson else None,
            'average_rating': course.average_rating,
        })

    star_range = range(5)  # For star display in the template

    # Render the student dashboard template with course data
    return render(request, 'ArtiQuityapp/student_dashboard.html', {
        'course_data': course_data,
        'star_range': star_range,
    })


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
        form = LessonCreationForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, 'Lesson added successfully!')
            return redirect('course_detail', course_id=lesson.course_id,lesson_id=lesson.id)
    else:
        form = LessonCreationForm()
    
    return render(request, 'ArtiQuityapp/create_lesson.html', {'form': form, 'course': course})





def user_signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            # Hash the password before saving it
            raw_password = form.cleaned_data['password']
            user.password_hash = make_password(raw_password)
            try:
               user.save()
               messages.success(request,"Student account created successfully")
               return redirect('user_login')
            except IntegrityError as e:
                # Catch the duplicate key error and show a user-friendly message
                if 'duplicate key' in str(e):
                    form.add_error('email', 'An account with this email already exists for this role.')
                else:
                    form.add_error(None, 'An unexpected error occurred. Please try again.')
          
            #print(user.id)
              # Redirect to home page after successful signup
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
            #print (user.password_hash)
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
                messages.error(request,"Invalid Username or password")
                
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


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User, Course
def admin_dashboard(request):
    # Check if the logged-in user has the role of 'admin'
    if request.session.get('user_role') != 'admin':
        messages.error(request, "Access denied! Only admins can access this page.")
        return redirect('home')

    # Retrieve all users and count them
    users = User.objects.all()
    user_count = users.count()

    # Retrieve all courses and filter approved ones for counting active courses
    courses = Course.objects.all()
    active_courses_count = courses.filter(status='approved').count()

    # Filter courses with status 'pending'
    pending_courses = courses.filter(status='pending')

    # Search functionality for courses
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(title__icontains=search_query)

    # Debug print statement (optional, remove in production)
    print(f"Filtered courses: {courses}")

    # Render the admin dashboard with context data
    context = {
        'courses': courses,
        'users': users,
        'user_count': user_count,
        'active_courses_count': active_courses_count,
        'pending_courses': pending_courses,
        'search_query': search_query  # Pass the search query to maintain it in the template
    }
    return render(request, 'ArtiQuityapp/admin_dashboard.html', context)



def instructor_signup(request):
    if request.method == 'POST':
        form = InstructorSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            # Hash the password before saving it
            raw_password = form.cleaned_data['password']
            user.password_hash = make_password(raw_password)
            try:
               user.save()
               messages.success(request,"Instuctor account created successfully")
               return redirect('instructor_login')
            except IntegrityError as e:
                # Catch the duplicate key error and show a user-friendly message
                if 'duplicate key' in str(e):
                    form.add_error('email', 'An account with this email already exists for this role.')
                else:
                    form.add_error(None, 'An unexpected error occurred. Please try again.') 
            
              # Redirect to home page after successful signup
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
           
            if user is not None:
                request.session['user_id'] = user.id
                request.session['user_role'] = user.role
                request.session['username'] = user.username
                    

                print(f"User {user.username} is logged in: {user.is_authenticated}")  # Should print True
             
               
                print(f"Session Data: {request.session.items()}")
                update_session_auth_hash(request, user)
                print(f"Session Data: {request.session.items()}")
                return redirect('instructor_dashboard')
                
    
                
                
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
    #try:
    is_enrolled=Enrollment.objects.filter(course_id=course_id)
    print(is_enrolled)
    if request.method == 'POST':
        if not is_enrolled.exists():
            if 'thumbnail' in request.FILES and old_image_path:
                if os.path.isfile(old_image_path):
                    os.remove(old_image_path)  # Remove the old image file
            course.delete()
            messages.success(request, 'Course deleted successfully!')
            return redirect('instructor_dashboard')
        else:
            messages.error(request,"Course cannot be deleted")
            return redirect('instructor_dashboard')

    #except:
        #messages.error(request,"something went wrong")

    return render(request, 'ArtiQuityapp/confirm_delete.html', {'course': course})


# Edit a Lesson
@login_required

def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    old_video_path = lesson.video_file.path if lesson.video_file else None  # Store the path of the old video file
    
    if request.method == 'POST':
        form = LessonCreationForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            # Check if a new video file is being uploaded
            if 'video_file' in request.FILES:
                # Remove the old video file if it exists
                if old_video_path and os.path.isfile(old_video_path):
                    os.remove(old_video_path)
                    
                # Update the video file with the new one
                lesson.video_file = request.FILES['video_file']
            
            form.save()  # Save the form to update the database
            messages.success(request, 'Lesson updated successfully!')
            return redirect('course_detail', lesson.course_id, lesson.id)
    else:
        form = LessonCreationForm(instance=lesson)
    
    return render(request, 'ArtiQuityapp/edit_lesson.html', {'form': form, 'lesson': lesson})



# Delete a Lesson
@login_required

def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    video_path = lesson.video_file.path if lesson.video_file else None  # Get the path of the video file
    left_lessons=Lesson.objects.filter(course_id=lesson.course_id)
    if request.method == 'POST':
        # Remove the video file if it exists
        if video_path and os.path.isfile(video_path):
            os.remove(video_path)
        
        lesson.delete()  # Delete the lesson from the database
        messages.success(request, 'Lesson deleted successfully!')
        
        
        return redirect('course_detail', lesson.course_id, left_lessons[0].id if left_lessons else 0)
       
    
    return render(request, 'ArtiQuityapp/lesson_delete.html', {'lesson': lesson})

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

from django.shortcuts import render, get_object_or_404
from .models import Course, Lesson, Enrollment, Progress

from django.shortcuts import render, get_object_or_404
from .models import Course, Lesson, Enrollment, Progress

# views.py


def course_detail_view(request, course_id, lesson_id=None):
    role = request.user.role
    user_id = request.user.id
    visibility = False

    # Get the course and check if the user is enrolled
    course = get_object_or_404(Course, id=course_id)
    enrolled = Enrollment.objects.filter(course_id=course.id, student_id=user_id).exists()
    if enrolled:
        visibility = True

    # Retrieve all lessons for the course
    lessons = course.lessons.all()
    
    # Determine the selected lesson; if lesson_id is not provided, use the first lesson
    selected_lesson = get_object_or_404(Lesson, id=lesson_id, course=course) if lesson_id else lessons.first()
    
    # Mark lesson as completed if the form is submitted
    if request.method == 'POST' and 'complete_lesson' in request.POST:
        Progress.objects.update_or_create(student_id=user_id, lesson=selected_lesson, defaults={'is_completed': True})
        messages.success(request, 'Lesson marked as completed!')
        return redirect('course_detail', course_id=course.id, lesson_id=selected_lesson.id)

    # Calculate course progress percentage
    completed_count = 0
    for lesson in lessons:
        # Check if each lesson is completed by the student
        lesson.is_completed = Progress.objects.filter(student_id=user_id, lesson=lesson, is_completed=True).exists()
        if lesson.is_completed:
            completed_count += 1
    progress_percentage = (completed_count / lessons.count()) * 100 if lessons.exists() else 0
    if progress_percentage == 100:
        enrollment = Enrollment.objects.get(course_id=course.id, student_id=user_id)
        # Generate the certificate if it doesn't exist
        Certificate.objects.get_or_create(
            enrollment=enrollment,
            defaults={
                'certificate_url': f'/certificates/{enrollment.id}.pdf',  # Example URL
                'issued_date': timezone.now()
            }
        )

    # Handle review submission
    if request.method == 'POST' and 'submit_review' in request.POST:
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.student = request.user
            review.course = course
            review.save()
            messages.success(request, 'Thank you for your review!')
            return redirect('course_detail', course_id=course_id, lesson_id=selected_lesson.id)
    else:
        review_form = ReviewForm()

    # Get existing reviews and calculate average rating
    reviews = course.reviews.all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0  # Defaults to 0 if no reviews
    course.average_rating = round(avg_rating, 1)
    star_range = range(5)

    context = {
        'course': course,
        'lessons': lessons,
        'selected_lesson': selected_lesson,
        'role': role,
        'visibility': visibility,
        'progress_percentage': progress_percentage,
        'review_form': review_form,
        'reviews': reviews,
        'average_rating': course.average_rating,
        'star_range': star_range,
        'enrollment':enrollment,
    }
    return render(request, 'ArtiQuityapp/course_detail.html', context)


def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST, request.FILES)

        if form.is_valid():
                  
            email=request.POST['email']
            role=request.POST['role']
            print(email)

            try:
                user_obj = User.objects.get(email=email,role=role)
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


# Add course to cart
@login_required
def add_to_cart(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrolled=None
    try:
        enrolled=Enrollment.objects.get(course_id=course_id,student_id=request.user.id)
    except:
        pass
    if( not enrolled):
        cart_item, created = Cart.objects.get_or_create(user=request.user, course=course)
        if created:
            cart_item.save()
            messages.success(request,"Course has been added to your cart")
            return redirect('student_dashboard')
        else:
            return redirect('view_cart')
    else:
        messages.error(request,"You are already enrolled in the course")
        return redirect('student_dashboard')
     
@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.course.price for item in cart_items)
    
    return render(request, 'ArtiQuityapp/cart.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def remove_from_cart(request, course_id):
    cart_item = get_object_or_404(Cart, user=request.user, course_id=course_id)
    cart_item.delete()
    messages.success(request," Course has been removed from your cart")
    return redirect('view_cart')

stripe.api_key = settings.STRIPE_SECRET_KEY

# Checkout View
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    
    # Check if the cart is empty
    if not cart_items.exists():
        messages.error(request, "Your cart is empty. Please add courses before proceeding to checkout.")
        return redirect('view_cart')  # Redirect to the cart page or any relevant page

    total_price = sum(item.course.price for item in cart_items)
    print(cart_items)
    print(total_price)

    # Display the checkout page
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY
    }
    return render(request, 'ArtiQuityapp/checkout.html', context)

 # Assuming Cart model is defined

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def process_payment(request):
    if request.method == 'POST':
        # Get payment details from form
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        stripe_token = request.POST.get('stripeToken')

        # Validate form fields
        if not full_name or not email or not stripe_token:
            messages.error(request, "Missing required payment information.")
            return redirect('checkout')
        else:
        # Calculate total price from cart
            cart_items = Cart.objects.filter(user=request.user)
            total_price = sum(item.course.price for item in cart_items)

            if total_price <= 0:
                messages.error(request, "Your cart is empty.")
                return redirect('checkout')

            else:
                try:
            # Create a Stripe charge
                    charge = stripe.Charge.create(
                            amount=int(total_price * 100),  # Stripe works with cents
                        currency='usd',
                        description=f"Charge for {request.user.username}",
                        source=stripe_token,
                        receipt_email=email,
                    )

            # If payment is successful, record payment and clear cart
                    payment = Payment.objects.create(
                            student=request.user,
                              amount=total_price,
                   
                                transaction_id=charge.id,  # Assuming you store Stripe charge IDs
                            )
                    for items in cart_items:
                            payment.courses.add(items.course)
                    payment.save()
                    if payment is not None:
                        for items in cart_items:
                              enrollment=Enrollment.objects.create(
                                   student=request.user,
                                   enrolled_at=timezone.now(),
                                   course=items.course
                              )
                              enrollment.save()

                              
                         
    


            # Clear the user's cart after successful payment
                    cart_items.delete()

            # Redirect to a success page (student dashboard)
                    messages.success(request, "Payment successful! Thank you for your purchase.")
                    return redirect('student_dashboard')

                except stripe.error.CardError as e:
            # Handle card errors
                        messages.error(request, f"Your card was declined: {e.user_message}")
                        print('1')
                        return redirect('checkout')
                except stripe.error.RateLimitError:
            # Too many requests made to the API too quickly
                        messages.error(request, "Rate limit error. Please try again.")
                        print('2')
                        return redirect('checkout')
                except stripe.error.InvalidRequestError:
            # Invalid parameters were supplied to Stripe's API
                        messages.error(request, "Invalid payment request. Please check your details.")
                        print('3')
                        return redirect('checkout')
                except stripe.error.AuthenticationError:
            # Authentication with Stripe's API failed (wrong API keys?)
                        messages.error(request, "Payment authentication failed. Please contact support.")
                        print('4')
                        return redirect('checkout')
                except stripe.error.APIConnectionError:
            # Network communication with Stripe failed
                        messages.error(request, "Network error. Please try again.")
                        print('5')
                        return redirect('checkout')
                except stripe.error.StripeError:
            # Generic Stripe error
                        messages.error(request, "Payment error. Please try again later.")
                        print('6')
                        return redirect('checkout')
                except Exception as e:
            # Handle other unforeseen errors
                        messages.error(request, f"An error occurred: {str(e)}")
                        print(f"Other Error: {str(e)}")
                        return redirect('checkout')

    # If the request is GET, show the checkout page
    return render(request, 'ArtiQuityapp/checkout.html')
from django.db.models import Avg

from .models import Enrollment, Course


def enrolled_courses(request):
    enrolls = Enrollment.objects.filter(student_id=request.user.id)
    en_course = []

    for enrollment in enrolls:
        course = Course.objects.filter(id=enrollment.course_id).first()
        
        if course:
            # Calculate the average rating for each course
            avg_rating = course.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            course.average_rating = round(avg_rating, 1)
            
            # Retrieve the first lesson ID if available
            first_lesson = course.lessons.first()  # Get the first lesson if it exists
            
            # Append course data with average rating and first lesson ID
            en_course.append({
                'course': course,
                'average_rating': course.average_rating,
                'first_lesson_id': first_lesson.id if first_lesson else None,
            })

    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        en_course = [
            course_info for course_info in en_course
            if search_query.lower() in course_info['course'].title.lower()
        ]

    return render(request, 'ArtiQuityapp/enrolled_courses.html', {
        'en_course': en_course,
        'search_query': search_query,
        'star_range': range(5),  # For star display in the template
    })
    
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Lesson, Progress
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Lesson, Enrollment, Progress
import json

@csrf_exempt
def mark_lesson_complete(request):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        lesson_id = data.get('lesson_id')
        
        try:
            # Check if the lesson exists
            lesson = Lesson.objects.get(id=lesson_id)

            # Check if the user is enrolled in the course
            if Enrollment.objects.filter(student=request.user, course=lesson.course).exists():
                # Update or create the progress entry for the lesson
                progress, created = Progress.objects.get_or_create(student=request.user, lesson=lesson)
                progress.is_completed = True
                progress.save()
                
                return JsonResponse({'status': 'success', 'message': 'Lesson marked as completed.'})

            else:
                return JsonResponse({'status': 'failed', 'message': 'User is not enrolled in this course.'}, status=403)
        
        except Lesson.DoesNotExist:
            return JsonResponse({'status': 'failed', 'message': 'Lesson not found.'}, status=404)
    
    return JsonResponse({'status': 'failed', 'message': 'Invalid request.'}, status=400)
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from .models import Certificate, Enrollment
from io import BytesIO

def generate_certificate_view(request, enrollment_id):
    # Fetch the enrollment and related certificate data
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    certificate = enrollment.certificates.first()  # Assuming one certificate per enrollment

    # Check if the user has access to this certificate
    if request.user != enrollment.student:
        return HttpResponse("You are not authorized to view this certificate.", status=403)

    # Render the template with context
    return render(request, 'ArtiQuityapp/certificate.html', {
        'enrollment': enrollment,
        'certificate': certificate,
    })

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.shortcuts import get_object_or_404
from .models import Enrollment

def download_certificate_as_pdf(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    # Fetch the template and render it with the enrollment context
    template_path = 'ArtiQuityapp\certificate.html'# Replace with your actual template path
    context = {
        'enrollment': enrollment,
        'course': enrollment.course,
        'student': enrollment.student,
        'issued_date': enrollment.certificates.first().issued_date,
    }

    # Render the HTML with the context
    template = get_template(template_path)
    html = template.render(context)

    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{enrollment.student.username}.pdf"'

    # Use xhtml2pdf to convert HTML to PDF and write it to the response
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    # Check for errors
    if pisa_status.err:
        return HttpResponse('We had some errors with your PDF', status=500)

    return response

