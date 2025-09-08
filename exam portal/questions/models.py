from django.db import models
from django.core.exceptions import ValidationError
from reference.models import Trade
from datetime import timedelta

def validate_dat_file(value):
    """Validate that only .dat files are uploaded"""
    if not value.name.lower().endswith(".dat"):
        raise ValidationError("Only .dat files are allowed.")

class Question(models.Model):
    class Part(models.TextChoices):
        A = "A", "Part A - MCQ (Single Choice)"
        B = "B", "Part B - MCQ (Multiple Choice)"
        C = "C", "Part C - MCQ (Other format)"
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
    # ADD THIS NEW FIELD:
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
    is_common = models.BooleanField(default=False, editable=False)
    trade = models.ForeignKey(Trade, on_delete=models.PROTECT, null=True, blank=True)
    exam_duration = models.DurationField(
            null=True,
            blank=True,
            default=timedelta(hours=3),  # Default 3 hours
            help_text="Enter exam duration in format HH:MM:SS (e.g., 01:30:00 for 1h30m)"
        )
    qp_assign = models.ForeignKey(QuestionUpload, on_delete=models.SET_NULL, null=True, blank=True)
    questions = models.ManyToManyField("Question", through="PaperQuestion")

    class Meta:
        verbose_name = "QP Mapping"
        verbose_name_plural = "2 QP Mappings"
        ordering = ['-id']

    def save(self, *args, **kwargs):
        # Ensure is_common matches paper_type
        if self.question_paper == "Secondary":
            self.is_common = True
            self.trade = None  # force trade to None for Secondary
        else:
            self.is_common = False
        super().save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        """
        On deleting a QuestionPaper, delete questions that are *only* associated with this paper.
        If a Question is linked to other papers, we only remove the PaperQuestion relation.
        """
        # Collect question IDs linked to this paper
        from .models import PaperQuestion  # local import to avoid circular issues
        q_ids = list(PaperQuestion.objects.filter(paper=self).values_list("question_id", flat=True).distinct())

        # For each question: check if it's used by other papers
        from .models import Question  # local import
        for qid in q_ids:
            other_rel_count = PaperQuestion.objects.filter(question_id=qid).exclude(paper=self).count()
            if other_rel_count == 0:
                # safe to delete question entirely
                try:
                    Question.objects.filter(id=qid).delete()
                except Exception:
                    # swallow errors to avoid halting deletion
                    pass
            else:
                # If used elsewhere, just let the cascade remove the PaperQuestion link
                pass

        # Now delete the paper (this also deletes PaperQuestion rows via cascade)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.question_paper

class PaperQuestion(models.Model):
    paper = models.ForeignKey(QuestionPaper, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("paper", "question")
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.paper} - Q{self.order}"