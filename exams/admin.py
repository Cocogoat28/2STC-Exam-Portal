# admin.py
from __future__ import annotations
from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.http import HttpResponse, HttpResponseForbidden
from django.template.response import TemplateResponse
import time

from .models import Candidate, Question, Answer
from openpyxl import load_workbook, Workbook


# ------------ Excel helpers ------------

REQUIRED_COLS = {"army_no", "exam_type", "question", "answer"}
KNOWN_COLS = {
    "s_no", "name", "photo", "fathers_name", "dob", "trade", "army_no", "adhaar_no",  # Added trade
    "name_of_qualification", "duration_of_qualification", "credits", "nsqf_level",
    "training_center", "district", "state", "viva_1", "viva_2",
    "practical_1", "practical_2", "exam_type", "question",
    "answer", "correct_answer", "max_marks",
}


def _normalize_header(val: str) -> str:
    return (
        (val or "")
        .strip()
        .lower()
        .replace(".", "_")
        .replace(" ", "_")
    )


def _read_rows_from_excel(file):
    wb = load_workbook(file, data_only=True)
    ws = wb.worksheets[0]

    headers = [_normalize_header(c.value) for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=False))]
    header_index = {h: idx for idx, h in enumerate(headers) if h}

    missing = REQUIRED_COLS - set(header_index)
    if missing:
        raise ValueError(f"Missing required columns in Excel: {', '.join(missing)}")

    for row in ws.iter_rows(min_row=2, values_only=True):
        data = {}
        for key, idx in header_index.items():
            data[key] = row[idx]
        yield data


def _get_or_create_question(exam_type, text, correct, max_marks):
    q = Question.objects.filter(exam_type=exam_type, question=text).first()
    if q is None:
        q = Question.objects.create(
            exam_type=exam_type,
            question=text,
            correct_answer=correct or "",
            max_marks=max_marks or 0,
        )
    return q


