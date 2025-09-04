from django.db import models


class Trade(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class ExamConfig(models.Model):
    EXAM_CHOICES = (
        ("Primary", "Primary"),
        ("Secondary", "Secondary"),
    )

    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name="exam_configs")
    exam_type = models.CharField(max_length=20, choices=EXAM_CHOICES)

    max_theory_marks = models.PositiveIntegerField(default=0)
    max_practical_marks = models.PositiveIntegerField(default=0)
    max_viva_marks = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.trade.name} - {self.exam_type}"

    def total_marks(self):
        return self.max_theory_marks + self.max_practical_marks + self.max_viva_marks


class Candidate(models.Model):
    is_checked = models.BooleanField(default=False)

    TRADE_CHOICES = [
        ('TTC', 'TTC'), ('OCC', 'OCC'), ('DTMN', 'DTMN'), ('EFS', 'EFS'),
        ('DMV', 'DMV'), ('LMN', 'LMN'), ('CLK SD', 'CLK SD'), ('STEWARD', 'STEWARD'),
        ('WASHERMAN', 'WASHERMAN'), ('CHEFCOM', 'CHEFCOM'), ('HOUSE KEEPER', 'HOUSE KEEPER'),
        ('MESS KEEPER', 'MESS KEEPER'), ('SKT', 'SKT'), ('MUSICIAN', 'MUSICIAN'),
        ('ARTSN WW', 'ARTSN WW'), ('HAIR DRESSER', 'HAIR DRESSER'), ('SP STAFF', 'SP STAFF'),
    ]

    CENTER_CHOICES = [
    ('SWC-Jaipur', 'SWC-Jaipur'), ('SWC-Hissar', 'SWC-Hissar'), ('SWC-Bathinda', 'SWC-Bathinda'),
    ('SWC-Sriganganagar', 'SWC-Sriganganagar'), ('SWC-Bikaner', 'SWC-Bikaner'), ('SWC-Suratgarh', 'SWC-Suratgarh'),
    ('SWC-Kota', 'SWC-Kota'), ('ARTRAC-Port Blair', 'ARTRAC-Port Blair'),
    ('ARTRAC-Ahmednagar', 'ARTRAC-Ahmednagar'), ('ARTRAC-Bangalore', 'ARTRAC-Bangalore'),
    ('ARTRAC-Chennai', 'ARTRAC-Chennai'), ('SWC-Pune MINTSD', 'SWC-Pune MINTSD'),
    ('ARTRAC-MCTE Mhow', 'ARTRAC-MCTE Mhow'), ('SC-Secunderabad', 'SC-Secunderabad'),
    ('SC-Jhansi', 'SC-Jhansi'), ('SC-Ahmedabad', 'SC-Ahmedabad'), ('SC-Jodhpur', 'SC-Jodhpur'),
    ('SC-Saugor', 'SC-Saugor'), ('SC-Bhopal', 'SC-Bhopal'), ('SC-Pune', 'SC-Pune'),
    ('EC-Binaguri', 'EC-Binaguri'), ('EC-Kolkata', 'EC-Kolkata'), ('EC-Missamari', 'EC-Missamari'),
    ('EC-Rangapahar', 'EC-Rangapahar'), ('EC-Dinjan', 'EC-Dinjan'), ('EC-Gangtok', 'EC-Gangtok'),
    ('EC-Leimakhong', 'EC-Leimakhong'), ('EC-Tenga', 'EC-Tenga'), ('EC-Panagarh', 'EC-Panagarh'),
    ('EC-Ranchi', 'EC-Ranchi'), ('EC-Likabali', 'EC-Likabali'), ('EC-Tejpur', 'EC-Tejpur'),
    ('EC-Kalimpong', 'EC-Kalimpong'), ('WC-Jalandhar', 'WC-Jalandhar'), ('WC-Ambala', 'WC-Ambala'),
    ('WC-Delhi', 'WC-Delhi'), ('WC-Amritsar', 'WC-Amritsar'), ('WC-Ferozepur', 'WC-Ferozepur'),
    ('WC-Patiala', 'WC-Patiala'), ('WC-Jammu', 'WC-Jammu'), ('WC-Pathankot', 'WC-Pathankot'),
    ('WC-Chandimandir', 'WC-Chandimandir'), ('WC-Meerut', 'WC-Meerut'),
    ('CC-Agra', 'CC-Agra'), ('CC-Bareilly', 'CC-Bareilly'), ('CC-Jabalpur', 'CC-Jabalpur'),
    ('CC-Lucknow', 'CC-Lucknow'), ('CC-Ranikhet', 'CC-Ranikhet'), ('CC-Dehradun', 'CC-Dehradun'),
    ('NC-Udhampur', 'NC-Udhampur'), ('NC-Baramula', 'NC-Baramula'), ('NC-Kargil', 'NC-Kargil'),
    ('NC-Leh', 'NC-Leh'), ('NC-Srinagar', 'NC-Srinagar'), ('NC-Kupwara', 'NC-Kupwara'),
    ('NC-Allahabad', 'NC-Allahabad'), ('NC-Rajouri', 'NC-Rajouri'), ('NC-Akhnoor', 'NC-Akhnoor'),
    ('NC-Nagrota', 'NC-Nagrota'), ('NC-Palampur', 'NC-Palampur'), ('NC-Mathura', 'NC-Mathura'),
    ('NC-Karu', 'NC-Karu'),
]


    s_no = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    center = models.CharField(max_length=255, choices=CENTER_CHOICES, blank=True, null=True)
    photo = models.CharField(max_length=255, blank=True, null=True)
    fathers_name = models.CharField(max_length=255, null=True, blank=True)
    trade = models.CharField(max_length=50, choices=TRADE_CHOICES, blank=True, null=True)
    rank = models.CharField(max_length=255, null=True, blank=True)
    dob = models.DateField(blank=True, null=True)
    army_no = models.CharField(max_length=50, unique=True)
    adhaar_no = models.CharField(max_length=20, blank=True, null=True)
    primary_qualification = models.CharField(max_length=255, blank=True, null=True)
    primary_duration = models.PositiveIntegerField(default=0)
    primary_credits = models.PositiveIntegerField(default=0)

    secondary_qualification = models.CharField(max_length=255, blank=True, null=True)
    secondary_duration = models.PositiveIntegerField(default=0)
    secondary_credits = models.PositiveIntegerField(default=0)

    nsqf_level = models.FloatField(default=0)
    training_center = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    viva_1 = models.IntegerField(default=0)
    viva_2 = models.IntegerField(default=0)
    practical_1 = models.IntegerField(default=0)
    practical_2 = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.army_no} - {self.name or ''}"

    # ✅ Totals (fixed, no nesting)
    def total_primary(self):
        return sum((a.marks_obt or 0) for a in self.answer_set.filter(question__exam_type__iexact="primary"))
    total_primary.short_description = "Primary Total"

    def total_secondary(self):
        return sum((a.marks_obt or 0) for a in self.answer_set.filter(question__exam_type__iexact="secondary"))
    total_secondary.short_description = "Secondary Total"

    def viva_practical_total(self):
        return (self.viva_1 or 0) + (self.viva_2 or 0) + (self.practical_1 or 0) + (self.practical_2 or 0)

    def grand_total(self):
        return self.total_primary() + self.total_secondary() + self.viva_practical_total()
    grand_total.short_description = "Grand Total"

    # ✅ Percentage
    def percentage(self, exam_type="Primary"):
        from django.core.exceptions import ObjectDoesNotExist
        try:
            trade_obj = Trade.objects.get(name=self.trade)
            config = trade_obj.exam_configs.get(exam_type=exam_type)
        except (Trade.DoesNotExist, ObjectDoesNotExist):
            return 0

        if exam_type == "Primary":
            scored = self.total_primary() + (self.viva_1 or 0) + (self.practical_1 or 0)
            max_marks = config.max_theory_marks + config.max_viva_marks + config.max_practical_marks
        else:
            scored = self.total_secondary() + (self.viva_2 or 0) + (self.practical_2 or 0)
            max_marks = config.max_theory_marks + config.max_viva_marks + config.max_practical_marks

        if max_marks == 0:
            return 0
        return round((scored / max_marks) * 100, 2)


class Question(models.Model):
    EXAM_TYPES = [
        ("primary", "Primary"),
        ("secondary", "Secondary"),
    ]
    PART_CHOICES = [
        ("A", "Part A"), ("B", "Part B"), ("C", "Part C"),
        ("D", "Part D"), ("E", "Part E"), ("F", "Part F"),
    ]

    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, default="primary")
    part = models.CharField(max_length=2, choices=PART_CHOICES, blank=True, null=True)
    question = models.TextField()
    correct_answer = models.CharField(max_length=255, blank=True, null=True)
    max_marks = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.exam_type} {self.part or ''}: {self.question[:40]}"


class Answer(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True)
    marks_obt = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.candidate.army_no} - {self.question.exam_type}"
