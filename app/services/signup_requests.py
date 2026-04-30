from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import TempleSubscription
from app.schemas.signup_request import TempleSubscriptionItem, TempleSubscriptionResponse


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

    @staticmethod
    def _format_subscription_id(row_id: int) -> str:
        return f"SUB-{row_id:05d}"

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
