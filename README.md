# Medway API Project

A Django RESTful API for managing exams, students, submissions, and results.

![medway-db](https://github.com/user-attachments/assets/32884074-dc46-425e-aa5d-d284d78f4a9f)

## Features

- **Student Management**: Create and manage student profiles.
- **Exam Management**: Create exams with associated questions and alternatives.
- **Exam Submission**: Students can submit answers to exams.
- **Result Retrieval**: Retrieve exam results, including scores and correct answers.

## Installation

1. **Clone the repository**:

```bash
git clone https://github.com/yourusername/medway-api.git
cd medway-api
```

2. **Build and start Docker containers**:

```bash
docker-compose up --build
```

## Usage

The API is accessible at http://localhost:8000/.
You can access the admin panel http://0.0.0.0:8000/admin/ using the credentials after creating an user/student (inside the container):

```bash
docker exec -it medway-api bash
python manage.py migrate
python manage.py createsuperuser
```

### Submit Exam Answers

**Endpoint**: POST `/students/<student_id>/exams/<exam_id>/submissions/`

**Description**: Submit answers to an exam.

**Request Body Example**:
```bash
{
  "answers": [
    {
      "question": 1,
      "selected_alternative": 4
    },
    {
      "question": 2,
      "selected_alternative": 7
    }
  ]
}
```

### Retrieve Exam Result

**Endpoint**: GET `/students/<student_id>/exams/<exam_id>/submissions/result/`

**Description**: Retrieve the result of an exam submission.

## Development

1. **Access running container**:

```bash
docker exec -it medway-api bash
```

2. **Run tests**:

```bash
pytest
```

3. **Run lint/formatter**:

```bash
ruff check . --fix
ruff check .
black .
```

4. **Access database**:

```bash
docker exec -it medway-api_db_1 bash
psql -U teste -d teste
```

## Future Implementation Ideas

- `conftest.py` file for tests
- Pre-commit hook
- Admin interface for saving and visualizing submissions
- [uv]([url](https://github.com/astral-sh/uv)) package manager
- Authentication
- Logging
