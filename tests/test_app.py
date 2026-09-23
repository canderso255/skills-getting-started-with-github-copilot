from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(app_module.activities)

    yield

    app_module.activities.clear()
    app_module.activities.update(original_activities)


def activity_path(activity_name):
    return quote(activity_name, safe="")


def participant_path(email):
    return quote(email, safe="")


def test_get_activities_returns_all_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert set(activities) == set(app_module.activities)
    assert activities["Chess Club"] == app_module.activities["Chess Club"]


def test_signup_adds_unique_participant():
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    response = client.post(
        f"/activities/{activity_path(activity_name)}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant():
    activity_name = "Chess Club"
    email = app_module.activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{activity_path(activity_name)}/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_requires_email():
    response = client.post(
        f"/activities/{activity_path('Chess Club')}/signup"
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]


def test_unregister_removes_existing_participant():
    activity_name = "Chess Club"
    email = app_module.activities[activity_name]["participants"][0]

    response = client.delete(
        f"/activities/{activity_path(activity_name)}/participants/"
        f"{participant_path(email)}"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity():
    response = client.delete(
        "/activities/Unknown%20Club/participants/student%40mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_unknown_participant():
    activity_name = "Chess Club"
    email = "not.registered@mergington.edu"

    response = client.delete(
        f"/activities/{activity_path(activity_name)}/participants/"
        f"{participant_path(email)}"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
