from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from users.forms import UserRegistrationForm


class UserRegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = "users/register.html"

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return redirect("tickets:list")


class UserLoginView(LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True
    next_page = reverse_lazy("tickets:list")
