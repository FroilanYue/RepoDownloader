# -*- coding: utf-8 -*-

import os
import argparse
import sys

SUFFIX = {
    'C': ['.c', '.h', '.cpp', '.hpp', '.cc'],
    'C++': ['.c', '.h', '.cpp', '.hpp', '.cc'],
    'Java': ['.java'],
    'JavaScript': ['.js'],
    'Python': ['.py'],
    'C#': ['.cs']
}


def normalize(language, root_path):
    """
    Post order traversal to normalize repo,
    only leave source code files.
    :param language: language now processing
    :param root_path: root path of repo
    :return:
    """
    if os.path.isdir(root_path):
        files = os.listdir(root_path)
        for file in files:
            normalize(language, os.path.join(root_path, file))
        if len(os.listdir(root_path)) == 0:
            os.rmdir(root_path)

    if os.path.isfile(root_path):
        is_source = False
        for s in SUFFIX[language]:
            if root_path.endswith(s):
                is_source = True
        if not is_source:
            os.remove(root_path)


def main():
    parser = argparse.ArgumentParser(description="wipe except source code files.")
    parser.add_argument('language', choices=['C', 'C++', 'Java', 'JavaScript', 'Python', 'C#'],
                        help="programming language to process")
    parser.add_argument('path', help="repo root path")
    args = parser.parse_args(sys.argv[1:])

    affirm = raw_input("Are you sure to normalize %s ?\nThis operation is **irreversible**.[y/N]" % args.path)

    if affirm.lower() == "y" or affirm.lower() == "yes":
        normalize(args.language, args.path)


if __name__ == '__main__':
    main()
