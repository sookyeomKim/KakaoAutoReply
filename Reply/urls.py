from django.urls import include, path
from Reply.views import *

app_name = "Reply"
urlpatterns = [
    path('trigger', trigger, name='trigger'),
    path('create', ReplyCV.as_view(), name='create'),
    path('update', ReplyUV.as_view(), name='update'),
    path('delete', ReplyDV.as_view(), name='delete'),
]
