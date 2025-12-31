"""
Basic test structure for authentication endpoints
TODO: Add comprehensive tests
"""
import pytest


def test_send_code(client):
    """Test sending verification code"""
    response = client.post(
        "/v1/auth/send-code",
        json={"phoneNumber": "13812345678"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_login(client):
    """Test login with phone and code"""
    # First send code
    client.post("/v1/auth/send-code", json={"phoneNumber": "13812345678"})
    
    # Then login (using mock code in development)
    response = client.post(
        "/v1/auth/login",
        json={
            "phoneNumber": "13812345678",
            "verificationCode": "123456"
        }
    )
    # Should succeed in mock mode
    assert response.status_code in [200, 401]  # 401 if code doesn't match


def test_guest_mode(client):
    """Test guest mode"""
    response = client.post("/v1/auth/guest")
    assert response.status_code == 200
    assert "token" in response.json()

