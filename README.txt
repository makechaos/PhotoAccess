# Author: Vikram Melapudi aka makechaos (makechaos [at] gmail [dot] com)
# Updated: 07 Jan 2014
# Started: 25 Dec 2013

Files:
simpleServer.py: very simple server based on web.py
photoServer.py: backend processing of user inputs and link with MongoDB database
addDirImagesToDB.py: batch processing of directory to find and add images to dB
pyflickr.py: code to upload images to flickr user account
startServer.sh: script to start MongoDB server and the photo-server

Architecture:
(user) webpage request
<----> simpleServer.py
<----> photoServer.py | <---> MongoDB (using pymongo)
                      | <---> addDirImagesToDB.py 
                      |       --> MongoDB
                      | <---> pyflickr.py 
                      |       <--> MongDB 
                      |       <--> flickr.com

Admin Codes:
1. Sync album with flickr: <...>/sync/<album name>
2. Sync dir to database  : <...>/syncdir/<dir name>


