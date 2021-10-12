from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from apps.activity.models import Activity


class IndexView(TemplateView):
    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ["page/home.html"]
        return ["page/index.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            stats = Activity.get_last_year_stats(self.request.user.id)
            context.update(stats)

        return context


class AthleteView(TemplateView):
    template_name = "page/athlete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        username = kwargs.get('username')
        user = get_object_or_404(User, username=username)
        stats = Activity.get_last_year_stats(user.id)

        context.update(stats)
        context["username"] = user.username

        return context
