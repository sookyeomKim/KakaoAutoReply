import os
import sys
import logging

import json
import pymysql

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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

def lambda_handler(event, context):
    try:
        db = pymysql.connect(os.getenv('DB_HOST'), user=os.getenv('DB_USER'),
                             password=os.getenv('DB_PASSWD'), database=os.getenv('DB_DATABASE'), connect_timeout=5,
                             charset='utf8mb4', autocommit=True)

        logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

        if check_table_exists(db, 'Post'):
            dbcur = db.cursor(pymysql.cursors.DictCursor)
            dbcur.execute("""
                                SELECT * FROM `Reply` reply
                                WHERE reply.end_time < NOW()
                                AND reply.trigger = TRUE
                                """)

            rows = dbcur.fetchall()

            if not rows:
                raise Exception("실행될 레코드가 없습니다.")

            logger.info("실행될 레코드 수 : " + str(len(rows)))

            for row in rows:
                logger.info(str(row['id']) + "번 태스크 종료")
                dbcur.execute(
                    """
                    UPDATE `Reply` reply
                    SET reply.trigger = FALSE 
                    WHERE reply.id = '{}'
                    """.format(row['id']))
            db.close()
            logger.info("SUCCESS: Termination to RDS mysql instance succeeded")

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
