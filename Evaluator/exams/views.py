# exams/views.py
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def export_evaluation_short_url(request):
    # Redirect to the actual model-scoped admin view
    return redirect("admin:exams_export_evaluation_page")
