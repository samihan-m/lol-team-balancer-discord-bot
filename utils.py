'''
Created on Mar 27, 2021

@author: ssmup
'''

if __package__ is None or __package__ == "":
    from runner import Runner
else:
    from .runner import Runner

"""
Functions to implement:

RIOT API
Summoner name verifyer
Rank string fetcher

OPGG
Previous season rank fetcher

"""

#For accessing Riot API
from riotwatcher.LolWatcher import LolWatcher
from riotwatcher.Handlers import ApiError

#For web-scraping from op.gg
import requests
from bs4 import BeautifulSoup

#For writing/reading the player_list
import pickle

#For loading environment variables (such as API key)
import os
from dotenv import load_dotenv

on_heroku = False
    if 'ON_HEROKU' in os.environ:
        on_heroku = True
if not on_heroku:
    load_dotenv()
    riot_api_key = os.environ.get("RIOT_API_KEY")
else:
    riot_api_key = os.getenv("RIOT_API_KEY")


riot_api = LolWatcher(riot_api_key)

#Dictionary of sensible region strings to Riot API region codes
regions = {
    "NA": "na1",
   "EUW": "euw1",
   "EUNE": "eune1",
   "KR": "kr",
   "LAN": "la1",
   "LAS": "la2",
   "OCE": "oc1",
   "BR": "br1",
   "TR": "tr1",
   "RU": "ru",
   "JP": "jp1"
   }
regions_to_country = {
    "NA": "North America",
   "EUW": "EU West",
   "EUNE": "EU Northeast",
   "KR": "Korea",
   "LAN": "Latin America North",
   "LAS": "Latin America South",
   "OCE": "Oceania",
   "BR": "Brazil",
   "TR": "Turkey",
   "RU": "Russia",
   "JP": "Japan"
    }

#A function that lets Riot API region codes be turned into sensible region strings
def get_key(region):
    for key, value in regions.items():
        if(region == value):
            return key

#Dictionary of LoL tiers and mappings to rank code points
tiers = {   
    'IRON': 0,
    'BRONZE': 1,
    'SILVER': 2,
    'GOLD': 3,
    'PLATINUM': 4,
    'DIAMOND': 5,
    'MASTER': 6,
    'GRANDMASTER': 7,
    'CHALLENGER': 8
    }

#Dictionary of LoL ranks and mappings to rank code points
ranks = {
    'I': 3,
    'II': 2,
    'III': 1,
    'IV': 0,
    #The numbers are for compatibility with op.gg rank_strings
    '1': 3,
    '2': 2,
    '3': 1,
    '4': 0
    }

def verify_summoner_name(summoner_name, region_code, input_is_id = False):
    """
    Given a summoner name and a region, uses riot's api to check if the summoner is real.
    Region must be in the form of Riot API region codes
    
    Also can work with summoner_id if input_is_id is set to True
    
    Returns a dictionary of keys:
        valid_summoner (if the summoner exists in that region)
        rate_limit_error (if the request exceeded the rate limit)
        other_error (if the error was something else unchecked)
        summoner (None if valid_summoner is false, otherwise the data for the summoner)
    """ 
    
    print("Veryifying in region: %s summoner name: %s" % (region_code, summoner_name))
    
    #Values to be returned
    valid_summoner = False
    rate_limit_error = False
    other_error = False
    retrieved_summoner = None
    
    try:
        print(summoner_name, region_code)
        if input_is_id is False:
            retrieved_summoner = riot_api.summoner.by_name(region_code, summoner_name)
        else:
            print(f"Verifying by summoner_id {summoner_name}")
            retrieved_summoner = riot_api.summoner.by_id(region_code, summoner_name)
    except ApiError as err:
        if err.response.status_code == 429:
            print('We should retry in {} seconds.'.format(err.headers['Retry-After']))
            print('this retry-after is handled by default by the RiotWatcher library')
            print('future requests wait until the retry-after time passes')
            rate_limit_error = True
        elif err.response.status_code == 404:
            print('No summoner with that name found.')
        else:
            raise Exception("non 429 or 404 error")
            other_error = True
        print(repr(err))
    if(retrieved_summoner):
        valid_summoner = True
        
    output = {'valid_summoner': valid_summoner, 'rate_limit_error': rate_limit_error, 'other_error': other_error, 'summoner': retrieved_summoner}
        
    print("Verification complete:", output)
    return output

def verify_role_preference_code(role_preference_code):
    """
    The Role Preference Code is a 5 digit number. The code should have the digits 1,2,3,4, and 5 without repeating.
    Returns True if the given string is a valid role_preference_code, false if not.
    """
    valid = False
    
    numstr = role_preference_code
    if(len(numstr) == 5) and '1' in numstr and '2' in numstr and '3' in numstr and '4' in numstr and '5' in numstr:
        valid = True
        
    return valid

