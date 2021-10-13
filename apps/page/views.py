from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.core.paginator import Paginator

from apps.activity.models import Activity


PAGE_SIZE = 3


class IndexView(TemplateView):
    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ["page/home.html"]
        return ["page/index.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            stats = Activity.get_last_year_stats(user.id)
            context.update(stats)

            user_activities = Activity.objects.filter(user_id=user.id).order_by('-id')
            paginator = Paginator(user_activities, PAGE_SIZE)
            page_number = self.request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            context["page_obj"] = page_obj
            context["total"] = user_activities.count()

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

        user_activities = Activity.objects.filter(user_id=user.id).order_by('-id')
        context["page_obj"] = user_activities[:PAGE_SIZE]
        context["total"] = user_activities.count()

        return context
