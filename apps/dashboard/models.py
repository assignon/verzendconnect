from django.db import models

# Dashboard app uses data from other models for analytics.
# No additional models needed here, but we could add:
# - Saved reports
# - Dashboard preferences
# - Scheduled report configurations

# This file is intentionally minimal - analytics are computed from
# Order, Product, and User models in views/services.

