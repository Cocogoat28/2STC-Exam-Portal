# at top of your views.py - ensure these imports exist (add any you don't already have)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.views.decorators.cache import never_cache
from django.db.models import Count
from .models import CandidateProfile
from reference.models import Trade
from .forms import CandidateRegistrationForm
from django.contrib import messages

from questions.models import QuestionPaper, Question, PaperQuestion, ExamSession
from results.models import CandidateAnswer

# other imports you already had
from django.http import FileResponse, Http404
import os, tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.pdfencrypt import StandardEncryption


@login_required
def candidate_dashboard(request):
    candidate_profile = get_object_or_404(CandidateProfile, user=request.user)
    exams_scheduled, upcoming_exams, completed_exams, results = [], [], [], []
    return render(request, "registration/dashboard.html", {
        "candidate": candidate_profile,
        "exams_scheduled": exams_scheduled,
        "upcoming_exams": upcoming_exams,
        "completed_exams": completed_exams,
        "results": results,
    })


def register_candidate(request):
    if request.method == "POST":
        form = CandidateRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect("login")
        else:
            print("Registration form invalid:", form.errors)
    else:
        form = CandidateRegistrationForm()
    return render(request, "registration/register_candidate.html", {"form": form})


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from questions.models import QuestionPaper, Question
from results.models import CandidateAnswer
from registration.models import CandidateProfile
from questions.models import PaperQuestion  # if this is where PaperQuestion lives

# registration/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from questions.models import Question, QuestionPaper, PaperQuestion
from results.models import CandidateAnswer
from registration.models import CandidateProfile
from django.views.decorators.cache import never_cache

from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.db.models import Count

@never_cache
@login_required
def exam_interface(request):
    """
    Starts (or resumes) an ExamSession for the logged-in candidate and serves
    the randomized questions assigned to that session.
    """
    candidate_profile = get_object_or_404(CandidateProfile, user=request.user)

    # Determine candidate trade (assumes CandidateProfile.trade is a FK to Trade)
    trade_obj = getattr(candidate_profile, "trade", None)

    # 1) Prefer a common/secondary paper if present (latest), else try trade-specific primary paper
    paper = QuestionPaper.objects.filter(is_common=True, is_active=True) \
        .annotate(num_qs=Count("paperquestion")).filter(num_qs__gt=0).order_by("-id").first()
    if not paper and trade_obj:
        paper = QuestionPaper.objects.filter(trade=trade_obj, is_common=False).order_by("-id").first()

    if not paper:
        messages.warning(request, "No exam papers are available for your trade. Please contact admin or try later.")
        return redirect("login")

    # 2) Try to find an existing session for this user + paper (resume) OR create a new randomized session
    session = ExamSession.objects.filter(paper=paper, user=request.user).order_by("-started_at").first()
    if not session:
        try:
            # For a common paper (is_common=True) we pass the candidate's trade so selection is trade-aware.
            session = paper.generate_for_candidate(user=request.user, trade=trade_obj)
        except ValidationError as e:
            print(f"Validation error generating exam session: {e}")
            return render(request, "registration/exam_not_started.html", {
                "message": f"Exam cannot be started: {e}"
            })
        except Exception as e:
            print(f"Unexpected error generating exam session: {e}")
            return render(request, "registration/exam_not_started.html", {
                "message": f"Unexpected error trying to start exam: {e}"
            })

    # ---------- NEW: Prevent reopening after submission ----------
    # Consider a session finished if completed_at is set or explicit answers exist for this candidate+paper
    session_finished = bool(session.completed_at)
    # answers_exist = CandidateAnswer.objects.filter(candidate=candidate_profile, paper=session.paper).exists()

    # If session finished OR answers already submitted -> do not allow the candidate to access the exam again.
    if session_finished:
        # If this is a POST (accidental double submit), ignore and redirect to success page:
        if request.method == "POST":
            # Optionally show a message
            messages.info(request, "Your exam has already been submitted. You cannot resubmit.")
            # Ensure user is logged out (you were logging them out on submit previously)
            try:
                logout(request)
            except Exception:
                pass
            return redirect("exam_success")

        # For GET requests, show a friendly page or redirect
        messages.info(request, "You have already submitted this exam. You cannot restart it.")
        # Render a page that tells the user they've already submitted, or redirect to exam_success
        # return render(request, "registration/exam_already_submitted.html", {"candidate": candidate_profile, "paper": session.paper})
        return redirect("exam_success")
    # ---------- END NEW guard ----------

    # 3) Get questions from the session (ExamQuestion objects)
    exam_questions_qs = session.questions  # uses ExamSession.questions property -> ordered ExamQuestion queryset
    # convert to a list of Question objects for template convenience
    questions = [eq.question for eq in exam_questions_qs if eq.question.is_active]

    duration_seconds = int(session.duration.total_seconds()) if session.duration else (int(paper.exam_duration.total_seconds()) if paper.exam_duration else 7200)

    # POST: candidate submitting answers (partial or final).
    if request.method == "POST":
        # Double-check again inside POST transaction in case of race conditions
        if session.completed_at:
            messages.info(request, "Your exam has already been submitted.")
            try:
                logout(request)
            except Exception:
                pass
            return redirect("exam_success")

        # Use atomic transaction for consistency
        with transaction.atomic():
            # Ensure user is submitting answers for the session's paper
            for key, value in request.POST.items():
                if key.startswith("question_"):
                    # format question_<id>
                    _, qid = key.split("_", 1)
                    try:
                        question = Question.objects.get(id=qid)
                    except Question.DoesNotExist:
                        continue

                    # link answer to candidate_profile and the session.paper
                    CandidateAnswer.objects.update_or_create(
                        candidate=candidate_profile,
                        paper=session.paper,
                        question=question,
                        defaults={"answer": value.strip() if isinstance(value, str) else value}
                    )

            # mark session finished so completed_at is set
            try:
                if hasattr(session, "finish") and callable(session.finish):
                    session.finish()
                else:
                    session.completed_at = timezone.now()
                    session.save(update_fields=["completed_at"])
            except Exception:
                # last-ditch attempt
                try:
                    session.completed_at = timezone.now()
                    session.save(update_fields=["completed_at"])
                except Exception:
                    # swallow to not block user; but log in real app
                    pass

        # End exam for this candidate: logout and redirect
        try:
            logout(request)
        except Exception:
            pass
        return redirect("exam_success")

    # GET: render exam interface
    return render(request, "registration/exam_interface.html", {
        "candidate": candidate_profile,
        "paper": session.paper,
        "session": session,
        "questions": questions,
        "duration_seconds": duration_seconds,
    })



