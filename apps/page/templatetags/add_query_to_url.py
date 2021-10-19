from django import template
from django.utils.http import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def add_query_to_url(context, **kwargs):
    query = context['request'].GET.dict()
    path = context['request'].path
    query.update(kwargs)
    return path + '?' + urlencode(query)