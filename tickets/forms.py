from django import forms

from tickets.models import Ticket
from users.models import User


class TicketCreateForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        label="Title",
        widget=forms.TextInput(attrs={"class": "form-control mb-3"}),
    )
    description = forms.CharField(
        max_length=10000,
        label="Description",
        widget=forms.Textarea(attrs={"class": "form-control mb-3", "rows": 6}),
    )


class ManagerTicketUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=Ticket.Status.choices,
        label="Status",
    )
    assignee = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.DEVELOPER),
        required=False,
        label="Assignee",
    )
    priority = forms.ChoiceField(
        choices=Ticket.Priority.choices,
        label="Priority",
    )
    manager_notes = forms.CharField(
        widget=forms.Textarea,
        max_length=2500,
        required=False,
        label="Manager notes",
    )


class DeveloperTicketUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            (
                Ticket.Status.PENDING_DEVELOPMENT,
                Ticket.Status.PENDING_DEVELOPMENT.label,
            ),
            (
                Ticket.Status.IN_PROGRESS,
                Ticket.Status.IN_PROGRESS.label,
            ),
            (
                Ticket.Status.PENDING_REVIEW,
                Ticket.Status.PENDING_REVIEW.label,
            ),
        ],
        label="Status",
    )
    resolution_notes = forms.CharField(
        widget=forms.Textarea,
        max_length=5000,
        required=False,
        label="Resolution notes",
    )


class CommentCreateForm(forms.Form):
    body = forms.CharField(
        widget=forms.Textarea,
        max_length=500,
        label="Comment",
    )
