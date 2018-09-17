from django.urls import include, path

from Api.views import check_cookie

app_name = "Api"
urlpatterns = [
    path('check_cookie', check_cookie, name='check_cookie'),
]
