'''
Created on Mar 29, 2021

@author: ssmup
'''

"""
In here will go all of the matchmaking-relevant code
RankDiffReports, Team, TeamDiffReports, all of the functions, etc.

The game plan is to port literally all of the old functions.
I just need to add some code to turn rank strings into rank codes.
And it will be ready to go.
"""

#For using maxsize in sorting algorithm
import sys

class Matchup:
    """
    Stores matchup information between two players
    """
    def __init__(self,player_one, player_two, rank_delta = None):
        self.player_one = player_one
        self.player_two = player_two
        if rank_delta is None:
            self.rank_delta = self.player_one.rank_score - self.player_two.rank_score
        else:
            self.rank_delta = rank_delta
            
    def has_player(self, player):
        """
        Given a player object, if either the player_one or player_two field is that player, returns True.
        Otherwise, returns True.
        """
        has_player = False
        if self.player_one == player or self.player_two == player:
            has_player = True
        return has_player
        
    def __str__(self):
        return f"{self.player_one} vs. {self.player_two} ({self.rank_delta})"
    
class Team:
    """
    Stores the information of one team of players
    """
    def __init__(self, top_player, jungle_player, mid_player, bot_player, support_player):
        self.top = top_player
        self.jug = jungle_player
        self.mid = mid_player
        self.bot = bot_player
        self.sup = support_player
        self.players = top_player, jungle_player, mid_player, bot_player, support_player
        self.total_rank_score = 0
        for player in self.players:
            self.total_rank_score += player.rank_score
            
    def __str__(self):
        return f"{self.top}, {self.jug}, {self.mid}, {self.bot}, {self.sup} - {self.total_rank_score}"
            
class TeamMatchup:
    """
    Stores matchup information between two teams
    """
    def __init__(self, team_one, team_two):
        self.team_one = team_one
        self.team_two = team_two
        self.rank_delta = team_one.total_rank_score - team_two.total_rank_score
        
    def __str__(self):
        return f"{self.team_one} vs {self.team_two} ({self.rank_delta})"
    
    
def create_role_pools(queued_player_list):
    """
    Turn the given player list (ASSUMES THEY ARE IN QUEUE) into 5 pools of players, one for each role, based on their role preference codes.
    Returns a dictionary of 5 lists, one for each role.
    The way the lists are built means that elements in the front want to play that role more.
    returns
        {
        top: list of Player objects
        jug: same
        mid: same
        bot: same
        sup: same
        }
    """
    
    print(f"Creating role pools from {queued_player_list}")
    
    top = []
    jug = []
    mid = []
    bot = []
    sup = []
    
    #set to none by default, becomes False/True in the loop
    are_roles_pools_filled = None
    
    while are_roles_pools_filled is not True:
        #go through their rank codes, digit by digit
        for i in range(0, 5):
            for player in queued_player_list:       
                #print(player.role_preference_code[i])
                if player.role_preference_code[i] == "1":
                    #print(f"Adding {player.name} to the pool of potential Top players")
                    top.append(player)
                elif player.role_preference_code[i] == "2":
                    #print(f"Adding {player.name} to the pool of potential Jungle players")
                    jug.append(player)
                elif player.role_preference_code[i] == "3":
                    #print(f"Adding {player.name} to the pool of potential Mid players")
                    mid.append(player)
                elif player.role_preference_code[i] == "4":
                    #print(f"Adding {player.name} to the pool of potential Bot players")
                    bot.append(player)
                elif player.role_preference_code[i] == "5":
                    #print(f"Adding {player.name} to the pool of potential Support players")
                    sup.append(player)
                else:
                    print(f"Why is there a player with a role preference digit that isn't between 1 to 5? {player.role_preference_code[i]}")
                """"""
            
            print(f"Iteration {i}")
            #check if pools have enough players
            if len(top) < 3 or len(jug) < 3 or len(mid) < 3 or len(bot) < 3 or len(sup) < 3:
                are_roles_pools_filled = False
                print(f"A pool has less than 3 players, running through player list again.")
            else:
                are_roles_pools_filled = True
                #exit early, don't go through every digit unless NECESSARY
                print(f"Finished pool creation; used first {i+1} digits of role preference code.")
                break
    filled_pools = {"top": top, "jug": jug, "mid": mid, "bot": bot, "sup": sup}
    #print(filled_pools)
    return filled_pools
                
