from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Choice, Course, Enrollment, Question, Submission


class AssessmentFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='learner', password='test-pass-123')
        self.course = Course.objects.create(
            name='Learning Django',
            image='course_images/django.png',
            description='A test course',
        )
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        self.question = Question.objects.create(
            course=self.course,
            content='Is Django a Python framework?',
            grade=100,
        )
        self.correct = Choice.objects.create(
            question=self.question,
            content='Yes',
            is_correct=True,
        )
        self.incorrect = Choice.objects.create(
            question=self.question,
            content='No',
            is_correct=False,
        )

    def test_question_requires_exact_correct_choice_set(self):
        self.assertTrue(self.question.is_get_score([self.correct.id]))
        self.assertFalse(self.question.is_get_score([self.incorrect.id]))
        self.assertFalse(self.question.is_get_score([self.correct.id, self.incorrect.id]))

    def test_submit_creates_submission_and_redirects_to_results(self):
        self.client.login(username='learner', password='test-pass-123')
        response = self.client.post(
            reverse('onlinecourse:submit', args=[self.course.id]),
            {f'choice{self.correct.id}': str(self.correct.id)},
        )

        submission = Submission.objects.get()
        self.assertRedirects(
            response,
            reverse(
                'onlinecourse:show_exam_result',
                args=[self.course.id, submission.id],
            ),
        )
        self.assertEqual(list(submission.choices.all()), [self.correct])

    def test_result_page_shows_passing_score_and_details(self):
        submission = Submission.objects.create(enrollment=self.enrollment)
        submission.choices.add(self.correct)
        self.client.login(username='learner', password='test-pass-123')

        response = self.client.get(
            reverse(
                'onlinecourse:show_exam_result',
                args=[self.course.id, submission.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Congratulations!')
        self.assertContains(response, '100%')
        self.assertContains(response, self.question.content)