# @login_required
# def exam_success(request):
#     return render(request, "registration/exam_success.html")


# views.py
from django.shortcuts import render
from django.views.decorators.cache import never_cache
def exam_success(request):
    # Your existing success view is fine; @never_cache adds no-store headers.
    return render(request, "registration/exam_success.html")

@never_cache
def exam_goodbye(request):
    # NEW: the goodbye view (non-cacheable)
    return render(request, "registration/exam_goodbye.html")

def export_answers_pdf(request, candidate_id):
    try:
        answers = CandidateAnswer.objects.filter(candidate_id=candidate_id).select_related(
            "candidate", "paper", "question"
        )
        if not answers.exists():
            raise Http404("No answers found for this candidate.")

        candidate = answers[0].candidate
        army_no = getattr(candidate, "army_no", candidate.user.username)
        candidate_name = candidate.user.get_full_name()

        filename = f"{army_no}_answers.pdf"
        tmp_path = os.path.join(tempfile.gettempdir(), filename)

        enc = StandardEncryption(
            userPassword=army_no,
            ownerPassword="sarthak",
            canPrint=1,
            canModify=0,
            canCopy=0,
            canAnnotate=0
        )

        c = canvas.Canvas(tmp_path, pagesize=A4, encrypt=enc)
        width, height = A4
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 1 * inch, "Candidate Answers Export")
        c.setFont("Helvetica", 12)
        c.drawString(1 * inch, height - 1.5 * inch, f"Army No: {army_no}")
        c.drawString(1 * inch, height - 1.8 * inch, f"Name: {candidate_name}")
        c.drawString(1 * inch, height - 2.1 * inch, f"Trade: {candidate.trade}")
        c.drawString(1 * inch, height - 2.4 * inch, f"Paper: {answers[0].paper.title}")

        y = height - 3 * inch
        c.setFont("Helvetica", 11)
        for idx, ans in enumerate(answers, start=1):
            question_text = (ans.question.text[:80] + "...") if len(ans.question.text) > 80 else ans.question.text
            c.drawString(1 * inch, y, f"Q{idx}: {question_text}")
            y -= 0.3 * inch
            c.drawString(1.2 * inch, y, f"Answer: {ans.answer}")
            y -= 0.5 * inch
            if y < 1.5 * inch:
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - 1 * inch

        c.save()
        return FileResponse(open(tmp_path, "rb"), as_attachment=True, filename=filename)

    except Exception as e:
        raise Http404(f"Error exporting candidate answers: {e}")
    



# views.py
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CandidateProfile  # adjust to your model

@login_required
def clear_shift_and_start_exam(request):
    candidate = get_object_or_404(CandidateProfile, user=request.user)
    candidate.shift = None  
    candidate.save()
    return redirect("exam_interface")
