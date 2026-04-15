from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, JSON, ForeignKey, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from enum import Enum


class ProjectStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"


class PatternStatus(str, Enum):
    DEVELOPING = "DEVELOPING"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"


class SampleSuccessFlag(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class InkCategory(str, Enum):
    COLOR = "COLOR"
    TRANSPARENT = "TRANSPARENT"
    EFFECT = "EFFECT"
    ADDITIVE = "ADDITIVE"


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String, primary_key=True)
    project_name = Column(String, nullable=False)
    customer = Column(String, nullable=True)
    status = Column(String, default=ProjectStatus.IN_PROGRESS.value)
    start_date = Column(Date, nullable=True)
    target_completion = Column(Date, nullable=True)
    memo = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    patterns = relationship("Pattern", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_project_name', 'project_name'),
        Index('idx_project_status', 'status'),
    )


class Pattern(Base):
    __tablename__ = "patterns"

    pattern_id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=False)
    pattern_name = Column(String, nullable=False)
    total_print_layers = Column(Integer, nullable=False)
    target_base_color_sci = Column(JSON, nullable=True)
    target_base_color_sce = Column(JSON, nullable=True)
    target_base_material = Column(String, nullable=True)
    status = Column(String, default=PatternStatus.DEVELOPING.value)
    notes = Column(Text, nullable=True)
    approved_sample_id = Column(String, ForeignKey("samples.sample_id"), nullable=True)
    success_rate = Column(Float, nullable=True)
    avg_delta_e = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="patterns")
    rounds = relationship("Round", back_populates="pattern", cascade="all, delete-orphan")
    samples = relationship("Sample", back_populates="pattern", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_pattern_name', 'pattern_name'),
        Index('idx_pattern_project', 'project_id'),
        Index('idx_pattern_status', 'status'),
    )


class Round(Base):
    __tablename__ = "rounds"

    round_id = Column(String, primary_key=True)
    pattern_id = Column(String, ForeignKey("patterns.pattern_id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    work_date = Column(Date, nullable=True)
    operator = Column(String, nullable=True)
    work_location = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    pattern = relationship("Pattern", back_populates="rounds")
    samples = relationship("Sample", back_populates="round", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_round_pattern', 'pattern_id'),
        Index('idx_round_number', 'round_number'),
    )


class Sample(Base):
    __tablename__ = "samples"

    sample_id = Column(String, primary_key=True)
    round_id = Column(String, ForeignKey("rounds.round_id"), nullable=False)
    pattern_id = Column(String, ForeignKey("patterns.pattern_id"), nullable=False)
    sample_number = Column(Integer, nullable=False)
    base_color_sci = Column(JSON, nullable=True)
    base_color_sce = Column(JSON, nullable=True)
    base_material = Column(String, nullable=True)
    layers = Column(JSON, nullable=True)
    final_delta_e = Column(Float, nullable=True)
    success_flag = Column(String, nullable=True)
    success_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    round = relationship("Round", back_populates="samples")
    pattern = relationship("Pattern", back_populates="samples")

    __table_args__ = (
        Index('idx_sample_pattern', 'pattern_id'),
        Index('idx_sample_round', 'round_id'),
        Index('idx_sample_number', 'sample_number'),
    )


class Ink(Base):
    __tablename__ = "inks"

    ink_id = Column(String, primary_key=True)
    ink_name = Column(String, nullable=False)
    ink_category = Column(String, default=InkCategory.COLOR.value)
    manufacturer = Column(String, nullable=True)
    is_blend_ink = Column(Boolean, default=False)
    blend_recipe = Column(JSON, nullable=True)
    solid_color_sci = Column(JSON, nullable=True)
    solid_color_sce = Column(JSON, nullable=True)
    delta_sci_sce = Column(Float, nullable=True)
    gloss_index = Column(Float, nullable=True)
    gloss_GU = Column(Float, nullable=True)
    viscosity = Column(Float, nullable=True)
    density = Column(Float, nullable=True)
    memo = Column(Text, nullable=True)
    registered_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_ink_name', 'ink_name'),
        Index('idx_ink_category', 'ink_category'),
        Index('idx_ink_blend', 'is_blend_ink'),
    )
