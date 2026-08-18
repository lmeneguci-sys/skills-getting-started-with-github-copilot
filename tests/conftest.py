"""
Pytest configuration and shared fixtures for activities API tests.
"""
import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def activities_backup():
    """Backup of the original activities for test isolation."""
    return copy.deepcopy(activities)


@pytest.fixture
def client(activities_backup):
    """Create a test client and restore activities state after each test."""
    yield TestClient(app)
    # Restore activities to original state
    activities.clear()
    activities.update(activities_backup)


@pytest.fixture
def sample_activity_data():
    """Sample activity data for testing."""
    return {
        "Test Activity": {
            "description": "A test activity",
            "schedule": "Monday, 3:00 PM - 4:00 PM",
            "max_participants": 5,
            "participants": ["existing@test.com"]
        }
    }


@pytest.fixture
def test_emails():
    """Sample test email addresses."""
    return {
        "existing": "existing@test.com",
        "new": "newstudent@test.com",
        "another": "another@test.com",
        "empty": "",
    }
