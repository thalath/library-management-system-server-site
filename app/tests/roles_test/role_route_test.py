from unittest.mock import MagicMock
from flask_jwt_extended import create_access_token
from app.routes import role_route


def test_get_all_roles_success(client, app, monkeypatch):
    mock_roles = [
        MagicMock(
            id=1,
            name="Admin",
            description="Administrator role"
        ),
        MagicMock(
            id=2,
            name="User",
            description="Normal user role"
        )
    ]

    monkeypatch.setattr(
        role_route.RoleService,
        "get_all",
        lambda: mock_roles
    )
    with app.app_context():
        token = create_access_token(identity="1")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        "/roles/",
        headers=headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 2
    assert data[0]["name"] == "Admin"
    assert data[0]["name"] == "User"