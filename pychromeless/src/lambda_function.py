import os
import sys
import uuid
import shutil
import logging

import json
import time
import html
import random
import decimal
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
for i in range(2, 30, 2):
    # for i in numpy.arange(1.5, 23.5, 2.0):
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
                             charset='utf8mb4')
        dbcur = db.cursor(pymysql.cursors.DictCursor)
        dbcur.execute("""SELECT * FROM `Channel` channel WHERE channel.id = '{}'""".format(row['channel_id']))
        get_channel = dbcur.fetchone()
        channel_name = get_channel['channel_title']

        dbcur = db.cursor(pymysql.cursors.DictCursor)
        dbcur.execute(
            """SELECT * FROM `auth_user` auth_user WHERE auth_user.id = '{}'""".format(get_channel['owner_id']))
        get_user = dbcur.fetchone()

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
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920x3080')
        chrome_options.add_argument('--user-data-dir={}'.format(_tmp_folder + '/user-data'))
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.add_argument('--v=99')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--data-path={}'.format(_tmp_folder + '/data-path'))
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--homedir={}'.format(_tmp_folder))
        chrome_options.add_argument('--disk-cache-dir={}'.format(_tmp_folder + '/cache-dir'))
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3165.0 Safari/537.36')

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
        ran_num = ran_num + float(decimal.Decimal(random.randrange(0, 5)) / 10)
        time.sleep(ran_num)

        _driver.get(row['post_url'])
        logger.info(row['post_title'] + " 게시글 오픈")
        try:
            # get_btn_more = _driver_wait.until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, "div.scope_comment button.btn_more")))
            time.sleep(3)
            get_btn_more = _driver.find_element_by_css_selector(".btn_more")
            get_btn_more.click()
        except Exception as e:
            logger.info(e)
        # finally:
        #     _driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        get_list_comment = _driver_wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list_comment li")))

        try:
            try:
                # 첫 댓글 이모티콘인지 체크
                get_list_comment[0].find_element_by_css_selector(
                    ".post_comment > .info_story > div > .channel_emoticon")
                logger.info(row['post_title'] + " 첫 댓글 이모티콘 ok")
            except:
                raise Exception(row['post_title'] + " 첫 댓글 이모티콘 no")

            get_box_text = _driver.find_element_by_css_selector(".box_text")
            get_box_text.click()

            _driver.execute_script("arguments[0].innerHTML = arguments[1];", get_box_text,
                                   html.unescape(row['content']))
            time.sleep(1)

            for comment in get_list_comment:
                # 댓글이 이모티콘인 유저만 콜
                try:
                    try:
                        comment.find_element_by_css_selector(
                            ".channel_emoticon")
                    except:
                        raise Exception(row['post_title'] + " 이모티콘 아닌건 패스")
                    get_link_title = comment.find_element_by_css_selector(
                        ".link_title")
                    if channel_name is get_link_title.text:
                        break
                    get_link_title.click()

                except Exception as e:
                    logger.info(e)

            time.sleep(1)

            get_submit_button = _driver.find_element_by_css_selector(".btn_type2")
            get_submit_button.click()
        except Exception as e:
            logger.info(e)
        finally:
            _driver.quit()
            # ran_num 다시 ready 상태로
            random_num_dict[ran_num] = "ready"

            # Remove specific tmp dir of this "run"
            shutil.rmtree(_tmp_folder)

            # Remove possible core dumps
            folder = '/tmp'
            for the_file in os.listdir(folder):
                file_path = os.path.join(folder, the_file)
                try:
                    if 'core.headless-chromi' in file_path and os.path.exists(file_path) and os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.info(e)
    except Exception as e:
        logger.info(e)
        sys.exit()


def lambda_handler(event, context):
    try:
        # start_time = time.time()
        db = pymysql.connect(os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
                             password=os.getenv('DB_PASSWD'), database=os.getenv('DB_DATABASE'), connect_timeout=5,
                             charset='utf8mb4')

        logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

        if check_table_exists(db, 'Post'):
            dbcur = db.cursor(pymysql.cursors.DictCursor)
            dbcur.execute("""
                    SELECT * FROM `Post` post INNER JOIN `Reply` reply ON post.id = reply.post_id WHERE `trigger` IS TRUE 
                    """)
            rows = dbcur.fetchall()
            db.close()

            logger.info("SUCCESS: Termination to RDS mysql instance succeeded")
            logger.info("실행될 레코드 수 : " + str(len(rows)))

            executor = concurrent.futures.ThreadPoolExecutor(10)
            futures = [executor.submit(reply_executor, row) for row in rows]
            concurrent.futures.wait(futures)
        else:
            logger.info("FAILED : no table")
            db.close()
            sys.exit()

        # e = int(time.time() - start_time)
        # print('{:02d}:{:02d}:{:02d}'.format(e // 3600, (e % 3600 // 60), e % 60))

    except Exception as e:
        logger.info(e)
        sys.exit()

    return {
        "statusCode": 200,
        "body": json.dumps('Hello from Lambda!')
    }
