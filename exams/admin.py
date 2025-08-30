# your_app/admin.py
import gzip
import json
import decimal
from django import forms
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.contrib import admin, messages
from django.utils import timezone
from django.template.response import TemplateResponse
from django.http import HttpResponse
import openpyxl
from openpyxl.utils import get_column_letter
from django.utils.html import format_html
from django.db.models import Max

from .models import Candidate, Question, Answer

# ---------------------------
# Helper utilities
# ---------------------------
def _safe_float(v):
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        try:
            return float(str(v))
        except Exception:
            return None


def _find_or_create_question(item, create_if_missing=True):
    """
    Find a Question for an answer item from the exported JSON.
    Order:
      1) pk lookup using question_id
      2) exact text match
      3) partial text match (first)
      4) number lookup (Question.number)
      5) optionally create Question (safe) so answers can be stored
    Returns Question instance or None.
    """
    q = None

    # 1) pk lookup
    qid = item.get("question_id") or item.get("questionNumber") or item.get("question_number")
    if qid is not None:
        try:
            q = Question.objects.filter(pk=int(qid)).first()
        except Exception:
            q = None

    # 2) exact text
    if q is None:
        text = item.get("question_text") or item.get("question") or item.get("questionText")
        if text:
            q = Question.objects.filter(text__iexact=text).first()

    # 3) partial text
    if q is None and text:
        q = Question.objects.filter(text__icontains=text[:60]).first()

    # 4) number lookup
    if q is None:
        try:
            qnum = item.get("question_number") or item.get("question_no") or item.get("number")
            if qnum is None and qid is not None:
                # qid might actually be the question.number in some exports
                qnum = qid
            if qnum is not None:
                q = Question.objects.filter(number=int(qnum)).first()
        except Exception:
            q = None

    # 5) create if still not found and allowed
    if q is None and create_if_missing:
        # Build safe create payload
        create_payload = {}
        create_text = item.get("question_text") or item.get("question") or item.get("questionText") or f"Imported question ({qid})"
        create_payload["text"] = create_text

        # choose a sensible number: prefer qnum if valid, else max+1
        try:
            if 'qnum' in locals() and qnum:
                create_payload["number"] = int(qnum)
            else:
                max_num = Question.objects.aggregate(max_num=Max("number"))["max_num"] or 0
                create_payload["number"] = (int(max_num) + 1)
        except Exception:
            # fallback
            create_payload["number"] = None

        # create the question
        try:
            # If number is None, omit it
            if create_payload["number"] is None:
                q = Question.objects.create(text=create_payload["text"])
            else:
                q = Question.objects.create(number=create_payload["number"], text=create_payload["text"])
            # Logging (visible in runserver console)
            print(f"[IMPORT] Created Question id={q.pk} number={getattr(q,'number',None)} text={q.text[:60]!r}")
        except Exception as e:
            print(f"[IMPORT] Failed to create Question for item {item!r} -> {e}")
            q = None

    return q


