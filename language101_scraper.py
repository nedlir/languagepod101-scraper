#!/usr/bin/env python3
# language101 scraper helps you scrape full language courses from sites like
# japanesepod101.com, spanishpod101.com, chineseclass101.com and more!

import argparse
import configparser
from os.path import expanduser
from os import path

from getpass import getpass
import pickle
import random
import time

import json
import os

from sys import exit
from urllib.parse import urlparse

import requests

from bs4 import BeautifulSoup
import anki_export

import logging

MAJOR_VERSION = 0
MINOR_VERSION = 5
PATCH_LEVEL = 3

VERSION_STRING = str(MAJOR_VERSION) + "." + \
    str(MINOR_VERSION) + "." + str(PATCH_LEVEL)
__version__ = VERSION_STRING

FAKE_BROWSER_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.366",
    "accept-language": "en-US,en;q=0.9,ja;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-fetch-mode":
    "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1"
}


class LanguagePod101Downloader:
    """Wrapper class for storing states e.g. arguments or config states"""

    def __init__(self, args):
        self.m_arguments = vars(args)
        self.sanity_check()

    def sanity_check(self):
        boolean_values = ["video", "audio", "document", "anki_deck"]
        for i in ["video", "audio", "document", "anki_deck"]:
            if type(self.m_arguments.get(i)) is not bool:
                self.m_arguments[i] = self.m_arguments.get(i).lower() in [
                    'true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']  # convert to bool

        for i in ["min_delay", "max_delay"]:
            if type(self.m_arguments.get(i)) is str:
                self.m_arguments[i] = int(self.m_arguments.get(i))

        minD = self.m_arguments.get("min_delay")
        maxD = self.m_arguments.get("max_delay")
        # check if min and max value are really min and max
        if type(minD) is int and type(maxD) is int:
            # Do the old switcheroo if necessary and bind to a minimum of zero
            self.m_arguments["min_delay"] = max(0, min(minD, maxD))
            self.m_arguments["max_delay"] = max(0, max(minD, maxD))
            if self.m_arguments["min_delay"] != minD or self.m_arguments.get("max_delay") != maxD:
                logging.warning("Delay is not correctly set. New delay is: ")
                logging.warning("min:" + str(self.m_arguments["min_delay"]))
                logging.warning("max:" + str(self.m_arguments["max_delay"]))

        debugConfigWithoutPassword = self.m_arguments
        # no need for blasting out the password in a log
        debugConfigWithoutPassword["password"] = 8 * "*"
        logging.debug(debugConfigWithoutPassword)

    def parse_url(self, url):
        """Parse the course URL"""
        obj = urlparse(url)
        root_url = f'{obj.scheme}://{obj.netloc}'
        login_url = f'{root_url}/member/login_new.php'

        return root_url, login_url

    def place_cookie(self, session_cookie):
        cookiepath = expanduser("~") + "/.config/languagepod101/"
        cookie_file = "lastsession"
        if not path.exists(cookiepath):
            mkdir(cookiepath)
        with open(cookiepath + cookie_file, 'wb') as f:
            pickle.dump(session_cookie, f)

    def load_cookie(self):
        cookiepath = expanduser("~") + "/.config/languagepod101/"
        cookie_file = "lastsession"
        if not path.exists(cookiepath+cookie_file):
            return None
        with open(cookiepath + cookie_file, 'rb') as f:
            try:
                content = pickle.load(f)
                return content
            except Exception as e:
                logging.error(e)
                logging.error("Restoring from cookie failed")
        return None

    def check_if_authenticated(self, response):
        returnValue = False
        try:
            response.raise_for_status()
        except Exception as e:
            logging.error(e)
            logging.error(
                'Could not reach site. Please check URL and internet connection.')
            exit(1)

        if 'X-Ill-Member' not in response.headers:
            return False
        return True

    def authenticate(self, url, username, password):
        """Logs in to the website via an old session or a new one"""
        root_url, login_url = self.parse_url(url)

        logging.debug(f'Trying to log in to {root_url}')
        self.m_session = requests.Session()
        cachedSession = False
        loadCookie = self.load_cookie()
        self.m_session.headers.update(FAKE_BROWSER_HEADERS)

        if loadCookie is not None:
            self.m_session.cookies.update(loadCookie)
            response = self.m_session.post(login_url)
            if self.check_if_authenticated(response):
                logging.info('Sucessfully logged in via old session.')
                cachedSession = True
                return
        if not cachedSession:
            credentials = {'amember_login': username, 'amember_pass': password}
            response = self.m_session.post(login_url, data=credentials)
            self.place_cookie(self.m_session.cookies.get_dict())
            if self.check_if_authenticated(response):
                logging.info('Sucessfully logged in with new session.')
                return
        if not self.check_if_authenticated(response):
            logging.error('Could not log in. Please check your credentials.')
            exit(1)

    def download_audios(self, lesson_number, lesson_soup):
        """Download the audio files of a lesson"""
        audio_soup = lesson_soup.find_all('audio')

        if audio_soup:
            logging.info(
                f'Downloading Lesson {str(lesson_number).zfill(2)} - {lesson_soup.title.text} audio')
            for audio_file in audio_soup:
                try:
                    file_url = audio_file['data-trackurl']
                except Exception as e:
                    logging.debug(e)
                    logging.debug(
                        'Tag "data-trackurl" was not found, trying to reach "data-url" tag instead')
                    try:
                        file_url = audio_file['data-url']
                    except Exception as e:
                        logging.error(e)
                        logging.error(f'Could not retrieve URL: {file_url}')
                        continue

                # Verifies that the file is 'mp3' format, if so, builds a clean str name for the file:
                if file_url.endswith('.mp3'):
                    logging.debug(f'Successfully retrieved URL: {file_url}')

                    # Create a clean filename string with prefix, body, suffix and extension.
                    # Files are numbered using the 'lesson_number' variable
                    file_prefix = str(lesson_number).zfill(2)
                    file_body = self.get_filename_body(lesson_soup)

                    file_suffix = file_url.split('/')[-1]
                    # Verifies clean version of file name by removing junk suffix string that may appear:
                    if 'dialog' in file_suffix.lower() or 'dialogue' in file_suffix.lower():
                        file_suffix = 'Dialogue'
                    elif 'review' in file_suffix.lower():
                        file_suffix = 'Review'
                    else:
                        file_suffix = 'Main Lesson'

                    file_ext = file_url.split('.')[-1]
                    file_name = f'{file_prefix} - {file_body} - {file_suffix}.{file_ext}'

                    self.save_file(file_url, file_name)

    def download_vocabulary(self, root_url, lesson_soup):
        """Download the vocabulary, currently only japanese is supported. This should be extended """
        voc_scraper = anki_export.Language()
        downloadList = []
        if root_url.lower().find("japanese") != -1:
            voc_scraper = anki_export.Japanese()
            downloadList = voc_scraper.Scraper(root_url, lesson_soup)
        else:
            logging.warning("Unknown language")

        for i in downloadList:
            name = i.split('/')[-1]
            self.save_file(i, name)
        voc_scraper.CreateDeck(lesson_soup.title.text)

    def download_pdfs(self, root_url, lesson_soup):
        """Download the PDF files of a lesson"""
        # Beware: Access to PDFs requires Basic or Premium membership
        pdf_links = lesson_soup.select('#pdfs a')
        if pdf_links:
            for pdf_link in pdf_links:
                pdf_url = pdf_link.get('href')
                if pdf_url.startswith('/pdfs/'):
                    pdf_url = root_url + pdf_url
                pdf_name = pdf_url.split('/')[-1]
                self.save_file(pdf_url, pdf_name)

    def download_videos(self, lesson_number, lesson_soup):
        """Download the video files of a lesson"""
        video_soup = lesson_soup.find_all('source')

        if video_soup:
            logging.info(
                f'Downloading Lesson {str(lesson_number).zfill(2)} - {lesson_soup.title.text} video')
            for video_file in video_soup:
                try:
                    if video_file['type'] == 'video/mp4':
                        if self.m_arguments["download_all_videos"] or video_file['data-quality'] == 'h' or video_file['data-quality'] == 'm':
                            file_url = video_file['src']
                    else:
                        continue
                except Exception as e:
                    logging.warning(e)
                    logging.warning(
                        'Could not find out the URL for this lesson\'s video.')
                    continue

                # Verifies that the file is in 'mp4' or 'm4v' format.
                # If so, builds a clean str name for the file:
                if file_url.endswith('.mp4') or file_url.endswith('.m4v'):
                    logging.debug(f'Successfully retrieved URL: {file_url}')

                    # Create a clean file name string with prefix, body and extension.
                    # Files are numbered using the 'lesson_number' variable
                    file_prefix = str(lesson_number).zfill(2)
                    file_body = self.get_filename_body(lesson_soup)
                    file_ext = file_url.split('.')[-1]
                    file_name = f'{file_prefix} - {file_body}.{file_ext}'

                    self.save_file(file_url, file_name)

    def get_filename_body(self, lesson_soup):
        """Generate main body of filename from page's title"""
        filename_body = lesson_soup.title.text

        # Sanitize filename. It avoids `OSError: [Errno 22]` while file writing
        # and some potentially problematic characters in filenames
        invalid_chars = '#%&\/?:*"<>{|}\t'
        for char in invalid_chars:
            filename_body = filename_body.replace(char, '')

        return filename_body

    def get_soup(self, url):
        """Return the BeautifulSoup object for the given URL"""
        res = self.m_session.get(url)
        try:
            res.raise_for_status()
        except Exception as e:
            logging.error(e)
            logging.error(
                'Could not download web page. Please make sure the URL is accurate.')
            exit(1)

        try:
            soup = BeautifulSoup(res.text, 'lxml')
        except Exception as e:
            logging.error(e)
            logging.error(
                'Failed to parse the webpage, "lxml" package might be missing.')
            exit(1)

        return soup

    def get_lessons_urls(self, pathway_url):
        """Return a list of the URLs of the lessons in the given pathway URL"""
        root_url, _ = self.parse_url(pathway_url)
        pathway_soup = self.get_soup(pathway_url)
        div = pathway_soup.select_one('#pw_page')
        entries = json.loads(div['data-collection-entries'])
        lessons_urls = [root_url + entry['url']
                        for entry in entries if entry.get('url')]
        return lessons_urls

    def get_pathways_urls(self, level_url):
        """Return a lists of the URLs of the pathways in the given language level URL"""
        root_url, _ = self.parse_url(level_url)
        level_soup = self.get_soup(level_url)
        level_name = level_url.split('/')[-1].replace('-', '')
        pathways_links = level_soup.select(f'a[data-{level_name}="1"]')
        pathways_urls = set([root_url + link['href']
                             for link in pathways_links])
        return pathways_urls

    def download_pathway(self, pathway_url):
        """Download the lessons in the given pathway URL"""
        lessons_urls = self.get_lessons_urls(pathway_url)

        pathway_name = pathway_url.split('/')[-2]
        if not os.path.isdir(pathway_name):
            os.mkdir(pathway_name)

        return [pathway_name, lessons_urls]

    def check_for_lessons_library(self, level_url):
        return 'lesson-library' not in level_url

    def download_level(self, level_url):
        """Download all the pathways in the given language level URL"""
        # This option is unfeasable for use as a standard behavior even with restoring the last download state
        url_parts = level_url.split('/')
        if self.check_for_lessons_library(level_url):
            e = '''You should provide the URL for a language level, not a lesson.
            Eg: https://www.japanesepod101.com/lesson-library/absolute-beginner'''
            logging.error(e)
            exit(1)
        level_name = url_parts[-1]
        if not os.path.isdir(level_name):
            os.mkdir(level_name)
        pathways_urls = self.get_pathways_urls(level_url)
        return [level_name, pathways_urls]

    def create_stack_for_level(self, level_url):
        stack = dict()
        [level_name, pathways_urls] = self.download_level(level_url)
        logging.info(pathways_url)
        stack["version"] = __version__
        stack["lesson"] = dict()
        stack["start_url"] = level_url
        for i in pathways_url:
            [pathway_name, lessons] = self.download_pathway(i)
            logging.info(lessons)
            for j in lessons:
                stack["lesson"][j] = [level_name + pathway_name, False]
        self.save_download_stack(stack)
        return stack

    def create_stack_for_lesson(self, level_url):
        stack = dict()
        logging.info(level_url)
        stack["version"] = __version__
        stack["lesson"] = dict()
        stack["start_url"] = level_url
        [pathway_name, lessons] = self.download_pathway(level_url)
        logging.info(lessons)
        for j in lessons:
            stack["lesson"][j] = [pathway_name, False]
        self.save_download_stack(stack)
        return stack

    def create_download_stack(self, level_url):
        if self.check_for_lessons_library(level_url):
            return self.create_stack_for_level(level_url)
        else:
            return self.create_stack_for_lesson(level_url)

    def save_download_stack(self, stack):
        stackpath = expanduser("~") + "/.config/languagepod101/"
        stack_file = "laststack"
        if not path.exists(stackpath):
            mkdir(stackpath)
        with open(stackpath + stack_file, 'wb') as f:
            pickle.dump(stack, f)
        logging.info("Download stack stored")

    def load_download_stack(self):
        stackpath = expanduser("~") + "/.config/languagepod101/"
        stack_file = "laststack"

        try:
            with open(stackpath + stack_file, 'rb') as f:
                try:
                    stack = pickle.load(f)
                    if stack["version"] != __version__:
                        logging.warning(
                            "Attention trying to use an old download stack with a newer version, this might cause undefined behavior. If you are unsure create a backup and continue with YES.")
                        if input("Please confirm with YES (all capital) to continue. No further warning will happen:\r\n") != "YES":
                            exit(1)
                        logging.info("Rewriting version of download stack")
                        stack["version"] = __version__
                        self.save_download_stack(stack)
                    logging.info("Download stack restored")
                    return stack
                except Exception as e:
                    logging.error(e)
                    logging.error("Restoring download stack failed")
            return None
        except Exception as e:
            logging.debug(e)
            logging.debug("No download stack found")
        return None

    def save_file(self, file_url, file_name):
        """Save file on local folder"""
        if os.path.isfile(file_name):
            logging.debug(f'{file_name} was already downloaded.')
            return

        try:
            lesson_response = self.m_session.get(file_url)
            with open(file_name, 'wb') as f:
                f.write(lesson_response.content)
                logging.debug(f'{file_name} saved on local device!')
        except Exception as e:
            logging.warning(e)
            logging.warning(f'Failed to save {file_name} on local device.')

    def work_on_stack(self, stack):
        # stack
        # key lessonurl:  path, Done?
        lessons_counter = dict()
        old_cwd = os.getcwd()
        for sublesson in stack["lesson"]:

            lesson_url = sublesson
            path = stack["lesson"][sublesson][0]
            isFinished = stack["lesson"][sublesson][-1]
            if lessons_counter.get(path) is None:
                lessons_counter[path] = 0
            lessons_counter[path] += 1
            if isFinished == True:
                logging.debug("Skipping Lesson" + str(lessons_counter[path]))
                continue

            lesson_number = lessons_counter[path]
            os.chdir(path)

            root_url, _ = self.parse_url(lesson_url)
            lesson_soup = self.get_soup(lesson_url)
            self.save_file(
                lesson_url, f'{str(lesson_number).zfill(2)} - {lesson_soup.title.text}.html')
            if self.m_arguments.get("audio"):
                self.download_audios(lesson_number, lesson_soup)
            if self.m_arguments.get("video"):
                self.download_videos(lesson_number, lesson_soup)
            if self.m_arguments.get("document"):
                self.download_pdfs(root_url, lesson_soup)
            if self.m_arguments.get("anki_deck"):
                self.download_vocabulary(root_url, lesson_soup)

            stack["lesson"][sublesson][-1] = True
            self.save_download_stack(stack)

            if self.m_arguments.get("min_delay") and self.m_arguments.get("max_delay"):
                delay = random.randrange(
                    self.m_arguments["min_delay"], self.m_arguments["max_delay"])
                logging.debug("Sleeping for " + str(delay) + " seconds")
                time.sleep(delay)
            os.chdir(old_cwd)
        # empty stack and save
        stack = None
        self.save_download_stack(stack)

    def force_new_download_stack(self):
        if self.m_arguments.get("force-new-download-stack") is None:
            return False

        if self.m_arguments.get("force-new-download-stack") is False:
            return False
        else:
            return True


