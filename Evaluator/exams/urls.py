from django.contrib import admin
from django.urls import path
from .views import export_evaluation_short_url

urlpatterns = [
    # Short URL that redirects to the model-scoped admin view
    path(
        "admin/exams/export-evaluation/",
        admin.site.admin_view(export_evaluation_short_url),
        name="export_evaluation_short_url",
    ),
]
