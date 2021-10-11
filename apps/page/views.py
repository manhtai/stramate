from django.views.generic import TemplateView
from apps.activity.models import Activity
from datetime import datetime, timedelta


class IndexView(TemplateView):
    template_name = "page/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            user_activities = Activity.objects.filter(
                user=self.request.user
            ).order_by('-start_date')[:3]

            last_year = datetime.utcnow() - timedelta(days=365)
            last_year_count = Activity.objects.filter(
                user=self.request.user, start_date__gte=last_year
            ).count()

            context["last_year_count"] = last_year_count
            context["activities"] = user_activities

        return context
