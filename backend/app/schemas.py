from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserLogin(BaseModel):
    login: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class GroupSimple(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class GroupBase(BaseModel):
    name: str

class Group(GroupBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    id: int
    email: str
    login: str
    fio: str
    role: str
    group_id: Optional[int] = None
    group: Optional[GroupSimple] = None

    class Config:
        from_attributes = True

class CourseBase(BaseModel):
    name: str

class CourseCreate(BaseModel):
    name: str
    teacher_id: int
    group_id: int

class Course(CourseBase):
    id: int
    teacher_id: int
    group_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TestBase(BaseModel):
    name: str

class TestCreate(BaseModel):
    name: str
    course_id: int

class Test(TestBase):
    id: int
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CompletedTestBase(BaseModel):
    score: int

class CompletedTestCreate(CompletedTestBase):
    test_id: int

class CompletedTest(CompletedTestBase):
    id: int
    student_id: int
    test_id: int
    completed_at: datetime

    class Config:
        from_attributes = True

class StudentProgress(BaseModel):
    student_id: int
    student_name: str
    tests_completed: int
    total_tests: int
    average_score: float
    test_details: List[dict]

class GroupProgress(BaseModel):
    group_id: int
    group_name: str
    average_progress: float
    students: List[StudentProgress]
        
class CourseWithDetails(BaseModel):
    id: int
    name: str
    teacher: UserProfile
    group: Group
    created_at: datetime

    total_tests: Optional[int] = 0
    completed_tests: Optional[int] = 0
    completion_rate: Optional[float] = 0.0

    student_count: Optional[int] = 0
    average_progress: Optional[float] = 0.0

    class Config:
        from_attributes = True

class TeacherStats(BaseModel):
    course_count: int
    group_count: int 
    student_count: int

class AdminStats(BaseModel):
    course_count: int
    user_count: int
    group_count: int

class TestWithCompletion(BaseModel):
    id: int
    name: str
    course_id: int
    created_at: datetime
    completed: bool
    score: Optional[int] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TestResult(BaseModel):
    test_id: int
    score: int

class StudentStats(BaseModel):
    completed_tests_count: int
    average_score: float
    total_tests_count: int
    completion_percentage: float

class StudentTestDetail(BaseModel):
    test_name: str
    course_name: str
    score: int
    max_score: int
    completed_at: datetime
    teacher_name: str

    class Config:
        from_attributes = True
        
class StudentProgress(BaseModel):
    student_id: int
    student_name: str
    student_login: str
    completed_tests: int
    total_tests: int
    completion_rate: float
    average_score: float
    last_activity: Optional[datetime] = None

class CourseStatistics(BaseModel):
    course_id: int
    course_name: str
    group_name: str
    total_students: int
    total_tests: int
    average_completion_rate: float
    average_score: float
    student_progress: List[StudentProgress]
        
class TestWithStatistics(BaseModel):
    id: int
    name: str
    course_id: int
    created_at: datetime
    total_students: int
    completed_count: int
    average_score: float
    completion_rate: float

    class Config:
        from_attributes = True
        
class TestWithCourse(BaseModel):
    id: int
    name: str
    course_id: int
    created_at: datetime
    course: Optional[Course] = None

    class Config:
        from_attributes = True
        
class TestWithCourseAndGroup(BaseModel):
    id: int
    name: str
    course_id: int
    created_at: datetime
    course: CourseWithDetails

    class Config:
        from_attributes = True