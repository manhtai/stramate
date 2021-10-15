from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.activity.models import Activity


class RouteView(TemplateView):
    template_name = "page/map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        activity_id = kwargs.get('activity_id')
        activity = get_object_or_404(Activity, id=activity_id)
        context["activity"] = activity

        return context


class DetailView(LoginRequiredMixin, TemplateView):
    template_name = "activity/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        activity_id = kwargs.get('activity_id')
        activity = get_object_or_404(Activity, id=activity_id, user_id=self.request.user.id)
        context["activity"] = activity
        return context
