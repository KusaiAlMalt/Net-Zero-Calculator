from django.db import models

# Create your models here.
class Result(models.Model):
    id = models.AutoField(primary_key=True)

    scope1 = models.IntegerField(max_length=20)
    scope2 = models.IntegerField(max_length=20)
    scope3 = models.IntegerField(max_length=20)
    profit = models.IntegerField(max_length=20)

    pdfname = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(max_length=100, null=True)