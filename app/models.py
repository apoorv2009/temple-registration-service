from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TempleSubscription(Base):
    __tablename__ = "temple_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    temple_id: Mapped[str] = mapped_column(String(20), index=True)
    temple_name: Mapped[str] = mapped_column(String(120))
    requester_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ShantidharaBooking(Base):
    __tablename__ = "shantidhara_bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    temple_id: Mapped[str] = mapped_column(String(20), index=True)
    temple_name: Mapped[str] = mapped_column(String(120))
    slot_id: Mapped[str] = mapped_column(String(32), index=True)
    slot_label: Mapped[str] = mapped_column(String(40))
    slot_date: Mapped[date] = mapped_column(Date, index=True)
    amount_label: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class DonationOrder(Base):
    __tablename__ = "donation_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    donation_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    temple_id: Mapped[str] = mapped_column(String(20), index=True)
    temple_name: Mapped[str] = mapped_column(String(120))
    donation_type: Mapped[str] = mapped_column(String(20), index=True)
    amount_label: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(30), index=True)
    entity_id: Mapped[str] = mapped_column(String(32), index=True)
    amount_label: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