def get_summoner_rank_string(summoner, region_code):
    """
    Assumes the given summoner is legitimate. (can be retrieved from verify_summoner_name)
    Uses Riot API to fetch the current rank of the given summoner.
    Returns a dictionary of keys:
        is_currently_ranked (if the player is currently ranked)
        has_solo_rank (if player is ranked in solo queue)
        has_flex_rank (if player is ranked in flex queue)
        solo_rank_string (the player's solo queue rank string (ex. SILVER 1 - None if player is not ranked))
        flex_rank_string (the player's flex queue rank string (ex. SILVER 1 - None if player is not ranked))
    """
    
    print("Fetching rank string in region: %s for summoner: %s" % (region_code, summoner['name']))
    
    is_currently_ranked = False
    has_solo_rank = False
    has_flex_rank = False
    solo_rank_string = None
    flex_rank_string = None
    
    #league_list contains one dict for each ranked leage the player has a rank in
    league_list = riot_api.league.by_summoner(region_code, summoner['id'])
    
    #solo queue : queueType = "RANKED_SOLO_5x5"
    #flex queue : queueType = "RANKED_FLEX_SR"
    
    #check if the player is in ANY leagues - easy way to check if ranked at all
    if(len(league_list) > 0):
        is_currently_ranked = True
        
        #check for solo queue rank
        for league in league_list:
            if(league['queueType'] == "RANKED_SOLO_5x5"):
                has_solo_rank = True
                solo_rank_string = "%s %s" % (league['tier'], league['rank'])
            if(league['queueType'] == "RANKED_FLEX_SR"):
                has_flex_rank = True
                flex_rank_string = "%s %s" % (league['tier'], league['rank'])
                
    output = {"is_currently_ranked": is_currently_ranked, "has_solo_rank": has_solo_rank, "has_flex_rank": has_flex_rank,
              "solo_rank_string": solo_rank_string, "flex_rank_string": flex_rank_string}
    
    print("Rank string fetch complete:", output)
    return output

def generate_opgg_link(summoner_name, region_code):
    """
    Given a summoner name and region code (ex: na1), returns the link to that summoner's op.gg page.
    """
    
    #First, turn the region and summoner name into the appropriate link.
    url_prefix = get_key(region_code).lower()
    #There's an exception; Korea's op.gg is at www.op.gg
    if(url_prefix == 'kr'):
        url_prefix = 'www'
        
    #If there are spaces in the summoner name, replace them with + (or _) (or %20)
    
    summoner_name = summoner_name.replace(" ", "+")
    
    return f"https://{url_prefix}.op.gg/summoner/userName={summoner_name}"

def get_previous_rank_string(summoner, region_code):
    """
    Assumes the given summoner is legitimate. (can be retrieved from verify_summoner_name)
    Scrapes from OP.GG to fetch the previous rank of the summoner.
    Returns a dictionary of keys:
        has_previous_rank (if op.gg has evidence of a rank from a previous season)
        previous_rank_string (the player's previous season rank string, None if op.gg doesn't have anything)
    """
        
    print("Fetching previous rank string in region: %s for summoner: %s" % (region_code, summoner['name']))
    
    has_previous_rank = False
    previous_rank_string = None
    
    opgg_page = generate_opgg_link(summoner['name'], region_code)
    
    #change times_to_scrape from 1 to a higher number if the scrape isn't accurate
    #loading the page more than once (on my browser at least) makes it work better
    times_to_scrape = 1
    for i in range(0, times_to_scrape):
        print("Making request #%d to op.gg for rank" % (i + 1))
        #requesting page multiple times because it doesn't load the past rank list correctly every time
        page = requests.get(opgg_page)
        
    soup = BeautifulSoup(page.text, "html.parser")
    past_rank_list = soup.find_all("li", {"class": "Item tip"})
    
    if(len(past_rank_list) != 0):
        
        has_previous_rank = True      
        
        #grab the most recent one.                 
        most_recent_rank = past_rank_list[len(past_rank_list) - 1]
        
        #format: Element # ##LP
        print("Most recent rank:", most_recent_rank['title'])
        rank_info = most_recent_rank['title'].split()
        tier = rank_info[0].upper()
        
        #two cases: tier is not masters/grandmasters/challenger, tier is masters/grandmasters/challenger
        if(tier == "MASTER" or tier == "GRANDMASTER" or tier == "CHALLENGER"):
            previous_rank_string = tier
        else:
            division = int(rank_info[1])
            #handling cases from older seasons where divisions could go lower than 4
            if division > 4: 
                division = 4
                
            #Turn digit division into roman numerals
            division = int_to_roman_numerals(division)
                
            previous_rank_string = f"{tier} {division}"
            
    output = {"has_previous_rank": has_previous_rank, "previous_rank_string": previous_rank_string}
    
    print("Finished OP.GG rank fetch:", output)
    
    return output

