from django import template
import json

register = template.Library()

@register.filter(name='tojson')
def tojson_filter(value):
    """
    Safely serializes a Python value to a JSON string for inline JS use.
    Escapes </script> to prevent breaking out of script blocks.
    Usage: {{ my_var|tojson|safe }}
    """
    serialized = json.dumps(value, ensure_ascii=False, default=str)
    # Prevent </script> from terminating the enclosing script block
    serialized = serialized.replace('</', '<\\/')
    return serialized
