#!/usr/bin/env python3
# Initially created by airmack 21.Dec.2020

from bs4 import BeautifulSoup
import genanki
from genanki.model import Model

import time
import logging

BASIC_AND_REVERSED_CARD_JP_MODEL = Model(
    12938895,
    'Basic (and reversed card) (genanki)',
    fields=[
        {
            'name': 'Kana',
            'font': 'Arial',
        },
        {
            'name': 'English',
            'font': 'Arial',
        },
        {
            'name': 'Kanji',
            'font': 'Arial',
        },
        {
            'name': 'Audio',
            'font': 'Arial',
        },

    ],
    templates=[
        {
            'name': 'Card 1',
            'qfmt': '{{Kanji}}',
            'afmt': '{{FrontSide}}\n\n<hr id=answer>\n\n{{Kana}}{{Audio}}<br>{{English}}',
        },
        {
            'name': 'Card 2',
            'qfmt': '{{English}}',
            'afmt': '{{FrontSide}}\n\n<hr id=answer>\n\n{{Kanji}}<br>{{Kana}}{{Audio}}',
        },
    ],
    css='.card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n',
)


def createKeyIfNeeded(parent, cards):
    if cards.get(parent) == None:
        cards[parent] = dict()
    return cards


class Language:
    """Primitive class with abstract function.
       Scraper needs to return a list of files that need to be downloaded. The download itself need to be done somplace else.
       CreateDeck creates the anki deck from the vocabulary."""

    def __init__(self):
        self.language = ""

    def Scraper(self, root_url, lesson_soup):
        return []

    def CreateDeck(self, title):
        pass


class Japanese(Language):
    def __init__(self):
        """Several states need to be stored. They are defined here and later on used when creating the deck."""
        self.language = "Japanese"
        self.cards = dict()
        self.audio_files = []

    def Scraper(self, root_url, lesson_soup):
        """Parse through the vocabulary section and get kanji, kana, english definition and audio."""
        needsToBeDownloaded = []
        for i in lesson_soup.find_all("span",  {"lang": "ja", "class": None}):
            parent = hash(i.find_parent("tr"))
            self.cards = createKeyIfNeeded(parent, self.cards)
            self.cards[parent]["japanese_kana"] = i.get_text().strip()

        for i in lesson_soup.find_all("span",  {"lang": "ja", "class": "lsn3-lesson-vocabulary__pronunciation"}):
            parent = hash(i.find_parent("tr"))
            self.cards = createKeyIfNeeded(parent, self.cards)
            self.cards[parent]["japanese_pronaunciation"] = i.get_text().strip()[
                1:-1].strip()

        for i in lesson_soup.find_all("span",  {"class": "lsn3-lesson-vocabulary__definition", "dir": "ltr"}):
            # we ignore sample sentences
            if i.find_parent("span", {"class": "lsn3-lesson-vocabulary__sample js-lsn3-vocabulary-examples"}):
                continue
            parent = hash(i.find_parent("tr"))
            self.cards = createKeyIfNeeded(parent, self.cards)
            self.cards[parent]["english_definition"] = i.get_text().strip()

        for i in lesson_soup.find_all("button",  {"class": "js-lsn3-play-vocabulary", "data-type": "audio/mp3", "data-speed": None}):
            if i.find_parent("span", {"class": "lsn3-lesson-vocabulary__sample js-lsn3-vocabulary-examples"}) or i.find_parent("td", {"class": "lsn3-lesson-vocabulary__td--play05 play05"}):
                continue
            url_filename = i["data-src"].strip()
            needsToBeDownloaded.append(url_filename)
            name = url_filename.split('/')[-1]
            self.audio_files.append(name)

            parent = hash(i.find_parent("tr"))
            self.cards = createKeyIfNeeded(parent, self.cards)
            self.cards[parent]["japanese_audio"] = "[sound:" + name + "]"
            self.cards[parent]["audio_files"] = name
        self.SanityCheck()

        return needsToBeDownloaded

    def SanityCheck(self):
        for i in self.cards:
            for j in ["japanese_pronaunciation", "english_definition", "japanese_kana", "japanese_audio"]:
                if self.cards[i].get(j) is None:
                    self.cards[i][j] = ""
                    logging.warning(j + " does not exist")

    def CreateDeck(self, title):
        """Create a deck from all vocabulary entries"""
        deck = genanki.Deck(abs(hash(title)), title)
        for i in self.cards:
            deck.add_note(genanki.Note(BASIC_AND_REVERSED_CARD_JP_MODEL, [self.cards[i].get("japanese_pronaunciation"), self.cards[i].get(
                "english_definition"), self.cards[i].get("japanese_kana"), self.cards[i].get("japanese_audio")]))
        my_package = genanki.Package(deck)
        my_package.media_files = self.audio_files
        local_file = "".join(title.split()) + ".apkg"
        my_package.write_to_file(local_file, timestamp=time.time())
        logging.info("Created " + local_file)