def get_summoner_icon(summoner, region_code):
    """
    Uses the same scraping method as get_previous_rank_string to instead fetch the profile icon off of op.gg
    Note: the icon will be out-of-date if the op.gg page has not been refreshed in a while
    """
    
    print("Fetching summoner icon in region: %s for summoner: %s" % (region_code, summoner['name']))
    
    #default image to use if the web scrape is unsuccessful
    default_image = "https://cdn.discordapp.com/attachments/763533415978762261/826030723114336257/Default_Image_750x750.png"
    summoner_icon_link = default_image
    
    opgg_page = generate_opgg_link(summoner['name'], region_code)
    
    times_to_scrape = 1
    for i in range(0, times_to_scrape):
        print("Making request #%d to op.gg for icon" % (i + 1))
        #requesting page multiple times because it doesn't load the past rank list correctly every time
        page = requests.get(opgg_page)
        
    soup = BeautifulSoup(page.text, "html.parser")
    profile_icon_img = soup.find("img", {"class": "ProfileImage"})
    
    #If the image is found, fetch that source
    if profile_icon_img:
        print("Summoner icon found")
        summoner_icon_link = "https:" + profile_icon_img['src']
        
    print("Finished OP.GG summoner icon fetch:", summoner_icon_link)
    
    return summoner_icon_link
            
"""
#Tests
names = ["Vanea", "AgentPine", "breadpudding82", "error_bad_name"]
for summoner_name in names:
    summoner = verify_summoner_name(summoner_name, "na1")['summoner']
    if summoner is not None:
        get_summoner_rank_string(summoner, "na1")
        get_previous_rank_string(summoner, "na1")
    print()
"""   

def get_role_emote_string(role_preference_code):
    """
    Given a role preference code, returns a Discord embed-ready string of role emotes that represent the role preference code.
    """
    print("Converting role preference code to role emote string")
    role_to_emote = {
        '1': "<:Top:826682003503316992>",
        '2': "<:Jungle:826682003587727370>",
        '3': "<:Mid:826682003624820736>",
        '4': "<:Bot:826682003339477013>",
        '5': "<:Support:826682003435814952>"
        }

    role_emote_string = ""
    
    for digit in role_preference_code:
        role_emote_string += role_to_emote.get(digit)
    
    return role_emote_string
    
#def write_object(object_to_write):
    """
    
    The plan for writing objects:
    There will be a folder called 'data'
    In that folder will be a bunch of folders, one for each server with a runner. The folders are named after the unique server IDs.
    In each folder is a bunch of text files for each player in that server.
    
    on addPlayer, removePlayer, editPlayer (which should be remove player and add player), activate/deactivate, and startGame should all trigger a write.
    A write means the given runner (and maybe every other one?) writes their player list to the appropriate folder.
    
    on bot init, there is a file that it reads - (or it creates 1 runner for every file in data) to initalize the runners then call readPlayers on each
    
    """
    
def retrieve_runner_list(data_directory):
    """
    Take the names of all files in a given directory, instantiating a Runner object for each one, using the name as the server_id.
    Returns the list of runners.
    """
    print("Retrieving runner list from %s" % data_directory)
    server_id_list = []
    try:
        server_id_list = os.listdir(data_directory)
    except:
        print("Data directory does not exist")
    runner_list = list()
    for server_id in server_id_list:
        try:
            runner = pickle.load(open(r"%s/%s" % (data_directory, server_id), "rb+"))
        #runner = Runner(server_id)
        #runner.read_players(data_directory)
            runner_list.append(runner)
            print("Regenerated:", str(runner))
        except Exception as e:
            print(f"Error retrieving runner #{server_id}")
            print(repr(e))
        
    return runner_list

def store_runner_list(runner_list, data_directory):
    """
    Given a runner_list, writes each runner to a file based on the runner's server_id.
    Returns True if the write succeeds. False if an error occurs (in any of the write_players calls).
    """
    print("Storing runner list at %s" % data_directory)
    success = True
    for runner in runner_list:
        #print(f"Writing {runner} to " + r"%s/%s" % (data_directory, runner.server_id))
        try:
            pickle.dump(runner, open(r"%s/%s" % (data_directory, runner.server_id), "wb+"))
        #write_success = runner.write_players(data_directory)
        except Exception as e:
            success = False
            print(repr(e))
    print(f"Write success: {success}")
    return success

