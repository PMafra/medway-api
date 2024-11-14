from rest_framework import serializers
from .models import ExamSubmission, Answer
from student.models import Student
from exam.models import Exam
from question.models import Alternative, Question
from django.shortcuts import get_object_or_404

class AnswerSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    selected_alternative = serializers.PrimaryKeyRelatedField(queryset=Alternative.objects.all())

    class Meta:
        model = Answer
        fields = ['question', 'selected_alternative']

class ExamSubmissionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = ExamSubmission
        fields = ['answers']
        read_only_fields = ['submission_time']

    def validate(self, data):
        kwargs = self.context['view'].kwargs
        student_id = kwargs.get('student_id')
        exam_id = kwargs.get('exam_id')

        student = get_object_or_404(Student, id=student_id)
        exam = get_object_or_404(Exam, id=exam_id)

        if ExamSubmission.objects.filter(student=student, exam=exam).exists():
            raise serializers.ValidationError("This student has already submitted this exam.")

        answers = data.get('answers', [])

        self.__validate_answers(answers, exam)

        return data

    def __validate_answers(self, answers, exam):
        num_questions = exam.questions.count()
        if len(answers) != num_questions:
            raise serializers.ValidationError(f"The number of answers does not match the number of questions in the exam: {num_questions}.")

        exam_question_ids = set(exam.questions.values_list('id', flat=True))
        submitted_question_ids = set()

        for answer in answers:
            question = answer['question']

            if question.id not in exam_question_ids:
                raise serializers.ValidationError(f"The question {answer['question'].id} does not belong to exam {exam.id}.")

            if question.id in submitted_question_ids:
                raise serializers.ValidationError(
                    f"The answer for question {question.id} is duplicated."
                )
            submitted_question_ids.add(question.id)

            if answer['selected_alternative'].question.id != question.id:
                raise serializers.ValidationError(
                    f"The alternative {answer['selected_alternative'].id} does not belong to question {question.id}."
                )

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        kwargs = self.context['view'].kwargs
        student_id = kwargs.get('student_id')
        exam_id = kwargs.get('exam_id')
        submission = ExamSubmission.objects.create(student_id=student_id, exam_id=exam_id)
        for answer_data in answers_data:
            Answer.objects.create(submission=submission, **answer_data)
        return submission


class AnswerResultSerializer(serializers.ModelSerializer):
    question = serializers.StringRelatedField()
    selected_alternative = serializers.StringRelatedField()
    is_correct = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = ['question', 'selected_alternative', 'is_correct']

    def get_is_correct(self, obj):
        return obj.selected_alternative.is_correct

class ExamResultSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField()
    exam = serializers.StringRelatedField()
    answers = AnswerResultSerializer(many=True)
    total_correct = serializers.SerializerMethodField()
    percentage_score = serializers.SerializerMethodField()

    class Meta:
        model = ExamSubmission
        fields = ['student', 'exam', 'submission_time', 'answers', 'total_correct', 'percentage_score']

    def get_total_correct(self, obj):
        return sum(1 for answer in obj.answers.all() if answer.selected_alternative.is_correct)

    def get_percentage_score(self, obj):
        total_questions = obj.answers.count()
        total_correct = self.get_total_correct(obj)
        if total_questions > 0:
            return (total_correct / total_questions) * 100
        return 0
