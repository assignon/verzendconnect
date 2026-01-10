"""
Core template tags for VerzendConnect.
"""
from django import template
from apps.core.models import Costs

register = template.Library()


@register.simple_tag
def get_costs():
    """Get costs settings."""
    return Costs.get_costs()

