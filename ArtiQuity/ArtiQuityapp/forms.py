from django import forms
from .models import User
from .models import Course, Lesson

class UserSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

    def save(self, commit=True):
        user = super(UserSignupForm, self).save(commit=False)
        user.password_hash = self.cleaned_data['password']  # Save the password temporarily
        user.role = 'student'  # Set role to 'student' by default
        if commit:
            user.save()
        return user

class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}), max_length=255, required=True)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}), required=True)

class InstructorSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

    def save(self, commit=True):
        user = super(InstructorSignupForm, self).save(commit=False)
        user.password_hash = self.cleaned_data['password']  # Save the password temporarily
        user.role = 'instructor'  # Set role to 'student' by default
        if commit:
            user.save()
        return user
class InstructorLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}), max_length=255, required=True)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}), required=True)



class CourseCreationForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'price', 'thumbnail']

class LessonCreationForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'video_url', 'content']
