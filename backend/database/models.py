"""
SQLAlchemy models for the Process-to-Role Intelligence AI application.

Schema mirrors the design agreed for Assignment 4:
industries -> processes -> activities <-> roles (many-to-many via role_activities)
activities -> ai_impact (one-to-one, AI-generated but persisted)
roles/activities -> future_responsibilities (AI-generated, persisted)
analysis_history stores every query's full reasoning trace + LLM output for traceability.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Industry(Base):
    __tablename__ = "industries"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    source_notes = Column(Text)  # where the industry research came from

    processes = relationship("Process", back_populates="industry", cascade="all, delete-orphan")


class Process(Base):
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True)
    industry_id = Column(Integer, ForeignKey("industries.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)

    industry = relationship("Industry", back_populates="processes")
    activities = relationship("Activity", back_populates="process", cascade="all, delete-orphan")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    frequency = Column(String)        # daily / weekly / monthly / ad-hoc
    data_intensity = Column(String)   # low / medium / high

    process = relationship("Process", back_populates="activities")
    role_links = relationship("RoleActivity", back_populates="activity", cascade="all, delete-orphan")
    ai_impact = relationship("AIImpact", back_populates="activity", uselist=False, cascade="all, delete-orphan")
    future_responsibilities = relationship(
        "FutureResponsibility", back_populates="activity", cascade="all, delete-orphan"
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    department = Column(String)
    seniority_level = Column(String)  # e.g. Associate / Analyst / Manager

    activity_links = relationship("RoleActivity", back_populates="role", cascade="all, delete-orphan")
    future_responsibilities = relationship(
        "FutureResponsibility", back_populates="role", cascade="all, delete-orphan"
    )


class RoleActivity(Base):
    """Many-to-many join: who performs which activities, and how."""

    __tablename__ = "role_activities"
    __table_args__ = (UniqueConstraint("role_id", "activity_id", name="uq_role_activity"),)

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    involvement_level = Column(String)  # primary / secondary / reviewer

    role = relationship("Role", back_populates="activity_links")
    activity = relationship("Activity", back_populates="role_links")


class AIImpact(Base):
    """
    AI-generated (but persisted) judgment of how AI affects a given activity.
    This is seeded from research for the MVP; in the live app, new activities
    would get this populated by the reasoning engine + LLM synthesis step.
    """

    __tablename__ = "ai_impact"

    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False, unique=True)
    automation_potential = Column(Float)  # 0.0 - 1.0
    impact_type = Column(String)          # automate / augment / eliminate / create-new
    rationale = Column(Text)
    evidence_source = Column(Text)        # citation: report/org + URL
    confidence_score = Column(Float)      # 0.0 - 1.0, how confident the judgment is
    generated_at = Column(DateTime, default=datetime.utcnow)

    activity = relationship("Activity", back_populates="ai_impact")


class FutureResponsibility(Base):
    """What a role's responsibility looks like after the activity's AI impact plays out."""

    __tablename__ = "future_responsibilities"

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    description = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role", back_populates="future_responsibilities")
    activity = relationship("Activity", back_populates="future_responsibilities")


class AnalysisHistory(Base):
    """
    Persisted record of every query run through the reasoning engine + LLM.
    This is what proves outputs are traceable and that a restart doesn't
    wipe accumulated intelligence.
    """

    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True)
    query_type = Column(String)           # e.g. "role_impact", "chat:multi_process_roles"
    target_id = Column(Integer, nullable=True)  # e.g. role_id being queried; null for list-style queries
    user_query = Column(Text, nullable=True)    # original free-text question, for chat-originated analyses
    reasoning_trace_json = Column(Text)   # the structured evidence bundle handed to the LLM
    llm_output = Column(Text)             # the synthesized narrative
    created_at = Column(DateTime, default=datetime.utcnow)


def get_engine(db_path: str = "sqlite:///./enterprise_ai.db"):
    return create_engine(db_path, echo=False)


def init_db(engine) -> None:
    Base.metadata.create_all(engine)


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()