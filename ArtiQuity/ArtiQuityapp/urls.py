from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
urlpatterns = [
    path('about/',views.about, name='about'),
    path('',views.home ,name='home'),
    path('signup/', views.user_signup, name='user_signup'),
    path('login/',views.user_login, name='user_login'),
     path('instructor_signup/', views.instructor_signup, name='instructor_signup'),
    path('instructor_login/',views.instructor_login, name='instructor_login'),
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('instructor/create-course/', views.create_course, name='create_course'),
    path('instructor/create-lesson/<int:course_id>/', views.create_lesson, name='create_lesson'),
    path('instructor/edit-course/<int:course_id>/', views.edit_course, name='edit_course'),
    path('instructor/delete-course/<int:course_id>/', views.delete_course, name='delete_course'),
    path('instructor/edit-lesson/<int:lesson_id>/', views.edit_lesson, name='edit_lesson'),
    path('instructor/delete-lesson/<int:lesson_id>/', views.delete_lesson, name='delete_lesson'),
     path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
     path('logout/', views.user_logout, name='user_logout'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
