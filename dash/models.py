from django.db import models


class BytesRecord(models.Model):
    """
    Tracks historical records of bytes so we can show speeds.
    """

    key = models.CharField(max_length=100, db_index=True)
    time = models.FloatField(db_index=True)
    value = models.IntegerField()
