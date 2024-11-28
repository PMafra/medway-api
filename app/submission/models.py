from django.db import models
from student.models import Student
from exam.models import Exam
from question.models import Question, Alternative
from django.db.models import Sum, Case, When, IntegerField, Count, Prefetch


class ExamSubmissionQuerySet(models.QuerySet):
    def with_total_correct(self):
        return self.annotate(
            total_correct=Sum(
                Case(
                    When(
                        answers__selected_alternative__is_correct=True,
                        then=1,
                    ),
                    default=0,
                    output_field=IntegerField(),
                )
            )
        )

    def with_total_questions(self):
        return self.annotate(total_questions=Count("answers"))

    def annotate_performance_metrics(self):
        answers_prefetch = Prefetch(
            "answers",
            queryset=Answer.objects.select_related("selected_alternative", "question"),
        )
        return (
            self.with_total_correct()
            .with_total_questions()
            .select_related("student", "exam")
            .prefetch_related(answers_prefetch)
        )


class ExamSubmission(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="submissions"
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="submissions")
    submission_time = models.DateTimeField(auto_now_add=True)

    objects = ExamSubmissionQuerySet.as_manager()

    class Meta:
        unique_together = ("student", "exam")

    def __str__(self):
        return f"Submission of {self.student} for {self.exam}"


class Answer(models.Model):
    submission = models.ForeignKey(
        ExamSubmission, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_alternative = models.ForeignKey(Alternative, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("submission", "question")

    def __str__(self):
        return f"Answer to {self.question} in {self.submission}"
