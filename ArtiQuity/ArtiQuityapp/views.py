
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
    id=request.user.id
    print(role)
    visibility=False
    enrolled=None
    course = get_object_or_404(Course, id=course_id)
    try: 
        enrolled = Enrollment.objects.get(course_id=course_id)
        if enrolled.student_id==id:
            visibility=True
    except:
        pass
    
    lessons = course.lessons.all()  # Retrieve all lessons for the course
    context = {
        'course': course,
        'lessons': lessons,
        'role':role,
        'visibility':visibility

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

def enrolled_courses(request):
    enrolls=Enrollment.objects.filter(student_id=request.user)
    if enrolls:
        en_course=[]
        
        print(enrolls)
        for e in enrolls:
            en_course.append(Course.objects.filter(id=e.course_id).first())
            print(e.id)
            print(e.student_id)
            print(e.course_id)
        print(en_course)
        print(en_course[0].id)
    
    
        search_query = request.GET.get('search', '')
        if search_query:
            en_course_search=[]
            for e in en_course:
               search_course = Course.objects.filter(title__icontains=search_query,id=e.id)
               print(search_course)
               if search_course:
                   en_course_search.append(search_course.first())
            print(en_course_search)

            
            return render(request, 'ArtiQuityapp/enrolled_courses.html', {'en_course': en_course_search}) 
        else:
            return render(request, 'ArtiQuityapp/enrolled_courses.html', {'en_course': en_course })
    else:
        return render(request, 'ArtiQuityapp/enrolled_courses.html', {'en_course': en_course})
