import os
import sys
import logging

import json
import _pickle as c_pickle
from datetime import datetime

import concurrent.futures

import boto3
import boto3.session

import pymysql

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
        cookie_state = "2"
        session = boto3.session.Session(aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
                                        aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
                                        region_name='ap-northeast-2')
        s3_client = session.client('s3')
        try:
            s3_response = s3_client.get_object(Bucket=os.getenv('STORAGE_BUCKET_NAME'),
                                               Key='uploads/cookies/' + row['username'].replace("@", "") + '.pkl')
            get_cookies = s3_response['Body'].read()

            get_cookie_list = c_pickle.loads(get_cookies)

            try:
                # 쿠키 생성 시간 + 1day - 3hour = expire_datetime_1
                # *카카오가 왜 -3시간을 했는지는 모르겠네 멀까
                expire_datetime_1 = datetime.fromtimestamp(int(get_cookie_list[0]['value']))

                # 쿠기 생성 시간 + 1day = expire_datetime_2(로그인 유지 체크 해제)
                # 쿠기 생성 시간 + 1month = expire_datetime_2(로그인 유지 체크 설정)
                # expire_datetime_2 = datetime.fromtimestamp(int(get_cookie_list[1]['value']))

                current_time = datetime.now()

                activate_time = expire_datetime_1 - current_time

                activate_time_second = activate_time.total_seconds()

                if activate_time_second <= 0:  # 인증이 만료됨
                    cookie_state = "0"
                elif activate_time_second >= 10800:  # 인증 중
                    cookie_state = "1"
                elif activate_time_second < 10800:  # 인증시간이 거의 끝나감
                    cookie_state = "3"
            except Exception as e:
                cookie_state = "4"
                logger.info(e)
                logger.info("인증되지 않은 쿠키입니다.")
        except Exception as e:
            logger.info(e)
            logger.info("쿠키가 존재하지 않습니다.")
        finally:
            db = pymysql.connect(os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
                                 password=os.getenv('DB_PASSWD'), database=os.getenv('DB_DATABASE'), connect_timeout=5,
                                 charset='utf8mb4', autocommit=True)
            dbcur = db.cursor(pymysql.cursors.DictCursor)
            dbcur.execute(
                """
                UPDATE `auth_user` owner
                JOIN `auth_user_profile` profile
                ON owner.id = profile.user_id
                SET profile.cookie_status = '{1}', profile.modify_date = NOW()
                WHERE owner.id = '{0}'
                """.format(row['id'], cookie_state))
            db.close()
            logger.info(row['username']+" 상태 갱신 완료")
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
