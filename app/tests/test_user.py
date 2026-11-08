import pytest

from unittest.mock import MagicMock
from app.routes import user_route

def test_get_user_success(client, monkeypatch):
    mock_users = [
        MagicMock(
            id=1,
            username="test1",
            full_name="Thalath",
            email="test1@gmail.com",
            is_active=True
        ),
        MagicMock(
            id=2,
            username="test2",
            full_name="Test User",
            email="test2@gmail.com",
            is_active=True
        )
    ]
    
    monkeypatch.setattr(
        user_route.UserService,
        "get_all",
        lambda: mock_users
    )
    
    monkeypatch.setattr(
        user_route.UserResponseSchema,
        "dump",
        lambda self, users: [
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "is_active": user.is_active
            }
            for user in users
        ]
    )
    
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == 200
    assert data["message"] == "Users retrived successfully"
    assert len(data["data"]) == 2
    assert data["data"][0]["username"] == "test1"
    
def test_get_users_not_found(client, monkeypatch):
    monkeypatch.setattr(
        user_route.UserService,
        "get_all",
        lambda: None
    )

    response = client.get("/users/")

    assert response.status_code == 404
    assert response.get_json()["message"] == "Users not found."
    
def test_get_users_empty(client, monkeypatch):
    monkeypatch.setattr(
        user_route.UserService,
        "get_all",
        lambda: []
    )

    response = client.get("/users/")

    assert response.status_code == 500
    assert response.get_json()["status"] == 500