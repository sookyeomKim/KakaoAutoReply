from django.db import models


# Create your models here.
class FileUpload(models.Model):
    file = models.FileField(upload_to='cookies/')
    create_date = models.DateTimeField('CREATE_DATE', auto_now_add=True)
    modify_date = models.DateTimeField('MODIFY_DATE', auto_now=True)

    class Meta:
        db_table = 'FileUpload'
