from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    with TestClient(app) as test_client:
        yield test_client
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_catalog(client):
    # Arrange
    expected_activity_names = set(activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert set(response.json()) == expected_activity_names


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "new-student@mergington.edu"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    participants_before = activities[activity_name]["participants"].copy()
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 409
    assert response.json() == {"detail": "Student is already signed up for this activity"}
    assert activities[activity_name]["participants"] == participants_before


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_path, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    participants_before = activities[activity_name]["participants"].copy()
    unregister_path = (
        f"/activities/{quote(activity_name, safe='')}"
        f"/participants/{quote(email, safe='')}"
    )

    # Act
    response = client.delete(unregister_path)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert activities[activity_name]["participants"] == participants_before[1:]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"
    unregister_path = (
        f"/activities/{quote(activity_name, safe='')}"
        f"/participants/{quote(email, safe='')}"
    )

    # Act
    response = client.delete(unregister_path)

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "not-registered@mergington.edu"
    unregister_path = (
        f"/activities/{quote(activity_name, safe='')}"
        f"/participants/{quote(email, safe='')}"
    )

    # Act
    response = client.delete(unregister_path)

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}