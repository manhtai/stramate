from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View
from django import template
from django.utils.http import urlencode

from apps.activity.models import Activity, Analytic

GUEST_PAGE_SIZE = 3
OWNER_PAGE_SIZE = 10
register = template.Library()



class IndexView(View):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy("page:profile", args=(self.request.user.username,)))
        return render(self.request, "page/index.html")


class ProfileView(TemplateView):
    template_name = "page/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        username = kwargs.get('username')
        user = get_object_or_404(User, username=username)

        stats = {}
        analytic = Analytic.objects.filter(user_id=user.id).order_by('date').last()
        if analytic:
            stats = analytic.heatmap
            stats["fitness"] = analytic.fitness

        user_activities = Activity.objects.filter(
            user_id=user.id
        ).order_by('-start_date')

        context.update(stats)
        context["username"] = user.username

        if self.request.user.is_authenticated and self.request.user == user:
            q = self.request.GET.get('q')
            if q:
                user_activities = user_activities.filter(
                    Q(name__icontains=q) | Q(start_location__icontains=q)
                )

            page_number = self.request.GET.get('page')
            paginator = Paginator(user_activities, OWNER_PAGE_SIZE)
            page_obj = paginator.get_page(page_number)

            context["page_obj"] = page_obj
        else:
            context["page_obj"] = user_activities[:GUEST_PAGE_SIZE]

        return context
