# -*- coding: utf-8 -*-

import argparse
import sys
import os
import logging
import logging.config
from datetime import date
from web_interface.github_crawl import fetch_all, download_all
from db_interface.sql_conn import SqlConn, info_to_db
from tools import licenser, normalizer

logging.config.fileConfig('log/logging.config')
logger = logging.getLogger('info')


def main():
    parser = argparse.ArgumentParser(description='crawl repo info, download repo, then save info to MySQL')
    parser.add_argument('language', choices=['C', 'C++', 'Java', 'JavaScript', 'Python', 'C#'],
                        help='Programming language to download')
    parser.add_argument('startDate',
                        help='Start date in format YYYY-MM-DD')
    parser.add_argument('-d', '--days', default=-1, type=int,
                        help='days to download, default till today')
    parser.add_argument('-m', '--minStar', default=0, type=int,
                        help='threshold of star, default 0')
    parser.add_argument('-o', '--output', required=True,
                        help='output repo dir')
    parser.add_argument('--noinfo', action='store_true',
                        help='if set, not crawl new info, use crawled info today')
    parser.add_argument('--nodownload', action='store_true',
                        help='if set, not download repo, only fetch info')
    parser.add_argument('--nodb', action='store_true',
                        help='if set, not save repo info to MySQL')
    parser.add_argument('--licenser', action='store_true',
                        help='activate tool to extract project license and save to MySQL')
    parser.add_argument('--normalizer', action='store_true',
                        help='activate tool to delete irrelevant file and only leave source code file')
    parser.add_argument('--pauseID', default=None,
                        help='give an project ID & restart from the breakpoint')
    args = parser.parse_args(sys.argv[1:])
    print args

    if not os.path.isdir(args.output):
        logger.error("output path is not directory.")
        return
    logger.info("Downloading %s repo from %s with stars more than %d" % (args.language, args.startDate, args.minStar))

    info_path = os.path.join(args.output, "info_%s.json" % date.today().isoformat())
    conn = SqlConn(args.language)
    if not args.noinfo:
        logger.info("start crawling info.")
        fetch_all(args.language, args.startDate, args.days, args.minStar, info_path)
    if not args.nodownload:
        logger.info("start downloading repo.")
        download_all(info_path, args.output, conn, args.pauseID)
    if not args.nodb:
        logger.info("start writing info to MySQL.")
        info_to_db(args.language, info_path, args.output)
    if args.licenser:
        logger.info("start extracting licenses.")
        licenser.extract_all(args.language, args.output, conn)
    if args.normalizer:
        logger.info("start normalizing.")
        normalizer.normalize(args.language, args.output)


if __name__ == '__main__':
    main()
