from uuid import uuid4


def submit_to_mock_maitri(profile_id: str, file_name: str, review_id: str) -> dict[str, str | bool]:
    return {
        "submission_id": f"MAITRI-SIM-{uuid4().hex[:10].upper()}",
        "status": "received_for_simulated_review",
        "message": f"{file_name} linked to profile {profile_id} with review {review_id}.",
        "simulated": True,
    }