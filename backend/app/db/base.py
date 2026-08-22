# SQLAlchemy declarative base and common model attributes will go here
from app.db.database import Base

from app.models.faculty import Faculty
from app.models.student import Student
from app.models.student_project import StudentProject
from app.models.student_skill import StudentSkill
from app.models.certification import Certification
from app.models.drive import Drive
from app.models.recommendation import Recommendation