def generate_matchups(role_pools):
    """
    From a dictionary of role pools (retrieved from create_role_pools), generate a list of every possible matchup for each role.
    Returns the dictionary.
    returns
        {
        top: list of Matchup objects
        jug: same
        mid: same
        bot: same
        sup: same
        }
    """
    
    print(f"Generating matchups!")
    
    matchups = {"top": [], "jug": [], "mid": [], "bot": [], "sup": []}
    
    for role in role_pools:
        print(f"Generating matchups for {role}")
        #Create a Matchup object between a player and every other player
        player_list = role_pools[role]
        for i in range(0, len(player_list)):
            #i+1 so a matchup isn't created with a player against themselves
            for j in range(i+1, len(player_list)):
                #print(f"Creating matchup between {player_list[i].name} and {player_list[j].name}")
                matchup = Matchup(player_list[i], player_list[j])
                matchups[role].append(matchup)
                
    sorted_matchups = {"top": [], "jug": [], "mid": [], "bot": [], "sup": []}        
    
    #Sort matchups by decreasing rank delta
    for role in matchups:
        role_list = matchups[role]
        while len(role_list) > 0:
            #Creating a dummy matchup with maximum possible rank delta for purposes of it being a maximum in the sort algorithm
            most_fair_matchup = Matchup({}, {}, sys.maxsize)
            for matchup in role_list:
                if abs(matchup.rank_delta) < abs(most_fair_matchup.rank_delta):
                    most_fair_matchup = matchup
            sorted_matchups[role].append(most_fair_matchup)
            role_list.remove(most_fair_matchup)
            
    print(f"Finished sorting matchups!")
    
    return sorted_matchups

def select_matchups(sorted_matchups, player_list):
    """
    From a dictionary of sorted matchups (retrieved from generate_matchups) generate a list of the optimal matchups for each role.
    
    Also takes in a player_list for autofill purposes.
    
    Returns the list.
    """
    
    print(f"Generating teams")
    #Iterate through each role pool and pick the most balanced matchup from it.
    #Start with the roles that have the smallest player pools.
    #This sorts the lists in the sorted_matchups dictionary to be in order of least to greatest length.
    prioritized_matchups = sorted(sorted_matchups.items(), key = lambda x: len(x[1]), reverse = False)
    """
    for list in sorted_matchups:
        print(list)
    """
    
    selected_matchups = {"top": [], "jug": [], "mid": [], "bot": [], "sup": []}
    
    for i in range(0, 5):
        role = prioritized_matchups[i][0]
        matchup_list = prioritized_matchups[i][1]
        
        #check if there are any matchups left - if not, we need to autofill
        if len(matchup_list) > 0:
            print(f"Picking most balanced matchup for {role}")
            #selecting most balanced matchup (which is the first one in the list)
            matchup = matchup_list[0]
            
            player_one = matchup.player_one
            player_two = matchup.player_two
            selected_matchups[role].append(player_one)
            selected_matchups[role].append(player_two)
            
            #Remove all other matchups with those players
            print(f"Removing matchups with {player_one} or {player_two}")
            for i in range(0, 5):
                role = prioritized_matchups[i][0]
                matchup_list = prioritized_matchups[i][1]
                copy_of_matchup_list = list(matchup_list)
                print(f"Scanning {role} list.")
                for matchup in copy_of_matchup_list:
                    if matchup.has_player(player_one) or matchup.has_player(player_two):
                        print(f"Removing {matchup}")
                        matchup_list.remove(matchup)
            
        else:
            #need to autofill
            print(f"Need to autofill for {role}")
            #autofill will be handled later
            for role in selected_matchups:
                print(role)
                for player in selected_matchups[role]:
                    print(player)
                    
    
    #perform autofill check
    unfilled_matchups = [role for role in selected_matchups if len(selected_matchups[role]) < 2]
    selected_players = [player for role in selected_matchups.values() for player in role]
    remaining_players = [player for player in player_list if player not in selected_players]
    
    if len(remaining_players) > 0:
        print(f"Performing autofill protocol for {unfilled_matchups}")
        for role in unfilled_matchups:
            selected_matchups[role].append(remaining_players[0])
            selected_matchups[role].append(remaining_players[1])
            print(f"Filling {role} with {remaining_players}")
    
    
    #turn the selected matchups 
    return selected_matchups

def generate_teams(selected_matchups):
    """
    Given a dictionary of the two players for each of the five roles (from select_matchups), creates a list of every team combination. (32)
    Returns a list, sorted from smallest to largest team rank delta.
    """
    
    print("Generating team combinations!")
    
    team_combinations = []
    
    #Use nested for loops to generate the combinations
    #It's like counting in binary
    #From 00000 to 11111
    #0 in the first position means team_one gets the first top laner in the top laner list in selected_matchups
    #1 means team_two gets the first top laner in the top laner list
    #etc.
    for team in range(0, 32):
        roster = f"{team:05b}"
        
        #blue side
        team_one = {"top": None, "jug": None, "mid": None, "bot": None, "sup": None}
        #red side
        team_two = {"top": None, "jug": None, "mid": None, "bot": None, "sup": None}
        
        for index, role in enumerate(["top", "jug", "mid", "bot", "sup"]):
            if roster[index] == "0":
                team_one[role] = selected_matchups[role][0]
                team_two[role] = selected_matchups[role][1]
            else:
                team_one[role] = selected_matchups[role][1]
                team_two[role] = selected_matchups[role][0]
                
        #assemble team objects
        blue_side = Team(*team_one.values())
        red_side = Team(*team_two.values())
        
        team_matchup = TeamMatchup(blue_side, red_side)
        
        team_combinations.append(team_matchup)
        
    #Sort team combinations
    team_combinations = sorted(team_combinations, key = lambda x: abs(x.rank_delta))
    
    for combo in team_combinations:
        print(combo)
        
    return team_combinations
    
    
    
    