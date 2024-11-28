import pytest
from rest_framework.exceptions import ValidationError
from submission.serializers import ExamSubmissionSerializer, ExamResultSerializer
from submission.models import ExamSubmission, Answer
from student.models import Student
from exam.models import Exam, ExamQuestion
from question.models import Question, Alternative
from django.http import Http404


@pytest.fixture
def student(db):
    return Student.objects.create_user(
        username="teststudent", email="student@example.com", password="testpass"
    )


@pytest.fixture
def exam(db):
    return Exam.objects.create(name="Test Exam")


@pytest.fixture
def questions(db, exam):
    q1 = Question.objects.create(content="What is 2+2?")
    q2 = Question.objects.create(content="What is the capital of France?")
    ExamQuestion.objects.create(exam=exam, question=q1, number=1)
    ExamQuestion.objects.create(exam=exam, question=q2, number=2)
    return [q1, q2]


@pytest.fixture
def alternatives(db, questions):
    alternatives = []
    for question in questions:
        for idx, option in enumerate(["Option A", "Option B", "Option C"], start=1):
            alternative = Alternative.objects.create(
                question=question, content=option, option=idx, is_correct=(idx == 1)
            )
            alternatives.append(alternative)
    return alternatives


@pytest.fixture
def serializer_context(rf, student, exam):
    request = rf.post("/fake-path/")
    context = {
        "request": request,
        "view": type(
            "FakeView",
            (object,),
            {"kwargs": {"student_id": student.id, "exam_id": exam.id}},
        )(),
    }
    return context


def test_successful_submission(
    db, student, exam, questions, alternatives, serializer_context
):
    answers_data = []
    for question in questions:
        correct_alternative = Alternative.objects.get(
            question=question, is_correct=True
        )
        answers_data.append(
            {"question": question.id, "selected_alternative": correct_alternative.id}
        )
    data = {"answers": answers_data}
    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    assert serializer.is_valid(), serializer.errors
    submission = serializer.save()
    assert submission.student == student
    assert submission.exam == exam
    assert submission.answers.count() == len(questions)


def test_student_already_submitted(
    db, student, exam, questions, alternatives, serializer_context
):
    answers_data = []
    for question in questions:
        correct_alternative = Alternative.objects.get(
            question=question, is_correct=True
        )
        answers_data.append(
            {"question": question.id, "selected_alternative": correct_alternative.id}
        )
    data = {"answers": answers_data}
    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)
    assert "This student has already submitted this exam." in str(exc_info.value)


def test_incorrect_number_of_answers(
    db, student, exam, questions, alternatives, serializer_context
):
    correct_alternative = Alternative.objects.get(
        question=questions[0], is_correct=True
    )
    data = {
        "answers": [
            {
                "question": questions[0].id,
                "selected_alternative": correct_alternative.id,
            }
        ]
    }
    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)
    assert (
        "The number of answers does not match the number of questions in the exam"
        in str(exc_info.value)
    )


def test_question_not_in_exam(
    db, student, exam, questions, alternatives, serializer_context
):
    extra_question = Question.objects.create(content="Extra Question")
    extra_alternative = Alternative.objects.create(
        question=extra_question, content="Extra Option", option=1, is_correct=True
    )
    correct_alternative = Alternative.objects.get(
        question=questions[0], is_correct=True
    )
    data = {
        "answers": [
            {
                "question": questions[0].id,
                "selected_alternative": correct_alternative.id,
            },
            {
                "question": extra_question.id,
                "selected_alternative": extra_alternative.id,
            },
        ]
    }
    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)
    expected_error = (
        f"The question {extra_question.id} does not belong to exam {exam.id}."
    )
    assert expected_error in str(exc_info.value)


def test_duplicate_answers(
    db, student, exam, questions, alternatives, serializer_context
):
    correct_alternative_q1 = Alternative.objects.get(
        question=questions[0], is_correct=True
    )
    correct_alternative_q2 = Alternative.objects.filter(
        question=questions[1], is_correct=False
    ).first()
    answers_data = [
        {
            "question": questions[0].id,
            "selected_alternative": correct_alternative_q1.id,
        },
        {
            "question": questions[0].id,
            "selected_alternative": correct_alternative_q2.id,
        },
    ]
    data = {"answers": answers_data}
    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)
    expected_error = f"The answer for question {questions[0].id} is duplicated."
    assert expected_error in str(exc_info.value)


def test_alternative_not_belong_to_question(
    db, student, exam, questions, alternatives, serializer_context
):
    alternative_from_other_question = Alternative.objects.filter(
        question=questions[1]
    ).first()
    correct_alternative_q2 = Alternative.objects.get(
        question=questions[1], is_correct=True
    )
    answers_data = [
        {
            "question": questions[0].id,
            "selected_alternative": alternative_from_other_question.id,
        },
        {
            "question": questions[1].id,
            "selected_alternative": correct_alternative_q2.id,
        },
    ]
    data = {"answers": answers_data}
    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)
    expected_error = f"The alternative {alternative_from_other_question.id} does not belong to question {questions[0].id}."
    assert expected_error in str(exc_info.value)


