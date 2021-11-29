import argparse
import random
import os.path
import certifi
import requests
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from plexapi.playlist import Playlist
from plexapi.exceptions import NotFound
#import tvdb_api
import re
import logging
import urllib3
from collections import defaultdict

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

args = None

# list of series to never include

if os.path.isfile("blacklist.txt"):
    logger.info("Blacklist file was found.")
    text_file = open("blacklist.txt", "r")
    BLACKLIST = text_file.read().splitlines()
    text_file.close()
else:
    logger.info("Blacklist file NOT found. Continuing without.")
    BLACKLIST = []


def get_args():
    parser = argparse.ArgumentParser(description='Create playlist of unwatched episodes from random shows '
                                                 'but in correct episode order.')
    parser.add_argument('--name', help='Playlist Name', default='Random Season, Next Unwatched')
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
    group_behaviour.add_argument('--randomize', action='store_true', help='Randomize selected episodes, not next unwatched')
    group_behaviour.add_argument('--include-watched', action='store_true', help='include watched episodes (use with --randomize')
    parser.add_argument('--debug', '-d', help='Debug Logging', action="store_true")
    return parser.parse_args()


def get_random_episodes(all_shows, n=10):
    show_episodes = dict()
    for show in all_shows.all():
        if args.include_watched is True:
            if args.randomize is False:
                logger.warning("Setting --randomized flag, or playlist will always start at Episode 1 for each series")
                args.randomize = True

        if show.isWatched and args.include_watched is not True:
            continue
        if show.title in BLACKLIST:
            logger.debug(f'GET_EPISODES: Show Blacklisted: {show.title}')
            continue
        if args.include_watched is True:
            show_episodes[show.title] = show.episodes()
        else:
            show_episodes[show.title] = show.unwatched()
        # Move season 0 specials to end of array
        seasons_list = defaultdict(int)
        for episode in show_episodes[show.title]:
            seasons_list[episode.parentIndex] += 1
        if len(seasons_list) > 1 and seasons_list[0] > 0:
            while show_episodes[show.title][0].seasonNumber == 0:
                show_episodes[show.title].append(show_episodes[show.title][0])
                logger.debug(f'get_random_episodes: Series 0 Episode Appended to end of list'
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
            if args.randomize:
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
        session.verify = False
        logger.debug(session.verify)
        plex = PlexServer(baseurl, token, session)
    else:
        exit(1)

    all_shows = plex.library.section('TV Shows')

    episodes = get_random_episodes(all_shows, n=args.number)
    for episode in episodes:
        season_episode = episode.seasonEpisode
        print(f'{episode.grandparentTitle} - {episode.parentTitle} - '
              f'{episode.index}. {episode.title}')

    try:
        plex.playlist(title=args.name).delete()
    except NotFound as e:
        logger.debug(f"Playlist {args.name} does not exist to delete.")
    Playlist.create(server=plex, title=args.name, items=episodes)


if __name__ == '__main__':
    main()
