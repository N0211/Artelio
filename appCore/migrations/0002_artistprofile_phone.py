from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("appCore", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="artistprofile",
            name="phone",
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
