from rest_framework import generics
from .models import ExamSubmission
from exam.models import Exam
from student.models import Student
from .serializers import ExamResultSerializer, ExamSubmissionSerializer


class ExamSubmissionCreateView(generics.CreateAPIView):
    serializer_class = ExamSubmissionSerializer

    def perform_create(self, serializer):
        student_id = self.kwargs.get("student_id")
        exam_id = self.kwargs.get("exam_id")
        student = generics.get_object_or_404(Student, id=student_id)
        exam = generics.get_object_or_404(Exam, id=exam_id)
        serializer.save(student=student, exam=exam)


class ExamResultView(generics.RetrieveAPIView):
    serializer_class = ExamResultSerializer
    lookup_fields = ("student_id", "exam_id")

    def get_queryset(self):
        return ExamSubmission.objects.annotate_performance_metrics()

    def get_object(self):
        queryset = self.get_queryset()
        student_id = self.kwargs.get("student_id")
        exam_id = self.kwargs.get("exam_id")
        student = generics.get_object_or_404(Student, id=student_id)
        exam = generics.get_object_or_404(Exam, id=exam_id)
        return generics.get_object_or_404(queryset, student=student, exam=exam)
