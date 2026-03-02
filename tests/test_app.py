import pytest
from fastapi.testclient import TestClient
from copy import deepcopy

import src.app as app_module

# preserve original activities for resetting state
_original_activities = deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: run before every test to clear and restore in-memory data"""
    app_module.activities.clear()
    app_module.activities.update(deepcopy(_original_activities))
    yield
    # no cleanup needed after, fixture handles it


# ------ helper client -------
client = TestClient(app_module.app)


def test_root_redirect():
    # Arrange: client created above
    # Act (don't follow redirects so we can inspect status code)
    resp = client.get("/", follow_redirects=False)
    # Assert
    assert resp.status_code in (307, 302)
    assert resp.headers.get("location", "").endswith("/static/index.html")


def test_get_activities():
    # Arrange
    # Act
    resp = client.get("/activities")
    # Assert
    assert resp.status_code == 200
    assert resp.json() == _original_activities


def test_signup_for_activity_success():
    # Arrange
    activity = "Chess Club"
    email = "newstudent@mergington.edu"
    # Act
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert resp.status_code == 200
    assert email in app_module.activities[activity]["participants"]


def test_signup_nonexistent_activity():
    # Arrange
    activity = "Nonexistent"
    email = "someone@mergington.edu"
    # Act
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert resp.status_code == 404


def test_signup_duplicate():
    # Arrange
    activity = "Chess Club"
    existing = _original_activities[activity]["participants"][0]
    # Act
    resp = client.post(f"/activities/{activity}/signup", params={"email": existing})
    # Assert
    assert resp.status_code == 400


def test_remove_participant_success():
    # Arrange
    activity = "Chess Club"
    email = _original_activities[activity]["participants"][0]
    # Act
    resp = client.delete(f"/activities/{activity}/participants", params={"email": email})
    # Assert
    assert resp.status_code == 200
    assert email not in app_module.activities[activity]["participants"]


def test_remove_participant_nonexistent_activity():
    # Arrange
    activity = "Nobody Club"
    email = "nobody@mergington.edu"
    # Act
    resp = client.delete(f"/activities/{activity}/participants", params={"email": email})
    # Assert
    assert resp.status_code == 404


def test_remove_participant_not_signed_up():
    # Arrange
    activity = "Chess Club"
    email = "notregistered@mergington.edu"
    # Act
    resp = client.delete(f"/activities/{activity}/participants", params={"email": email})
    # Assert
    assert resp.status_code == 404
