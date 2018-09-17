import json
import _pickle as c_pickle
from decouple import config
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import boto3

# Create your views here.
from django.views.generic import ListView

from Channel.models import Channel


class ChannelLV(ListView):
    model = Channel


def renew_channel(request):
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
        username = request.user.username

        print("웹드라이버 시작 완료")

        chrome_driver.get("https://accounts.kakao.com")

        s3_client = boto3.client('s3', region_name='ap-northeast-2',
                                 aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                                 aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'))
        s3_response = s3_client.get_object(Bucket=config('AWS_STORAGE_BUCKET_NAME'),
                                           Key='uploads/cookies/' + username.replace('@', '') + '.pkl')
        get_cookies = s3_response['Body'].read()

        # for cookie in pickle.load(open("./uploads/cookies/" + username + ".pkl", "rb")):
        for cookie in c_pickle.loads(get_cookies):
            chrome_driver.add_cookie(cookie)
        chrome_driver.get('https://ch.kakao.com/channels')
        channel_card_list = chrome_driver_wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".section_mychannel > .list_section > li")))
        for item in channel_card_list:
            channel_title = item.find_element_by_css_selector(".tit_subject").text
            channel_url = item.find_element_by_css_selector(".link_card").get_attribute("href")
            channel_e_title = channel_url.split("/")[4][1:]
            channel_thumbnail_url = item.find_element_by_css_selector(".img_comm img").get_attribute("src")
            channel_news_count = item.find_element_by_css_selector(".append_info dd:nth-of-type(2)").text.replace(
                "명이 소식 받는 중", "").replace(",", "")
            channel_subscriber_count = item.find_element_by_css_selector(
                ".info_data .define_data:nth-of-type(1) dd").text.replace(",", "")
            channel_visitor_count = item.find_element_by_css_selector(
                ".info_data .define_data:nth-of-type(2) dd").text.replace(",", "")
            channel_activity_users_count = item.find_element_by_css_selector(
                ".info_data .define_data:nth-of-type(3) dd").text.replace(",", "")
            owner_id = request.user.id

            try:
                # update
                check_channel = Channel.objects.get(owner_id=owner_id, channel_title=channel_title)
                check_channel.channel_url = channel_url
                check_channel.channel_e_title = channel_e_title
                check_channel.channel_thumbnail_url = channel_thumbnail_url
                check_channel.channel_news_count = channel_news_count
                check_channel.channel_subscriber_count = channel_subscriber_count
                check_channel.channel_visitor_count = channel_visitor_count
                check_channel.channel_activity_users_count = channel_activity_users_count
                check_channel.save()
            except ObjectDoesNotExist:
                # create
                channel = Channel(
                    channel_title=channel_title,
                    channel_url=channel_url,
                    channel_thumbnail_url=channel_thumbnail_url,
                    channel_e_title=channel_e_title,
                    channel_news_count=channel_news_count,
                    channel_subscriber_count=channel_subscriber_count,
                    channel_visitor_count=channel_visitor_count,
                    channel_activity_users_count=channel_activity_users_count,
                    owner_id=owner_id
                )
                channel.save()
    except Exception as e:
        print(e)
        success = False
    finally:
        chrome_driver.close()
    return HttpResponse(json.dumps(success), content_type="application/json")
