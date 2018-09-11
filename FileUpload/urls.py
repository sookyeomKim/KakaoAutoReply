from django.urls import include, path
from FileUpload.views import *

app_name = "FileUpload"
urlpatterns = [
    path('', FileUploadLV.as_view(), name='index'),
]
