from django.db import models
from student.models import Student
from exam.models import Exam
from question.models import Question, Alternative

class ExamSubmission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='submissions')
    submission_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f'Submission of {self.student} for {self.exam}'

class Answer(models.Model):
    submission = models.ForeignKey(ExamSubmission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_alternative = models.ForeignKey(Alternative, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('submission', 'question')

    def __str__(self):
        return f'Answer to {self.question} in {self.submission}'
