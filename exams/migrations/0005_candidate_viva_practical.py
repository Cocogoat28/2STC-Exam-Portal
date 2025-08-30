from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0004_candidate_rank_candidate_unit_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='viva_marks',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='candidate',
            name='practical_marks',
            field=models.IntegerField(default=0),
        ),
    ]
