import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from student.models import Student
from exam.models import Exam, ExamQuestion
from question.models import Question, Alternative, AlternativesChoices
from submission.models import ExamSubmission, Answer


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student(db):
    return Student.objects.create_user(
        username="teststudent", email="student@example.com", password="testpass"
    )


@pytest.fixture
def exam(db):
    return Exam.objects.create(name="Test Exam")


@pytest.fixture
def questions(db):
    q1 = Question.objects.create(content="What is 2+2?")
    q2 = Question.objects.create(content="What is the capital of France?")
    return [q1, q2]


@pytest.fixture
def exam_questions(db, exam, questions):
    for idx, question in enumerate(questions, start=1):
        ExamQuestion.objects.create(exam=exam, question=question, number=idx)


@pytest.fixture
def alternatives(db, questions):
    alternatives = []
    for question in questions:
        alternatives.extend(
            [
                Alternative.objects.create(
                    question=question,
                    content="Option A",
                    option=AlternativesChoices.A,
                    is_correct=True if question.content == "What is 2+2?" else False,
                ),
                Alternative.objects.create(
                    question=question,
                    content="Option B",
                    option=AlternativesChoices.B,
                    is_correct=(
                        True
                        if question.content == "What is the capital of France?"
                        else False
                    ),
                ),
                Alternative.objects.create(
                    question=question,
                    content="Option C",
                    option=AlternativesChoices.C,
                    is_correct=False,
                ),
            ]
        )
    return alternatives


def test_create_submission_success(
    api_client, student, exam, exam_questions, alternatives
):
    url = reverse(
        "create-submission", kwargs={"student_id": student.id, "exam_id": exam.id}
    )
    answers = []
    for question in exam.questions.all():
        correct_alternative = Alternative.objects.get(
            question=question, is_correct=True
        )
        answers.append(
            {"question": question.id, "selected_alternative": correct_alternative.id}
        )
    data = {"answers": answers}
    response = api_client.post(url, data, format="json")
    assert response.status_code == 201

    submission = ExamSubmission.objects.get(student=student, exam=exam)
    assert submission.answers.count() == len(answers)


def test_create_submission_duplicate(
    api_client, student, exam, exam_questions, alternatives
):
    url = reverse(
        "create-submission", kwargs={"student_id": student.id, "exam_id": exam.id}
    )
    answers = []
    for question in exam.questions.all():
        correct_alternative = Alternative.objects.get(
            question=question, is_correct=True
        )
        answers.append(
            {"question": question.id, "selected_alternative": correct_alternative.id}
        )
    data = {"answers": answers}
    response = api_client.post(url, data, format="json")
    assert response.status_code == 201

    response = api_client.post(url, data, format="json")
    assert response.status_code == 400
    assert "This student has already submitted this exam." in str(response.data)


def test_create_submission_invalid_answers(
    api_client, student, exam, exam_questions, alternatives
):
    url = reverse(
        "create-submission", kwargs={"student_id": student.id, "exam_id": exam.id}
    )
    answers = []
    for idx, question in enumerate(exam.questions.all()):
        if idx == 0:
            correct_alternative = Alternative.objects.get(
                question=question, is_correct=True
            )
            answers.append(
                {
                    "question": question.id,
                    "selected_alternative": correct_alternative.id,
                }
            )
    data = {"answers": answers}
    response = api_client.post(url, data, format="json")
    assert response.status_code == 400
    assert (
        "The number of answers does not match the number of questions in the exam"
        in str(response.data)
    )


def test_get_submission_result_success(
    api_client, student, exam, exam_questions, alternatives
):
    submission = ExamSubmission.objects.create(student=student, exam=exam)
    for question in exam.questions.all():
        correct_alternative = Alternative.objects.get(
            question=question, is_correct=True
        )
        Answer.objects.create(
            submission=submission,
            question=question,
            selected_alternative=correct_alternative,
        )
    url = reverse("exam-result", kwargs={"student_id": student.id, "exam_id": exam.id})
    response = api_client.get(url, format="json")
    assert response.status_code == 200
    data = response.data
    assert data["student"] == str(student)
    assert data["exam"] == exam.name
    assert data["total_correct"] == exam.questions.count()
    assert data["percentage_score"] == 100.0


