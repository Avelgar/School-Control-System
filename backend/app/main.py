from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from typing import List, Optional
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from typing import List
import datetime

from .database import get_db, engine, Base
from . import models
from .models import User, Group, Course, Test, CompletedTest
from . import schemas
from .schemas import (
    UserLogin, Token, UserProfile, Group, Course, Test,
    CompletedTest, StudentProgress, GroupProgress,
    CompletedTestCreate, CourseWithDetails, TeacherStats, AdminStats, 
    TestWithCompletion, TestResult, StudentStats, StudentTestDetail, CourseStatistics, StudentProgress,
    TestWithStatistics, CourseCreate, TestCreate, GroupBase, TestWithCourse, TestWithCourseAndGroup
)
from .auth import verify_password, create_access_token, verify_token, get_password_hash

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Distance Learning System API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_user_by_login(db: Session, login: str):
    return db.query(User).filter(User.login == login).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация"
        )
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен"
        )
    
    login = payload.get("login")
    if not login:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )
    
    user = get_user_by_login(db, login)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    return user

@app.get("/", response_class=FileResponse)
async def read_root():
    return FileResponse("../frontend/index.html")

@app.get("/css/{file_path:path}", response_class=FileResponse)
async def serve_css(file_path: str):
    return FileResponse(f"../frontend/css/{file_path}")

@app.get("/js/{file_path:path}", response_class=FileResponse)
async def serve_js(file_path: str):
    return FileResponse(f"../frontend/js/{file_path}")

@app.get("/main-page")
def main_page_html():
    return FileResponse("../frontend/main.html")

@app.post("/auth/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    if not (user.login and user.password):
        raise HTTPException(status_code=400, detail="Недостаточно данных")
    
    if "@" in user.login:
        db_user = get_user_by_email(db, user.login)
    else:
        db_user = get_user_by_login(db, user.login)
    
    if not db_user:
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    access_token = create_access_token(
        data={"login": db_user.login}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserProfile)
def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация"
        )
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен"
        )
    
    login = payload.get("login")
    if not login:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )
    
    user = get_user_by_login(db, login)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    return user

