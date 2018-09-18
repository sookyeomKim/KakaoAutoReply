import os
import sys
import uuid
import shutil
import logging

import json
import time
import html
import random
import _pickle as c_pickle

import concurrent.futures

import boto3
import boto3.session

import pymysql

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

logger = logging.getLogger()
logger.setLevel(logging.INFO)

random_num_dict = {}
for i in range(2, 36, 3):
    random_num_dict[i] = 'ready'


def check_table_exists(db, table_name):
    dbcur = db.cursor()
    dbcur.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}' 
        """.format(table_name.replace('\'', '\'\'')))
    if dbcur.fetchone()[0] == 1:
        dbcur.close()
        return True

    dbcur.close()
    return False


def reply_executor(row):
    try:
        db = pymysql.connect(os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
                             password=os.getenv('DB_PASSWD'), database=os.getenv('DB_DATABASE'), connect_timeout=5,
                             charset='utf8mb4', autocommit=True)
        dbcur = db.cursor(pymysql.cursors.DictCursor)

        chrome_options = webdriver.ChromeOptions()
        _tmp_folder = '/tmp/{}'.format(uuid.uuid4())

        if not os.path.exists(_tmp_folder):
            os.makedirs(_tmp_folder)

        if not os.path.exists(_tmp_folder + '/user-data'):
            os.makedirs(_tmp_folder + '/user-data')

        if not os.path.exists(_tmp_folder + '/data-path'):
            os.makedirs(_tmp_folder + '/data-path')

        if not os.path.exists(_tmp_folder + '/cache-dir'):
            os.makedirs(_tmp_folder + '/cache-dir')

        chrome_options.add_argument('--headless')
        chrome_options.add_argument(
            '--no-sandbox')  # sandbox를 사용하지 않는다 보안 이슈가 있어 권고사항이 아니지만 크롤링목적으로 띄우는 브라우저에서는 딱히 무관한 이슈라고나 할까 무튼 헤드리스 동작시키려면 필수 옵션
        chrome_options.add_argument('--disable-gpu')  # gpu를 사용x 윈도우에서는 실행 시 필요한 옵션, for headless
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')  # 이미지 방지
        chrome_options.add_argument('--window-size=1024x3072')
        chrome_options.add_argument("--disable-infobars")  # 정보바 끄기
        chrome_options.add_argument("--disable-extensions")  # 확장기능 끄기
        chrome_options.add_argument("--disable-dev-shm-usage")  # 리소스 제한 문제 끄기
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--single-process')  # problem : unable to discover open pages
        chrome_options.add_argument('--homedir={}'.format(_tmp_folder))
        chrome_options.add_argument('--data-path={}'.format(_tmp_folder + '/data-path'))
        chrome_options.add_argument('--user-data-dir={}'.format(_tmp_folder + '/user-data'))
        chrome_options.add_argument('--disk-cache-dir={}'.format(_tmp_folder + '/cache-dir'))

        chrome_options.binary_location = os.getcwd() + "/bin/headless-chromium"

        _driver = webdriver.Chrome(chrome_options=chrome_options)
        _driver_wait = WebDriverWait(_driver, 10)

        _driver.get(
            "https://accounts.kakao.com/login?continue=https%3A%2F%2Faccounts.kakao.com%2Fweblogin%2Faccount%2Finfo")
        try:
            # 동시 처리할 경우 endpoint_resolved 에러 발생
            # 개별 세션을 만들어줘서 s3연결 처리
            session = boto3.session.Session(aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
                                            aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
                                            region_name='ap-northeast-2')
            s3_client = session.client('s3')
            s3_response = s3_client.get_object(Bucket=os.getenv('STORAGE_BUCKET_NAME'),
                                               Key='uploads/cookies/' + get_user['username'].replace("@", "") + '.pkl')
            get_cookies = s3_response['Body'].read()
        except Exception as e:
            logger.info(e)
            raise

        # for cookie in pickle.load(open("./uploads/cookies/" + username + ".pkl", "rb")):
        for cookie in c_pickle.loads(get_cookies):
            _driver.add_cookie(cookie)
        # pickle_byte_obj = c_pickle.dumps(_driver.get_cookies())
        # s3_client.put_object(Bucket='kakao-auto-reply', Body=pickle_byte_obj,
        #                      Key='uploads/cookies/' + username.replace('@', '') + '.pkl')

        # 동시 처리 하면 일시적인 오류 뜨는 현상 발생
        # 랜덤 딜레이 줘서 방지
        # time.sleep(float(decimal.Decimal(random.randrange(200, 1000)) / 100))
        # ran_num = random.randrange(2, 11 * 3, 2)
        # 실행 중인 future들이 유니크한 시간을 가질 수 있도록 설정하여 가동 중 중복 실행 방지
        while True:
            ran_num = list(random_num_dict)[random.randrange(len(random_num_dict) - 1)]
            check_rn_status = random_num_dict[ran_num]
            if check_rn_status is "ready":
                random_num_dict[ran_num] = "working"
                break
        # ran_num = ran_num + float(decimal.Decimal(random.randrange(0, 10)) / 10)
        ran_num = float(ran_num) + round(float((random.randint(0, 10) / 10)), 1)
        time.sleep(ran_num)
        _driver.get(row['post_url'])




        _driver.quit()
        db.close()
    except Exception as e:
        logger.info(e)
        sys.exit()


def lambda_handler(event, context):
    try:
        db = pymysql.connect(os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
                             password=os.getenv('DB_PASSWD'), database=os.getenv('DB_DATABASE'), connect_timeout=5,
                             charset='utf8mb4')

        logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

        if check_table_exists(db, 'Post'):
            dbcur = db.cursor(pymysql.cursors.DictCursor)
            dbcur.execute("""
                    SELECT * FROM `auth_user` owner 
                    JOIN `auth_user_profile` profile 
                    ON owner.id = profile.user_id
                    WHERE owner.username NOT IN ('admin')
                    """)
            rows = dbcur.fetchall()
            db.close()

            logger.info("SUCCESS: Termination to RDS mysql instance succeeded")
            for item in rows:
                print(item)

            if not rows:
                raise Exception("실행될 레코드가 없습니다.")

            logger.info("실행될 레코드 수 : " + str(len(rows)))

            executor = concurrent.futures.ThreadPoolExecutor(10)
            futures = [executor.submit(reply_executor, row) for row in rows]
            concurrent.futures.wait(futures)

            return {
                "statusCode": 200,
                "body": json.dumps('SUCCESS')
            }
        else:
            db.close()
            raise Exception("FAILED : no table")
    except Exception as e:
        logger.info(e)
        sys.exit()
