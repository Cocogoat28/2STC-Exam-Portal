from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from .models import CandidateProfile
from reference.models import Trade
from .forms import CandidateRegistrationForm
from django.contrib import messages
from questions.models import QuestionPaper, Question, PaperQuestion
from results.models import CandidateAnswer
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

@never_cache
@login_required
def exam_interface(request):
    candidate_profile = get_object_or_404(CandidateProfile, user=request.user)

    # if not candidate_profile.can_start_exam:
    #     return render(request, "registration/exam_not_started.html", {
    #         "message": "You cannot start the exam yet."
    #     })

    

    # Step 1: Try to fetch trade-specific paper

    part_a = QuestionPaper.objects.filter(is_common=True).order_by('-id').first()

    trade_obj=None
    if not part_a:
        trade_obj = candidate_profile.trade
        part_a = QuestionPaper.objects.filter(trade=trade_obj, is_common=False).order_by('-id').first()

    # Step 2: Fallback to common if no trade-specific exists
    # Step 3: Final fallback
    if not part_a:
        return render(request, "registration/exam_not_started.html", {
            "message": "No exam papers are available for your trade."
        })

    # Step 4: Fetch questions through PaperQuestion
    paper_questions = (PaperQuestion.objects
                       .filter(paper=part_a)
                       .select_related("question")
                       .order_by("order", "id"))
    questions = [pq.question for pq in paper_questions if pq.question.is_active]

    duration_seconds = int(part_a.exam_duration.total_seconds()) if part_a.exam_duration else 7200

    if request.method == "POST":
        paper_id = request.POST.get("paper_id")
        paper = get_object_or_404(QuestionPaper, id=paper_id)

        # Save/update answers — category is derived later from paper.is_common
        for key, value in request.POST.items():
            if key.startswith("question_"):
                qid = key.split("_", 1)[1]
                try:
                    question = Question.objects.get(id=qid)
                except Question.DoesNotExist:
                    continue

                CandidateAnswer.objects.update_or_create(
                    candidate=candidate_profile,
                    paper=paper,
                    question=question,
                    defaults={"answer": value.strip() if isinstance(value, str) else value}
                )
        logout(request)

        return redirect("exam_success")

    return render(request, "registration/exam_interface.html", {
        "candidate": candidate_profile,
        "part_a": part_a,
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
