from django.urls import path
from .views import ExamSubmissionCreateView, ExamResultView

urlpatterns = [
    path('students/<int:student_id>/exams/<int:exam_id>/submissions/', ExamSubmissionCreateView.as_view(), name='create-submission'),
    path('students/<int:student_id>/exams/<int:exam_id>/submissions/result/', ExamResultView.as_view(), name='exam-result'),
]
