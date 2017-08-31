# -*- coding: utf-8 -*-

import mysql.connector
from mysql.connector import errorcode
import logging
import json
import os
import time

logger = logging.getLogger('info')
# TODO: An API to exec queries without SQL
# QUERY = {
#     'insert': "INSERT INTO repo.repo_{0} (projID, projName, location, revision, star, license, branch) VALUES ({1}, '{2}', '{3}', '{4}', {5}, '{6}', '{7}');",
#     'select': "SELECT * FROM repo.repo_{0} WHERE projID={1};",
#     'update': "UPDATE repo.repo_{0} SET {1}={2} WHERE projID={3};"
# }
BASE = "INSERT INTO repo.repo_{0} (projID, projName, location, revision, star, license, branch) VALUES ({1}, '{2}', '{3}', '{4}', {5}, '{6}', '{7}');"
INFO = "SELECT * FROM repo.repo_{0} WHERE projID={1};"
UPDATE = "UPDATE repo.repo_{0} SET {1} WHERE projID={2};"
config = dict(user='root', password='Xei1LuQuaeCheegu', host='121.42.59.117', database='repo')
RETRY = 3


class SqlConn(object):
    def __init__(self, language):
        self.language = language
        self.conn = None
        self.start_connect()

    def __del__(self):
        self.conn.close()

    def start_connect(self):
        try:
            self.conn = mysql.connector.connect(**config)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                logger.error('Wrong username or password')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logger.error('Database not exist')
            else:
                logger.error(err)

    def reconnect(self):
        self.conn.close()
        time.sleep(20)
        self.start_connect()
        logger.warn("Connection reestablished.")

    def exec_queries(self, queries):
        """
        execute a list of SQL queries
        :param queries: list() of SQL queries
        """
        retry = RETRY
        while retry > 0:
            try:
                cur = self.conn.cursor()
                for query in queries:
                    cur.execute(query)
                self.conn.commit()
                cur.close()
                break
            except mysql.connector.errors.OperationalError, e:
                logger.error("MySQL Error for while execute queries: %s" % e)
                self.reconnect()
                retry -= 1
                continue
            except Exception, e:
                logger.error(e)
                retry -= 1

    def project_info(self, project_id):
        """
        get project info, return None if not exist
        :param language: language now processing
        :param project_id: projectID to search in DB
        :return: tuple of info in DB of this project, or None if not exist
        """
        retry = RETRY
        while retry > 0:
            try:
                cur = self.conn.cursor()
                cur.execute(INFO.format(self.language, project_id))
                r = cur.fetchone()
                cur.close()
                return r
            except mysql.connector.errors.OperationalError, e:
                logger.error("MySQL Error for project %s: %s" % (project_id, e))
                self.reconnect()
                retry -= 1
                continue
            except Exception, e:
                logger.error("%s meets error: %s" % (project_id, e))
                retry -= 1
        return None

    def check_updated(self, project_id, revision):
        r = self.project_info(project_id)
        if r is None:
            return True
        elif str(r[3]) != str(revision):
            return True
        else:
            return False

    def update_field_str(self, fields):
        """
        get field string in UPDATE SQL.
        :param fields: dict() contains fields to update.
        :return: a string that {1} in UPDATE
        """
        columns = []
        for (k, v) in fields.items():
            columns.append("{0}='{1}'".format(k, v))
        return ",".join(str)


def info_to_db(language, infoPath, outputPath):
    try:
        info_file = open(infoPath, 'r')
        items = json.load(info_file)
    except Exception, e:
        logger.error("Can not find info.json: %s" % e)
        return

    queries = []
    conn = SqlConn(language)
    for item in items:
        dir_name = "{id}_{fullname}".format(id=item["id"], fullname=item["full_name"].replace('/', '_'))
        project_path = os.path.join(outputPath, dir_name)
        if os.path.exists(project_path):
            if conn.project_info(item["id"]) is None:
                query = BASE.format(language, item["id"], item["full_name"], project_path.replace('\\', '\\\\'),
                                    item["pushed_at"], item["stargazers_count"], "Unknown", item["default_branch"])
            else:
                columns = dict(revision=item["pushed_at"], star=item["stargazers_count"])
                query = UPDATE.format(language, conn.update_field_str(columns))
            queries.append(query)

    conn.exec_queries(queries)
    del conn


def test():
    conn = cur = None
    try:
        conn = mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        print err
    else:
        cur = conn.cursor()
        cur.execute('SELECT * FROM repo.repo_Java WHERE projID=286803541;')
        # for row in cur.fetchall():
        #     print row

        a = cur.fetchone()
        print a

        # cur.execute(
        #     "INSERT INTO repo.repo_Java (projID, projName, location, revision, star, license, branch) VALUES (69842894, 'KingsMentor/IntentManip', '69842894_KingsMentor_IntentManip', '2016-10-12T14:55:50Z', 41, 'Unknown', 'master');")
        # conn.commit()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == '__main__':
    test()
