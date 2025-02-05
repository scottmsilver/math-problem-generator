from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()

class DifficultyLevel(enum.Enum):
    SAME = 'same'
    CHALLENGE = 'challenge'
    HARDER = 'harder'

class Provider(enum.Enum):
    CLAUDE = 'claude'
    GEMINI = 'gemini'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    problem_sets = db.relationship('ProblemSet', backref='user', lazy=True)

class ProblemSet(db.Model):
    __tablename__ = 'problem_sets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    original_pdf_path = db.Column(db.String(512))
    latex_template = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    generated_sets = db.relationship('GeneratedSet', backref='problem_set', lazy=True)

class GeneratedSet(db.Model):
    __tablename__ = 'generated_sets'
    id = db.Column(db.Integer, primary_key=True)
    problem_set_id = db.Column(db.Integer, db.ForeignKey('problem_sets.id'), nullable=False)
    provider = db.Column(db.Enum(Provider), nullable=False)
    difficulty = db.Column(db.Enum(DifficultyLevel), nullable=False)
    num_problems = db.Column(db.Integer, nullable=False, default=5)
    problems_pdf_path = db.Column(db.String(512), nullable=False)
    solutions_pdf_path = db.Column(db.String(512), nullable=False)
    problems_latex = db.Column(db.Text, nullable=False)
    solutions_latex = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