@app.get("/api/courses/my", response_model=List[CourseWithDetails])
def get_my_courses(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Получить курсы текущего пользователя с деталями"""
    if current_user.role == "student":
        courses = db.query(models.Course)\
            .filter(models.Course.group_id == current_user.group_id)\
            .options(
                joinedload(models.Course.teacher),
                joinedload(models.Course.group)
            )\
            .all()

        courses_with_progress = []
        for course in courses:
            total_tests = db.query(models.Test)\
                .filter(models.Test.course_id == course.id)\
                .count()

            completed_tests = db.query(models.CompletedTest)\
                .join(models.Test, models.CompletedTest.test_id == models.Test.id)\
                .filter(
                    models.CompletedTest.student_id == current_user.id,
                    models.Test.course_id == course.id
                )\
                .count()

            completion_rate = round((completed_tests / total_tests * 100), 1) if total_tests > 0 else 0.0
            
            course_dict = {
                "id": course.id,
                "name": course.name,
                "teacher": course.teacher,
                "group": course.group,
                "created_at": course.created_at,
                "total_tests": total_tests,
                "completed_tests": completed_tests,
                "completion_rate": completion_rate
            }
            courses_with_progress.append(course_dict)
        
        return courses_with_progress
    
    elif current_user.role == "teacher":
        courses = db.query(models.Course)\
            .filter(models.Course.teacher_id == current_user.id)\
            .options(
                joinedload(models.Course.teacher),
                joinedload(models.Course.group)
            )\
            .all()

        courses_with_stats = []
        for course in courses:
            total_tests = db.query(models.Test)\
                .filter(models.Test.course_id == course.id)\
                .count()

            student_count = db.query(models.User)\
                .filter(
                    models.User.group_id == course.group_id,
                    models.User.role == "student"
                )\
                .count()

            completed_tests_count = db.query(models.CompletedTest)\
                .join(models.Test, models.CompletedTest.test_id == models.Test.id)\
                .filter(models.Test.course_id == course.id)\
                .count()
            
            total_possible_tests = student_count * total_tests
            average_progress = round((completed_tests_count / total_possible_tests * 100), 1) if total_possible_tests > 0 else 0.0

            course_dict = {
                "id": course.id,
                "name": course.name,
                "teacher": course.teacher,
                "group": course.group,
                "created_at": course.created_at,
                "total_tests": total_tests,
                "student_count": student_count,
                "average_progress": average_progress
            }
            courses_with_stats.append(course_dict)
        
        return courses_with_stats
    
    else:  # admin
        courses = db.query(models.Course)\
            .options(
                joinedload(models.Course.teacher),
                joinedload(models.Course.group)
            )\
            .all()

        return courses

@app.get("/api/courses/{course_id}/tests")
def get_course_tests(course_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получить тесты курса"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    if current_user.role == "student" and course.group_id != current_user.group_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому курсу")
    
    tests = db.query(Test).filter(Test.course_id == course_id).all()
    return tests

@app.get("/api/courses/{course_id}/tests-with-completion", response_model=List[TestWithCompletion])
def get_course_tests_with_completion(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить тесты курса с информацией о прохождении для текущего пользователя"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Доступно только студентам")

    course = db.query(models.Course)\
        .filter(models.Course.id == course_id)\
        .first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    if course.group_id != current_user.group_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому курсу")

    tests = db.query(models.Test)\
        .filter(models.Test.course_id == course_id)\
        .all()

    tests_with_completion = []
    for test in tests:
        completed_test = db.query(models.CompletedTest)\
            .filter(
                models.CompletedTest.test_id == test.id,
                models.CompletedTest.student_id == current_user.id
            )\
            .first()
        
        tests_with_completion.append(TestWithCompletion(
            id=test.id,
            name=test.name,
            course_id=test.course_id,
            created_at=test.created_at,
            completed=completed_test is not None,
            score=completed_test.score if completed_test else None,
            completed_at=completed_test.completed_at if completed_test else None
        ))

    return tests_with_completion

@app.post("/api/completed-tests")
def submit_test_result(
    completed_test: CompletedTestCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Отправить результат теста (для студентов)"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Только студенты могут отправлять результаты тестов")

    test = db.query(models.Test).filter(models.Test.id == completed_test.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    course = db.query(models.Course).filter(models.Course.id == test.course_id).first()
    if course.group_id != current_user.group_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому тесту")

    existing = db.query(models.CompletedTest).filter(
        models.CompletedTest.student_id == current_user.id,
        models.CompletedTest.test_id == completed_test.test_id
    ).first()
    
    if existing:
        existing.score = completed_test.score
        existing.completed_at = datetime.utcnow()
    else:
        new_completed_test = models.CompletedTest(
            student_id=current_user.id,
            test_id=completed_test.test_id,
            score=completed_test.score
        )
        db.add(new_completed_test)
    
    db.commit()
    return {"message": "Результат теста сохранен"}

@app.get("/api/progress/courses/{course_id}")
def get_course_progress(course_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получить прогресс по курсу"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
@app.get("/api/teacher/stats", response_model=TeacherStats)
def get_teacher_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику для преподавателя"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Доступно только преподавателям")

    course_count = db.query(models.Course)\
        .filter(models.Course.teacher_id == current_user.id)\
        .count()

    group_count = db.query(models.Course.group_id)\
        .filter(models.Course.teacher_id == current_user.id)\
        .distinct()\
        .count()

    student_count = db.query(models.User)\
        .join(models.Course, models.User.group_id == models.Course.group_id)\
        .filter(
            models.Course.teacher_id == current_user.id,
            models.User.role == "student"
        )\
        .distinct()\
        .count()

    return {
        "course_count": course_count,
        "group_count": group_count,
        "student_count": student_count
    }

@app.get("/api/admin/stats", response_model=AdminStats)
def get_admin_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику для администратора"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")

    course_count = db.query(models.Course).count()

    user_count = db.query(models.User).count()

    group_count = db.query(models.Group).count()

    return {
        "course_count": course_count,
        "user_count": user_count,
        "group_count": group_count
    }


@app.get("/api/student/stats", response_model=StudentStats)
def get_student_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику студента"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Доступно только студентам")

    completed_tests = db.query(models.CompletedTest)\
        .filter(models.CompletedTest.student_id == current_user.id)\
        .all()

    total_tests = db.query(models.Test)\
        .join(models.Course, models.Test.course_id == models.Course.id)\
        .filter(models.Course.group_id == current_user.group_id)\
        .count()

    completed_tests_count = len(completed_tests)

    if completed_tests_count > 0:
        total_score = sum(test.score for test in completed_tests)
        average_score = round(total_score / completed_tests_count, 1)
    else:
        average_score = 0.0

    completion_percentage = round((completed_tests_count / total_tests * 100), 1) if total_tests > 0 else 0.0

    return {
        "completed_tests_count": completed_tests_count,
        "average_score": average_score,
        "total_tests_count": total_tests,
        "completion_percentage": completion_percentage
    }

@app.get("/api/student/completed-tests", response_model=List[StudentTestDetail])
def get_student_completed_tests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить детальную информацию о пройденных тестах студента"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Доступно только студентам")

    completed_tests = db.query(
        models.CompletedTest,
        models.Test,
        models.Course,
        models.User
    )\
        .join(models.Test, models.CompletedTest.test_id == models.Test.id)\
        .join(models.Course, models.Test.course_id == models.Course.id)\
        .join(models.User, models.Course.teacher_id == models.User.id)\
        .filter(models.CompletedTest.student_id == current_user.id)\
        .order_by(models.CompletedTest.completed_at.desc())\
        .all()

    result = []
    for completed_test, test, course, teacher in completed_tests:
        result.append(StudentTestDetail(
            test_name=test.name,
            course_name=course.name,
            score=completed_test.score,
            max_score=10,
            completed_at=completed_test.completed_at,
            teacher_name=teacher.fio
        ))

    return result


@app.get("/api/teacher/courses/{course_id}/statistics", response_model=CourseStatistics)
def get_course_statistics(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить детальную статистику по курсу для преподавателя"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Доступно только преподавателям")

    course = db.query(models.Course)\
        .filter(
            models.Course.id == course_id,
            models.Course.teacher_id == current_user.id
        )\
        .first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден или нет доступа")

    students = db.query(models.User)\
        .filter(
            models.User.group_id == course.group_id,
            models.User.role == "student"
        )\
        .all()

    tests = db.query(models.Test)\
        .filter(models.Test.course_id == course_id)\
        .all()
    
    total_tests = len(tests)
    student_progress_list = []
    total_completion_rate = 0
    total_score = 0
    active_students = 0

    for student in students:
        completed_tests = db.query(models.CompletedTest)\
            .join(models.Test, models.CompletedTest.test_id == models.Test.id)\
            .filter(
                models.CompletedTest.student_id == student.id,
                models.Test.course_id == course_id
            )\
            .all()
        
        completed_count = len(completed_tests)
        completion_rate = round((completed_count / total_tests * 100), 1) if total_tests > 0 else 0.0

        if completed_count > 0:
            student_avg_score = sum(test.score for test in completed_tests) / completed_count
            total_score += student_avg_score
            active_students += 1
        else:
            student_avg_score = 0

        last_activity = None
        if completed_tests:
            last_activity = max(test.completed_at for test in completed_tests)

        student_progress = StudentProgress(
            student_id=student.id,
            student_name=student.fio,
            student_login=student.login,
            completed_tests=completed_count,
            total_tests=total_tests,
            completion_rate=completion_rate,
            average_score=round(student_avg_score, 1),
            last_activity=last_activity
        )
        
        student_progress_list.append(student_progress)
        total_completion_rate += completion_rate

    total_students = len(students)
    avg_completion_rate = round(total_completion_rate / total_students, 1) if total_students > 0 else 0.0
    avg_score = round(total_score / active_students, 1) if active_students > 0 else 0.0

    return CourseStatistics(
        course_id=course.id,
        course_name=course.name,
        group_name=course.group.name,
        total_students=total_students,
        total_tests=total_tests,
        average_completion_rate=avg_completion_rate,
        average_score=avg_score,
        student_progress=student_progress_list
    )

@app.get("/api/teacher/courses/{course_id}/tests", response_model=List[TestWithStatistics])
def get_course_tests_with_statistics(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить тесты курса со статистикой для преподавателя"""
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Доступно только преподавателям")

    course = db.query(models.Course)\
        .filter(
            models.Course.id == course_id,
            models.Course.teacher_id == current_user.id
        )\
        .first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден или нет доступа")

    tests = db.query(models.Test)\
        .filter(models.Test.course_id == course_id)\
        .all()

    students = db.query(models.User)\
        .filter(
            models.User.group_id == course.group_id,
            models.User.role == "student"
        )\
        .all()
    
    total_students = len(students)
    tests_with_stats = []

    for test in tests:
        completed_tests = db.query(models.CompletedTest)\
            .filter(models.CompletedTest.test_id == test.id)\
            .all()
        
        completed_count = len(completed_tests)

        if completed_count > 0:
            total_score = sum(ct.score for ct in completed_tests)
            average_score = round(total_score / completed_count, 1)
        else:
            average_score = 0.0

        completion_rate = round((completed_count / total_students * 100), 1) if total_students > 0 else 0.0

        tests_with_stats.append(TestWithStatistics(
            id=test.id,
            name=test.name,
            course_id=test.course_id,
            created_at=test.created_at,
            total_students=total_students,
            completed_count=completed_count,
            average_score=average_score,
            completion_rate=completion_rate
        ))

    return tests_with_stats

@app.get("/api/admin/users", response_model=List[UserProfile])
def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить всех пользователей (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")

    users = db.query(User).options(joinedload(User.group)).all()
    return users

@app.get("/api/groups", response_model=List[Group])
def get_all_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить все группы"""
    groups = db.query(models.Group).all()
    return groups

@app.post("/api/admin/users", response_model=UserProfile)
def create_user(
    user_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать пользователя (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")

    existing_user = db.query(User).filter(
        (User.login == user_data["login"]) | (User.email == user_data["email"])
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином или email уже существует")

    hashed_password = get_password_hash(user_data["password"])
    
    new_user = User(
        login=user_data["login"],
        email=user_data["email"],
        fio=user_data["fio"],
        password_hash=hashed_password,
        role=user_data["role"],
        group_id=user_data.get("group_id")
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.put("/api/admin/users/{user_id}", response_model=UserProfile)
def update_user(
    user_id: int,
    user_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить пользователя (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    existing_user = db.query(User).filter(
        (User.login == user_data["login"]) | (User.email == user_data["email"]),
        User.id != user_id
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином или email уже существует")

    user.login = user_data["login"]
    user.email = user_data["email"]
    user.fio = user_data["fio"]
    user.role = user_data["role"]
    user.group_id = user_data.get("group_id")

    if user_data.get("password"):
        user.password_hash = get_password_hash(user_data["password"])
    
    db.commit()
    db.refresh(user)
    
    return user

@app.delete("/api/admin/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить пользователя (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    try:
        db.delete(user)
        db.commit()
        
        return {"message": "Пользователь удален"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении пользователя: {str(e)}")
        
@app.get("/api/admin/groups", response_model=List[Group])
def get_all_groups_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить все группы (для администратора)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")
    
    groups = db.query(models.Group).all()
    return groups

@app.post("/api/admin/groups", response_model=Group)
def create_group(
    group_data: GroupBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать группу (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")
    
    existing_group = db.query(models.Group).filter(models.Group.name == group_data.name).first()
    if existing_group:
        raise HTTPException(status_code=400, detail="Группа с таким названием уже существует")
    
    new_group = models.Group(name=group_data.name)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    return new_group

@app.put("/api/admin/groups/{group_id}", response_model=Group)
def update_group(
    group_id: int,
    group_data: GroupBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить группу (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")
    
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    existing_group = db.query(models.Group).filter(
        models.Group.name == group_data.name,
        models.Group.id != group_id
    ).first()
    
    if existing_group:
        raise HTTPException(status_code=400, detail="Группа с таким названием уже существует")
    
    group.name = group_data.name
    db.commit()
    db.refresh(group)
    
    return group

@app.delete("/api/admin/groups/{group_id}")
def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить группу (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")
    
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    try:
        db.query(models.User).filter(models.User.group_id == group_id).update({"group_id": None})

        db.delete(group)
        db.commit()
        
        return {"message": "Группа удалена"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении группы: {str(e)}")

@app.get("/api/admin/tests", response_model=List[TestWithCourseAndGroup])
def get_all_tests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить все тесты с информацией о курсах и группах (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")

    tests = db.query(models.Test)\
        .options(
            joinedload(models.Test.course).joinedload(models.Course.group),
            joinedload(models.Test.course).joinedload(models.Course.teacher)
        )\
        .all()

    return tests

@app.post("/api/admin/tests")
def create_test(
    test_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать тест (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")

    new_test = models.Test(
        name=test_data["name"],
        course_id=test_data["course_id"]
    )
    
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    
    return new_test

@app.put("/api/admin/tests/{test_id}")
def update_test(
    test_id: int,
    test_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить тест (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")

    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    test.name = test_data["name"]
    test.course_id = test_data["course_id"]
    
    db.commit()
    db.refresh(test)
    
    return test

@app.delete("/api/admin/tests/{test_id}")
def delete_test(
    test_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить тест (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")

    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    completed_tests_count = db.query(models.CompletedTest)\
        .filter(models.CompletedTest.test_id == test_id)\
        .count()
    
    if completed_tests_count > 0:
        raise HTTPException(
            status_code=400, 
            detail="Нельзя удалить тест, так как есть связанные результаты студентов"
        )
    
    db.delete(test)
    db.commit()
    
    return {"message": "Тест удален"}

@app.get("/api/admin/courses", response_model=List[CourseWithDetails])
def get_all_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить все курсы (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")

    courses = db.query(models.Course)\
        .options(
            joinedload(models.Course.teacher),
            joinedload(models.Course.group)
        )\
        .all()

    return courses

@app.post("/api/admin/courses", response_model=Course)
def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать курс (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")

    teacher = db.query(models.User).filter(
        models.User.id == course_data.teacher_id,
        models.User.role == "teacher"
    ).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    
    group = db.query(models.Group).filter(models.Group.id == course_data.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    new_course = models.Course(
        name=course_data.name,
        teacher_id=course_data.teacher_id,
        group_id=course_data.group_id
    )
    
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    return new_course

@app.put("/api/admin/courses/{course_id}", response_model=Course)
def update_course(
    course_id: int,
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить курс (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")
    
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")

    teacher = db.query(models.User).filter(
        models.User.id == course_data.teacher_id,
        models.User.role == "teacher"
    ).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    
    group = db.query(models.Group).filter(models.Group.id == course_data.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    course.name = course_data.name
    course.teacher_id = course_data.teacher_id
    course.group_id = course_data.group_id
    
    db.commit()
    db.refresh(course)
    
    return course

@app.delete("/api/admin/courses/{course_id}")
def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить курс (только для администраторов)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступно только администраторам")
    
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    try:
        db.delete(course)
        db.commit()
        
        return {"message": "Курс удален"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении курса: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=25526)