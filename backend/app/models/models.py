from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index
)
from sqlalchemy.orm import relationship
from app.database.connection import Base


def utc_now():
    return datetime.now(timezone.utc)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    run_id = Column(String(64), primary_key=True)
    source_file = Column(String(255), nullable=False)
    file_format = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="PENDING")
    start_time = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    total_input_records = Column(Integer, nullable=False, default=0)
    valid_records = Column(Integer, nullable=False, default=0)
    rejected_records = Column(Integer, nullable=False, default=0)
    duplicate_records = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    logs = relationship("ApplicationLog", back_populates="run", cascade="all, delete-orphan")
    rejected_logs = relationship("RejectedLog", back_populates="run", cascade="all, delete-orphan")
    metrics = relationship("LogMetric", back_populates="run", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "run_id": self.run_id,
            "source_file": self.source_file,
            "file_format": self.file_format,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "total_input_records": self.total_input_records,
            "valid_records": self.valid_records,
            "rejected_records": self.rejected_records,
            "duplicate_records": self.duplicate_records,
            "is_reconciled": (self.valid_records + self.rejected_records) == self.total_input_records,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ApplicationLog(Base):
    __tablename__ = "application_logs"

    event_id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("pipeline_runs.run_id", ondelete="SET NULL"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    severity = Column(String(16), nullable=False, index=True)
    service = Column(String(64), nullable=False, index=True)
    message = Column(Text, nullable=False)
    response_ms = Column(Float, nullable=True, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    endpoint = Column(String(255), nullable=True)
    http_status = Column(Integer, nullable=True)
    is_failure = Column(Boolean, nullable=False, default=False, index=True)
    source_file = Column(String(255), nullable=False)
    ingested_at = Column(DateTime(timezone=True), default=utc_now)

    run = relationship("PipelineRun", back_populates="logs")

    __table_args__ = (
        Index("idx_app_logs_composite", "service", "severity", "timestamp"),
    )

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "severity": self.severity,
            "service": self.service,
            "message": self.message,
            "response_ms": self.response_ms,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "http_status": self.http_status,
            "is_failure": self.is_failure,
            "source_file": self.source_file,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
        }


class RejectedLog(Base):
    __tablename__ = "rejected_logs"

    reject_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("pipeline_runs.run_id", ondelete="CASCADE"), nullable=True, index=True)
    source_file = Column(String(255), nullable=False)
    raw_record = Column(Text, nullable=False)
    reason = Column(String(255), nullable=False, index=True)
    rejected_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    run = relationship("PipelineRun", back_populates="rejected_logs")

    def to_dict(self):
        return {
            "reject_id": self.reject_id,
            "run_id": self.run_id,
            "source_file": self.source_file,
            "raw_record": self.raw_record,
            "reason": self.reason,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
        }


class LogMetric(Base):
    __tablename__ = "log_metrics"

    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("pipeline_runs.run_id", ondelete="CASCADE"), nullable=True, index=True)
    service = Column(String(64), nullable=False, index=True)
    total_logs = Column(Integer, nullable=False, default=0)
    info_count = Column(Integer, nullable=False, default=0)
    warning_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    critical_count = Column(Integer, nullable=False, default=0)
    failed_requests = Column(Integer, nullable=False, default=0)
    error_rate_pct = Column(Float, nullable=False, default=0.0)
    avg_latency_ms = Column(Float, nullable=True)
    p50_latency_ms = Column(Float, nullable=True)
    p95_latency_ms = Column(Float, nullable=True)
    p99_latency_ms = Column(Float, nullable=True)
    max_latency_ms = Column(Float, nullable=True)
    calculated_at = Column(DateTime(timezone=True), default=utc_now)

    run = relationship("PipelineRun", back_populates="metrics")

    def to_dict(self):
        return {
            "metric_id": self.metric_id,
            "run_id": self.run_id,
            "service": self.service,
            "total_logs": self.total_logs,
            "info_count": self.info_count,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "critical_count": self.critical_count,
            "failed_requests": self.failed_requests,
            "error_rate_pct": round(self.error_rate_pct, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2) if self.avg_latency_ms is not None else None,
            "p50_latency_ms": round(self.p50_latency_ms, 2) if self.p50_latency_ms is not None else None,
            "p95_latency_ms": round(self.p95_latency_ms, 2) if self.p95_latency_ms is not None else None,
            "p99_latency_ms": round(self.p99_latency_ms, 2) if self.p99_latency_ms is not None else None,
            "max_latency_ms": round(self.max_latency_ms, 2) if self.max_latency_ms is not None else None,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
        }
