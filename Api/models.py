from django.db import models
from enumfields import EnumField
from enumfields import Enum
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.

class Status(Enum):
    DEACTIVATE = '0'
    ACTIVATE = '1'
    EMPTY = '2'
    WARNING = '3'
    ERROR = '4'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cookie_status = EnumField(Status, max_length=1, default=Status.EMPTY)
    # TODO 암호화할 수 있는 방법 찾기
    kakao_passwd = models.CharField(max_length=128)
    modify_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auth_user_profile'

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()
