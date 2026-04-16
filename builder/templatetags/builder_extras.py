import json
from django import template

register = template.Library()

@register.filter(is_safe=True)
def tojson(value):
    """
    Safely serializes a Python value to a JSON string for inline JS use.
    Usage: {{ my_var|tojson|safe }}
    """
    return json.dumps(value)