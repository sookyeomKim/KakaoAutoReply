from django.db import models

from Channel.models import Channel


# Create your models here.


class Post(models.Model):
    post_title = models.CharField(max_length=50)
    post_register_date = models.DateTimeField()
    post_url = models.CharField(max_length=100)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Post'
        ordering = ['-post_register_date']
