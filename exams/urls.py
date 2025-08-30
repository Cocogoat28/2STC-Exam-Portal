from django.urls import path
from . import views

urlpatterns = [
    # old
# path("upload_pdf/", views.upload_pdf, name="upload_pdf"),

# new
    # path("upload_dat/", views.upload_dat, name="upload_dat"),
    # path("candidates/", views.candidate_list, name="candidate_list"),
    # path("result/<int:candidate_id>/", views.candidate_result, name="candidate_result"),
    # path("export_excel/", views.export_results_excel, name="export_results_excel"),
]