# ---------------------------
# CandidateAdmin
# ---------------------------
@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = (
        "army_number", "name", "category", "paper",
        "viva_marks", "practical_marks", "objective_marks",
        "total_marks", "admin_actions"
    )
    list_editable = ("viva_marks", "practical_marks")
    search_fields = ("army_number", "name", "category", "paper")
    # (optional) change_list template path if you added a custom one; otherwise remove/comment:
    change_list_template = "admin/exams/candidate/change_list.html"

    actions = ["export_results_excel_action"]

    # Add custom URLs (import, grade, export results)
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "import-dat/",
                self.admin_site.admin_view(self.import_dat_view),
                name="yourapp_candidate_import_dat"
            ),
            path(
                "grade/<int:pk>/",
                self.admin_site.admin_view(self.grade_candidate_view),
                name="yourapp_candidate_grade"
            ),
            path(
                "export-results-excel/",
                self.admin_site.admin_view(self.export_results_excel),
                name="yourapp_export_results_excel"
            ),
        ]
        return custom + urls

    # action for selected rows export
    def export_results_excel_action(self, request, queryset):
        return self._generate_results_excel(queryset)

    export_results_excel_action.short_description = "Export selected results to Excel"

    # column to show per-row action links (Grade)
    def admin_actions(self, obj):
        grade_url = reverse("admin:yourapp_candidate_grade", args=[obj.pk])
        return format_html('<a class="button" href="{}">Grade</a>', grade_url)

    admin_actions.short_description = "Actions"

    # ---------------------------
    # Import endpoint
    # ---------------------------
    def import_dat_view(self, request):
        """
        Upload gzipped JSON `.dat` file and import candidates + answers.
        This importer:
         - creates/updates Candidate by army_number
         - finds or creates Questions and creates Answers attached to candidate+question
        """
        if request.method == "POST":
            uploaded = request.FILES.get("datfile")
            if not uploaded:
                messages.error(request, "Please choose a .dat file to upload.")
                return redirect(".")

            try:
                raw = uploaded.read()
                decompressed = gzip.decompress(raw)
                payload = json.loads(decompressed.decode("utf-8"))
            except Exception as e:
                messages.error(request, f"Failed to read/parse file: {e}")
                return redirect("..")

            created_candidates = 0
            updated_candidates = 0
            created_answers = 0
            updated_answers = 0
            created_questions = 0

            # iterate candidates
            for cand_item in payload.get("candidates", []):
                # the exporter might use "army_no" or "army_number"
                army_no = cand_item.get("army_no") or cand_item.get("army_number") or cand_item.get("armyNumber") or cand_item.get("army")
                if not army_no:
                    continue

                # find or create candidate by army_number
                defaults = {}
                if cand_item.get("name"):
                    defaults["name"] = cand_item.get("name")
                if cand_item.get("category"):
                    defaults["category"] = cand_item.get("category")
                if cand_item.get("paper") or cand_item.get("paper_title"):
                    defaults["paper"] = cand_item.get("paper") or cand_item.get("paper_title")

                v = cand_item.get("viva_marks") or cand_item.get("viva")
                p = cand_item.get("practical_marks") or cand_item.get("practical")
                if v is not None:
                    vf = _safe_float(v)
                    if vf is not None:
                        defaults["viva_marks"] = int(round(vf))
                if p is not None:
                    pf = _safe_float(p)
                    if pf is not None:
                        defaults["practical_marks"] = int(round(pf))

                candidate_obj, created = Candidate.objects.get_or_create(
                    army_number=str(army_no),
                    defaults=defaults
                )
                if created:
                    created_candidates += 1
                else:
                    updated = False
                    for fld in ("name", "category", "paper"):
                        if cand_item.get(fld) and getattr(candidate_obj, fld, None) != cand_item.get(fld):
                            setattr(candidate_obj, fld, cand_item.get(fld))
                            updated = True
                    if v is not None:
                        vf = _safe_float(v)
                        if vf is not None and candidate_obj.viva_marks != int(round(vf)):
                            candidate_obj.viva_marks = int(round(vf))
                            updated = True
                    if p is not None:
                        pf = _safe_float(p)
                        if pf is not None and candidate_obj.practical_marks != int(round(pf)):
                            candidate_obj.practical_marks = int(round(pf))
                            updated = True
                    if updated:
                        candidate_obj.save()
                        updated_candidates += 1

                # import answers array
                for ans_item in cand_item.get("answers", []):
                    # Try find / create question
                    q = _find_or_create_question(ans_item, create_if_missing=True)
                    if not q:
                        # If still not found/created, log and skip
                        print(f"[IMPORT] Could not find or create Question for answer item: {ans_item!r}")
                        continue

                    # create / update answer
                    answer_text = ans_item.get("answer") or ans_item.get("answer_text") or ans_item.get("response") or ""
                    try:
                        answer_obj, ans_created = Answer.objects.update_or_create(
                            candidate=candidate_obj,
                            question=q,
                            defaults={"answer_text": answer_text}
                        )
                        if ans_created:
                            created_answers += 1
                        else:
                            updated_answers += 1
                    except Exception as e:
                        print(f"[IMPORT] Failed to create/update Answer for candidate {candidate_obj}: {e}")
                        continue

            messages.success(
                request,
                f"Import finished. Candidates created: {created_candidates}, updated: {updated_candidates}. "
                f"Answers created: {created_answers}, updated: {updated_answers}."
            )
            return redirect("..")

        context = dict(
            self.admin_site.each_context(request),
            title="Import candidates (.dat)",
        )
        return TemplateResponse(request, "admin/exams/candidate/import_dat.html", context)

    # ---------------------------
    # Grade candidate view
    # ---------------------------
    def grade_candidate_view(self, request, pk):
        candidate = Candidate.objects.filter(pk=pk).first()
        if not candidate:
            messages.error(request, "Candidate not found.")
            return redirect("..")

        # fetch all answers (these should now be created by importer)
        answers_qs = Answer.objects.filter(candidate=candidate).select_related("question").order_by("question__number")

        if request.method == "POST":
            v = request.POST.get("viva_marks")
            p = request.POST.get("practical_marks")
            saved_count = 0
            if v is not None:
                try:
                    candidate.viva_marks = int(float(v))
                except Exception:
                    pass
            if p is not None:
                try:
                    candidate.practical_marks = int(float(p))
                except Exception:
                    pass
            candidate.save()

            for ans in answers_qs:
                key = f"mark_{ans.pk}"
                if key in request.POST:
                    raw = request.POST.get(key)
                    try:
                        val = int(float(raw))
                    except Exception:
                        val = None
                    if val is not None:
                        ans.marks_awarded = val
                        ans.save(update_fields=["marks_awarded"])
                        saved_count += 1

            messages.success(request, f"Saved marks for {saved_count} answers and updated viva/practical.")
            return redirect(reverse("admin:yourapp_candidate_grade", args=[pk]))

        context = dict(
            self.admin_site.each_context(request),
            title=f"Grade {candidate.army_number} — {candidate.name}",
            candidate=candidate,
            answers=answers_qs,
        )
        return TemplateResponse(request, "admin/exams/candidate/grade_candidate.html", context)

    # ---------------------------
    # Results Excel export (all or selected)
    # ---------------------------
    def _generate_results_excel(self, queryset):
        """
        Build an Excel workbook with candidate results:
        Army Number, Name, Category, Paper, Viva, Practical, ObjectiveMarks, Total, Percentage
        """
        from django.conf import settings
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Results"

        headers = [
            "Army Number", "Name", "Category", "Paper",
            "Viva Marks", "Practical Marks", "Objective Marks",
            "Total Marks", "Percentage"
        ]
        for cidx, h in enumerate(headers, start=1):
            ws.cell(row=1, column=cidx).value = h

        row = 2
        for c in queryset:
            obj_marks = sum((a.marks_awarded or 0) for a in c.answers.all())
            viva = c.viva_marks or 0
            prac = c.practical_marks or 0
            total = obj_marks + viva + prac

            max_total = getattr(settings, "EXAM_MAX_TOTAL", None)
            if max_total:
                try:
                    pct = round((total / float(max_total)) * 100.0, 2)
                except Exception:
                    pct = None
            else:
                pct = None

            row_values = [
                c.army_number,
                c.name,
                c.category,
                c.paper,
                viva,
                prac,
                obj_marks,
                total,
                pct
            ]
            for idx, val in enumerate(row_values, start=1):
                ws.cell(row=row, column=idx).value = val
            row += 1

        for i in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(i)].width = 18

        output = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        ts = timezone.now().strftime("%Y%m%d%H%M%S")
        output["Content-Disposition"] = f'attachment; filename="results_{ts}.xlsx"'
        wb.save(output)
        return output

    def export_results_excel(self, request):
        qs = self.get_queryset(request)
        return self._generate_results_excel(qs)
