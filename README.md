<div align='center'>
:zap: languagepod101-scraper :zap:
==================================

![Languages available](readme/language_selection.jpg)

_languagepod101-scraper is a resource for dozens of language learning courses and study material for FREE._
</div>

---

## :mortar_board: About

languagepod101-scraper helps you download full online language courses and save them on your local folder as MP3/MP4 files.
The courses are produced and distributed by [Innovative Language](https://www.innovativelanguage.com/online-language-courses),
who provides language learning courses from a selection of dozens of languages. Each lesson is usually 10-20 minutes long.

To get started, [choose one of the languages courses](https://www.innovativelanguage.com/online-language-courses)
offered by Innovative Language and create a free account.

## :pushpin: Usage

To use the script, fulfill the requirements and follow the example as demonstrated below.

### :electric_plug: Requirements

- Download and install [Python 3.9+](https://www.python.org/).
- Install required packages from [requirements.txt](requirements.txt) file using
  [pip](https://packaging.python.org/tutorials/installing-packages/).

  ```sh
  pip install -r requirements.txt
  ```

### :bookmark_tabs: Example

For the sake of example, the process of downloading of a level from
[Japanese Pod 101](https://www.japanesepod101.com/) will be demonstrated.

Japanese Pod 101 and all other sites have a similar structure which looks as following:

  ```
  Japanesepod101
  ├─ Level 1 - Absolute Beginner
  │  ├─ Newbie Season 1
  │  │  ├─ lesson 01
  │  │  ├─ lesson 02
  │  │  ├─ lesson 03
  │  │  ├─ ...
  │  ├─ Newbie Season 2
  │  ├─ ...
  ├─ Level 2 - Beginner
  │  ├─ Lower Beginner Season 1
  │  │  ├─ lesson 01
  │  │  ├─ lesson 02
  │  │  ├─ lesson 03
  │  │  ├─ ...
  │  ├─ ...
  ├─ Level 3 - Intermediate
  │  ├─ ...
  │  │  ├─ ...
  │  │  ├─ ...
  │  ├─ ...
  │  ├─ ...
  ├─ Level 4 - Upper Intermediate
  │  ├─ ...
  ├─ Level 5 - Advanced
  │  ├─ ...
  ```

- To download *Level 2 - Beginner* we will have to use our web browser to navigate
  to this course.

  Navigation would look like this: `Japanesepod101` → `Level 2 - Beginner`.
  
  Save the URL for the address bar, as you will have to provide it to the script later on.
- Run the [language101_scraper.py](language101_scraper.py) script, and follow the instructions.
  You will have to provide:

  - the email you used to sign up for the course
  - your password for the course
  - the URL for the language study level you have navigated through earlier
    (something like `https://www.japanesepod101.com/lesson-library/beginner`).

- Alternatively, you can pass the data as parameters when invoking the script:

  ```sh
  ./language101_scraper.py -u $USERNAME -p $PASSWORD --url YOUR_LEVEL_URL
  ```

- It is again possible to download single lessons with the same syntax as before. However, rather than providing the language study level, the course's lesson URL has to be provided
  ( for example: `lesson 01` of the `Lower Beginner Season 1` course).

- The script will start downloading the MP3/MP4 files into the local navigated folder.
  Any possible errors would be printed out.

- Output inside folder should look like this:

  ```
  beginner
  ├─level-2-japanese
  | ├─01 - A Formal Japanese Introduction - JapanesePod101 - Dialogue.mp3
  | ├─01 - A Formal Japanese Introduction - JapanesePod101 - Review.mp3
  | ├─01 - A Formal Japanese Introduction - JapanesePod101 - Main Lesson.mp3
  | ├─02 - Which Famous Tokyo Tower is That - JapanesePod101 - Dialogue.mp3
  | └─...
  ├─japanese-grammar-made-easy
  | ├─01 - How to Talk About Your Family - JapanesePod101.mp4
  | ├─02 - How to Express Desire in Japanese Want To - JapanesePod101.mp4
  | └─...
  └─...
  ```

## :clipboard: Disclaimer and known issues

- Any usage of the script is under user's responsibility only. Users of the script must act according to site's terms.

- As of today, Innovative Language's terms of use does not forbid usage of crawlers or scrapers on any of their sites.
This may change in the future, so be aware.

- If you like the services Innovative Language provides you should consider a monthly subscription. Basic programs start at around $5 per month and include support from native speaker teachers.

- As with all websites, the site's structure may change in the future and thus, as often happens with scraping scripts, deprecate it. It is not really a question of *if* the site's source code will change but rather **when** (so enjoy it while it's still working :grin:).

## :lock: License

All of the content presented in the websites belongs to the original creators (Innovative Language) and I have nothing to do with it.

The license below refers only to the script and not to the downloaded content.

[License - MIT](LICENSE.md)
