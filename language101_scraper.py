#!/usr/bin/env python3
# language101 scraper helps you scrape full language courses from sites like
# japanesepod101.com, spanishpod101.com, chineseclass101.com and more!

import argparse

from sys import exit
from urllib.parse import urlparse

import requests

from bs4 import BeautifulSoup

session = None

def parse_url(url):
    """Parse the course URL"""
    obj = urlparse(url)
    root_url = f'{obj.scheme}://{obj.netloc}'
    login_url = f'{root_url}/member/login_new.php'

    return root_url, login_url

def authenticate(url, username, password):
    """Logs in to the website"""
    root_url, login_url = parse_url(url)
    credentials = {
        'amember_login': username,
        'amember_pass': password,
    }

    print(f'Trying to log in to {root_url}')
    global session
    session = requests.Session()
    response = session.post(login_url, data=credentials)

    try:
        response.raise_for_status()
    except Exception as e:
        print(e)
        print('Could not reach site. Please check URL and internet connection.')
        exit(1)

    if 'X-Ill-Member' not in response.headers:
        print('Could not log in. Please check your credentials.')
        exit(1)
    print(f'Successfully logged in as {username}')

def download_audios(file_index, lesson_soup):
    """Download the audio files of a lesson"""
    audio_soup = lesson_soup.find_all('audio')

    if audio_soup:
        print(
            f'Downloading Lesson {str(file_index).zfill(2)} - {lesson_soup.title.text} audio')
        for audio_file in audio_soup:
            try:
                file_url = audio_file['data-trackurl']
            except Exception as e:
                print(e)
                print(
                    'Tag "data-trackurl" was not found, trying to reach "data-url" tag instead')
                try:
                    file_url = audio_file['data-url']
                except Exception as e:
                    print(e)
                    print(f'Could not retrieve URL: {file_url}')
                    continue

            # Verifies that the file is 'mp3' format, if so, builds a clean str name for the file:
            if file_url.endswith('.mp3'):
                print(f'Successfully retrieved URL: {file_url}')

                # Create a clean filename string with prefix, body, suffix and extension.
                # Files are numbered using the 'file_index' variable
                file_prefix = str(file_index).zfill(2)
                file_body = get_filename_body(lesson_soup)

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

                try:
                    save_file(file_url, file_name)
                except Exception as e:
                    continue

def download_pdfs(root_url, lesson_soup):
    """Download the PDF files of a lesson"""
    # Beware: Access to PDFs requires Basic or Premium membership
    pdf_links = lesson_soup.select('#pdfs a')
    if pdf_links:
        for pdf_link in pdf_links:
            pdf_url = pdf_link.get('href')
            if pdf_url.startswith('/pdfs/'):
                pdf_url = root_url + pdf_url
            pdf_name = pdf_url.split('/')[-1]
            try:
                save_file(pdf_url, pdf_name)
            except Exception:
                continue

def download_videos(file_index, lesson_soup):
    """Download the video files of a lesson"""
    video_soup = lesson_soup.find_all('source')

    if video_soup:
        print(
            f'Downloading Lesson {str(file_index).zfill(2)} - {lesson_soup.title.text} video')
        for video_file in video_soup:
            try:
                if video_file['type'] == 'video/mp4' and video_file['data-quality'] == 'h':
                    file_url = video_file['src']
                else:
                    continue
            except Exception as e:
                print(e)
                print('Could not find out the URL for this lesson\'s video.')
                continue

            # Verifies that the file is in 'mp4' or 'm4v' format.
            # If so, builds a clean str name for the file:
            if file_url.endswith('.mp4') or file_url.endswith('.m4v'):
                print(f'Successfully retrieved URL: {file_url}')

                # Create a clean file name string with prefix, body and extension.
                # Files are numbered using the 'file_index' variable
                file_prefix = str(file_index).zfill(2)
                file_body = get_filename_body(lesson_soup)
                file_ext = file_url.split('.')[-1]
                file_name = f'{file_prefix} - {file_body}.{file_ext}'

                try:
                    save_file(file_url, file_name)
                except Exception as e:
                    continue

def get_filename_body(lesson_soup):
    """Generate main body of filename from page's title"""
    filename_body = lesson_soup.title.text

    # Sanitize filename. It avoids `OSError: [Errno 22]` while file writing
    # and some potentially problematic characters in filenames
    invalid_chars = '#%&\/?:*"<>{|}'
    for char in invalid_chars:
        filename_body = filename_body.replace(char, '')

    return filename_body

def save_file(file_url, file_name):
    """Save file on local folder"""
    try:
        lesson_response = session.get(file_url)
        with open(file_name, 'wb') as f:
            f.write(lesson_response.content)
            print(f'{file_name} saved on local device!')
    except Exception as e:
        print(e)
        print(f'Failed to save {file_name} on local device.')
        raise e


def main(username, password, url):
    USERNAME = username or input('Username (mail): ')
    PASSWORD = password or input('Password: ')
    COURSE_URL = url or input('Please insert first lesson URL of the desired course, for example:\n'
        ' * https://www.japanesepod101.com/lesson/lower-beginner-1-a-formal-japanese-introduction/?lp=116\n'
        ' * https://www.spanishpod101.com/lesson/basic-bootcamp-1-a-pleasure-to-meet-you/?lp=425\n'
        ' * https://www.chineseclass101.com/lesson/absolute-beginner-1-meeting-whats-your-name/?lp=208\n')

    authenticate(COURSE_URL, USERNAME, PASSWORD)
    root_url, _ = parse_url(COURSE_URL)

    try:
        course_source = session.get(COURSE_URL)
    except Exception as e:
        print(e)
        print('Loading of course URL page failed, please make sure URL is accurate.')
        exit(1)

    # Creates a list of course urls which will be downloaded:
    try:
        course_soup = BeautifulSoup(course_source.text, 'lxml')
    except Exception as e:
        print(e)
        print("Failed to parse the course's webpage, 'lxml' package might be missing.")
        exit(1)

    soup_urls = course_soup.find_all('option')
    course_urls = list()

    for u in soup_urls:
        if u['value'].startswith('/lesson/'):
            course_urls.append(root_url + u['value'])

    print('Lessons URLs successfully listed.')

    # Traverses list of course's lesson urls and downloads them:
    file_index = 1  # Used for numbering of file name strings
    for lesson_url in course_urls:
        lesson_source = session.get(lesson_url)
        lesson_soup = BeautifulSoup(lesson_source.text, 'lxml')

        download_audios(file_index, lesson_soup)
        download_videos(file_index, lesson_soup)
        download_pdfs(root_url, lesson_soup)

        file_index += 1

    print('Yatta! Finished downloading the course~')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape full language courses by Innovative Language.')
    parser.add_argument('-u', '--username', help='Username (email)')
    parser.add_argument('-p', '--password', help='Password for the course')
    parser.add_argument('--url', help='URL for the first lesson of the course')

    args = parser.parse_args()
    main(args.username, args.password, args.url)
