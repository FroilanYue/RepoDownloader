# -*- coding: utf-8 -*-

import os
import re
import logging
import argparse
import sys

logger = logging.getLogger('tool')
BASE = "UPDATE repo.repo_{0} SET license='{1}' WHERE projID={2};"
BATCHSIZE = 32

LICENSE = {
    "Academic Free License 3.0": "AFL-3.0",
    "Affero General Public License 3.0": "AGPL-3.0",
    "Affero General Public License": "AGPL",
    "Apache License version 2.0": "Apache v2",
    "Apache License": "Apache",
    "http://www.apache.org/licenses/": "Apache",
    "Apple Public Source License": "APSL-2.0",
    "BSD 3-Clause License": "BSD-3-Clause",
    "BSD 2-Clause License": "BSD-2-Clause",
    "BSD License": "BSD",
    "Common Development and Distribution License": "CDDL",
    "Eclipse Public License": "EPL",
    "GNU General Public License version 3": "GPLv3",
    "GNU General Public License version 2": "GPLv2",
    "GNU General Public License": "GPL",
    "GNU Library General Public License": "LGPL",
    'GNU Library or "Lesser" General Public License': "LGPL",
    "The MIT License": "MIT",
    "Mozilla Public License 2.0": "MPL-2.0",
    "Mozilla Public License": "MPL",
    "Microsoft Community License": "Ms-CL",
    "Microsoft Public License": "Ms-PL",
    "Microsoft Reciprocal License": "Ms-RL",
    "W3C License": "W3C"
}


def find_license_file(root_path):
    license_ptn = re.compile(r"LICEN[S|C]E", re.IGNORECASE)
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if license_ptn.match(file):
                return os.path.join(root, file)
    return None


# TODO:add Unknown
def extract(license_file):
    try:
        f = open(license_file, 'r')
        text = f.read()
        f.close()
    except Exception, e:
        logger.error("Wrong while reading license file")
        return "Custom"

    for (pattern, license) in LICENSE.items():
        if re.match(pattern.strip(), text.strip(), re.IGNORECASE):
            return license
    return "Custom"


def extract_all(language, repo_path, connection):
    queries = []
    projects = os.listdir(repo_path)
    dir_ptn = re.compile(r"^(\d+)_([^_]+)_(.+)$")
    batch_size = 0
    for project in projects:
        m = dir_ptn.match(project)
        if not m:
            logger.error("cannot get ID of %s" % project)
            continue
        project_id = m.group(1)

        if connection.project_info(project_id) == None:
            logger.warn("Project %s don't exist in DB." % project_id)
            continue

        project_path = os.path.join(repo_path, project)
        license_file = find_license_file(project_path)
        if license_file is None:
            logger.warn("No license file found for %s." % project_id)
            continue

        license = extract(license_file)
        queries.append(BASE.format(language, license, project_id))
        logger.info("Found %s licensed %s" % (project_id, license))

        batch_size += 1
        if batch_size % BATCHSIZE == 0:
            connection.exec_queries(queries)
            batch_size = 0
            queries = []

    connection.exec_queries(queries)
    logger.info("License info has already been saved to DB.")


def main():
    parser = argparse.ArgumentParser(description="extract license and save to MySQL.")
    parser.add_argument('language', choices=['C', 'C++', 'Java', 'JavaScript', 'Python', 'C#'],
                        help="programming language to process")
    parser.add_argument('path', help="repo root path")
    args = parser.parse_args(sys.argv[1:])

    sys.path.append("..")
    from db_interface.sql_conn import SqlConn

    conn = SqlConn(args.language)
    extract_all(args.language, args.path, conn)
    del conn


if __name__ == '__main__':
    main()
