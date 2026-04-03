import pytest
from django.contrib.auth import SESSION_KEY
from django.urls import reverse

from users.models import User


@pytest.mark.django_db
class TestUserRegisterView:
    def test_register_view_creates_user_logs_in_and_redirects(self, client):
        response = client.post(
            reverse("users:register"),
            data={
                "username": "example_user",
                "email": "example_user@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )

        user = User.objects.get(email="example_user@example.com")

        assert response.status_code == 302
        assert response.url == reverse("tickets:list")
        assert user.role == User.Role.CLIENT
        assert client.session[SESSION_KEY] == str(user.pk)

    def test_register_view_returns_errors_for_invalid_data(self, client):
        users_count_before = User.objects.count()

        response = client.post(
            reverse("users:register"),
            data={
                "username": "example_user",
                "email": "invalid-email",
                "password1": "StrongPassword123!",
                "password2": "DifferentPassword123!",
            },
        )

        assert response.status_code == 200
        assert User.objects.count() == users_count_before
        assert response.context["form"].errors


@pytest.mark.django_db
class TestUserLoginView:
    def test_login_view_logs_in_user_and_redirects(self, client):
        user = User.objects.create_user(
            username="example_user",
            email="example_user@example.com",
            password="StrongPassword123!",
            role=User.Role.CLIENT,
        )

        response = client.post(
            reverse("users:login"),
            data={
                "username": "example_user@example.com",
                "password": "StrongPassword123!",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("tickets:list")
        assert client.session[SESSION_KEY] == str(user.pk)

    def test_login_view_returns_errors_for_invalid_credentials(self, client):
        User.objects.create_user(
            username="example_user",
            email="example_user@example.com",
            password="StrongPassword123!",
            role=User.Role.CLIENT,
        )

        response = client.post(
            reverse("users:login"),
            data={
                "username": "example_user@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 200
        assert SESSION_KEY not in client.session
        assert response.context["form"].errors
