import logging
from django.contrib.auth.models import User
import json
from django.http import HttpResponse
from enumfields.fields import EnumFieldMixin

from Api.models import Status

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def check_cookie(request):
    # Post.objects.all().delete()
    result = {
        "status": True
    }
    try:
        user_id = request.GET.get('user_id')
        user = User.objects.get(pk=user_id)
        cookie_status = user.profile.cookie_status

        if cookie_status is Status.DEACTIVATE:
            result['cookie_status'] = "0"
        elif cookie_status is Status.ACTIVATE:
            result['cookie_status'] = "1"
        elif cookie_status is Status.EMPTY:
            result['cookie_status'] = "2"
        elif cookie_status is Status.WARNING:
            result['cookie_status'] = "3"
        elif cookie_status is Status.ERROR:
            result['cookie_status'] = "4"
    except Exception as e:
        logger.info(e)
        result["status"] = False
    return HttpResponse(json.dumps(result), content_type="application/json")
