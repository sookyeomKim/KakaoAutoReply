from django.db import models
from django.utils.safestring import mark_safe
from enumfields import EnumField
from enumfields import Enum
# Create your models here.
from Channel.models import Channel
from Post.models import Post


class Type(Enum):
    EMOTICON = '0'
    REPLY = '1'


class Reply(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    execute_time = models.DateTimeField()
    interval_time = models.IntegerField()
    type = EnumField(Type, max_length=1, default=Type.EMOTICON)
    content = models.TextField()
    trigger = models.BooleanField(default=False)
    post = models.OneToOneField(Post, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    modify_date = models.DateTimeField(auto_now=True)

    def display_safefield(self):
        return mark_safe(self.content)

    class Meta:
        db_table = 'Reply'
