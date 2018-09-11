from django.urls import include, path
from Channel.views import *

app_name = "Channel"
urlpatterns = [
    path('', ChannelLV.as_view(), name='index'),
    path('<int:pk>', ChannelDV.as_view(), name='detail'),
    path('renew_channel', renew_channel, name='renew_channel'),
    path('<int:pk>/Post/', include('Post.urls'))
]