# ------------ Custom Admins ------------

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    change_list_template = "admin/exams/candidate/change_list.html"
    change_form_template = "admin/exams/candidate/change_form.html"
    list_display = ("army_no", "name", "trade", "total_primary", "total_secondary", "grand_total")  # Added trade
    list_filter = ("trade", "district", "state")  # Added trade filter
    search_fields = ("army_no", "name", "fathers_name", "district", "state", "trade")  # Added trade

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("import-excel/", self.admin_site.admin_view(self.import_excel_view),
                 name="exams_candidate_import_excel"),
            path("export-results-excel/", self.admin_site.admin_view(self.export_results_excel_view),
                 name="exams_export_results_excel"),
            path("<int:candidate_id>/save-grades/", self.admin_site.admin_view(self.save_grades_view),
                 name="exams_candidate_save_grades"),
            path("<int:candidate_id>/grade-answers/", self.admin_site.admin_view(self.grade_answers_view),
                 name="exams_candidate_grade_answers"),
        ]
        return custom + urls

    # ---------- Candidate change form ----------
    def change_view(self, request, object_id, form_url="", extra_context=None):
        cand = Candidate.objects.get(pk=object_id)
        answers = Answer.objects.filter(candidate=cand).select_related("question")

        primary = [a for a in answers if a.question.exam_type.lower() == "primary"]
        secondary = [a for a in answers if a.question.exam_type.lower() == "secondary"]

        extra_context = extra_context or {}
        extra_context["primary_answers"] = primary
        extra_context["secondary_answers"] = secondary
        extra_context["viva_total"] = cand.viva_1 + cand.viva_2
        extra_context["practical_total"] = cand.practical_1 + cand.practical_2
        extra_context["show_grade_button"] = True
        
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    # ---------- Grade Answers View ----------
    def grade_answers_view(self, request, candidate_id):
        if not request.user.has_perm('exams.change_answer'):
            return HttpResponseForbidden("You don't have permission to grade answers")
        
        cand = Candidate.objects.get(pk=candidate_id)
        answers = Answer.objects.filter(candidate=cand).select_related("question")
        
        # Separate answers by exam type
        primary_answers = [a for a in answers if a.question.exam_type.lower() == "primary"]
        secondary_answers = [a for a in answers if a.question.exam_type.lower() == "secondary"]
        
        if request.method == "POST":
            # Process the form submission
            for answer in answers:
                field_name = f"marks_{answer.id}"
                if field_name in request.POST:
                    try:
                        new_marks = int(request.POST[field_name])
                        if 0 <= new_marks <= answer.question.max_marks:
                            answer.marks_obt = new_marks
                            answer.save()
                    except ValueError:
                        pass
            
            # Force refresh of the candidate object to ensure latest data
            cand = Candidate.objects.get(pk=candidate_id)
            
            self.message_user(request, "Grades updated successfully", level=messages.SUCCESS)
            # Add a cache-busting parameter to the redirect URL
            return redirect(f"{reverse('admin:exams_candidate_change', args=[candidate_id])}?t={time.time()}")
        
        primary_total_obtained = sum(a.marks_obt for a in primary_answers)
        primary_total_max = sum(a.question.max_marks for a in primary_answers)
        secondary_total_obtained = sum(a.marks_obt for a in secondary_answers)
        secondary_total_max = sum(a.question.max_marks for a in secondary_answers)
        
        context = {
            **self.admin_site.each_context(request),
            "title": f"Grade Answers - {cand.name} ({cand.army_no}) - {cand.trade}",  # Added trade
            "candidate": cand,
            "primary_answers": primary_answers,
            "secondary_answers": secondary_answers,
            "primary_total_obtained": primary_total_obtained,
            "primary_total_max": primary_total_max,
            "secondary_total_obtained": secondary_total_obtained,
            "secondary_total_max": secondary_total_max,
            "opts": self.model._meta,
        }
        
        return TemplateResponse(request, "admin/exams/candidate/grade_answers.html", context)

    def save_grades_view(self, request, candidate_id):
        cand = Candidate.objects.get(pk=candidate_id)
        if request.method == "POST":
            for ans in Answer.objects.filter(candidate=cand):
                field_name = f"marks_{ans.id}"
                if field_name in request.POST:
                    try:
                        new_marks = int(request.POST[field_name])
                        ans.marks_obt = new_marks
                        ans.save()
                    except ValueError:
                        pass
            self.message_user(request, "Grades updated", level=messages.SUCCESS)
        return redirect("admin:exams_candidate_change", cand.id)

    # ---------- Import Excel ----------
    def import_excel_view(self, request):
        if request.method == "POST" and request.FILES.get("excel"):
            excel_file = request.FILES["excel"]
            created_candidates = updated_candidates = 0
            created_answers = updated_answers = 0
            created_questions = 0

            try:
                with transaction.atomic():
                    seen_questions_before = set(Question.objects.values_list("id", flat=True))
                    for row in _read_rows_from_excel(excel_file):
                        army = (row.get("army_no") or "").strip()
                        if not army:
                            continue

                        cand_defaults = {
                            "s_no": row.get("s_no") or 0,
                            "name": row.get("name") or "",
                            "fathers_name": row.get("fathers_name") or "",
                            "dob": row.get("dob") or None,
                            "trade": row.get("trade") or "",  # Added trade
                            "adhaar_no": row.get("adhaar_no") or "",
                            "name_of_qualification": row.get("name_of_qualification") or "",
                            "duration_of_qualification": row.get("duration_of_qualification") or "",
                            "credits": row.get("credits") or 0,
                            "nsqf_level": row.get("nsqf_level") or 0,
                            "training_center": row.get("training_center") or "",
                            "district": row.get("district") or "",
                            "state": row.get("state") or "",
                            "viva_1": row.get("viva_1") or 0,
                            "viva_2": row.get("viva_2") or 0,
                            "practical_1": row.get("practical_1") or 0,
                            "practical_2": row.get("practical_2") or 0,
                        }
                        cand, created = Candidate.objects.get_or_create(
                            army_no=army, defaults=cand_defaults
                        )
                        if not created:
                            for k, v in cand_defaults.items():
                                if v and getattr(cand, k) != v:
                                    setattr(cand, k, v)
                            cand.save()
                            updated_candidates += 1
                        else:
                            created_candidates += 1

                        q = _get_or_create_question(
                            exam_type=row.get("exam_type") or "",
                            text=row.get("question") or "",
                            correct=row.get("correct_answer") or "",
                            max_marks=row.get("max_marks") or 0,
                        )
                        if q.id not in seen_questions_before:
                            created_questions += 1
                            seen_questions_before.add(q.id)

                        ans_text = (row.get("answer") or "").strip()
                        marks = row.get("marks_obt") or 0

                        ans, a_created = Answer.objects.get_or_create(
                            candidate=cand, question=q,
                            defaults={"answer": ans_text, "marks_obt": int(marks)},
                        )
                        if a_created:
                            created_answers += 1
                        else:
                            if ans.answer != ans_text or ans.marks_obt != int(marks):
                                ans.answer = ans_text
                                ans.marks_obt = int(marks)
                                ans.save()
                                updated_answers += 1

                self.message_user(
                    request,
                    (
                        f"Import complete. "
                        f"Candidates: +{created_candidates} / updated {updated_candidates}. "
                        f"Questions: +{created_questions}. "
                        f"Answers: +{created_answers} / updated {updated_answers}."
                    ),
                    level=messages.SUCCESS,
                )
                return redirect("admin:exams_candidate_changelist")

            except Exception as e:
                self.message_user(request, f"Import failed: {e}", level=messages.ERROR)

        ctx = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Import candidates & answers from Excel",
        }
        return render(request, "admin/exams/candidate/import_excel.html", ctx)

    # ---------- Export ----------
    def export_results_excel_view(self, request):
        wb = Workbook()
        ws = wb.active
        ws.title = "Results"

        headers = [
            "s_no", "name", "fathers_name", "dob", "trade", "army_no", "adhaar_no",  # Added trade
            "name_of_qualification", "duration_of_qualification", "credits", "nsqf_level",
            "training_center", "district", "state", "viva_1", "viva_2", "practical_1", "practical_2",
            "exam_type", "question", "answer", "correct_answer", "max_marks", "marks_obt",
        ]
        ws.append(headers)

        for ans in Answer.objects.select_related("candidate", "question").all().order_by(
            "candidate__army_no", "question__id"
        ):
            c, q = ans.candidate, ans.question
            ws.append([
                c.s_no, c.name, c.fathers_name, c.dob, c.trade, c.army_no, c.adhaar_no,  # Added trade
                c.name_of_qualification, c.duration_of_qualification, c.credits, c.nsqf_level,
                c.training_center, c.district, c.state, c.viva_1, c.viva_2,
                c.practical_1, c.practical_2,
                q.exam_type, q.question, ans.answer, q.correct_answer, q.max_marks, ans.marks_obt,
            ])

        resp = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        resp["Content-Disposition"] = 'attachment; filename="results.xlsx"'
        wb.save(resp)
        return resp

    # ---------- Totals ----------
    def total_primary(self, obj):
        return sum(a.marks_obt for a in obj.answer_set.filter(question__exam_type__iexact="primary"))

    def total_secondary(self, obj):
        return sum(a.marks_obt for a in obj.answer_set.filter(question__exam_type__iexact="secondary"))

    def grand_total(self, obj):
        viva_practical = obj.viva_1 + obj.viva_2 + obj.practical_1 + obj.practical_2
        return self.total_primary(obj) + self.total_secondary(obj) + viva_practical


# remove Question from sidebar
try:
    admin.site.unregister(Question)
except admin.sites.NotRegistered:
    pass