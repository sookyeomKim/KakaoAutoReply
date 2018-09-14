from django.urls import include, path
from Post.views import *

app_name = "Post"
urlpatterns = [
    path('', PostLV.as_view(), name='index'),
    path('<int:pk2>/Reply/', include('Reply.urls')),

    path('renew_post', renew_post, name='renew_post'),
]

