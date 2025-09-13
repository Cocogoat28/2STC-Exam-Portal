# questions/models.py
from django.db import models, transaction
from django.core.exceptions import ValidationError
from reference.models import Trade
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
import re

User = get_user_model()

def validate_dat_file(value):
    """Validate that only .dat files are uploaded"""
    if not value.name.lower().endswith(".dat"):
        raise ValidationError("Only .dat files are allowed.")

# ---------------------------
# Hard-coded trade & distribution config (edit here to change defaults)
# ---------------------------
# YOUR 17 trades (keys are normalized to uppercase and single spaces)
HARD_CODED_TRADE_CONFIG = {
    # Format: "TRADE NAME": {"total_questions": int, "part_distribution": {"A":n, "B":n, "C":n, "D":n, "E":n, "F":n}}
    "TTC": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "OCC": {
        "total_questions": 54,
        "part_distribution": {"A": 20, "B": 0, "C": 5, "D": 15, "E": 4, "F": 10},
    },
    "DTMN": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "EFS": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "DMV": {
        "total_questions": 54,
        "part_distribution": {"A": 20, "B": 0, "C": 5, "D": 15, "E": 4, "F": 10},
    },
    "LMN": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "CLK SD": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "STEWARD": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "WASHERMAN": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "HOUSE KEEPER": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "CHEFCOM": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "MESS KEEPER": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "SKT": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "MUSICIAN": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "ARTSN WW": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "HAIR DRESSER": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
    "SP STAFF": {
        "total_questions": 43,
        "part_distribution": {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
    },
}

# Default common distribution used when a Secondary paper is generated with NO trade provided.
# This sums to 43.
# HARD_CODED_COMMON_DISTRIBUTION = {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10},
HARD_CODED_COMMON_DISTRIBUTION = {"A": 15, "B": 0, "C": 5, "D": 10, "E": 3, "F": 10}
# Helper to normalize trade names for lookup.
def _normalize_trade_name(name: str) -> str:
    if not name:
        return ""
    # collapse whitespace and uppercase
    return re.sub(r"\s+", " ", name.strip()).upper()

# ------------------------------
# Models (keeps your original structure, adds ExamSession/ExamQuestion)
# ------------------------------
class Question(models.Model):
    class Part(models.TextChoices):
        A = "A", "Part A - MCQ (Single Choice)"
        B = "B", "Part B - MCQ (Multiple Choice)"
        C = "C", "Part C - Short answer (20-30 words)"
        D = "D", "Part D - Fill in the blanks"
        E = "E", "Part E - Long answer (100-120 words)"
        F = "F", "Part F - True/False"

    text = models.TextField()
    part = models.CharField(max_length=1, choices=Part.choices, default="A")
    marks = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    options = models.JSONField(blank=True, null=True)
    correct_answer = models.JSONField(blank=True, null=True)
    trade = models.ForeignKey(Trade, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "QP Delete"
        verbose_name_plural = "3 QP Delete"

    def __str__(self):
        return f"[{self.get_part_display()}] {self.text[:60]}..."


class QuestionUpload(models.Model):
    file = models.FileField(upload_to="uploads/questions/", validators=[validate_dat_file])
    uploaded_at = models.DateTimeField(auto_now_add=True)
    decryption_password = models.CharField(max_length=255, default="default123")
    trade = models.ForeignKey(
        Trade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If set, all imported questions will be tagged with this trade."
    )

    class Meta:
        verbose_name = "QP Upload"
        verbose_name_plural = "1 QP Upload"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file.name} ({self.uploaded_at.strftime('%Y-%m-%d %H:%M')})"


class QuestionPaper(models.Model):
    PAPER_TYPE_CHOICES = [
        ("Primary", "Primary"),
        ("Secondary", "Secondary"),
    ]

    question_paper = models.CharField(
        max_length=20,
        choices=PAPER_TYPE_CHOICES,
        default="Primary",
        help_text="Select whether this is a Primary or Secondary paper"
    )
    is_active = models.BooleanField(default=False,null=True)
    is_common = models.BooleanField(default=False, editable=False)

    trade = models.ForeignKey(Trade, on_delete=models.PROTECT, null=True, blank=True)
    exam_duration = models.DurationField(
        null=True,
        blank=True,
        default=timedelta(hours=3),
        help_text="Enter exam duration in format HH:MM:SS (e.g., 01:30:00 for 1h30m)"
    )
    qp_assign = models.ForeignKey(QuestionUpload, on_delete=models.SET_NULL, null=True, blank=True)
    questions = models.ManyToManyField("Question", through="PaperQuestion")

    # Optional (admin editable) override. If empty, hard-coded values will be used.
    part_distribution = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional manual override per paper. If empty, code uses hard-coded trade config."
    )

    class Meta:
        verbose_name = "QP Mapping"
        verbose_name_plural = "2 QP Mappings"
        ordering = ['-id']

    def save(self, *args, **kwargs):
        if self.question_paper == "Secondary":
            self.is_common = True
            self.trade = None  # ensure Secondary is common
        else:
            self.is_common = False
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from .models import PaperQuestion, Question  # local import to avoid circular import
        q_ids = list(PaperQuestion.objects.filter(paper=self).values_list("question_id", flat=True).distinct())
        for qid in q_ids:
            other_rel_count = PaperQuestion.objects.filter(question_id=qid).exclude(paper=self).count()
            if other_rel_count == 0:
                try:
                    Question.objects.filter(id=qid).delete()
                except Exception:
                    pass
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.question_paper

    # ------------------------------
    # Helper methods for using hard-coded config
    # ------------------------------
    def _validate_distribution(self, dist):
        if not isinstance(dist, dict):
            raise ValidationError("part_distribution must be a dict mapping part letters to counts.")
        allowed = {p.value for p in Question.Part}
        for k, v in dist.items():
            if k not in allowed:
                raise ValidationError(f"Invalid part '{k}'. Allowed: {allowed}")
            if not isinstance(v, int) or v < 0:
                raise ValidationError(f"Count for part {k} must be non-negative integer.")

    def _get_hardcoded_for_trade(self, trade_obj):
        """
        Return (part_distribution_dict, total_questions) or None.
        Matching tries: Trade.name, Trade.code, Trade.slug (if present) normalized.
        """
        if not trade_obj:
            return None
        # try several likely fields
        possible = []
        for fld in ("name", "code", "slug"):
            val = getattr(trade_obj, fld, None)
            if val:
                possible.append(_normalize_trade_name(str(val)))
        # remove duplicates preserving order
        seen = set()
        possible = [x for x in possible if not (x in seen or seen.add(x))]

        for key in possible:
            cfg = HARD_CODED_TRADE_CONFIG.get(key)
            if cfg:
                # return a copy so callers can mutate safely
                return cfg["part_distribution"].copy(), int(cfg["total_questions"])
            # also try removing spaces
            cfg = HARD_CODED_TRADE_CONFIG.get(key.replace(" ", ""))
            if cfg:
                return cfg["part_distribution"].copy(), int(cfg["total_questions"])
        return None

    # def generate_for_candidate(self, user: User, trade: Trade = None, shuffle_within_parts: bool = True):
    #     """
    #     Create an ExamSession for the given user and populate it with randomly selected questions
    #     according to the paper's distribution OR hard-coded trade config if paper.part_distribution is empty.

    #     Behavior:
    #     - If self.part_distribution is set -> use it.
    #     - Else if self.is_common -> use HARD_CODED_COMMON_DISTRIBUTION (43 qns) UNLESS paper.part_distribution overrides.
    #     - Else try to find HARD_CODED_TRADE_CONFIG for the effective trade (self.trade or passed trade).
    #     - If still not found -> fallback to HARD_CODED_COMMON_DISTRIBUTION.
    #     """
    #     from .models import Question, ExamSession, ExamQuestion  # local import
    #     import random

    #     # choose effective trade:
    #     # For a common (Secondary) paper we purposely IGNORE the passed-in trade so common papers
    #     # always use the common default distribution unless overridden by part_distribution.
    #     if self.is_common:
    #         effective_trade = None
    #     else:
    #         # For primary papers prefer self.trade (paper-level) then the passed trade argument.
    #         effective_trade = self.trade or trade

    #     # choose distribution: explicit -> common-without-trade -> hard-coded trade -> fallback common
    #     if self.part_distribution:
    #         chosen_distribution = self.part_distribution.copy()
    #     else:
    #         # If common paper (Secondary) use global common default (43).
    #         if self.is_common:
    #             chosen_distribution = HARD_CODED_COMMON_DISTRIBUTION.copy()
    #         else:
    #             # try trade-config lookup (effective_trade may be None)
    #             hc = self._get_hardcoded_for_trade(effective_trade)
    #             if hc:
    #                 chosen_distribution = hc[0]
    #             else:
    #                 # fallback to global common distribution
    #                 chosen_distribution = HARD_CODED_COMMON_DISTRIBUTION.copy()

    #     # validate distribution
    #     self._validate_distribution(chosen_distribution)

    #     # Build the session and pick random questions per part
    #     with transaction.atomic():
    #         session = ExamSession.objects.create(
    #             paper=self,
    #             user=user,
    #             trade=effective_trade,
    #             started_at=timezone.now(),
    #             duration=self.exam_duration
    #         )

    #         order_counter = 1
    #         for part_letter, count in (chosen_distribution or {}).items():
    #             cnt = int(count)
    #             if cnt <= 0:
    #                 continue

    #             qset = Question.objects.filter(is_active=True, part=part_letter)
    #             if effective_trade is not None:
    #                 qset = qset.filter(trade=effective_trade)

    #             available_count = qset.count()
    #             if available_count < cnt:
    #                 # fallback: allow questions from any trade for this part to fulfill count (safer)
    #                 qset = Question.objects.filter(is_active=True, part=part_letter)

    #             chosen = list(qset.order_by('?')[:cnt])
    #             if len(chosen) < cnt:
    #                 raise ValidationError(
    #                     f"Not enough active questions for part {part_letter}. Requested {cnt}, found {len(chosen)}."
    #                 )

    #             if shuffle_within_parts:
    #                 random.shuffle(chosen)

    #             for q in chosen:
    #                 ExamQuestion.objects.create(session=session, question=q, order=order_counter)
    #                 order_counter += 1

    #         # update total_questions count on session
    #         session.total_questions = session.examquestion_set.count()
    #         session.save()

    #     return session

    def generate_for_candidate(self, user: User, trade: Trade = None, shuffle_within_parts: bool = True):
        """
        Create an ExamSession for the given user and populate it with randomly selected questions
        according to the paper's distribution OR hard-coded trade config if paper.part_distribution is empty.

        STRICT RULES:
        - If this QuestionPaper is Secondary (is_common=True) -> only pick questions that are attached
            to this QuestionPaper (via PaperQuestion). If there are not enough questions for any part,
            raise ValidationError.
        - If this QuestionPaper is Primary -> behavior is same as before: prefer trade-specific pools,
            fall back to global pool if necessary.
        """
        from .models import Question, ExamSession, ExamQuestion  # local import
        import random

        # Determine effective trade:
        if self.is_common:
            # Secondary/common papers are NOT trade-specific for distribution,
            # and MUST use only paper-attached questions (enforced below).
            effective_trade = None
        else:
            effective_trade = self.trade or trade

        # Choose distribution (explicit override first, else defaults)
        if self.part_distribution:
            chosen_distribution = self.part_distribution.copy()
        else:
            if self.is_common:
                # For Secondary use the global common distribution (43 by your config)
                chosen_distribution = HARD_CODED_COMMON_DISTRIBUTION.copy()
            else:
                hc = self._get_hardcoded_for_trade(effective_trade)
                if hc:
                    chosen_distribution = hc[0]
                else:
                    chosen_distribution = HARD_CODED_COMMON_DISTRIBUTION.copy()

        # Validate distribution
        self._validate_distribution(chosen_distribution)

        # Build the session and pick random questions per part
        with transaction.atomic():
            session = ExamSession.objects.create(
                paper=self,
                user=user,
                trade=effective_trade,
                started_at=timezone.now(),
                duration=self.exam_duration
            )

            order_counter = 1

            for part_letter, count in (chosen_distribution or {}).items():
                cnt = int(count)
                if cnt <= 0:
                    continue

                if self.is_common:
                    # STRICT: Only use questions that are attached to this QuestionPaper for this part.
                    qset = Question.objects.filter(
                        is_active=True,
                        part=part_letter,
                        paperquestion__paper=self
                    )
                    available_count = qset.count()

                    if available_count < cnt:
                        # Not enough paper-assigned questions — fail loudly so admin can fix the paper.
                        raise ValidationError(
                            f"Secondary paper '{self}' does not have enough questions for part {part_letter}. "
                            f"Requested {cnt}, found {available_count}. Populate the paper via admin."
                        )

                else:
                    # Primary paper: prefer trade-filtered questions from the DB; fall back to global part pool.
                    qset = Question.objects.filter(is_active=True, part=part_letter)
                    if effective_trade is not None:
                        trade_qs = qset.filter(trade=effective_trade)
                        if trade_qs.count() >= cnt:
                            qset = trade_qs
                    # if trade_qs insufficient, qset remains the broader part pool (fallback)

                # Randomly choose `cnt` items
                chosen = list(qset.order_by('?')[:cnt])
                if len(chosen) < cnt:
                    # Should not happen for Secondary (already guarded), but guard anyway.
                    raise ValidationError(
                        f"Not enough active questions available for part {part_letter}. "
                        f"Requested {cnt}, found {len(chosen)}."
                    )

                if shuffle_within_parts:
                    random.shuffle(chosen)

                for q in chosen:
                    ExamQuestion.objects.create(session=session, question=q, order=order_counter)
                    order_counter += 1

            # update actual total_questions and save
            session.total_questions = session.examquestion_set.count()
            session.save()

        return session




class PaperQuestion(models.Model):
    paper = models.ForeignKey(QuestionPaper, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("paper", "question")
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.paper} - Q{self.order}"


class ExamSession(models.Model):
    paper = models.ForeignKey(QuestionPaper, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trade = models.ForeignKey(Trade, on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    total_questions = models.PositiveIntegerField(default=0)
    score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"ExamSession: {self.user} - {self.paper} ({self.started_at})"

    @property
    def questions(self):
        return self.examquestion_set.select_related("question").order_by("order")

    def finish(self):
        self.completed_at = timezone.now()
        self.save()


class ExamQuestion(models.Model):
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("session", "question")

    def __str__(self):
        return f"{self.session} - Q{self.order} ({self.question.pk})"
