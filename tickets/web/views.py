from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from tickets.forms import (
    CommentCreateForm,
    DeveloperTicketUpdateForm,
    ManagerTicketUpdateForm,
    TicketCreateForm,
)
from tickets.models import Ticket
from tickets.services import (
    CLOSED_STATUSES,
    DEVELOPER_ALLOWED_STATUSES,
    create_comment,
    create_ticket,
    developer_update_ticket,
    manager_update_ticket,
)
from users.models import User


def _visible_tickets(user):
    queryset = Ticket.objects.select_related("creator", "assignee").order_by(
        "-created_at"
    )

    if user.role == User.Role.MANAGER:
        return queryset

    if user.role == User.Role.DEVELOPER:
        return queryset.filter(assignee=user)

    if user.role == User.Role.CLIENT:
        return queryset.filter(creator=user)

    raise PermissionDenied


def _get_visible_ticket(user, pk):
    return get_object_or_404(_visible_tickets(user), pk=pk)


def _add_service_errors(form, error):
    if hasattr(error, "message_dict"):
        for field, messages in error.message_dict.items():
            for message in messages:
                if field in form.fields:
                    form.add_error(field, message)
                else:
                    form.add_error(None, message)
    else:
        for message in error.messages:
            form.add_error(None, message)


def _manager_ticket_update_view(request, pk):
    ticket = _get_visible_ticket(request.user, pk=pk)

    if ticket.status in CLOSED_STATUSES:
        raise PermissionDenied

    if request.method == "POST":
        form = ManagerTicketUpdateForm(request.POST)

        if form.is_valid():
            try:
                ticket = manager_update_ticket(
                    actor=request.user,
                    ticket=ticket,
                    status=form.cleaned_data["status"],
                    assignee=form.cleaned_data["assignee"],
                    priority=form.cleaned_data["priority"],
                    manager_notes=form.cleaned_data["manager_notes"],
                )
                return redirect("tickets:detail", pk=ticket.pk)
            except ValidationError as error:
                _add_service_errors(form, error)
    else:
        form = ManagerTicketUpdateForm(
            initial={
                "status": ticket.status,
                "assignee": ticket.assignee,
                "priority": ticket.priority,
                "manager_notes": ticket.manager_notes,
            }
        )

    return render(
        request,
        "tickets/update.html",
        {
            "form": form,
            "ticket": ticket,
        },
    )


def _developer_ticket_update_view(request, pk):
    ticket = _get_visible_ticket(request.user, pk=pk)

    if ticket.status not in DEVELOPER_ALLOWED_STATUSES:
        raise PermissionDenied

    if request.method == "POST":
        form = DeveloperTicketUpdateForm(request.POST)

        if form.is_valid():
            try:
                ticket = developer_update_ticket(
                    actor=request.user,
                    ticket=ticket,
                    status=form.cleaned_data["status"],
                    resolution_notes=form.cleaned_data["resolution_notes"],
                )
                return redirect("tickets:detail", pk=ticket.pk)
            except ValidationError as error:
                _add_service_errors(form, error)
    else:
        form = DeveloperTicketUpdateForm(
            initial={
                "status": ticket.status,
                "resolution_notes": ticket.resolution_notes,
            }
        )

    return render(
        request,
        "tickets/update.html",
        {
            "form": form,
            "ticket": ticket,
        },
    )


@login_required
def ticket_list_view(request):
    tickets = _visible_tickets(request.user)
    return render(request, "tickets/list.html", {"tickets": tickets})


@login_required
def ticket_detail_view(request, pk):
    ticket = _get_visible_ticket(request.user, pk=pk)

    data = {
        "ticket": ticket,
        "comments": ticket.comments.select_related("user").order_by("created_at"),
        "comment_form": CommentCreateForm(),
    }
    return render(request, "tickets/detail.html", data)


@login_required
def ticket_create_view(request):
    if request.user.role != User.Role.CLIENT:
        raise PermissionDenied

    if request.method == "POST":
        form = TicketCreateForm(request.POST)

        if form.is_valid():
            try:
                ticket = create_ticket(
                    actor=request.user,
                    title=form.cleaned_data["title"],
                    description=form.cleaned_data["description"],
                )
                return redirect("tickets:detail", pk=ticket.pk)
            except ValidationError as error:
                _add_service_errors(form, error)
    else:
        form = TicketCreateForm()

    return render(request, "tickets/create.html", {"form": form})


@login_required
def ticket_update_view(request, pk):
    if request.user.role == User.Role.MANAGER:
        return _manager_ticket_update_view(request, pk)

    if request.user.role == User.Role.DEVELOPER:
        return _developer_ticket_update_view(request, pk)

    raise PermissionDenied


@login_required
def comment_create_view(request, pk):
    ticket = _get_visible_ticket(request.user, pk=pk)

    if request.method != "POST":
        return redirect("tickets:detail", pk=ticket.pk)

    form = CommentCreateForm(request.POST)

    if form.is_valid():
        try:
            create_comment(
                actor=request.user,
                ticket=ticket,
                body=form.cleaned_data["body"],
            )
            return redirect("tickets:detail", pk=ticket.pk)
        except ValidationError as error:
            _add_service_errors(form, error)

    data = {
        "ticket": ticket,
        "comments": ticket.comments.select_related("user").order_by("created_at"),
        "comment_form": form,
    }
    return render(request, "tickets/detail.html", data)
