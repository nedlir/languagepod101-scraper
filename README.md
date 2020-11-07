<h1 align="center">:zap: languagepod101-scraper	:zap:</h1>
<p align="center">
  <img src="readme\language_selection.jpg">
  <br>
  <i>languagepod101-scraper is a resource for dozen of language learning courses and study material for FREE.</i>
</p>
<hr>


##  :mortar_board: About
languagepod101-scraper helps you download full language courses and save them on your local folder as MP3 files.
The courses are produced and distributed by [Innovative Language](https://www.innovativelanguage.com/online-language-courses) who provides language learning courses from a selection of dozens languages. Each lesson is usually 10-20 minutes long.

To get started, [choose a language ](https://www.innovativelanguage.com/online-language-courses) course offered by Innovative Language.

##  :pushpin: Usage
To use the script, fulfill the requirements and follow the example as demonstrated below.

###  :electric_plug: Requirements

- Download and install [Python 3.9+](https://www.python.org/). 
- Install required packages from [requirements.txt](requirements.txt) file using [pip](https://packaging.python.org/tutorials/installing-packages/).

  ```
  pip install -r /path_to_requirements_file/requirements.txt
  ```

###  :bookmark_tabs: Example
For the sake of example, the process of downloading of a course from [Japanese Pod 101](https://www.japanesepod101.com/) will be demonstrated.

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
- To download *Lower Beginner Season 1* we will have to navigate to `lesson 1` of this course (any other lesson url from the **same course** is ok too...).

  Navigation would look like this: `Japanesepod101` -> `Level 2 - Beginner` -> `Lower Beginner Season 1`  -> `lesson 01`.
  
  Save the URL for `lesson 01` from the address bar as you will have to provide it in the script later on.

- Run the [language101_scraper.py](language101_scraper.py) file in dedicated course folder.

- Follow the instructions of the script. You will have to log in to the website through the script and insert the course's lesson URL you have navigated through earlier (in our example: `lesson 01` of the `Lower Beginner Season 1` course). The instructions that will appear on screen afterwards are pretty straight forward.

- The script will start downloading the MP3 files into the local navigated folder, any possible errors would be printed out.

- Output inside folder should look like this:
  ```
  ├─01 - A Formal Japanese Introduction - JapanesePod101 - Dialogue.mp3
  ├─01 - A Formal Japanese Introduction - JapanesePod101 - Review.mp3
  ├─01 - A Formal Japanese Introduction - JapanesePod101 - Main Lesson.mp3
  ├─02 - Which Famous Tokyo Tower is That - JapanesePod101 - Dialogue.mp3
  ├─02 - Which Famous Tokyo Tower is That - JapanesePod101 - Main Lesson.mp3
  ├─02 - Which Famous Tokyo Tower is That - JapanesePod101 - Review.mp3
  ├─03 - Networking in Japan - JapanesePod101 - Dialogue.mp3
  ├─03 - Networking in Japan - JapanesePod101 - Main Lesson.mp3
  ├─03 - Networking in Japan - JapanesePod101 - Review.mp3
  ├─...
  ```

##  :clipboard:	Disclaimer and known issues
- Any usage of the script is under user's responsibility only. Users of the script must act according to site's terms. 

- As of today, Innovative Language's terms of use does not forbid usage of crawlers or scrapers on any of their sites.
This may change in the future, so be aware. 

- If you like the services Innovative Language provides you should consider a monthly subscription. Basic programs start at around $5 per month and include support from native speaker teachers.

- As with all websites, the site's structure may change in the future and thus, as often happens with scraping scripts, deprecate it. It is not really a question of *if* the site's source code will change but rather **when** (so enjoy it while it's still working :grin:).

##  :lock: License

All of the content presented in the websites belongs to the original creators (Innovative Language) and I have nothing to do with it.

The license below refers only to the script and not to the downloaded content.

[License - MIT](LICENSE.md)