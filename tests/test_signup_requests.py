from app.services.signup_requests import TempleSubscriptionStore


def test_create_temple_subscription() -> None:
    store = TempleSubscriptionStore()

    response = store.create(
        user_id="USR-00011",
        temple_id="TMP-1002",
        temple_name="ISKCON Pune",
        requester_name="Apoorv Jain",
    )

    assert response.status == "pending"
    assert response.temple_id == "TMP-1002"
    assert response.requester_name == "Apoorv Jain"
    assert response.subscription_id.startswith("SUB-")
