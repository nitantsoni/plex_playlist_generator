import argparse
import random
import os.path
import certifi
import requests
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from plexapi.playlist import Playlist
from plexapi.exceptions import NotFound
import logging
import urllib3
from collections import defaultdict

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

args = None

def get_args():
    parser = argparse.ArgumentParser(description='Create playlist of unwatched episodes from random shows '
                                                 'but in correct episode order.')
    parser.add_argument('--name', help='Playlist Name', default='Next Unwatched TV Shows')
    parser.add_argument('--number', '-n', help='Number of episodes to add to play list', type=int, default=10)
    group_server = parser.add_argument_group('Server Connection Method')
    group_server.add_argument('--server', action='store_true', help='Server connection Method')
    group_server.add_argument('--baseurl', '-b', help='Base URL of Server')
    group_server.add_argument('--token', '-t', help='Authentication Token')
    group_account = parser.add_argument_group('Plex Account Connection Method')
    group_account.add_argument('--account', action='store_true', help='Account Connection Method')
    group_account.add_argument('--username', '-u', help='Plex Account Username')
    group_account.add_argument('--password', '-p', help='Plex AccountPassword')
    group_account.add_argument('--resource', '-r', help='Resource Name (Plex Server Name)')
    group_behaviour = parser.add_argument_group('Episode Selection Behaviour')
    group_behaviour.add_argument('--include-watched', action='store_true', help='include watched episodes, in random order')
    parser.add_argument('--debug', '-d', help='Debug Logging', action="store_true")
    parser.add_argument('--scheduled', '-s', help='Run the script in scheduled job mode', action="store_true")
    parser.add_argument('--blacklist', help='Path to "blacklist.txt" file. Default is current directory', default='./blacklist.txt')
    return parser.parse_args()

def playlist_uplayed_check(playlist_items):
    num_watched = 0
    for item in playlist_items:
        if item.isWatched:
                num_watched += 1
    if num_watched > len(playlist_items) - 6:
        logger.debug('5 or less unwatched episodes found')
        return True
    else:
        logger.debug('More than 5 unwatched episodes found')
        return False
    
    
def get_random_episodes(all_shows, n=10):
    # list of series to never include
    if os.path.isfile(args.blacklist):
        logger.info("Blacklist file was found.")
        text_file = open(args.blacklist, "r")
        BLACKLIST = text_file.read().splitlines()
        text_file.close()
    else:
        logger.info("Blacklist file NOT found. Continuing without.")
        BLACKLIST = []
    show_episodes = dict()
    for show in all_shows.all():
        if show.isWatched and args.include_watched is not True:
            continue
        if show.title in BLACKLIST:
            logger.debug(f'GET_EPISODES: Show Blacklisted: {show.title}')
            continue
        if args.include_watched is True:
            show_episodes[show.title] = show.episodes()
            # remove series 0 specials
            while show_episodes[show.title][0].seasonNumber == 0:
                season_episode = show_episodes[show.title][0].seasonEpisode
                episode_title = show_episodes[show.title][0].seasonEpisode
                show_episodes[show.title].pop(0)
                logger.debug(f'get_random_episodes: Series 0 Episode Removed: '
                             f'{show.title} - {episode_title} - {season_episode}')
        else:
            show_episodes[show.title] = show.unwatched()
            # Move season 0 specials to end of array
            seasons_list = defaultdict(int)
            for episode in show_episodes[show.title]:
                seasons_list[episode.parentIndex] += 1
            if len(seasons_list) > 1 and seasons_list[0] > 0:
                while show_episodes[show.title][0].seasonNumber == 0:
                    show_episodes[show.title].append(show_episodes[show.title][0])
                    logger.debug(f'get_random_episodes: Series 0 Episode moved to end of list: '
                                 f'{show.title} - {show_episodes[show.title][0].seasonEpisode}')
                    show_episodes[show.title].pop(0)
    next_n = []
    show_index = 0
    show_list = list(show_episodes.keys())
    random.shuffle(show_list)
    while len(next_n) < n:
        if show_index == len(show_list):
            show_index = 0
        show_name = show_list[show_index]
        if len(show_episodes[show_name]) >0:
            if args.include_watched:
                random.shuffle(show_episodes[show_name])
            next_n.append(show_episodes[show_name].pop(0))
            show_index += 1
        else:
            logger.debug(f'GET_EPISODES: No more unwatched episodes for {show_name}')
            show_index += 1
            continue
    return next_n


def main():
    global args
    args = get_args()
    plex = None
    if args.debug:
        logger.setLevel(logging.DEBUG)
    if args.account:
        # ## Connect via Account
        account = MyPlexAccount(args.username, args.password)
        plex = account.resource(args.resource).connect()
    elif args.server:
        # ## Connect via Direct URL
        baseurl = args.baseurl
        token = args.token
        session = requests.session()
        # disables HTTP Cert verification
#         session.verify = False 
        logger.debug(session.verify)
        plex = PlexServer(baseurl, token, session)
    else:
        exit(1)
    should_run = True
    if args.scheduled:
        should_run = playlist_uplayed_check(plex.playlist(title=args.name).items())

    if should_run:
        episodes = get_random_episodes(plex.library.section('TV Shows'), args.number)
        for episode in episodes:
            print(f'{episode.grandparentTitle} - {episode.parentTitle} - '
                  f'{episode.index}. {episode.title}')    
        try:
            plex.playlist(title=args.name).delete()
        except NotFound as e:
            logger.debug(f"Playlist {args.name} does not exist to delete.")
        Playlist.create(server=plex, title=args.name, items=episodes)
    print('Exiting')
if __name__ == '__main__':
    main()
