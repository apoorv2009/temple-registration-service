from datetime import UTC, date, datetime

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import DonationOrder, PaymentTransaction, ShantidharaBooking, TempleSubscription
from app.schemas.signup_request import (
    DonationItem,
    DonationResponse,
    ShantidharaBookingItem,
    ShantidharaBookingResponse,
    TempleSubscriptionItem,
    TempleSubscriptionResponse,
)


class TempleSubscriptionStore:
    def create(
        self,
        *,
        user_id: str,
        temple_id: str,
        temple_name: str,
        requester_name: str,
    ) -> TempleSubscriptionResponse:
        with SessionLocal() as session:
            existing_items = session.scalars(
                select(TempleSubscription).where(
                    TempleSubscription.user_id == user_id,
                    TempleSubscription.temple_id == temple_id,
                ),
            ).all()

            for subscription in existing_items:
                if subscription.status == "pending":
                    raise ValueError("Temple subscription request is already pending")
                if subscription.status == "approved":
                    raise ValueError("User is already subscribed to this temple")

            subscription = TempleSubscription(
                subscription_id="pending",
                user_id=user_id,
                temple_id=temple_id,
                temple_name=temple_name,
                requester_name=requester_name.strip(),
                status="pending",
                rejection_reason=None,
            )
            session.add(subscription)
            session.flush()
            subscription.subscription_id = self._format_subscription_id(subscription.id)
            session.commit()
            session.refresh(subscription)

            return TempleSubscriptionResponse(
                subscription_id=subscription.subscription_id,
                user_id=subscription.user_id,
                temple_id=subscription.temple_id,
                temple_name=subscription.temple_name,
                requester_name=subscription.requester_name,
                status="pending",
            )

    def list_for_user(self, user_id: str) -> list[TempleSubscriptionItem]:
        with SessionLocal() as session:
            items = session.scalars(
                select(TempleSubscription)
                .where(TempleSubscription.user_id == user_id)
                .order_by(TempleSubscription.requested_at.desc()),
            ).all()
            return [self._to_item(item) for item in items]

    def list_for_temple(
        self,
        temple_id: str,
        *,
        status_filter: str | None = None,
    ) -> list[TempleSubscriptionItem]:
        with SessionLocal() as session:
            query = (
                select(TempleSubscription)
                .where(TempleSubscription.temple_id == temple_id)
                .order_by(TempleSubscription.requested_at.desc())
            )
            if status_filter is not None:
                query = query.where(TempleSubscription.status == status_filter)
            items = session.scalars(query).all()
            return [self._to_item(item) for item in items]

    def approve(self, subscription_id: str) -> TempleSubscriptionItem | None:
        with SessionLocal() as session:
            subscription = session.scalar(
                select(TempleSubscription).where(
                    TempleSubscription.subscription_id == subscription_id,
                ),
            )
            if subscription is None:
                return None
            if subscription.status != "pending":
                raise ValueError("Only pending subscription requests can be approved")

            subscription.status = "approved"
            subscription.reviewed_at = datetime.now(UTC)
            subscription.rejection_reason = None
            session.commit()
            session.refresh(subscription)
            return self._to_item(subscription)

    def reject(self, subscription_id: str, reason: str) -> TempleSubscriptionItem | None:
        with SessionLocal() as session:
            subscription = session.scalar(
                select(TempleSubscription).where(
                    TempleSubscription.subscription_id == subscription_id,
                ),
            )
            if subscription is None:
                return None
            if subscription.status != "pending":
                raise ValueError("Only pending subscription requests can be rejected")

            subscription.status = "rejected"
            subscription.reviewed_at = datetime.now(UTC)
            subscription.rejection_reason = reason.strip()
            session.commit()
            session.refresh(subscription)
            return self._to_item(subscription)

    def create_shantidhara_booking(
        self,
        *,
        user_id: str,
        temple_id: str,
        temple_name: str,
        slot_id: str,
        slot_label: str,
        slot_date: date,
        amount_label: str,
    ) -> ShantidharaBookingResponse:
        with SessionLocal() as session:
            existing = session.scalar(
                select(ShantidharaBooking).where(
                    ShantidharaBooking.user_id == user_id,
                    ShantidharaBooking.slot_id == slot_id,
                    ShantidharaBooking.status.in_(["payment_pending", "confirmed"]),
                ),
            )
            if existing is not None:
                raise ValueError("A Shantidhara booking already exists for this slot")

            booking = ShantidharaBooking(
                booking_id="pending",
                user_id=user_id,
                temple_id=temple_id,
                temple_name=temple_name,
                slot_id=slot_id,
                slot_label=slot_label,
                slot_date=slot_date,
                amount_label=amount_label,
                status="payment_pending",
            )
            session.add(booking)
            session.flush()
            booking.booking_id = self._format_booking_id(booking.id)

            payment = PaymentTransaction(
                payment_id="pending",
                entity_type="shantidhara_booking",
                entity_id=booking.booking_id,
                amount_label=amount_label,
                status="payment_pending",
            )
            session.add(payment)
            session.flush()
            payment.payment_id = self._format_payment_id(payment.id)

            session.commit()
            session.refresh(booking)
            session.refresh(payment)

            return ShantidharaBookingResponse(
                booking_id=booking.booking_id,
                user_id=booking.user_id,
                temple_id=booking.temple_id,
                temple_name=booking.temple_name,
                slot_id=booking.slot_id,
                slot_label=booking.slot_label,
                slot_date=booking.slot_date.isoformat(),
                amount_label=booking.amount_label,
                status="payment_pending",
                payment_id=payment.payment_id,
            )

    def list_shantidhara_bookings(
        self,
        *,
        user_id: str,
        temple_id: str | None = None,
    ) -> list[ShantidharaBookingItem]:
        with SessionLocal() as session:
            query = (
                select(ShantidharaBooking)
                .where(ShantidharaBooking.user_id == user_id)
                .order_by(ShantidharaBooking.created_at.desc())
            )
            if temple_id is not None:
                query = query.where(ShantidharaBooking.temple_id == temple_id)
            items = session.scalars(query).all()
            return [
                ShantidharaBookingItem(
                    booking_id=item.booking_id,
                    user_id=item.user_id,
                    temple_id=item.temple_id,
                    temple_name=item.temple_name,
                    slot_id=item.slot_id,
                    slot_label=item.slot_label,
                    slot_date=item.slot_date.isoformat(),
                    amount_label=item.amount_label,
                    status=item.status,  # type: ignore[arg-type]
                    created_at=item.created_at.isoformat(),
                )
                for item in items
            ]

    def create_donation(
        self,
        *,
        user_id: str,
        temple_id: str,
        temple_name: str,
        donation_type: str,
        amount_label: str,
    ) -> DonationResponse:
        with SessionLocal() as session:
            donation = DonationOrder(
                donation_id="pending",
                user_id=user_id,
                temple_id=temple_id,
                temple_name=temple_name,
                donation_type=donation_type,
                amount_label=amount_label,
                status="payment_pending",
            )
            session.add(donation)
            session.flush()
            donation.donation_id = self._format_donation_id(donation.id)

            payment = PaymentTransaction(
                payment_id="pending",
                entity_type="donation_order",
                entity_id=donation.donation_id,
                amount_label=amount_label,
                status="payment_pending",
            )
            session.add(payment)
            session.flush()
            payment.payment_id = self._format_payment_id(payment.id)

            session.commit()
            session.refresh(donation)
            session.refresh(payment)

            return DonationResponse(
                donation_id=donation.donation_id,
                user_id=donation.user_id,
                temple_id=donation.temple_id,
                temple_name=donation.temple_name,
                donation_type=donation.donation_type,  # type: ignore[arg-type]
                amount_label=donation.amount_label,
                status="payment_pending",
                payment_id=payment.payment_id,
            )

    def list_donations(
        self,
        *,
        user_id: str,
        temple_id: str | None = None,
    ) -> list[DonationItem]:
        with SessionLocal() as session:
            query = (
                select(DonationOrder)
                .where(DonationOrder.user_id == user_id)
                .order_by(DonationOrder.created_at.desc())
            )
            if temple_id is not None:
                query = query.where(DonationOrder.temple_id == temple_id)
            items = session.scalars(query).all()
            return [
                DonationItem(
                    donation_id=item.donation_id,
                    user_id=item.user_id,
                    temple_id=item.temple_id,
                    temple_name=item.temple_name,
                    donation_type=item.donation_type,  # type: ignore[arg-type]
                    amount_label=item.amount_label,
                    status=item.status,  # type: ignore[arg-type]
                    created_at=item.created_at.isoformat(),
                )
                for item in items
            ]

    @staticmethod
    def _format_subscription_id(row_id: int) -> str:
        return f"SUB-{row_id:05d}"

    @staticmethod
    def _format_booking_id(row_id: int) -> str:
        return f"BOOK-{row_id:05d}"

    @staticmethod
    def _format_donation_id(row_id: int) -> str:
        return f"DON-{row_id:05d}"

    @staticmethod
    def _format_payment_id(row_id: int) -> str:
        return f"PAY-{row_id:05d}"

    @staticmethod
    def _to_item(subscription: TempleSubscription) -> TempleSubscriptionItem:
        return TempleSubscriptionItem(
            subscription_id=subscription.subscription_id,
            user_id=subscription.user_id,
            temple_id=subscription.temple_id,
            temple_name=subscription.temple_name,
            requester_name=subscription.requester_name,
            status=subscription.status,  # type: ignore[arg-type]
            rejection_reason=subscription.rejection_reason,
            requested_at=subscription.requested_at.isoformat(),
            reviewed_at=subscription.reviewed_at.isoformat()
            if subscription.reviewed_at is not None
            else None,
        )


temple_subscription_store = TempleSubscriptionStore()
