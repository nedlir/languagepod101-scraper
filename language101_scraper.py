#!/usr/bin/env python3
# language101 scraper helps you scrape full language courses from sites like
# japanesepod101.com, spanishpod101.com, chineseclass101.com and more!

import argparse
import time
import json
import os
import re
import requests


from random import randint
from sys import exit
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from http.cookiejar import MozillaCookieJar
from urllib.parse import urlparse


parser = argparse.ArgumentParser(description='Scrape full language courses by Innovative Language.')
parser.add_argument('-u', '--username', help='Username (email)')
parser.add_argument('-p', '--password', help='Password for the course')
parser.add_argument('--url', help='URL for the first lesson of the course')

args = parser.parse_args()

USERNAME = args.username or input('Username (email): ')
PASSWORD = args.password or input('Password: ')
COURSE_URL = args.url or input('Please insert first lesson URL of the desired course, for example:\n'
                               '* https://www.japanesepod101.com/lesson/lower-beginner-1-a-formal-japanese'
                               '-introduction/?lp=116\n '
                               '* https://www.spanishpod101.com/lesson/basic-bootcamp-1-a-pleasure-to-meet-you/?lp'
                               '=425\n '
                               '* https://www.chineseclass101.com/lesson/absolute-beginner-1-meeting-whats-your-name'
                               '/?lp=208\n')

LOGIN_DATA = {
    'amember_login': USERNAME,
    'amember_pass': PASSWORD,
}

obj = urlparse(COURSE_URL)
SOURCE_URL = f'{obj.scheme}://{obj.netloc}'
LOGIN_URL = f'{SOURCE_URL}/member/login_new.php'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_FILE = os.path.join(SCRIPT_DIR, 'cookies.txt')
UA_FILE = os.path.join(SCRIPT_DIR, 'ua.txt')
PREFIX_DIGITS = 0


def save_cookies(session, filename=COOKIES_FILE):
    """Save session cookies to a Netscape format cookie file"""
    cookie_jar = MozillaCookieJar(filename)
    # Copy cookies from session to cookie jar
    for cookie in session.cookies:
        cookie_jar.set_cookie(cookie)
    cookie_jar.save(ignore_discard=True, ignore_expires=True)
    print(f"Cookies saved to {filename}")

def load_cookies(filename=COOKIES_FILE):
    """Load Netscape format cookies from file into a new session"""
    session = requests.Session()
    try:
        cookie_jar = MozillaCookieJar(filename)
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        session.cookies = requests.cookies.RequestsCookieJar()
        for cookie in cookie_jar:
            session.cookies.set_cookie(cookie)
        print(f"Cookies loaded from {filename}")
        return session
    except FileNotFoundError:
        print(f"No cookie file found at {filename}")
        return None

