from .user import user_views
from .index import index_views
from .auth import auth_views
from .admin import setup_admin
from .forms import forms_views
from .dashboard import dashboard_views   # ← ADD THIS

views = [
    user_views,
    index_views,
    auth_views,
    forms_views,
    dashboard_views   # ← ADD THIS
]