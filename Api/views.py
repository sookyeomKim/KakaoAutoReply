import logging
from datetime import datetime

from django.contrib.auth.models import User
import json
import _pickle as c_pickle
from decouple import config
from django.http import HttpResponse
import boto3

# Create your views here.
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
        username = user.username

        s3_client = boto3.client('s3', region_name='ap-northeast-2',
                                 aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                                 aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'))

        try:
            s3_response = s3_client.get_object(Bucket=config('AWS_STORAGE_BUCKET_NAME'),
                                               Key='uploads/cookies/' + username.replace('@', '') + '.pkl')
            get_cookies = s3_response['Body'].read()
            get_cookie_list = c_pickle.loads(get_cookies)

            # 쿠키 생성 시간 + 1day - 3hour = expire_datetime_1
            # *카카오가 왜 -3시간을 했는지는 모르겠네 멀까
            try:
                expire_datetime_1 = datetime.fromtimestamp(int(get_cookie_list[0]['value']))

                # 쿠기 생성 시간 + 1day = expire_datetime_2(로그인 유지 체크 해제)
                # 쿠기 생성 시간 + 1month = expire_datetime_2(로그인 유지 체크 설정)
                expire_datetime_2 = datetime.fromtimestamp(int(get_cookie_list[3]['value']))

                current_time = datetime.now()

                activate_time = expire_datetime_1 - current_time

                activate_time_second = activate_time.total_seconds()

                if activate_time_second < 10800:  # 인증시간이 거의 끝나감
                    result['cookie_state'] = "3"
                elif activate_time_second >= 10800:  # 인증 중
                    result['cookie_state'] = "1"
                elif activate_time_second <= 0:  # 인증이 만료됨
                    result['cookie_state'] = "0"
            except Exception as e:
                result['cookie_state'] = "4"
                logger.info(e)
                logger.info("인증되지 않은 쿠키입니다.")
        except Exception as e:
            result['cookie_state'] = "2"
            logger.info(e)
            logger.info("쿠키가 존재하지 않습니다.")
        finally:
            user.profile.cookie_status = result['cookie_state']
            user.save()
    except Exception as e:
        logger.info(e)
        result["status"] = False
    return HttpResponse(json.dumps(result), content_type="application/json")
