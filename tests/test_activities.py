"""
Tests for the FastAPI activities management API.
Covers GET /activities, POST /signup, and DELETE /unregister endpoints.
"""
import pytest
from src.app import activities


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response is a dict
        assert isinstance(data, dict)
        
        # Verify all expected activities are present
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Team", "Soccer Club", "Art Studio",
            "Drama Club", "Robotics Team", "Science Club"
        ]
        for activity in expected_activities:
            assert activity in data

    def test_get_activities_returns_valid_structure(self, client):
        """Test that activities have required fields."""
        response = client.get("/activities")
        data = response.json()
        
        # Check first activity has required fields
        first_activity = next(iter(data.values()))
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for field in required_fields:
            assert field in first_activity

    def test_get_activities_participants_is_list(self, client):
        """Test that participants field is a list."""
        response = client.get("/activities")
        data = response.json()
        
        for activity in data.values():
            assert isinstance(activity["participants"], list)
            for participant in activity["participants"]:
                assert isinstance(participant, str)

    def test_get_activities_max_participants_is_number(self, client):
        """Test that max_participants is a number."""
        response = client.get("/activities")
        data = response.json()
        
        for activity in data.values():
            assert isinstance(activity["max_participants"], int)
            assert activity["max_participants"] > 0


class TestSignUp:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, test_emails):
        """Test successful signup for an activity."""
        email = test_emails["new"]
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_adds_participant_to_activity(self, client, test_emails):
        """Test that signup actually adds the participant to the activity."""
        email = test_emails["new"]
        activity_name = "Chess Club"
        
        # Verify email is not already in the activity
        initial_response = client.get("/activities")
        initial_data = initial_response.json()
        initial_participants = initial_data[activity_name]["participants"]
        assert email not in initial_participants
        
        # Perform signup
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Verify email was added
        final_response = client.get("/activities")
        final_data = final_response.json()
        final_participants = final_data[activity_name]["participants"]
        assert email in final_participants
        assert len(final_participants) == len(initial_participants) + 1

    def test_signup_duplicate_email_rejected(self, client, test_emails):
        """Test that duplicate signups are rejected."""
        email = test_emails["new"]
        activity_name = "Chess Club"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "detail" in data
        assert "Already signed up" in data["detail"]

    def test_signup_activity_not_found(self, client, test_emails):
        """Test that signup to non-existent activity returns 404."""
        email = test_emails["new"]
        activity_name = "Non-Existent Activity"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_missing_email_parameter(self, client):
        """Test that signup without email parameter fails."""
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup"
        )
        
        # Missing query parameter should result in error
        assert response.status_code == 422  # Unprocessable Entity

    def test_signup_multiple_students_same_activity(self, client, test_emails):
        """Test that multiple students can sign up for the same activity."""
        activity_name = "Chess Club"
        email1 = test_emails["new"]
        email2 = test_emails["another"]
        
        # First student signs up
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        assert response1.status_code == 200
        
        # Second student signs up
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        assert response2.status_code == 200
        
        # Verify both are in the activity
        final_response = client.get("/activities")
        final_data = final_response.json()
        final_participants = final_data[activity_name]["participants"]
        assert email1 in final_participants
        assert email2 in final_participants

    def test_signup_special_characters_in_email(self, client):
        """Test signup with special characters in activity name."""
        email = "test@example.com"
        activity_name = "Art Studio"  # Contains space
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Should succeed even with spaces in activity name
        assert response.status_code == 200


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client, test_emails):
        """Test successful unregister from an activity."""
        email = test_emails["new"]
        activity_name = "Chess Club"
        
        # First sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_unregister_removes_participant(self, client, test_emails):
        """Test that unregister actually removes the participant."""
        email = test_emails["new"]
        activity_name = "Chess Club"
        
        # Sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Verify participant is there
        before_response = client.get("/activities")
        before_data = before_response.json()
        assert email in before_data[activity_name]["participants"]
        participants_before = len(before_data[activity_name]["participants"])
        
        # Unregister
        client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Verify participant was removed
        after_response = client.get("/activities")
        after_data = after_response.json()
        assert email not in after_data[activity_name]["participants"]
        participants_after = len(after_data[activity_name]["participants"])
        assert participants_after == participants_before - 1

    def test_unregister_not_registered_student(self, client, test_emails):
        """Test that unregistering a non-registered student returns error."""
        email = test_emails["new"]
        activity_name = "Chess Club"
        
        # Attempt to unregister without signing up
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not registered" in data["detail"].lower()

    def test_unregister_activity_not_found(self, client, test_emails):
        """Test that unregister from non-existent activity returns 404."""
        email = test_emails["new"]
        activity_name = "Non-Existent Activity"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_unregister_missing_email_parameter(self, client):
        """Test that unregister without email parameter fails."""
        activity_name = "Chess Club"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister"
        )
        
        # Missing query parameter should result in error
        assert response.status_code == 422  # Unprocessable Entity

    def test_unregister_from_existing_participant(self, client):
        """Test unregister from an activity with existing participants."""
        activity_name = "Science Club"
        
        # Get initial participant (from fixtures)
        initial_response = client.get("/activities")
        initial_data = initial_response.json()
        existing_participant = initial_data[activity_name]["participants"][0]
        
        # Unregister the existing participant
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": existing_participant}
        )
        
        assert response.status_code == 200
        
        # Verify they're removed
        final_response = client.get("/activities")
        final_data = final_response.json()
        assert existing_participant not in final_data[activity_name]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_signup_and_unregister_flow(self, client, test_emails):
        """Test complete flow: signup then unregister."""
        email = test_emails["new"]
        activity_name = "Programming Class"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        check_response = client.get("/activities")
        check_data = check_response.json()
        assert email in check_data[activity_name]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        final_response = client.get("/activities")
        final_data = final_response.json()
        assert email not in final_data[activity_name]["participants"]

    def test_multiple_signups_and_unregisters(self, client, test_emails):
        """Test multiple students signing up and unregistering."""
        activity_name = "Basketball Team"
        email1 = test_emails["new"]
        email2 = test_emails["another"]
        
        # Both students sign up
        client.post(f"/activities/{activity_name}/signup", params={"email": email1})
        client.post(f"/activities/{activity_name}/signup", params={"email": email2})
        
        # Verify both are signed up
        check1 = client.get("/activities")
        data1 = check1.json()
        assert email1 in data1[activity_name]["participants"]
        assert email2 in data1[activity_name]["participants"]
        
        # First student unregisters
        client.delete(f"/activities/{activity_name}/unregister", params={"email": email1})
        
        # Verify only email2 remains
        check2 = client.get("/activities")
        data2 = check2.json()
        assert email1 not in data2[activity_name]["participants"]
        assert email2 in data2[activity_name]["participants"]

    def test_resignup_after_unregister(self, client, test_emails):
        """Test that a student can re-signup after unregistering."""
        email = test_emails["new"]
        activity_name = "Soccer Club"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Unregister
        client.delete(f"/activities/{activity_name}/unregister", params={"email": email})
        
        # Re-signup should work
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify re-signup succeeded
        final = client.get("/activities")
        final_data = final.json()
        assert email in final_data[activity_name]["participants"]
