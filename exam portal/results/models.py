# results/models.py
from django.db import models
from questions.models import Question, QuestionPaper
from registration.models import CandidateProfile


class CandidateAnswer(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE)
    paper = models.ForeignKey(QuestionPaper, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.army_no} - {self.paper.question_paper} - {self.question.id}"

    @property
    def effective_category(self) -> str:
        """
        Computed label for downstream exports:
        - 'secondary' if the paper was common
        - 'primary' if the paper was trade-specific
        """
        is_common = getattr(self.paper, "is_common", False)
        return "secondary" if is_common else "primary"
