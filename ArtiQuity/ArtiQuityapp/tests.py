from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import (
    User,
    Course,
    Lesson,
    Progress,
    Enrollment,
    Payment,
    Review,
    Certificate,
    Cart,
)


class ModelsTestCase(TestCase):
    def setUp(self):
        # Create valid users
        self.instructor = User.objects.create(
            username="instructor1",
            email="instructor@example.com",
            first_name="John",
            last_name="Doe",
            role="instructor",
            is_authenticated=True,
        )
        self.student = User.objects.create(
            username="student1",
            email="student@example.com",
            first_name="Jane",
            last_name="Smith",
            role="student",
            is_authenticated=True,
        )

        # Create a valid course
        self.course = Course.objects.create(
            title="Sample Course",
            description="This is a test course",
            price=99.99,
            instructor=self.instructor,
        )

    # User Model Tests
    def test_user_creation_pass(self):
        user = User.objects.create(
            username="testuser",
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            role="student",
            is_authenticated=True,
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(User.objects.count(), 3)

    def test_user_creation_fail(self):
        with self.assertRaises(ValidationError):
            user = User(
                username="invalid user!",  # Invalid username
                email="invaliduser",  # Invalid email
                first_name="1234",  # Invalid first name
                last_name="",  # Empty last name
                role="invalid_role",  # Invalid role
            )
            user.full_clean()  # Triggers validation

    # Course Model Tests
    def test_course_creation_pass(self):
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(self.course.title, "Sample Course")
        self.assertEqual(self.course.price, 99.99)

    def test_course_creation_fail(self):
        with self.assertRaises(ValidationError):
            course = Course(
                title="",  # Empty title
                description="This course has no title",
                price=-10.99,  # Negative price
                instructor=self.instructor,
            )
            course.full_clean()

    # Lesson Model Tests
    def test_lesson_creation_pass(self):
        lesson = Lesson.objects.create(
            course=self.course, title="Lesson 1", content="Lesson 1 content"
        )
        self.assertEqual(Lesson.objects.count(), 1)
        self.assertEqual(lesson.title, "Lesson 1")

    def test_lesson_creation_fail(self):
        with self.assertRaises(ValidationError):
            lesson = Lesson(
                course=None,  # No associated course
                title="",  # Empty title
                content="Invalid lesson",
            )
            lesson.full_clean()

    # Enrollment Model Tests
    def test_enrollment_creation_pass(self):
        enrollment = Enrollment.objects.create(
            student=self.student, course=self.course
        )
        self.assertEqual(Enrollment.objects.count(), 1)
        self.assertEqual(enrollment.student, self.student)

    def test_enrollment_creation_fail(self):
        with self.assertRaises(ValidationError):
            enrollment = Enrollment(
                student=None,  # Missing student
                course=self.course,
            )
            enrollment.full_clean()

    # Payment Model Tests
    def test_payment_creation_pass(self):
        payment = Payment.objects.create(
            student=self.student,
            amount=99.99,
            payment_method="Stripe",
            transaction_id="txn_12345",
            payment_status="completed",
        )
        payment.courses.add(self.course)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(payment.amount, 99.99)

    def test_payment_creation_fail(self):
        with self.assertRaises(ValidationError):
            payment = Payment(
                student=self.student,
                amount=-99.99,  # Negative amount
                payment_method="InvalidMethod",  # Invalid payment method
                transaction_id="",  # Missing transaction ID
                payment_status="unknown",  # Invalid status
            )
            payment.full_clean()

    # Review Model Tests
    def test_review_creation_pass(self):
        review = Review.objects.create(
            student=self.student,
            course=self.course,
            rating=4,
            comment="Great course!",
        )
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(review.rating, 4)

    def test_review_creation_fail(self):
        with self.assertRaises(ValidationError):
            review = Review(
                student=self.student,
                course=self.course,
                rating=6,  # Invalid rating
                comment="Invalid rating",
            )
            review.full_clean()

    # Certificate Model Tests
    def test_certificate_creation_pass(self):
        enrollment = Enrollment.objects.create(
            student=self.student, course=self.course
        )
        certificate = Certificate.objects.create(
            enrollment=enrollment, certificate_url="http://example.com/cert.pdf"
        )
        self.assertEqual(Certificate.objects.count(), 1)
        self.assertEqual(certificate.certificate_url, "http://example.com/cert.pdf")

    def test_certificate_creation_fail(self):
        with self.assertRaises(ValueError):
            certificate = Certificate(
                enrollment=None,  # Missing enrollment
                certificate_url="",
            )
            certificate.full_clean()

    # Cart Model Tests
    def test_cart_creation_pass(self):
        cart = Cart.objects.create(user=self.student, course=self.course)
        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(cart.course, self.course)

    def test_cart_creation_fail(self):
        with self.assertRaises(ValueError):
            cart = Cart(user=None, course=self.course)
            cart.full_clean()
