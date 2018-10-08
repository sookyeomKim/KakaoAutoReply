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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

logger = logging.getLogger()
logger.setLevel(logging.INFO)

random_num_dict = {}


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
    logger.info(row['channel_title'] + " - " + row['post_title'] + " 댓글 달기 시작")
    try:
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

        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36")

        chrome_options.binary_location = os.getcwd() + "/bin/headless-chromium"

        _driver = webdriver.Chrome(chrome_options=chrome_options)

        _driver.get(
            "https://accounts.kakao.com/login?continue=https%3A%2F%2Faccounts.kakao.com%2Fweblogin%2Faccount%2Finfo")

        # 동시 처리할 경우 endpoint_resolved 에러 발생
        # 개별 세션을 만들어줘서 s3연결 처리
        session = boto3.session.Session(aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
                                        aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
                                        region_name='ap-northeast-2')
        s3_client = session.client('s3')
        s3_response = s3_client.get_object(Bucket=os.getenv('STORAGE_BUCKET_NAME'),
                                           Key='uploads/cookies/' + row['username'].replace("@", "") + '.pkl')
        get_cookies = s3_response['Body'].read()

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

        ran_num = float(ran_num) + round(float((random.randint(0, 10) / 10)), 1)

        time.sleep(ran_num)

        _driver.get(row['post_url'])
        logger.info(row['channel_title'] + " - " + row['post_title'] + " 게시글 오픈")
        time.sleep(1.5)
        try:
            get_btn_more = _driver.find_element_by_css_selector(".btn_more")
            get_btn_more.click()
            time.sleep(1.5)
        except:
            logger.info(row['channel_title'] + " - " + row['post_title'] + " 더 보기 버튼 없음")

        # get_list_comment = _driver_wait.until(
        #     EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list_comment li")))
        get_list_comment = _driver.find_elements_by_css_selector(".list_comment li")

        try:
            check_reply = False
            # try:
            #     # 첫 댓글 이모티콘인지 체크
            #     get_list_comment[0].find_element_by_css_selector(
            #         ".post_comment > .info_story > div > .channel_emoticon")
            #     logger.info(row['channel_title]+" - +row['post_title'] + " 첫 댓글 이모티콘 ok")
            # except:
            #     raise Exception(row['channel_title]+" - +row['post_title'] + " 첫 댓글 이모티콘 no")

            get_box_text = _driver.find_element_by_css_selector(".box_text")
            get_box_text.click()

            time.sleep(1)

            _driver.execute_script("arguments[0].innerHTML = arguments[1];", get_box_text,
                                   row[
                                       'content'] + "<div><br></div>" + "<div>1:1 문의하기는 밑에 링크를 클릭</div>" + "<div>https://plus.kakao.com/home/@" +
                                   row[
                                       'channel_title'] + "</div>" + "<div><br></div>" + "<div><br></div>")
            time.sleep(1)

            for comment in get_list_comment:
                # 댓글이 이모티콘인 유저만 콜
                try:
                    get_link_title = comment.find_element_by_css_selector(
                        ".link_title")

                    # 내가 단 댓글에 다다를 경우
                    if row['channel_title'] == get_link_title.text:
                        logger.info(row['channel_title'] + " - " + row['post_title'] + " 댓글 달기 종료")
                        break

                    try:
                        comment.find_element_by_css_selector(
                            ".channel_emoticon")
                    except:
                        raise Exception(row['channel_title'] + " - " + row['post_title'] + " 이모티콘 아닌건 패스")

                    get_link_title.click()
                    check_reply = True
                    time.sleep(0.1)
                    logger.info(row['channel_title'] + " - " + row['post_title'] + " - " + get_link_title.text + "태그")
                except Exception as e:
                    logger.info(e)

            if not check_reply:
                raise Exception(row['channel_title'] + " - " + row['post_title'] + " 댓글 안 달림")

            time.sleep(1)

            get_submit_button = _driver.find_element_by_css_selector(".btn_type2")

            get_submit_button.click()
            logger.info(row['channel_title'] + " - " + row['post_title'] + " 댓글 달림")

            time.sleep(3)

            _driver.save_screenshot(_tmp_folder + row['post_title'] + '.png')

            s3_client.upload_file(_tmp_folder + row['post_title'] + '.png', os.getenv('STORAGE_BUCKET_NAME'),
                                  'debug/' + row['post_title'] + '.png')

        except Exception as e:
            logger.info(e)
        finally:
            _driver.quit()
            db = pymysql.connect(os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
                                 password=os.getenv('DB_PASSWD'), database=os.getenv('DB_DATABASE'), connect_timeout=5,
                                 charset='utf8mb4', autocommit=True)
            dbcur = db.cursor()
            dbcur.execute(
                """
                UPDATE `Post` post
                JOIN `Reply` reply
                ON post.id = reply.post_id
                SET reply.execute_time = NOW()
                WHERE post.id = '{}'
                """.format(row['id']))
            db.close()

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
        db = pymysql.connect(os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
                             password=os.getenv('DB_PASSWD'), database=os.getenv('DB_DATABASE'), connect_timeout=5,
                             charset='utf8mb4')

        logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

        if check_table_exists(db, 'Post'):
            dbcur = db.cursor(pymysql.cursors.DictCursor)
            # TODO 이게 최적화는 아니겠지 당연히...
            dbcur.execute("""
                                SELECT * FROM `Post` post 
                                JOIN `Reply` reply 
                                ON post.id = reply.post_id
                                JOIN `Channel` channel
                                ON post.channel_id = channel.id
                                JOIN `auth_user` owner
                                ON channel.owner_id = owner.id
                                JOIN `auth_user_profile` owner_profile
                                ON channel.owner_id = owner_profile.user_id
                                WHERE reply.trigger IS TRUE 
                                AND reply.start_time <= NOW() 
                                AND reply.end_time >= NOW()
                                AND TIMESTAMPDIFF(SECOND, reply.execute_time, NOW()) >= interval_time*60
                                AND owner_profile.cookie_status = '1' OR owner_profile.cookie_status = '3'                              
                                """)
            rows = dbcur.fetchall()
            db.close()

            logger.info("SUCCESS: Termination to RDS mysql instance succeeded")

            if not rows:
                raise Exception("실행될 레코드가 없습니다.")

            logger.info("실행될 레코드 수 : " + str(len(rows)))

            max_loop_count = 10
            rows_length = len(rows)
            if rows_length > max_loop_count:
                rows_length = max_loop_count
            count = rows_length * 3 + 3
            for i in range(2, count, 3):
                random_num_dict[i] = 'ready'

            executor = concurrent.futures.ThreadPoolExecutor(max_loop_count)
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
