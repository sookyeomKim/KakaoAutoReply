from django.contrib.auth.models import User
from django.db import models


# Create your models here.


class Channel(models.Model):
    channel_title = models.CharField(max_length=50, null=False)
    channel_e_title = models.CharField(max_length=50, null=False)
    channel_thumbnail_url = models.CharField(max_length=256, null=False)
    channel_news_count = models.IntegerField(null=False)
    channel_subscriber_count = models.IntegerField(null=False)
    channel_visitor_count = models.IntegerField(null=False)
    channel_activity_users_count = models.IntegerField(null=False)
    channel_url = models.CharField(max_length=256, null=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Channel'