def main(username, password, url, args):
    USERNAME = username or input('Username (mail): ')
    PASSWORD = password or getpass('Password: ')
    level_url = url or input(
        'Please enter URL of the study level for the desired language. For example:\n'
        ' * https://www.japanesepod101.com/lesson-library/absolute-beginner\n'
        ' * https://www.spanishpod101.com/lesson-library/intermediate\n'
        ' * https://www.chineseclass101.com/lesson-library/advanced\n'
    )
    lpd = LanguagePod101Downloader(args)
    lpd.authenticate(level_url, USERNAME, PASSWORD)
    stack = None
    if not lpd.force_new_download_stack():
        stack = lpd.load_download_stack()
    if stack is None:
        stack = lpd.create_download_stack(level_url)
    lpd.work_on_stack(stack)

    logging.info('Yatta! Finished downloading the level!')


def check_all_arguments_empty(args):
    """This functions checks if all arguments e.g. provided by sys.arg"""
    vargs = vars(args)
    for i in vargs:
        if vargs[i] is not None:
            return False
    return True


def get_input_arguments():
    """Get the behavior either via the arguments or via a config file"""
    parser = argparse.ArgumentParser(
        description='Scrape full language courses by Innovative Language.Version = ' + __version__
    )
    parser.add_argument('-u', '--username', help='Username (email)')
    parser.add_argument('-p', '--password', help='Password for the course')
    parser.add_argument('-v', '--video', default=True,
                        type=bool, help='Download videos')
    parser.add_argument('-a', '--audio', default=True,
                        type=bool, help='Download audio')
    parser.add_argument('-d', '--document', default=True,
                        type=bool, help='Download documents e.g. pdfs')
    parser.add_argument('-f', '--force_new_download-stack', type=bool,
                        help='Forces a clean download stack and abandones old states')
    parser.add_argument('--url', help='URL for the language level to download')
    parser.add_argument('-c', '--config', help='Provide config file for input')
    parser.add_argument('--anki_deck', default=False,
                        help='Create anki decks from vocabulary')
    parser.add_argument('--download_all_videos', default=False,
                        type=bool, help='Downloads all videos independent of quality')
    args = parser.parse_args()
    vargs = vars(args)
    if args.config is not None:
        logging.info("reading config")
        config = configparser.ConfigParser()
        try:
            config.read(args.config)
        except Exception as e:
            logging.error(e)
            logging.error(f'Failed to load config file: ' + args.config)
            exit(1)
        for key, content in config['User'].items():
            vargs[key] = content

    elif check_all_arguments_empty(args):
        logging.debug("Trying to use default config file")
        configpath = expanduser("~") + "/.config/languagepod101/lp101.config"
        config = configparser.ConfigParser()
        if path.exists(configpath):
            try:
                config.read(configpath)
            except Exception as e:
                logging.warning(e)
                logging.warning(
                    f'Failed to load standard config file: ' + config)
            for key, content in config['User'].items():
                vargs[key] = content
        else:
            logging.warning("Couldn't find default config file")
    return args


def setupLoging():
    logingpath = expanduser("~") + "/.local/share/languagepod101/"
    if not path.exists(logingpath):
        os.mkdir(logingpath)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=logingpath + "lp101.log",
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


if __name__ == '__main__':
    setupLoging()
    args = get_input_arguments()
    main(args.username, args.password, args.url, args)
