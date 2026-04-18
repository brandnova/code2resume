from django import template
import json

register = template.Library()

@register.filter(name='tojson')
def tojson_filter(value):
    """
    Safely serializes a Python value to a JSON string for inline JS use.
    Usage: {{ my_var|tojson|safe }}
    """
    return json.dumps(value, ensure_ascii=False, default=str)