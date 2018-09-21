import json
import logging
import boto3
import _pickle as c_pickle
import pytz
from time import sleep
from decouple import config
from django.conf import settings
from django.http import HttpResponse
from django.utils.datetime_safe import datetime

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from django.core.exceptions import ObjectDoesNotExist
from Channel.models import Channel
from Post.models import Post

from django.views.generic import ListView

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class PostLV(ListView):
    model = Post

    def get_context_data(self, **kwargs):
        context = super(PostLV, self).get_context_data(**kwargs)
        pk = self.kwargs['pk']
        # request.GET['type']는 MultiValueDictKeyError 발생
        list_type = self.request.GET.get('list_type')
        channel = Channel.objects.get(id=pk)
        context['channel'] = channel
        if list_type == "register_task":
            context['posts'] = channel.post_set.filter(reply__isnull=False)
        elif list_type == "working":
            context['posts'] = channel.post_set.filter(reply__trigger=True)
        elif list_type == "stopping":
            context['posts'] = channel.post_set.filter(reply__trigger=False)
        elif list_type == "all":
            context['posts'] = channel.post_set.all()
        else:
            context['posts'] = channel.post_set.all()
        return context


def renew_post(request, pk):
    username = request.user.username
    channel_id = pk
    channel_url = request.GET.get('channel_url')

    success = True

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--window-size=1366x768')
    options.add_argument('--disable-gpu')
    options.add_argument('--lang=ko_KR')
    options.add_argument('--no-sandbox')
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36")
    chrome_driver = webdriver.Chrome(chrome_options=options)
    chrome_driver_wait = WebDriverWait(chrome_driver, 30)

    try:
        chrome_driver.get("https://accounts.kakao.com")

        s3_client = boto3.client('s3', region_name='ap-northeast-2',
                                 aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                                 aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'))
        s3_response = s3_client.get_object(Bucket=config('AWS_STORAGE_BUCKET_NAME'),
                                           Key='uploads/cookies/' + username.replace('@', '') + '.pkl')
        get_cookies = s3_response['Body'].read()

        for cookie in c_pickle.loads(get_cookies):
            chrome_driver.add_cookie(cookie)

        chrome_driver.get(channel_url)

        sleep(2)

        for i in range(1):
            chrome_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(5)

        post_post_list = chrome_driver_wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".story_channel")))

        for item in post_post_list:
            post_title = item.find_element_by_css_selector(".tit_story").text
            get_register_date = item.find_element_by_css_selector(".link_date").text
            get_register_date = get_register_date.split(" ")
            get_month = get_register_date[0].replace("월", "")
            get_day = get_register_date[1].replace("일", "")
            get_hour = get_register_date[3].split(":")[0]
            get_hour = get_hour if (get_register_date[2] == "오전") else str(int(get_hour) + 12)
            get_minute = get_register_date[3].split(":")[1]
            now = datetime.now()
            naive = datetime.strptime(
                str(now.year) + "-" + get_month + "-" + get_day + " " + get_hour + ":" + get_minute + ":00",
                "%Y-%m-%d %H:%M:%S")
            local = pytz.timezone(settings.TIME_ZONE)
            local_dt = local.localize(naive, is_dst=None)
            # datetimefield를 직접 넣으면 파싱한 시간 그대로 들어가져버려 tz이 꼬인다. 그래서 직접 utc로 바꿨다.
            post_register_date = local_dt.astimezone(pytz.utc)
            post_url = item.find_element_by_css_selector(".link_title").get_attribute("href")

            try:
                # update
                check_post = Post.objects.get(channel_id=channel_id, post_title=post_title)
                check_post.post_register_date = post_register_date
                check_post.post_url = post_url
                check_post.save()
            except ObjectDoesNotExist:
                # create
                post = Post(
                    post_title=post_title,
                    post_register_date=post_register_date,
                    post_url=post_url,
                    channel_id=channel_id
                )
                post.save()

    except Exception as e:
        logger.info(e)
        success = False
    finally:
        chrome_driver.close()
    return HttpResponse(json.dumps(success), content_type="application/json")
