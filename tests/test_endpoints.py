"""Unit tests for Mergington High School Activity Management API."""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities_success(self, client, reset_activities):
        """Test successful retrieval of all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        
    def test_get_activities_response_structure(self, client, reset_activities):
        """Test that activities have correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        # Check Chess Club structure
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        
    def test_get_activities_participant_counts(self, client, reset_activities):
        """Test that participant counts are correct."""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Programming Class"]["participants"]) == 2
        assert len(data["Basketball Team"]["participants"]) == 1
        
    def test_get_activities_participant_emails(self, client, reset_activities):
        """Test that correct participants are listed."""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]
        

class TestPostSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
    def test_signup_participant_added(self, client, reset_activities):
        """Test that participant is added to activity after signup."""
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        
        assert "newstudent@mergington.edu" in data["Chess Club"]["participants"]
        assert len(data["Chess Club"]["participants"]) == 3
        
    def test_signup_multiple_users_different_activities(self, client, reset_activities):
        """Test that different users can sign up for different activities."""
        client.post("/activities/Chess Club/signup?email=user1@mergington.edu")
        client.post("/activities/Programming Class/signup?email=user1@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        
        assert "user1@mergington.edu" in data["Chess Club"]["participants"]
        assert "user1@mergington.edu" in data["Programming Class"]["participants"]
        
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity returns 404."""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]
        
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that duplicate signup is rejected with 400."""
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Duplicate signup
        response2 = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response2.status_code == 400
        
        data = response2.json()
        assert "Already signed up" in data["detail"]
        
    def test_signup_activity_full(self, client, reset_activities):
        """Test signup fails when activity is at capacity."""
        # Basketball Team has max_participants=15 with 1 current participant
        for i in range(14):
            client.post(
                f"/activities/Basketball Team/signup?email=student{i}@mergington.edu"
            )
        
        # This should be the 16th participant (exceeds max)
        response = client.post(
            "/activities/Basketball Team/signup?email=fullstudent@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "full" in data["detail"].lower()
        
    def test_signup_fill_activity_to_capacity(self, client, reset_activities):
        """Test that activity fills to exactly max_participants."""
        # Basketball Team: max_participants=15, current=1
        # Need to add 14 more to reach capacity
        for i in range(14):
            response = client.post(
                f"/activities/Basketball Team/signup?email=student{i}@mergington.edu"
            )
            assert response.status_code == 200
        
        # Verify we're at capacity
        response = client.get("/activities")
        data = response.json()
        assert len(data["Basketball Team"]["participants"]) == 15
        
        # Try one more signup - should fail
        response = client.post(
            "/activities/Basketball Team/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 400


class TestDeleteSignup:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from activity."""
        response = client.delete(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        
    def test_unregister_participant_removed(self, client, reset_activities):
        """Test that participant is removed from activity after unregister."""
        client.delete("/activities/Chess Club/signup?email=michael@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]
        assert len(data["Chess Club"]["participants"]) == 1
        
    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister from non-existent activity returns 404."""
        response = client.delete(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]
        
    def test_unregister_not_signed_up(self, client, reset_activities):
        """Test unregister fails when student is not signed up with 400."""
        response = client.delete(
            "/activities/Chess Club/signup?email=notstudent@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "Not signed up" in data["detail"]
        
    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a student can signup again after unregistering."""
        # Unregister
        response1 = client.delete(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Signup again
        response2 = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response2.status_code == 200
        
        # Verify re-signup succeeded
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        
    def test_unregister_frees_capacity(self, client, reset_activities):
        """Test that unregistering frees up capacity for new signups."""
        # Basketball Team: max_participants=15, current=1
        # Fill to capacity
        for i in range(14):
            client.post(
                f"/activities/Basketball Team/signup?email=student{i}@mergington.edu"
            )
        
        # Verify full
        response = client.get("/activities")
        data = response.json()
        assert len(data["Basketball Team"]["participants"]) == 15
        
        # Unregister one participant
        client.delete("/activities/Basketball Team/signup?email=alex@mergington.edu")
        
        # Now signup should work
        response = client.post(
            "/activities/Basketball Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to HTML."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        
        # Check redirect location
        assert response.headers["location"] == "/static/index.html"
        
    def test_root_redirect_followed(self, client):
        """Test that the redirect target exists (static file serving works)."""
        response = client.get("/", follow_redirects=True)
        # Should get HTML content or 200
        assert response.status_code == 200
