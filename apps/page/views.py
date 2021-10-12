from django.views.generic import TemplateView
from apps.activity.models import Activity


class IndexView(TemplateView):
    template_name = "page/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            stats = Activity.get_last_year_stats(self.request.user.id)
            context["recent_activities"] = stats["recent_activities"]
            context["last_year_total"] = stats["last_year_total"]
            context["last_year_count"] = stats["last_year_count"]

        return context