def update_player(player):
    """
    Calls the appropriate API's to update a player's name, icon, and ranks.
    (Assumes region does not change)
    returns:
        not_found (True if the player isn't found anymore)
        has_changed (True if the player's information changes after the API calls)
        new_player_info (A dictionary containing all fields required for a Player object, None if not_found)
    """
    
    print(f"Updating player {player}")
    
    not_found = False
    has_changed = False
    new_player_info = None
    
    #Using summoner ID because it persists across summoner name changes
    summoner_id = player.summoner_id
    region_string = player.region
    
    region_code = regions.get(region_string)
    
    summoner_verification_report = verify_summoner_name(summoner_id, region_code, input_is_id = True)
    if summoner_verification_report['valid_summoner'] is False:
        not_found = True
    else:
        summoner = summoner_verification_report['summoner']
        rank_string_fetch = get_summoner_rank_string(summoner, region_code)
        new_solo_rank_string = rank_string_fetch['solo_rank_string']
        new_flex_rank_string = rank_string_fetch['flex_rank_string']
        
        new_previous_rank_string = get_previous_rank_string(summoner, region_code)['previous_rank_string']
        new_icon = get_summoner_icon(summoner, region_code)
        
        #Copying region because that can't have changed if control is in this code block.
        new_region = player.region
        #Copying role_preference_code because that information is user-supplied.
        new_role_preference_code = player.role_preference_code
        
        old_player_info = {"name": player.name, "region": player.region, "summoner_id": player.summoner_id, "solo_rank_string": player.solo_rank_string,
                      "flex_rank_string": player.flex_rank_string, "previous_rank_string": player.previous_rank_string, 
                      "role_preference_code": player.role_preference_code, "icon": player.icon}
        
        new_player_info = {"name": summoner['name'], "region": new_region, "summoner_id": summoner['id'], "solo_rank_string": new_solo_rank_string,
                      "flex_rank_string": new_flex_rank_string, "previous_rank_string": new_previous_rank_string, 
                      "role_preference_code": new_role_preference_code, "icon": new_icon}
        
        if old_player_info != new_player_info:
            has_changed = True
    
    output = {"not_found": not_found, "has_changed": has_changed, "new_player_info": new_player_info}
    
    return output

tiers = {
    'IRON': 0,
    'BRONZE': 1,
    'SILVER': 2,
    'GOLD': 3,
    'PLATINUM': 4,
    'DIAMOND': 5,
    'MASTER': 6,
    'GRANDMASTER': 7,
    'CHALLENGER': 8
    }

divisions = {
    'I': 3,
    'II': 2,
    'III': 1,
    'IV': 0
    }

def get_rank_score(player_rank_strings, solo_rank_weight = 1, flex_rank_weight = 0.7, previous_rank_weight = 0.8):
    """
    From a dictionary of a player's rank strings {solo: X, flex: X, previous: X}, gets their rank strings and converts it into a rank score.
    Change the weight fields to adjust how the rank is calculated
    Returns
        unranked (True if the player's rank strings are ALL None)
        rank_score
    """
    
    print(f"Getting rank code from {player_rank_strings}")
    rank_scores = []
    total_rank_score = 0
    weights = {"solo": solo_rank_weight, "flex": flex_rank_weight, "previous": previous_rank_weight}    
    unranked = True
    
    score_per_tier = 100
    score_per_division = score_per_tier / 4
    
    #Calculate individual rank score per rank string
    for queue in player_rank_strings:
        rank_string = player_rank_strings[queue]
        rank_score = -1
        #Check if they're ranked in the queue before operating on the value   
        if rank_string is not None:
            unranked = False
            if(rank_string == "MASTER" or rank_string == "GRANDMASTER" or rank_string == "CHALLENGER"):
                rank_score = score_per_tier*tiers[rank_string]
            else:
                split_rank_string = rank_string.split()
                tier_score = score_per_tier*tiers[split_rank_string[0]]
                division_score = score_per_division*divisions[split_rank_string[1]]
                rank_score = tier_score + division_score
            if rank_score >= 0:
                rank_scores.append({"queue": queue, "rank_score": rank_score})
    
    #Average rank scores into total rank score by given weights
    total_weight = 0
    for rank_score in rank_scores:
        multiplier = weights.get(rank_score["queue"], 1)
        #print(rank_score["queue"], rank_score, multiplier)
        total_weight += multiplier
        total_rank_score += rank_score["rank_score"]*multiplier
    #print(total_rank_score, total_weight)
    if total_weight == 0:
        total_weight = 1
    total_rank_score /= total_weight
               
    output = {"unranked": unranked, "rank_score": total_rank_score}
    #print(output)
    return output   
        
#From https://stackoverflow.com/questions/28777219/basic-program-to-convert-integer-to-roman-numerals - Thanks Aziz Alto
def int_to_roman_numerals(num):

    roman = ''
    
    num_map = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'),
           (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]

    while num > 0:
        for i, r in num_map:
            while num >= i:
                roman += r
                num -= i

    return roman

#Runner test
#runner = Runner(1, "./data")
#runner.player_list.append("hello")
#runner.write_players()

#runner.read_players()
#print(runner.player_list)

#runner_list = retrieve_runner_list("./data")