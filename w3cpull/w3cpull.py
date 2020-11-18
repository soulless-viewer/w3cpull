'''
W3Cpull

Usage:
    w3cpull --community-url=COMMUNITY_URL --target-dir=TARGET_DIR_PATH [--temp-dir=TEMP_DIR_PATH] [--w3id-auth=W3ID_AUTH] [--browser=BROWSER] [--recursive] [--visual]
    w3cpull -h | --help
    w3cpull -v | --version

Options:
    --community-url=COMMUNITY_URL   Set the URL of the target community
    --target-dir=TARGET_DIR_PATH    Set the path to the directory where the content will be saved
    --temp-dir=TEMP_DIR_PATH        Set the path to the folder where the content will be temporarily stored and processed (by default, /tmp)
    --w3id-auth=W3ID_AUTH           Set the uername:password value for automatic authentication
    --browser=BROWSER               Set the name of the browser to use (by default, Firefox)
    --recursive                     Set the recursive execution type (with subcommunity processing)
    --visual                        Set the visual execution type (with the browser open)
    -h, --help                      Show this help message.
    -v, --version                   Show the version.
'''

from schema import Schema, And, Or, Use, Optional, Regex, SchemaError
from docopt import docopt
from w3cpull import downloader as down
import logging as log
import datetime
import hashlib
import shutil
import time
import json
import sys
import os

SELENIUM_DEFAULT_DIR = '/tmp'
CONTENT_DIR = None
COMPLETED_STATUS = None

log.basicConfig(
    stream=sys.stdout,
    level=log.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)

def hash_path(location):
    return os.path.join(
        os.path.abspath(SELENIUM_DEFAULT_DIR),
        hashlib.md5(
            (
                "{0}_{1}".format(
                    location,
                    datetime.datetime.now(datetime.timezone.utc)
                    .replace(microsecond=0)
                    .astimezone()
                    .isoformat()
                ).encode("utf-8")
            )
        ).hexdigest()
    )

def validate_args(args):
    schema = Schema({
        '--community-url': Or(None,
            Regex(r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?!&//=]*)$'),
            error='The URL has an incorrect format'),
        '--target-dir': Or(None,
            Use(lambda d: (os.path.exists(d) and os.listdir(d)) or (os.path.exists(os.path.expanduser(d)) and os.listdir(os.path.expanduser(d)))),
            error = 'The target path does not exist or cannot be accessed'),
        '--temp-dir': Or(None,
            Use(lambda d: os.listdir(d)),
            error = 'The temporarily path does not exist or cannot be accessed'),
        '--w3id-auth': Or(None,
            Regex(r'^[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}\:.+$'),
            error = 'The credentials for W3ID are in the wrong format'),
        '--browser': Or(None,
            Regex(r'^((C|c)hrome|(F|f)irefox)$'),
            error='Specified browser not supported. Use Chrome or Firefox'),
        '--recursive': Or(True, False),
        '--visual': Or(True, False),
        '--help': Or(True, False),
        '--version': Or(True, False)
    })

    try:
        schema.validate(args)
        if not args['--community-url'] == None:
            if not down.check_if_url_accessible(args['--community-url']):
                log.error('The community URL does not exist or is unavailable')
                return False
        if not args['--visual']:
            if args['--w3id-auth'] == None:
                log.error('If you want to launch the app without opening the browser you must provide the w3id credentials')
                return False
    except SchemaError as e:
        log.error(e)
        return False

    return True

def download(community_url, target_dir, temp_dir, w3id_auth, recursive, visual, browser):
    global COMPLETED_STATUS
    global CONTENT_DIR
    global TEMP_TARGET_DIR
    global TEMP_DOWNLOAD_DIR

    COMPLETED_STATUS = False

    content_dir = None

    w3id_login = None
    w3id_password = None

    if not w3id_auth == None:
        w3id_login, w3id_password = w3id_auth.split(':', 1)

    TEMP_DOWNLOAD_DIR = os.path.abspath(hash_path('TEMP_DOWNLOAD_DIR'))
    TEMP_TARGET_DIR = os.path.abspath(hash_path('TARGET_DIR'))

    MODULE_DIR = down.__file__.rsplit('/', 1)[0]

    driver = down.init(MODULE_DIR, TEMP_TARGET_DIR, TEMP_DOWNLOAD_DIR, visual, browser)
    driver.implicitly_wait(10)

    try:
        log.info("Step 1/3 : Scanning the community and building the structure tree")
        communities_tree = down.create_communities_tree(driver, community_url, recursive, w3id_login, w3id_password)

        log.info("Step 2/3 : Creating a structure tree in the file system")
        communities_fs_mapping = down.create_fs_tree(TEMP_TARGET_DIR, communities_tree)

        log.info("Step 3/3 : Downloading community content")
        down.download_community(driver, communities_fs_mapping, TEMP_DOWNLOAD_DIR)
        if not target_dir == None:
            target_dir = (os.path.abspath(target_dir) if not target_dir[0] == '~' else os.path.expanduser(target_dir))
            try:
                content_dir = down.move_content(TEMP_TARGET_DIR, target_dir)[0]
                log.info("--- The structure and content of the community now in the {}".format(content_dir))
                shutil.rmtree(TEMP_TARGET_DIR)
            except shutil.Error as e:
                log.warning(e)
                log.info("--- The structure and content of the community now in the {}".format(TEMP_TARGET_DIR))
        else:
            content_dir = os.path.join(os.path.abspath(TEMP_TARGET_DIR), os.listdir(os.path.abspath(TEMP_TARGET_DIR))[0])

        COMPLETED_STATUS = True
    finally:
        down.finish(driver)

    CONTENT_DIR = content_dir

    return COMPLETED_STATUS


def main():
    args = docopt(__doc__, version='1.0.3')

    if validate_args(args):
        if not args['--temp-dir'] == None:
            SELENIUM_DEFAULT_DIR = args['--temp-dir']

        start_time = time.time()
        COMPLETED_STATUS = download(
            args['--community-url'],
            args['--target-dir'],
            args['--temp-dir'],
            args['--w3id-auth'],
            args['--recursive'],
            args['--visual'],
            args['--browser']
        )
        finish_time = time.time()

        shutil.rmtree(TEMP_DOWNLOAD_DIR)

        log.info("EXECUTION TIME: {0}, COMPLETED SUCCESSFULLY: {1}".format(str(datetime.timedelta(seconds=finish_time-start_time)), COMPLETED_STATUS))
        if not COMPLETED_STATUS:
            log.info('''
                TIP: Analyze the logs, try to find and fix the problem, and then perform the action again.
                If you can\'t find or fix the problem, please contact support.
                Sometimes it\'s enough to wait to solve a problem.
            ''')
