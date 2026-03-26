import pytest
from django.core.exceptions import ValidationError

from tickets.models import Ticket
from users.models import User

from .factories import ClientFactory, DeveloperFactory, TicketFactory, CommentFactory


@pytest.fixture
def user_client():
    return ClientFactory.create()


@pytest.fixture
def user_developer():
    return DeveloperFactory.create()

@pytest.fixture
def ticket_factory(user_client, user_developer):
    def make_ticket(status=Ticket.Status.NEW):
        return TicketFactory.create(
            creator=user_client,
            status=status,
            assignee=user_developer,
            priority=Ticket.Priority.HIGH,
        )
    return make_ticket

@pytest.mark.django_db
def test_creates_ticket_with_default_status_and_no_assignee():
    ticket = TicketFactory.create()

    assert ticket.status == Ticket.Status.NEW
    assert ticket.assignee is None

@pytest.mark.django_db
class TestTicketCreator:
    def test_accepts_client_as_creator(self, user_client):
        ticket = TicketFactory.build(creator=user_client)

        ticket.full_clean()

        assert ticket.creator.role == User.Role.CLIENT

    def test_rejects_non_client_as_creator(self, user_developer):
        ticket = TicketFactory.build(creator=user_developer)

        with pytest.raises(ValidationError) as excinfo:
            ticket.full_clean()

        assert excinfo.value.message_dict["creator"] == [
            "Creator must have client role."
        ]

    def test_rejects_null_creator(self):
        ticket = TicketFactory.build(creator=None)

        with pytest.raises(ValidationError) as excinfo:
            ticket.full_clean()

        assert excinfo.value.message_dict["creator"] == ["This field cannot be null."]


@pytest.mark.django_db
class TestTicketAssignee:
    def test_accepts_developer_as_assignee(self, user_client, user_developer):
        ticket = TicketFactory.build(
            creator=user_client,
            assignee=user_developer,
        )

        ticket.full_clean()

        assert ticket.assignee.role == User.Role.DEVELOPER

    def test_rejects_non_developer_as_assignee(self, user_client):
        ticket = TicketFactory.build(
            creator=user_client,
            assignee=user_client,
        )

        with pytest.raises(ValidationError) as excinfo:
            ticket.full_clean()

        assert excinfo.value.message_dict["assignee"] == [
            "Assignee must have developer role."
        ]


@pytest.mark.django_db
class TestTicketStatus:
    ALL_ACTIVE_STATUSES = [
        Ticket.Status.NEW,
        Ticket.Status.PENDING_DEVELOPMENT,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.PENDING_REVIEW,
        Ticket.Status.DONE,
        Ticket.Status.CANCELLED,
    ]

    STATUSES_REQUIRING_ASSIGNEE_AND_PRIORITY = [
        Ticket.Status.PENDING_DEVELOPMENT,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.PENDING_REVIEW,
        Ticket.Status.DONE,
    ]

    STATUSES_ALLOWING_EMPTY_ASSIGNEE_AND_PRIORITY = [
        Ticket.Status.NEW,
        Ticket.Status.CANCELLED,
    ]

    @pytest.mark.parametrize("status", ALL_ACTIVE_STATUSES)
    def test_accepts_all_statuses_with_developer_assignee_and_priority(
        self, user_client, user_developer, status
    ):
        ticket = TicketFactory.build(
            creator=user_client,
            status=status,
            assignee=user_developer,
            priority=Ticket.Priority.HIGH,
        )
        ticket.full_clean()

        assert ticket.status == status
        assert ticket.assignee.role == User.Role.DEVELOPER
        assert ticket.priority == Ticket.Priority.HIGH

    @pytest.mark.parametrize("status", STATUSES_ALLOWING_EMPTY_ASSIGNEE_AND_PRIORITY)
    def test_allows_new_and_cancelled_statuses_without_assignee_and_priority(
        self, user_client, status
    ):
        ticket = TicketFactory.build(
            creator=user_client,
            status=status,
        )
        ticket.full_clean()

        assert ticket.status == status
        assert ticket.assignee_id is None
        assert ticket.priority == ""

    @pytest.mark.parametrize("status", STATUSES_REQUIRING_ASSIGNEE_AND_PRIORITY)
    def test_rejects_missing_assignee_for_status_requiring_assignee(
        self, user_client, status
    ):
        ticket = TicketFactory.build(
            creator=user_client,
            status=status,
            priority=Ticket.Priority.HIGH,
        )

        with pytest.raises(ValidationError) as excinfo:
            ticket.full_clean()

        assert excinfo.value.message_dict["assignee"] == [
            "Assignee is required for this status."
        ]

    @pytest.mark.parametrize("status", STATUSES_REQUIRING_ASSIGNEE_AND_PRIORITY)
    def test_rejects_statuses_requiring_priority_without_priority(
        self, user_client, user_developer, status
    ):
        ticket = TicketFactory.build(
            creator=user_client,
            status=status,
            assignee=user_developer,
        )

        with pytest.raises(ValidationError) as excinfo:
            ticket.full_clean()

        assert excinfo.value.message_dict["priority"] == [
            "Priority is required for this status."
        ]

    def test_rejects_invalid_status(self, user_client):
        ticket = TicketFactory.build(
            creator=user_client,
            status="unknown_status",
        )

        with pytest.raises(ValidationError) as excinfo:
            ticket.full_clean()

        assert excinfo.value.error_dict["status"][0].code == "invalid_choice"


