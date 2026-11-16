import datetime
from zoneinfo import ZoneInfo

from django.db import migrations, models

NEW_YORK = ZoneInfo("America/New_York")


def fill_signup_deadline(apps, schema_editor):
    """Existing dinners get a deadline of the dinner date minus 2 days, 23:59 New York time."""
    Dinner = apps.get_model("dinners", "Dinner")
    for dinner in Dinner.objects.all():
        day = dinner.date - datetime.timedelta(days=2)
        dinner.signup_deadline = datetime.datetime.combine(day, datetime.time(23, 59), tzinfo=NEW_YORK)
        dinner.save(update_fields=["signup_deadline"])


class Migration(migrations.Migration):

    dependencies = [
        ("dinners", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="dinner",
            old_name="after_party_place",
            new_name="after_party_name",
        ),
        migrations.AddField(
            model_name="dinner",
            name="starter_time",
            field=models.TimeField(default=datetime.time(18, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="dinner",
            name="main_time",
            field=models.TimeField(default=datetime.time(19, 30)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="dinner",
            name="dessert_time",
            field=models.TimeField(default=datetime.time(21, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="dinner",
            name="after_party_address",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="dinner",
            name="signup_deadline",
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(fill_signup_deadline, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="dinner",
            name="signup_deadline",
            field=models.DateTimeField(),
        ),
    ]
