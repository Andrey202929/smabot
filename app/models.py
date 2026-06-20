from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, Index, func, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .db import Base

class Signal(Base):
    __tablename__ = "signals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    asset = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False, index=True)
    side = Column(String, nullable=False)
    entry = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    rr = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False, index=True)
    quality = Column(String, nullable=False)
    htf_context = Column(String, nullable=True)
    htf_zone = Column(String, nullable=True)
    ltf_trigger = Column(String, nullable=True)
    liquidity_taken = Column(String, nullable=True)
    reason = Column(JSON, nullable=True)
    raw = Column(JSON, nullable=True)
    fingerprint = Column(String, nullable=False, unique=True, index=True)
    notified = Column(Boolean, nullable=False, server_default=text("false"))

    __table_args__ = (
        Index("idx_signal_asset_timeframe_created", "asset", "timeframe", "created_at"),
    )

class Result(Base):
    __tablename__ = "results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    closed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    exit_price = Column(Float)
    pnl = Column(Float)
    rr_realized = Column(Float)
    win = Column(Boolean)
    raw = Column(JSON)

class Statistic(Base):
    __tablename__ = "statistics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period = Column(String, nullable=False)
    metrics = Column(JSON, nullable=False)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
