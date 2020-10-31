import requests

from bs4 import BeautifulSoup


print('Youkoso! Welcome to jpod101-scraper! This script helps you scrape full language courses from sites like japanesepod101.com, spanishpod101.com, chineseclass101.com and more!\n')

SOURCE_URL = input('Please insert source url, for example: https://www.japanesepod101.com or https://www.spanishpod101.com or https://www.chineseclass101.com\n')
SOURCE_URL = SOURCE_URL.removesuffix('/')
LOGIN_URL = f'{SOURCE_URL}/member/login_new.php'
COURSE_URL = input('Please insert first lesson url of the desired course, for example: https://www.japanesepod101.com/lesson/lower-beginner-1-a-formal-japanese-introduction/?lp=116   or\nhttps://www.spanishpod101.com/lesson/basic-bootcamp-1-a-pleasure-to-meet-you/?lp=425   or\nhttps://www.chineseclass101.com/lesson/absolute-beginner-1-meeting-whats-your-name/?lp=208\n')
USER = input('Username(mail):')
PASSWORD = input('Password: ')
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
        print('Login Failed, please check urls input, login details and internet connection.')
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
            print(
                f'Downloading Lesson {str(file_index).zfill(2)} - {lesson_soup.title.text}')
            for audio_file in audio_soup:
                try:
                    file_url = audio_file['data-trackurl']
                except:
                    print(
                        'Tag "data-trackurl" was not found, trying to reach "data-url" tag instead')
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
                    # Avoids OSError: [Errno 22] while file writing:
                    invalid_chars = '\/?:*"<>|'
                    for char in invalid_chars:
                        file_body = file_body.replace(char, "")

                    file_suffix = file_url.split('/')[-1]
                    # Verifis clean version of file name by removing junk sufix string that may appear:
                    if file_suffix[:3].isdigit():
                        file_suffix = file_suffix[4:]

                    file_name = f'{file_prefix} - {file_body} - {file_suffix}'

                    # Saves file on local folder:
                    try:
                        lesson_response = session.get(file_url)
                        with open(file_name, 'wb') as f:
                            f.write(lesson_response.content)
                            print(f'{file_name} saved on local device!')
                    except:
                        print(f'Failed to save {file_name} on local device.')
                    continue
            file_index += 1
print('Yatta! Finished downloading the course~')
