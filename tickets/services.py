from django.core.exceptions import ValidationError

from tickets.models import Comment, Ticket
from users.models import User

_UNSET = object()

CLOSED_STATUSES = {
    Ticket.Status.DONE,
    Ticket.Status.CANCELLED,
}

DEVELOPER_ALLOWED_STATUSES = {
    Ticket.Status.PENDING_DEVELOPMENT,
    Ticket.Status.IN_PROGRESS,
    Ticket.Status.PENDING_REVIEW,
}

def _ensure_ticket_is_not_closed(ticket):
    if ticket.status in CLOSED_STATUSES:
        raise ValidationError({"status": "Closed tickets cannot be changed."})


def create_ticket(*, actor, title, description):
    if actor.role != actor.Role.CLIENT:
        raise ValidationError("Only client can create ticket.")

    ticket = Ticket(
        creator=actor,
        title=title,
        description=description,
    )
    ticket.full_clean()
    ticket.save()
    return ticket


def manager_update_ticket(
    *,
    actor,
    ticket,
    status=None,
    assignee=_UNSET,
    priority=None,
    manager_notes=None,
):
    if actor.role != actor.Role.MANAGER:
        raise ValidationError("Only manager can update ticket.")

    _ensure_ticket_is_not_closed(ticket)

    target_status = status if status is not None else ticket.status

    if assignee is None and target_status != Ticket.Status.NEW:
        raise ValidationError({"assignee": "Assignee can be removed only in new status."})

    if assignee is not _UNSET and assignee is not None and assignee.role != User.Role.DEVELOPER:
        raise ValidationError({"assignee": "Assignee must have developer role."})

    if status is not None:
        ticket.status = status
    if assignee is not _UNSET:
        ticket.assignee = assignee
    if priority is not None:
        ticket.priority = priority
    if manager_notes is not None:
        ticket.manager_notes = manager_notes

    ticket.full_clean()
    ticket.save()
    return ticket


def developer_update_ticket(
    *,
    actor,
    ticket,
    status=None,
    resolution_notes=None,
):
    if actor.role != actor.Role.DEVELOPER:
        raise ValidationError("Only developer can update ticket.")

    _ensure_ticket_is_not_closed(ticket)

    if ticket.assignee_id != actor.id:
        raise ValidationError({"assignee": "Developer can update only assigned tickets."})


    if ticket.status == Ticket.Status.NEW:
        raise ValidationError(
            {"status": "Developer can update ticket only after pending_development."}
        )

    if status is not None and status not in DEVELOPER_ALLOWED_STATUSES:
        raise ValidationError({"status": "Developer can change status only within working area."})

    if status is not None:
        ticket.status = status

    if resolution_notes is not None:
        ticket.resolution_notes = resolution_notes

    ticket.full_clean()
    ticket.save()
    return ticket


def create_comment(*, actor, ticket, body):
    if actor.role == User.Role.CLIENT and ticket.creator_id != actor.id:
        raise ValidationError("Client can comment only on own tickets.")

    if actor.role == User.Role.DEVELOPER and ticket.assignee_id != actor.id:
        raise ValidationError("Developer can comment only on assigned tickets.")

    comment = Comment(
        user=actor,
        ticket=ticket,
        body=body,
    )
    comment.full_clean()
    comment.save()
    return comment
