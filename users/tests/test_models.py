import pytest
from django.core.exceptions import ValidationError

from users.models import User

from .factories import UserFactory


@pytest.mark.django_db
def test_creates_user_with_default_role():
    user_name = "user_example"
    user_email = "user@example.com"

    user = UserFactory.create(
        username=user_name,
        email=user_email,
    )

    assert user.role == User.Role.CLIENT


@pytest.mark.django_db
class TestUserEmail:
    def test_accepts_valid_email(self):
        user = UserFactory.build(email="test@example.com")

        user.full_clean()

    def test_rejects_duplicate_email(self):
        email = "duplicate@example.com"

        UserFactory.create(email=email)
        duplicate_user = UserFactory.build(email=email)

        with pytest.raises(ValidationError) as excinfo:
            duplicate_user.full_clean()

        assert excinfo.value.error_dict["email"][0].code == "unique"


@pytest.mark.django_db
class TestUserRole:
    @pytest.mark.parametrize(
        "role",
        [
            User.Role.CLIENT,
            User.Role.MANAGER,
            User.Role.DEVELOPER,
        ],
    )
    def test_accepts_allowed_roles(self, role):
        user = UserFactory.build(role=role)

        user.full_clean()

        assert user.role == role

    def test_rejects_invalid_role(self):
        user = UserFactory.build(role="unknown_role")

        with pytest.raises(ValidationError) as excinfo:
            user.full_clean()

        assert excinfo.value.error_dict["role"][0].code == "invalid_choice"