def test_nonexistent_student(db, exam, questions, alternatives, rf):
    non_existent_student_id = 9999
    request = rf.post("/fake-path/")
    context = {
        "request": request,
        "view": type(
            "FakeView",
            (object,),
            {"kwargs": {"student_id": non_existent_student_id, "exam_id": exam.id}},
        )(),
    }
    answers_data = []
    for question in questions:
        correct_alternative = Alternative.objects.get(
            question=question, is_correct=True
        )
        answers_data.append(
            {"question": question.id, "selected_alternative": correct_alternative.id}
        )
    data = {"answers": answers_data}
    serializer = ExamSubmissionSerializer(data=data, context=context)
    with pytest.raises(Http404) as exc_info:
        serializer.is_valid(raise_exception=True)
    assert "No Student matches the given query." in str(exc_info.value)


def test_nonexistent_exam(db, student, questions, alternatives, rf):
    non_existent_exam_id = 9999
    request = rf.post("/fake-path/")
    context = {
        "request": request,
        "view": type(
            "FakeView",
            (object,),
            {"kwargs": {"student_id": student.id, "exam_id": non_existent_exam_id}},
        )(),
    }
    answers_data = []
    for question in questions:
        correct_alternative = Alternative.objects.get(
            question=question, is_correct=True
        )
        answers_data.append(
            {"question": question.id, "selected_alternative": correct_alternative.id}
        )
    data = {"answers": answers_data}
    serializer = ExamSubmissionSerializer(data=data, context=context)
    with pytest.raises(Http404) as exc_info:
        serializer.is_valid(raise_exception=True)
    assert "No Exam matches the given query." in str(exc_info.value)


def test_nonexistent_alternative(db, student, exam, questions, serializer_context):
    nonexistent_alternative_id = 9999
    answers_data = []
    for question in questions:
        answers_data.append(
            {
                "question": question.id,
                "selected_alternative": nonexistent_alternative_id,
            }
        )
    data = {"answers": answers_data}
    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    assert not serializer.is_valid()
    for error in serializer.errors["answers"]:
        assert "Invalid pk" in str(error["selected_alternative"])


def test_nonexistent_question(db, student, exam, alternatives, serializer_context):
    nonexistent_question_id = 9999
    correct_alternative = Alternative.objects.filter(is_correct=True).first()
    answers_data = [
        {
            "question": nonexistent_question_id,
            "selected_alternative": correct_alternative.id,
        }
    ]
    data = {"answers": answers_data}
    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    assert not serializer.is_valid()
    for error in serializer.errors["answers"]:
        assert "Invalid pk" in str(error["question"])


def test_missing_answers_field(db, student, exam, serializer_context):
    data = {}
    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    assert not serializer.is_valid()
    assert "This field is required." in str(serializer.errors["answers"])


def test_empty_answers_list(
    db, student, exam, questions, alternatives, serializer_context
):
    data = {"answers": []}
    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)
    assert (
        "The number of answers does not match the number of questions in the exam"
        in str(exc_info.value)
    )


def test_invalid_data_types(db, student, exam, serializer_context):
    data = {
        "answers": [{"question": "invalid_id", "selected_alternative": "invalid_id"}]
    }
    serializer = ExamSubmissionSerializer(data=data, context=serializer_context)
    assert not serializer.is_valid()
    errors = serializer.errors["answers"][0]
    assert "Incorrect type" in str(errors["question"])
    assert "Incorrect type" in str(errors["selected_alternative"])


def test_exam_result_serializer(db, student, exam, questions, alternatives):
    submission = ExamSubmission.objects.create(student=student, exam=exam)
    for question in questions:
        correct_alternative = Alternative.objects.get(
            question=question, is_correct=True
        )
        Answer.objects.create(
            submission=submission,
            question=question,
            selected_alternative=correct_alternative,
        )

    submission = ExamSubmission.objects.with_total_correct().get(pk=submission.pk)
    serializer = ExamResultSerializer(instance=submission)

    data = serializer.data
    assert data["student"] == str(student)
    assert data["exam"] == exam.name
    assert data["total_correct"] == len(questions)
    assert data["percentage_score"] == 100.0


def test_exam_result_serializer_with_incorrect_answers(
    db, student, exam, questions, alternatives
):
    submission = ExamSubmission.objects.create(student=student, exam=exam)
    for idx, question in enumerate(questions):
        alternatives_q = Alternative.objects.filter(question=question)
        selected_alternative = (
            alternatives_q.filter(is_correct=False).first()
            if idx == 0
            else alternatives_q.get(is_correct=True)
        )
        Answer.objects.create(
            submission=submission,
            question=question,
            selected_alternative=selected_alternative,
        )

    submission = ExamSubmission.objects.with_total_correct().get(pk=submission.pk)
    serializer = ExamResultSerializer(instance=submission)

    data = serializer.data
    assert data["total_correct"] == len(questions) - 1
    percentage = ((len(questions) - 1) / len(questions)) * 100
    assert data["percentage_score"] == percentage
