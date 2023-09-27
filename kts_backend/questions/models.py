from dataclasses import dataclass

from kts_backend.store.database.sqlalchemy_base import db
from sqlalchemy import Column, BigInteger, String

@dataclass
class Question:
    id: int
    title: str
    answer: str

class QuestionModel(db):
    __tablename__ = "questions"
    id = Column(BigInteger, primary_key=True)
    title = Column(String, unique=True)
    answer = Column(String)