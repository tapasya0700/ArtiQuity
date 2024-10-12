from django.db import models
from .validations import *
# Create your models here.


# 1. Users Table
class User(models.Model):
    username = models.CharField(max_length=255, unique=True,validators=[ValidateUserName])
    email = models.EmailField(max_length=255,validators=[ValidateEmail])
    password_hash = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100,validators=[ValidateName])
    last_name = models.CharField(max_length=100,validators=[ValidateName])
    profile_picture = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=50, choices=[('student', 'Student'), ('instructor', 'Instructor'), ('admin', 'Admin')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_authenticated = models.BooleanField(default=False)
    reset_password_token = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'username'  # Use `username` to log in
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']  # Required fields for user creation

    
    class Meta:
        unique_together = ('email', 'role') 

    def _str_(self):
        return self.username


# 2. Courses Table
class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2,validators=[ValidatePrice])
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    
    # Status dropdown choices
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    
    # New field for tracking if the course has been sent for admin approval
    is_sent_for_approval = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def send_for_approval(self):
        """
        Method to update the course status and mark it as sent for admin approval.
        """
        self.is_sent_for_approval = True
        self.status = 'pending'
        self.save()



# 3. Lessons Table
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    video_url = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return self.title


# 4. Enrollments Table
class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    def _str_(self):
        return f'{self.student.username} enrolled in {self.course.title}'


# 5. Payments Table
class Payment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    courses = models.ManyToManyField(Course, related_name='payments') 
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=[('Stripe', 'Stripe'), ('PayPal', 'PayPal')])
    transaction_id = models.CharField(max_length=255)
    payment_status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')])
    payment_date = models.DateTimeField(auto_now_add=True)



    def _str_(self):
        return f'{self.student.username} paid for {self.course.title}'


# 6. Reviews Table
class Review(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    review_date = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f'Review by {self.student.username} on {self.course.title}'


# 7. Course Categories Table
class CourseCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def _str_(self):
        return self.name


# 8. Course Category Relations Table
class CourseCategoryRelation(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('course', 'category')

    def _str_(self):
        return f'{self.course.title} in {self.category.name}'


# 9. Certificates Table
class Certificate(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='certificates')
    certificate_url = models.CharField(max_length=255)
    issued_date = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f'Certificate for {self.enrollment.course.title} - {self.enrollment.student.username}'
    
# Cart Table 

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    