import json
import pickle
from time import sleep

import boto3
import _pickle as c_pickle
from decouple import config

from django.http import HttpResponse, QueryDict
from datetime import datetime

from django.views.generic import DetailView
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from Post.models import Post

def renew_post(request, pk):
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
        channel_id = pk
        query_dict = QueryDict(request.body)
        channel_url = query_dict.get('channel_url')
        username = request.user.username

        print("웹드라이버 시작 완료")

        chrome_driver.get("https://accounts.kakao.com/login")
        s3_client = boto3.client('s3', region_name='ap-northeast-2',
                                 aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                                 aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'))
        s3_response = s3_client.get_object(Bucket='kakao-auto-reply',
                                           Key='uploads/cookies/' + username.replace('@', '') + '.pkl')
        get_cookies = s3_response['Body'].read()

        # for cookie in pickle.load(open("./uploads/cookies/" + username + ".pkl", "rb")):
        for cookie in c_pickle.loads(get_cookies):
            chrome_driver.add_cookie(cookie)
        # pickle_byte_obj = c_pickle.dumps(chrome_driver.get_cookies())
        # s3_client.put_object(Bucket='kakao-auto-reply', Body=pickle_byte_obj,
        #                      Key='uploads/cookies/' + username.replace('@', '') + '.pkl')

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
            get_hour = get_hour if (get_register_date[2] is "오전") else str(int(get_hour) + 12)
            get_minute = get_register_date[3].split(":")[1]
            now = datetime.now()
            post_register_date = datetime(int(now.year), int(get_month), int(get_day), int(get_hour), int(get_minute))
            post_url = item.find_element_by_css_selector(".link_title").get_attribute("href")
            check_post = Post.objects.filter(channel_id=channel_id, post_title=post_title)
            if check_post.exists():
                check_post.update(
                    post_register_date=post_register_date,
                    post_url=post_url,
                    modify_date=datetime.now()
                )
            else:
                post = Post(
                    post_title=post_title,
                    post_register_date=post_register_date,
                    post_url=post_url,
                    channel_id=channel_id
                )
                post.save()

    except Exception as e:
        print(e)
        success = False
    finally:
        # pass
        chrome_driver.close()
    return HttpResponse(json.dumps(success), content_type="application/json")