@pytest.mark.django_db
class TestTicketPriority:
    @pytest.mark.parametrize(
        "priority",
        [
            Ticket.Priority.LOW,
            Ticket.Priority.MEDIUM,
            Ticket.Priority.HIGH,
        ],
    )
    def test_accepts_allowed_priority(self, user_client, priority):
        ticket = TicketFactory.build(
            creator=user_client,
            priority=priority,
        )

        ticket.full_clean()

        assert ticket.priority == priority

    def test_rejects_invalid_priority(self, user_client):
        ticket = TicketFactory.build(
            creator=user_client,
            priority="unknown_priority",
        )

        with pytest.raises(ValidationError) as excinfo:
            ticket.full_clean()

        assert excinfo.value.error_dict["priority"][0].code == "invalid_choice"

@pytest.mark.django_db
def test_creates_comment(user_client, ticket_factory):
    ticket = ticket_factory()

    comment = CommentFactory.create(
        user = user_client,
        ticket = ticket,
        body = 'fake_body',
    )

    assert comment.user == user_client
    assert comment.ticket == ticket
    assert comment.body == 'fake_body'


@pytest.mark.django_db
class TestCommentValidation:
    OPEN_STATUSES = [
        Ticket.Status.NEW,
        Ticket.Status.PENDING_DEVELOPMENT,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.PENDING_REVIEW,
    ]

    CLOSED_STATUSES = [
        Ticket.Status.DONE,
        Ticket.Status.CANCELLED,
    ]

    @pytest.mark.parametrize("status", OPEN_STATUSES)
    def test_allows_comment_for_open_ticket(self, user_client, ticket_factory, status):
        ticket = ticket_factory(status=status)

        comment = CommentFactory.build(
            user = user_client,
            ticket = ticket,
            body = 'fake_body',
        )

        comment.full_clean()

        assert comment.user == user_client
        assert comment.ticket == ticket
        assert comment.body == 'fake_body'

    def test_rejects_comment_with_blank_body(self, user_client, ticket_factory):
        ticket = ticket_factory()

        comment = CommentFactory.build(
            user = user_client,
            ticket = ticket,
            body="   ",
        )

        with pytest.raises(ValidationError) as excinfo:
            comment.full_clean()

        assert excinfo.value.message_dict["body"] == ["Comment body cannot be empty."]

    @pytest.mark.parametrize("status", CLOSED_STATUSES)
    def test_rejects_comment_for_closed_ticket(self, user_client, ticket_factory, status):
        ticket = ticket_factory(status=status)

        comment = CommentFactory.build(
            user = user_client,
            ticket = ticket,
        )

        with pytest.raises(ValidationError) as excinfo:
            comment.full_clean()

        assert excinfo.value.message_dict["ticket"] == ["Comments are not allowed for closed tickets."]
