from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import View
from django.views.generic.edit import UpdateView

from apps.account.forms import AthleteForm
from apps.account.models import Athlete


class AthleteView(LoginRequiredMixin, UpdateView):
    model = Athlete
    form_class = AthleteForm
    template_name = "account/athlete.html"

    def get_object(self, **kwargs):
        return Athlete.get_athlete(self.request.user)


class LogOutView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("/")