def load_ua(filename=UA_FILE):
    try:
        with open(filename, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print('Error: Please make a "ua.txt" file containing the User Agent of your browser in the directory of the python script.'
            + 'You can display your User Agent at https://dnschecker.org/user-agent-info.php.')
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    exit(1)

# Function to extract numeric prefixes with leading zeros
def get_existing_prefixes(directory):
    prefixes = set()
    for filename in os.listdir(directory):
        match = re.match(r"^(\d+)", filename)
        if match:
            prefixes.add(match.group(1))  # Add the number as a string (preserving leading zeros)
    return prefixes

def check_for_captcha(soup_or_element):
    """
    Check if a BeautifulSoup element contains captcha text
    Returns True if captcha is detected, False otherwise
    """
    try:
        element_text = soup_or_element.get_text().lower()
        return "captcha" in element_text
    except Exception as e:
        print(f"Error checking for captcha: {e}")
        return False


def check_login_required(html_content):
    """Check if the page contains a sign in button"""
    soup = BeautifulSoup(html_content, 'lxml')
    sign_in_buttons = soup.find_all(['button', 'a'], string=re.compile(r'Sign In', re.IGNORECASE))
    return len(sign_in_buttons) > 0

def check_http_error(response, fail_safe=False):
    if response.status_code == 200:
        return True
    elif response.status_code == 403:
        print(f"Error: 403 Forbidden")
    elif response.status_code >= 400:
        print(f"Error: Received status code {response.status_code}")
        # Optionally, handle specific error codes
        if response.status_code == 404:
            print("Resource not found (404).")
        elif response.status_code == 500:
            print("Server error (500).")
    else:
        print(f"Received unexpected status code: {response.status_code}")
    if fail_safe:
        return False
    exit(1)

class MediaDownloader:
    def __init__(self, session, source_url):
        self.session = session
        self.source_url = source_url
        self.invalid_chars = '\\/?:*"<>|'

    def clean_filename(self, text):
        """Remove invalid characters from filename"""
        for char in self.invalid_chars:
            text = text.replace(char, "")
        return text

    def create_filename(self, file_prefix, title, suffix, extension):
        """Create a standardized filename"""
        clean_title = self.clean_filename(title)
        return f'{file_prefix} - {clean_title} - {suffix}{extension}'

    def download_file(self, file_url, file_name):
        """Download and save a file"""
        if Path(file_name).exists():
            #print(f'\tFile {file_name} exists already, continuing...')
            return False

        try:
            response = self.session.get(file_url)
            ok = check_http_error(response, True)
            if not ok:
                return
            with open(file_name, 'wb') as f:
                f.write(response.content)
            print(f'\t{file_name} saved on local device!')
            return True
        except Exception as e:
            print(f'\tFailed to save {file_name}: {e}')
            return False

    def get_file_url(self, element, url_attributes):
        """Extract file URL from element using multiple possible attributes"""
        for attr in url_attributes:
            try:
                url = element[attr]
                if not url.startswith('http'):
                    url = self.source_url + url
                return url
            except (KeyError, AttributeError):
                continue
        return None

class MediaProcessor:
    def __init__(self, session, source_url):
        self.downloader = MediaDownloader(session, source_url)
        
    def process_audio(self, soup, file_prefix):
        """Process audio files"""
        audio_files = soup.find_all('audio')
        for audio in audio_files:
            file_url = self.downloader.get_file_url(audio, ['data-trackurl', 'data-url'])
            if not file_url or not file_url.endswith('.mp3'):
                continue

            suffix = self._determine_media_type(file_url)
            filename = self.downloader.create_filename(file_prefix, soup.title.text, suffix, '.mp3')
            self.downloader.download_file(file_url, filename)

    def process_video(self, soup, file_prefix):
        """Process video files"""
        video_files = soup.find_all('video')
        for video in video_files:
            file_url = self.downloader.get_file_url(video, ['data-trackurl', 'data-url'])
            if not file_url or not (file_url.endswith('.mp4') or file_url.endswith('.m4v')):
                continue

            extension = '.' + file_url.split('.')[-1]
            suffix = self._determine_media_type(file_url)
            filename = self.downloader.create_filename(file_prefix, soup.title.text, suffix, extension)
            self.downloader.download_file(file_url, filename)

    def process_pdf(self, soup, file_prefix):
        """Process PDF files"""
        pdf_links = soup.find_all('a', href=lambda x: x and x.endswith('.pdf'))
        pdfnum = 0
        for pdf in pdf_links:
            pdfnum += 1
            if pdfnum > 2 or "checklist" in pdf.text.lower():
                continue

            file_url = self.downloader.get_file_url(pdf, ['href'])
            if not file_url:
                continue

            suffix = 'Lesson Notes' if 'Lesson Notes' in pdf.text else \
                    'Lesson Transcript' if 'Lesson Transcript' in pdf.text else 'PDF'
            filename = self.downloader.create_filename(file_prefix, soup.title.text, suffix, '.pdf')
            self.downloader.download_file(file_url, filename)

    def _determine_media_type(self, file_url):
        """Determine media type based on URL"""
        filename = file_url.split('/')[-1].lower()
        if 'dialog' in filename or 'dialogue' in filename:
            return 'Dialogue'
        elif 'review' in filename:
            return 'Review'
        return 'Main Lesson'

def process_lesson(session, lesson_url, file_index, source_url):
    """Process a single lesson"""
    try:
        lesson_source = session.get(lesson_url)
        check_http_error(lesson_source)
        lesson_soup = BeautifulSoup(lesson_source.text, 'lxml')
        
        if check_for_captcha(lesson_soup):
            print("Lessons unavailable. Captcha required.")
            exit(1)

        processor = MediaProcessor(session, source_url)
        file_prefix = str(file_index).zfill(PREFIX_DIGITS)
        
        print(f'Processing Lesson {file_prefix} - {lesson_soup.title.text}')
        
        processor.process_audio(lesson_soup, file_prefix)
        processor.process_video(lesson_soup, file_prefix)
        processor.process_pdf(lesson_soup, file_prefix)
        
        return True

    except Exception as e:
        print(f"Error processing lesson: {e}")
        return False

    
def extract_lesson_urls(session, course_url, source_url):
    """Extract all lesson URLs from the course page"""
    try:
        course_source = session.get(course_url)
        check_http_error(course_source)
        course_soup = BeautifulSoup(course_source.text, 'lxml')
        
        if check_for_captcha(course_soup):
            print("Too many requests. Captcha required.")
            exit(1)

        lesson_urls = []
        soup_urls = course_soup.find_all('div')
        
        for u in soup_urls:
            if "class" in u.attrs and "js-pathway-context-data" in u.attrs['class']:
                obj = json.loads(u.attrs['data-collection-entities'])
                for lesson in obj:
                    if lesson['url'].startswith('/lesson/'):
                        full_url = source_url + lesson['url']
                        lesson_urls.append(full_url)
                        print("URL→" + full_url)

        print('Lessons URLs successfully listed.')
        #if len(lesson_urls) == 0:
        #    print(course_source.text)
        return lesson_urls

    except Exception as e:
        print(f"Error extracting course URLs: {e}")
        return None

def validate_course_url(url):
    """Validate that the URL is a lesson and not a lesson library"""
    try:
        url_split = url.split('/')
        if url_split[3] == 'lesson-library':
            raise ValueError('\nThe supplied URL is not a lesson - it is the course contents page!\n'
                           'Please click the first lesson and try that URL.')
        return True
    except Exception as e:
        print(e)
        return False

def main():
    print('Establishing a new session...')
    session = None
    UA = load_ua()
    
    # Try to load existing cookies first
    if os.path.exists(COOKIES_FILE):
        session = load_cookies()
        session.headers.update({
            'User-Agent': UA
        })
        if session:
            try:
                test_response = session.get(COURSE_URL)
                check_http_error(test_response)
                if not check_login_required(test_response.text):
                    print("Successfully authenticated using cookies")
                else:
                    print("Cookies expired, need to login again")
                    session = None
            except Exception as e:
                print(f"Error testing cookies: {e}")
                session = None

    # If no valid cookies, perform regular login
    if session is None:
        session = requests.Session()
        session.headers.update({
            'User-Agent': UA
        })
        
        try:
            print(f'Trying to login to {SOURCE_URL}')
            course_response = session.post(LOGIN_URL, data=LOGIN_DATA)
            check_http_error(course_response)
            print(f'Successfully logged in as {USERNAME}')
            save_cookies(session)
        except Exception as e:
            print(f'Login Failed: {e}')
            return
    
    if not validate_course_url(COURSE_URL):
        return

    lesson_urls = extract_lesson_urls(session, COURSE_URL, SOURCE_URL)
    if lesson_urls is None or len(lesson_urls) == 0:
        print("No lesson URLs found.")
        return
    PREFIX_DIGITS = len(lesson_urls)
    # Process each lesson
    file_index = 1
    for lesson_url in lesson_urls:
        file_prefix = str(file_index).zfill(2)
        existing_prefixes = get_existing_prefixes("./")
        
        if file_prefix in existing_prefixes:
            print(f"Skipping lesson with prefix {file_index} (already exists).")
            file_index += 1
            continue

        if process_lesson(session, lesson_url, file_index, SOURCE_URL):
            file_index += 1
            wait = randint(110, 300)
            print(f'Pausing {wait}s before scraping next lesson...\n')
            time.sleep(wait)
        else:
            break

    print('Yatta! Finished downloading the course~')

main()