def test_get_submission_result_not_found(api_client, student, exam):
    url = reverse("exam-result", kwargs={"student_id": student.id, "exam_id": exam.id})
    response = api_client.get(url, format="json")
    assert response.status_code == 404


def test_create_submission_invalid_question(
    api_client, student, exam, questions, exam_questions, alternatives
):
    url = reverse(
        "create-submission", kwargs={"student_id": student.id, "exam_id": exam.id}
    )
    extra_question = Question.objects.create(content="Extra Question")
    extra_alternative = Alternative.objects.create(
        question=extra_question,
        content="Extra Option",
        option=AlternativesChoices.A,
        is_correct=True,
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
    response = api_client.post(url, data, format="json")
    assert response.status_code == 400
    assert (
        f"The question {extra_question.id} does not belong to exam {exam.id}."
        in str(response.data)
    )


def test_create_submission_duplicate_answers(
    api_client, student, exam, exam_questions, alternatives
):
    url = reverse(
        "create-submission", kwargs={"student_id": student.id, "exam_id": exam.id}
    )
    question = exam.questions.first()
    correct_alternative = Alternative.objects.get(question=question, is_correct=True)
    incorrect_alternative = Alternative.objects.filter(
        question=question, is_correct=False
    ).first()
    answers = [
        {"question": question.id, "selected_alternative": correct_alternative.id},
        {"question": question.id, "selected_alternative": incorrect_alternative.id},
    ]
    data = {"answers": answers}
    response = api_client.post(url, data, format="json")
    assert response.status_code == 400
    assert f"The answer for question {question.id} is duplicated." in str(response.data)


def test_create_submission_invalid_alternative(
    api_client, student, exam, exam_questions, alternatives
):
    url = reverse(
        "create-submission", kwargs={"student_id": student.id, "exam_id": exam.id}
    )
    question = exam.questions.first()
    wrong_alternative = Alternative.objects.filter(
        question=exam.questions.last()
    ).first()
    answers = []
    for q in exam.questions.all():
        if q == question:
            selected_alternative = wrong_alternative
        else:
            selected_alternative = Alternative.objects.get(question=q, is_correct=True)
        answers.append(
            {"question": q.id, "selected_alternative": selected_alternative.id}
        )
    data = {"answers": answers}
    response = api_client.post(url, data, format="json")
    assert response.status_code == 400
    assert (
        f"The alternative {wrong_alternative.id} does not belong to question {question.id}."
        in str(response.data)
    )


def test_create_submission_nonexistent_student(
    api_client, exam, exam_questions, alternatives
):
    nonexistent_student_id = 9999
    url = reverse(
        "create-submission",
        kwargs={"student_id": nonexistent_student_id, "exam_id": exam.id},
    )
    answers = []
    for question in exam.questions.all():
        correct_alternative = Alternative.objects.get(
            question=question, is_correct=True
        )
        answers.append(
            {"question": question.id, "selected_alternative": correct_alternative.id}
        )
    data = {"answers": answers}
    response = api_client.post(url, data, format="json")
    assert response.status_code == 404


def test_create_submission_nonexistent_exam(
    api_client, student, exam_questions, alternatives
):
    nonexistent_exam_id = 9999
    url = reverse(
        "create-submission",
        kwargs={"student_id": student.id, "exam_id": nonexistent_exam_id},
    )
    answers = []
    data = {"answers": answers}
    response = api_client.post(url, data, format="json")
    assert response.status_code == 404


def test_create_submission_missing_answers(api_client, student, exam):
    url = reverse(
        "create-submission", kwargs={"student_id": student.id, "exam_id": exam.id}
    )
    data = {}
    response = api_client.post(url, data, format="json")
    assert response.status_code == 400
    assert "This field is required." in str(response.data["answers"])


def test_get_submission_result_nonexistent_student(api_client, exam):
    nonexistent_student_id = 9999
    url = reverse(
        "exam-result", kwargs={"student_id": nonexistent_student_id, "exam_id": exam.id}
    )
    response = api_client.get(url, format="json")
    assert response.status_code == 404


def test_get_submission_result_nonexistent_exam(api_client, student):
    nonexistent_exam_id = 9999
    url = reverse(
        "exam-result", kwargs={"student_id": student.id, "exam_id": nonexistent_exam_id}
    )
    response = api_client.get(url, format="json")
    assert response.status_code == 404
