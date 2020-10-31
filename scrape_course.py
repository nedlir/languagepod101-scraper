import os

import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv


load_dotenv(override=True)

# SOURCE_URL and COURSE_URL must be replaced with desired values to scrape
SOURCE_URL = r'https://www.japanesepod101.com'
# COURSE_URL should be any of the lessons of the desired course
COURSE_URL = r'https://www.japanesepod101.com/lesson/advanced-audio-blog-s6-1-japanese-tourist-spotshokkaido/?lp=221'
LOGIN_URL = f'{SOURCE_URL}/member/login_new.php'
USER = os.getenv('JPOD101_USERNAME')
PASSWORD = os.getenv('JPOD101_PASSWORD')
LOGIN_DATA = {
    'amember_login': USER,
    'amember_pass': PASSWORD
}

# Logins to the website:
print('Establishing a new session...')
with requests.Session() as session:    
    try:
        print(f'Trying to login to {SOURCE_URL}')
        course_response = session.post(LOGIN_URL, data=LOGIN_DATA)
        print(f'Successfully logged in as {USER}')
    except:
        print('Login Failed, please check login details or internet connection.')
        quit()
    try:
        course_source = session.get(COURSE_URL)
    except:
        print('Loading of course URL page failed, please make sure URL is accurate.')
        quit()

    # Creates a list of course urls which will be downloaded:
    course_soup = BeautifulSoup(course_source.text, 'lxml')
    soup_urls = course_soup.find_all('option')
    course_urls = list()

    for u in soup_urls:
        if u['value'].startswith('/lesson/'):
            course_urls.append(SOURCE_URL + u['value'])

    print('Lessons URLs successfully listed.')

     # Traverses list of course's lesson urls and downloads them:
    file_index = 1  # Used for numbering of file name strings
    for lesson_url in course_urls:
        lesson_source = session.get(lesson_url)
        lesson_soup = BeautifulSoup(lesson_source.text, 'lxml')
        audio_soup = lesson_soup.find_all('audio')

        # Downloads lesson audio files:
        if audio_soup:
            print(f'Downloading Lesson {str(file_index).zfill(2)} - {lesson_soup.title.text}')
            for audio_file in audio_soup:
                try:
                    file_url = audio_file['data-trackurl']
                except:
                    print('Tag "data-trackurl" was not found, trying to reach "data-url" tag instead')
                    try:
                        file_url = audio_file['data-url']
                    except:
                        print(f'Could not retrieve URL: {file_url}')
                        continue

                # Creates a file name and verifies that the file is 'mp3' format:
                if file_url.endswith('.mp3'):
                    print(f'Successfully retrieved URL: {file_url}')

                    # Creates a clean file name string:
                    file_prefix = str(file_index).zfill(2)
                    file_body = lesson_soup.title.text
                    file_suffix = file_url.split('/')[-1]

                    # Verifis clean version of file name by removing junk sufix string that may appear:
                    if file_suffix[:3].isdigit():
                        file_suffix = file_suffix[4:]

                    file_name = f'{file_prefix} - {file_body} - {file_suffix}'

                    # Saves file on local folder:
                    try:
                        with requests.get(file_url) as lesson_response:
                            try:
                                with open(file_name, 'wb') as f:
                                    f.write(lesson_response.content)
                                    print(f'{file_name} saved on local device!')
                            except:
                                print(f'{file_name} saving on local device failed.')
                    except:
                        print('Downloading of file failed.')
                        continue
            file_index += 1
print ('Yatta! Finished downloading the course~')
