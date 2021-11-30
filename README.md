# Plex Random Series Playlist Generator

Simple script to generate a playlist on a plex server that randomises the series, but plays the episodes within that 
series in order.

##Usage
```
usage: playlist_generator.py [-h] [--name NAME] [--number NUMBER] [--server]
                             [--baseurl BASEURL] [--token TOKEN] [--account]
                             [--username USERNAME] [--password PASSWORD]
                             [--resource RESOURCE] [--ignore-skipped]
                             [--randomize] [--include-watched] [--debug]

Create playlist of unwatched episodes from random shows but in correct episode
order.

optional arguments:
  -h, --help                    show this help message and exit
  --name NAME                   Playlist Name
  --number NUMBER, -n NUMBER    Number of episodes to add to play list
  --debug, -d                   Debug Logging
  --scheduled, -s		Run the script in scheduled job mode
  --blacklist			Path to the blacklist.txt file. Default is current directory

Server Connection Method:
  --server                      Server connection Method
  --baseurl BASEURL, -b BASEURL Base URL of Server
  --token TOKEN, -t TOKEN   Authentication Token

Plex Account Connection Method:
  --account              Account Connection Method
  --username USERNAME, -u USERNAME   Plex Account Username
  --password PASSWORD, -p PASSWORD   Plex AccountPassword
  --resource RESOURCE, -r RESOURCE   Resource Name (Plex Server Name)

Episode Selection Behaviour:
  --include-watched     include watched episodes, in random order
```
## Connection Methods
### Account
Uses your PlexTV Account, username and Resource Name (Server Name)  
e.g. `playlist_generator.py --account --username MyUserName --password Sh1tPass --resource MyServer`

### Server
Uses The Server URL and Authentication Token  
e.g. `playlist_generator.py --server --baseurl "http://172.16.1.100:32400" --token "fR5GrDxfLunKynNub5"`

### Authentication Token
To get your Auth token, browse to an episode in the web UI. Click on the `...` video and select `Get Info`.  In the 
popup window select `View XML` in the URL there is the `X-Plex-Token=XXXXXXXXXXXXXX`

### Blacklist
The Blacklist is read from an external file. Path can be optionally specified via the `--blacklist` argument. Defaults to "./blacklist.txt". A sample blacklist has been included. Add the shows to not include here and rename it to "blacklist.txt"
e.g. `playlist_generator.py --server --baseurl "http://172.16.1.100:32400" --token "fR5GrDxfLunKynNub5" --blacklist "path/to/blacklist.txt"`

### Season 0 Specials Handling
Episodes from Season 0 are now handled differently than the parent script. Incase the "Include Watched" option is selected, they are not added to the final playlist. Otherwise in normal mode, they are added once all other episodes have been marked as watched.

### Episode Selection
This now works differently from the parent script. The script will now ensure TV Shows are spaced out snd repetition is kept to a minimum. Each playlist entry will be from a different show if possible.

### Scheduled Job Mode
In this mode, the script will only run if 5 or less unwatched items remain in the playlist
