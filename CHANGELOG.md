Version 0.1.0
===========
- added support for config file
- added support getpass to not show sensitive login data

Version 0.2.0
===========
- added store for cookies
- added differentiation for downloading videos/audio/pdfs

Version 0.3.0
===========
- extract vocabulary for japanese and create anki decks

Version 0.4.0
===========
- degarbage output
- added "trustworthy" user-agent
- randomize delay while scraping. To not cause too much stress on the server side
- fixed issue with incorrectly handling config settings

Version 0.5.0
===========
- continue download from last successful downloaded lesson
- supports behavior for downloading levels and former lessons only

Version 0.5.1
===========
- fixed crashes for anki export if a single field is missing
- created commandline argument to force a new download "-f"

Version 0.5.2
===========
- fix in function call, when the download stack should be cleaned up after successfully downloading all elements

Version 0.5.3
===========
- fix in function call for download level URL

Version 0.5.4
===========
- merge with master from nedlir
- changed zfill to 3 instead of 2
- added try-block for 'data-collection-entries' from quique

Version 0.5.5
===========
- fixed recursive directory creation
