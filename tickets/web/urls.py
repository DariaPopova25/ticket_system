from django.urls import path

from .views import (
    ticket_list_view,
    ticket_detail_view,
    ticket_create_view,
    ticket_update_view,
    comment_create_view,
)

app_name = "tickets"

urlpatterns = [
    path("", ticket_list_view, name="list"),
    path("<int:pk>/", ticket_detail_view, name="detail"),
    path("create/", ticket_create_view, name="create"),
    path("<int:pk>/update/", ticket_update_view, name="update"),
    path("<int:pk>/comments/create/", comment_create_view, name="comment_create"),
]
