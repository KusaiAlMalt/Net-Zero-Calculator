from django.db import models

# Create your models here.
class Result(models.Model):
    id = models.AutoField(primary_key=True)

    scope1 = models.IntegerField()
    scope2 = models.IntegerField()
    scope3 = models.IntegerField()
    profit = models.IntegerField()

    pdfname = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(max_length=100, null=True)