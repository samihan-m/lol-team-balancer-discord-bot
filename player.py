'''
Created on Mar 27, 2021

@author: ssmup
'''

class Player(object):
    """
    Contains info for League of Legends players.
    """
    
    def __init__(self, name, region, summoner_id, solo_rank_string, flex_rank_string, previous_rank_string, rank_score, role_preference_code, icon):
        """
        Player constructor - takes League name, region, rank string, rank code, previous season rank string / rank code, role code, 
        """
        self.name = name
        self.region = region
        #Use summoner_id as the primary identification for a Player object. If possible.
        self.summoner_id = summoner_id
        self.solo_rank_string = solo_rank_string
        self.flex_rank_string = flex_rank_string
        self.previous_rank_string = previous_rank_string
        self.rank_score = rank_score
        self.role_preference_code = role_preference_code
        #should be a string, a link to an icon
        self.icon = icon
        
        #players are set to active by default. if they aren't active, why are they being created?
        #point is, if a player is adding their name to the bot, there's probably a game being made at that moment.
        #BUT it doesn't make sense to automatically be in queue.
        self.is_active = False
        
    def get_rank_code_from_rank_string(self, encode_function):
        """
        
        """
        
    def get_rank_strings(self):
        """
        Returns a dict with the player's ranked strings.
        """
        rank_strings = {"solo": self.solo_rank_string, "flex": self.flex_rank_string, "previous": self.previous_rank_string}
        return rank_strings
        
    def __str__(self):
        return f"{self.name}"