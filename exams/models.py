from django.db import models

class Candidate(models.Model):
    TRADE_CHOICES = [
        ('TTC', 'TTC'),
        ('OCC', 'OCC'),
        ('DTMN', 'DTMN'),
        ('EFS', 'EFS'),
        ('DVM', 'DVM'),
        ('LMN', 'LMN'),
        ('CLK SD', 'CLK SD'),
        ('STEWARD', 'STEWARD'),
        ('WASHERMAN', 'WASHERMAN'),
        ('CHEFCOM', 'CHEFCOM'),
        ('HOUSE KEEPER', 'HOUSE KEEPER'),
        ('MESS KEEPER', 'MESS KEEPER'),
        ('SKT', 'SKT'),
        ('MUSICIAN', 'MUSICIAN'),
        ('ARTSN WW', 'ARTSN WW'),
        ('HAIR DRESSER', 'HAIR DRESSER'),
        ('SP STAFF', 'SP STAFF'),
    ]

    CENTER_CHOICES = [
        ('Jaipur', 'Jaipur'), ('Hissar', 'Hissar'), ('Bathinda', 'Bathinda'),
        ('Sriganganagar', 'Sriganganagar'), ('Bikaner', 'Bikaner'), ('Suratgarh', 'Suratgarh'),
        ('Kota', 'Kota'), ('Port Blair', 'Port Blair'), ('Ahmednagar', 'Ahmednagar'),
        ('Bangalore', 'Bangalore'), ('Chennai', 'Chennai'), ('Pune MINTSD', 'Pune MINTSD'),
        ('MCTE Mhow', 'MCTE Mhow'), ('Secunderabad', 'Secunderabad'), ('Jhansi', 'Jhansi'),
        ('Ahmedabad', 'Ahmedabad'), ('Jodhpur', 'Jodhpur'), ('Saugor', 'Saugor'),
        ('Bhopal', 'Bhopal'), ('Pune', 'Pune'), ('Binaguri', 'Binaguri'),
        ('Kolkata', 'Kolkata'), ('Missamari', 'Missamari'), ('Rangapahar', 'Rangapahar'),
        ('Dinjan', 'Dinjan'), ('Gangtok', 'Gangtok'), ('Leimakhong', 'Leimakhong'),
        ('Tenga', 'Tenga'), ('Panagarh', 'Panagarh'), ('Ranchi', 'Ranchi'),
        ('Likabali', 'Likabali'), ('Tejpur', 'Tejpur'), ('Kalimpong', 'Kalimpong'),
        ('Jalandhar', 'Jalandhar'), ('Ambala', 'Ambala'), ('Delhi', 'Delhi'),
        ('Amritsar', 'Amritsar'), ('Ferozepur', 'Ferozepur'), ('Patiala', 'Patiala'),
        ('Jammu', 'Jammu'), ('Pathankot', 'Pathankot'), ('Chandimandir', 'Chandimandir'),
        ('Meerut', 'Meerut'), ('Agra', 'Agra'), ('Bareilly', 'Bareilly'),
        ('Jabalpur', 'Jabalpur'), ('Lucknow', 'Lucknow'), ('Ranikhet', 'Ranikhet'),
        ('Dehradun', 'Dehradun'), ('Udhampur', 'Udhampur'), ('Baramula', 'Baramula'),
        ('Kargil', 'Kargil'), ('Leh', 'Leh'), ('Srinagar', 'Srinagar'),
        ('Kupwara', 'Kupwara'), ('Allahabad', 'Allahabad'), ('Rajouri', 'Rajouri'),
        ('Akhnoor', 'Akhnoor'), ('Nagrota', 'Nagrota'), ('Palampur', 'Palampur'),
        ('Mathura', 'Mathura'), ('Karu', 'Karu'),
    ]

    s_no = models.IntegerField(null=True, blank=True)  
    name = models.CharField(max_length=255, blank=True, null=True)
    center = models.CharField(max_length=255, choices=CENTER_CHOICES, blank=True, null=True)  # 🔥 Updated with choices
    photo = models.ImageField(upload_to="photos/", blank=True, null=True)
    fathers_name = models.CharField(max_length=255, null=True, blank=True)
    trade = models.CharField(max_length=50, choices=TRADE_CHOICES, blank=True, null=True)  # Existing trade choices
    rank = models.CharField(max_length=255, null=True, blank=True)
    dob = models.DateField(blank=True, null=True)
    army_no = models.CharField(max_length=50, unique=True)
    adhaar_no = models.CharField(max_length=20, blank=True, null=True)
    name_of_qualification = models.CharField(max_length=255, blank=True, null=True)
    duration_of_qualification = models.CharField(max_length=50, blank=True, null=True)
    credits = models.IntegerField(default=0)
    nsqf_level = models.IntegerField(default=0)
    training_center = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    viva_1 = models.IntegerField(default=0)
    viva_2 = models.IntegerField(default=0)
    practical_1 = models.IntegerField(default=0)
    practical_2 = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.army_no} - {self.name or ''}"

    def total_primary(self):
        return sum(a.marks_obt for a in self.answer_set.filter(question__exam_type="primary"))

    def total_secondary(self):
        return sum(a.marks_obt for a in self.answer_set.filter(question__exam_type="secondary"))

    def viva_practical_total(self):
        return self.viva_1 + self.viva_2 + self.practical_1 + self.practical_2

    def grand_total(self):
        return self.total_primary() + self.total_secondary() + self.viva_practical_total()


class Question(models.Model):
    EXAM_TYPES = [
        ("primary", "Primary"),
        ("secondary", "Secondary"),
    ]
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, default="primary")
    question = models.TextField()
    correct_answer = models.CharField(max_length=255, blank=True, null=True)
    max_marks = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.exam_type}: {self.question[:40]}"


class Answer(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True)
    marks_obt = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.candidate.army_no} - {self.question.exam_type}"
