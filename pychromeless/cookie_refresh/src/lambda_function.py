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
from selenium.webdriver import ActionChains
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
        # db = pymysql.connect(os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
        #                      password=os.getenv('DB_PASSWD'), database=os.getenv('DB_DATABASE'), connect_timeout=5,
        #                      charset='utf8mb4', autocommit=True)
        # dbcur = db.cursor(pymysql.cursors.DictCursor)

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
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36")

        chrome_options.binary_location = os.getcwd() + "/bin/headless-chromium"

        _driver = webdriver.Chrome(chrome_options=chrome_options)
        _driver_wait = WebDriverWait(_driver, 10)

        while True:
            ran_num = list(random_num_dict)[random.randrange(len(random_num_dict) - 1)]
            check_rn_status = random_num_dict[ran_num]
            if check_rn_status is "ready":
                random_num_dict[ran_num] = "working"
                break

        ran_num = float(ran_num) + round(float((random.randint(0, 10) / 10)), 1)
        time.sleep(ran_num)

        _driver.get("https://accounts.kakao.com/login/kakaostory")

        input_id = _driver_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#loginEmail")))
        action = ActionChains(_driver).move_to_element(input_id).click().send_keys(row['username']).perform()
        input_passwd = _driver.find_element_by_css_selector("#loginPw")
        action = ActionChains(_driver).move_to_element(input_passwd).click().send_keys(row['kakao_passwd']).perform()

        try:
            _driver.find_element_by_css_selector("#recaptcha iframe")
            raise Exception(row['username'] + " 캡챠 등록해야 함")
        except:
            pass

        time.sleep(2)
        login_button = _driver.find_element_by_css_selector(".submit")
        action = ActionChains(_driver).move_to_element(login_button).click().perform()

        time.sleep(2)

        pickle_byte_obj = c_pickle.dumps(_driver.get_cookies())

        session = boto3.session.Session(aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
                                        aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
                                        region_name='ap-northeast-2')
        s3_client = session.client('s3')
        s3_client.put_object(Bucket=os.getenv('STORAGE_BUCKET_NAME'), Body=pickle_byte_obj,
                             Key='uploads/cookies/' + row['username'].replace('@', '') + '.pkl')
        _driver.quit()
        logger.info(row['username'] + " 쿠키 갱신 완료")
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
                            AND profile.cookie_status = '3'
                            """)
            rows = dbcur.fetchall()
            db.close()

            logger.info("SUCCESS: Termination to RDS mysql instance succeeded")

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
