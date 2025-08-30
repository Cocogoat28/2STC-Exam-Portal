from django.db import models


class Candidate(models.Model):
    army_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    rank = models.CharField(max_length=50, blank=True, null=True)
    unit = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    paper = models.CharField(max_length=100, blank=True, null=True)
    pdf_file = models.FileField(upload_to="pdfs/", blank=True, null=True)

    # viva/practical set by admin
    viva_marks = models.IntegerField(default=0)
    practical_marks = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.army_number})"

    @property
    def objective_marks(self):
        return sum(a.marks_awarded or 0 for a in self.answers.all())

    @property
    def total_marks(self):
        return (self.objective_marks or 0) + (self.viva_marks or 0) + (self.practical_marks or 0)


class Question(models.Model):
    number = models.IntegerField()
    text = models.TextField()

    def __str__(self):
        return f"Q{self.number}: {self.text[:50]}"


class Answer(models.Model):
    candidate = models.ForeignKey(Candidate, related_name="answers", on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True, null=True)
    marks_awarded = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.candidate.army_number} - Q{self.question.number}"
