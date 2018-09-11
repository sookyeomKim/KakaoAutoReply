from django.urls import include, path
from Post.views import *

app_name = "Post"
urlpatterns = [
    path('renew_post', renew_post, name='renew_post'),
    path('<int:pk2>/Reply/', include('Reply.urls'))
]
