# -*- coding: utf-8 -*-

import logging
import urllib
import urllib2
import json
import zipfile
import os
import shutil
import time
from datetime import date, timedelta

logger = logging.getLogger('info')
BASE = 'https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&access_token={token}&per_page=100&page={page}'
TOKEN = 'a1d6546e8874cfefb5cb5025ae096c20e48bc49e'
ZIP = 'https://github.com/{fullname}/archive/{branch}.zip'

items = []


def fetch_by_day(language, day, minStar):
    query = urllib.quote('created:{d} language:{l} stars:>{s}'.format(d=day, l=language, s=minStar))
    page = 1
    retry = 3
    while (True):
        url = BASE.format(query=query, token=TOKEN, page=page)
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) Chrome/53.0.2785.104 RepoDownloader/0.2')
        try:
            r = urllib2.urlopen(req)
            repo_info = json.loads(r.read())
        except Exception, e:
            logger.error("%s(%s) connection error: %s" % (day, page, e))
            if retry > 0:
                retry -= 1
                time.sleep(60)
                continue
            return

        global items
        items.extend(repo_info["items"])

        if repo_info["total_count"] <= page * 100:
            break
        page += 1

    logger.info("Fetched %s projects on %s" % (repo_info["total_count"], day))


def fetch_all(language, startDate, days, minStar, infoPath):
    year, month, day = [int(i) for i in startDate.split('-')]
    try:
        start_day = date(year, month, day)
    except ValueError, e:
        logger.error("Wrong startDate: %s", e)
        return

    if days < 0:
        end_day = date.today()
    else:
        end_day = start_day + timedelta(days=days)

    now_day = start_day
    one_day = timedelta(days=1)
    while (now_day != end_day):
        fetch_by_day(language, now_day.isoformat(), minStar)
        now_day += one_day

    global items
    try:
        info_file = open(infoPath, 'w')
        json.dump(items, info_file)
        info_file.close()
        logger.info("Fetch info successful.")
    except Exception, e:
        logger.error("Error while writing info: %s" % e)


def download(item, outputPath):
    """
    Download one project based on fetched info
    :param item: a dict that contains `id` and `full_name`
    :param outputPath: a string of directory path to save projects
    :return:
    """
    tmp_file = os.path.join(outputPath, "github.zip")
    if os.path.exists(tmp_file):
        os.remove(tmp_file)
    url = ZIP.format(fullname=item["full_name"], branch=item["default_branch"])

    try:
        u = urllib2.urlopen(url, timeout=300)
        f = open(tmp_file, 'wb')
        block_size = 8192
        while (True):
            buffer = u.read(block_size)
            if not buffer:
                break
            f.write(buffer)
        f.close()
    except Exception, e:
        logger.error("Wrong while downloading .zip file of %s: %s" % (item["id"], e))
        return

    try:
        dir_name = "{id}_{fullname}".format(id=item["id"], fullname=item["full_name"].replace('/', '_'))
        project_path = os.path.join(outputPath, dir_name)
        if os.path.exists(project_path):
            logger.warn("%s new revision! older project will be deleted." % dir_name)
            shutil.rmtree(project_path, ignore_errors=True)
        assert os.path.exists(project_path) is False
        os.mkdir(project_path.replace('\\', '\\\\'))

        zf = zipfile.ZipFile(tmp_file, 'r')
        zf.extractall(project_path)
        zf.close()
    except Exception, e:
        logger.error("Wrong while unzip file for %s: %s" % (item["id"], e))
        return
    logger.info("Downloaded and unzipped %s" % dir_name)


def download_all(infoPath, outputPath, connection, pause_id=None):
    global items
    if len(items) < 1:
        info_file = open(infoPath, 'r')
        items = json.load(info_file)
    logger.info("Downloading total %s projects" % len(items))

    if pause_id != None:
        paused = True
    else:
        paused = False

    for item in items:
        if paused:
            if str(item["id"]) != str(pause_id):
                continue
            else:
                paused = False
                logger.info("Restarted from next project of %s" % pause_id)
                continue

        if connection.check_updated(item["id"], item["pushed_at"]):
            download(item, outputPath)
