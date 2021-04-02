'''
Created on Mar 28, 2021

@author: ssmup
'''

#For loading environment variables (such as API key)
import os
from dotenv import load_dotenv

#For communicating with Discord API
import discord
#For adding commands to the bot
from discord.ext import commands

#For writing/reading information like the custom_prefixes dictionary
import pickle

#This is here because package is None when Heroku runs bot.py
if __package__ is None or __package__ == "":
    import utils
    import matchmaking
    from runner import Runner
    from player import Player
else:
    from . import utils as utils
    from . import matchmaking as matchmaking
    from .runner import Runner
    from .player import Player

load_dotenv()
#TOKEN = os.getenv('DISCORD_TOKEN')
TOKEN = os.getenv("TEST_TOKEN")


#Read custom prefixes from file - custom_prefixes.json
custom_prefixes_location = r"./custom_prefixes.json"
custom_prefixes = dict()
if not os.path.exists(custom_prefixes_location):
    open(custom_prefixes_location, 'w').close()
    print("Created custom prefixes file")
else:
    try:
        print("Loading custom prefixes from file %s" % custom_prefixes_location)
        custom_prefixes = pickle.load(open(custom_prefixes_location, "rb"))
        print("Loading custom prefixes succeeded")
    except:
        print("Loading custom prefixes failed")
    
default_prefixes = ["!", ">"]

async def get_prefixes(bot, message):
    """
    Checks if the message's guild has a custom_prefix. If so, returns that. Otherwise, returns the default prefix.
    """
    server = message.guild
    server_id = None
    
    if server:
        server_id = server.id
    
    #Get custom prefix list OR default prefixes
    prefixes = custom_prefixes.get(server_id, default_prefixes)
        
    return prefixes

bot = commands.Bot(command_prefix=get_prefixes, case_insensitive = True)
bot.remove_command("help")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name='%shelp' % default_prefixes[0]))
    print(f'{bot.user.name} has connected to Discord!')
    
    print("Starting start-up player updates")
    """
    for runner in runner_list:
        for player in runner.player_list:
            #Trying to fake a context object
            ctx = None
            await update_player(ctx, player.name, server_id = runner.server_id)
    """
    print("Done with updating players on start-up.")
            
    
#The directory in which runner's save their information
data_directory = "./data"

#retrieve runners
runner_list = utils.retrieve_runner_list(data_directory)
#Update all players on read
for runner in runner_list:
    for player in runner.player_list:
        #This is pointless because it doesn't do anything with the returned player objects.
        #To be a good update-on-start function I should call the update_player bot command
        #SEE on_ready() for implementation of above
        ##utils.update_player(player)
        """"""

#Links to images used in bot embeds
checkURL = "https://cdn.discordapp.com/attachments/714048183457677372/714239812504256552/checkMark.png"
crossURL = 'https://cdn.discordapp.com/attachments/714048183457677372/714239830820651008/crossMark.png'
league_logo = "https://cdn.discordapp.com/attachments/714048183457677372/714254584704663612/league-of-legends-logo.png"

@bot.command(name = 'prefix')
async def set_prefix(ctx, prefix):
    """
    Receives a prefix string from the user. If the user is an admin, then check the prefix to see if it's valid. 
    If valid, add it to the custom_prefixes dictionary.
    Also write the custom_prefixes list to file.
    """
    
    print("Executing command: set_prefix")
    
    server_id = ctx.guild.id
    
    embed = discord.Embed(
        title = "Add Custom Prefix",
        description = "",
        color = discord.Color.default()
        )
    
    print("Verifying user has administrator privileges")
    if ctx.message.author.guild_permissions.administrator: 
            print("User has administrator privileges")
            
            print("Verifying validity of given prefix")
            
            is_valid_prefix = False
            
            #Expand valididty checking later if necessary
            if prefix is not None:
                is_valid_prefix = True
            
            if(is_valid_prefix):
                print("Valid prefix. Adding to custom prefix dictionary")
                
                embed = discord.Embed(
                    title = f"Your New Command Prefix is {prefix}",
                    description = f"The bot will now recognize commands with this prefix.",
                    color = discord.Color.green()
                    )
                embed.set_author(name = "Custom Prefix Set", icon_url = checkURL)
                
                custom_prefixes[server_id] = prefix
                
                print("Attempting custom prefix dictionary write")
                try:
                    pickle.dump(custom_prefixes, open(custom_prefixes_location, "wb"))
                    print(f"Success writing custom prefix dictionary to {custom_prefixes_location}")
                    #Valid prefix embed - "Success setting the new prefix! Here is what commands will look like: "
                    
                except:
                    print(f"Failure writing custom prefix dictionary to {custom_prefixes_location}")
                    #Failure to write embed (Valid prefix, but failed writing - "The new prefix will most likely reset overnight - set it again soon!"
                    await ctx.send("There was an error in saving the prefix - it will most likely reset overnight - set it again soon!")
                
            else:
                print("Invalid prefix.")
                #Invalid prefix embed - "Try a new prefix
                embed = discord.Embed(
                    title = "Invalid Prefix",
                    description  = f"Try again with a different prefix.",
                    color = discord.Color.red()
                    )
                embed.set_author(name = "Error", icon_url = crossURL)
    else:
        print("User does not have administrator privileges")
        #Not administrator embed
        embed = discord.Embed(
                title = "Administrator Command Only",
                description  = f"Only users with Administrator privileges can use this command.",
                color = discord.Color.red()
                )
        embed.set_author(name = "Error", icon_url = crossURL)

    await ctx.send(embed = embed)
    
def get_runner(ctx, server_id = None):
    """
    Given ctx, fetches a Runner for that server. Or, if one doesn't exist, creates one with default values. (region = NA)
    Then, returns the Runner.
    
    Also, there's an option to provide a server_id directly. Set it to anything besides None.
    """
    
    if server_id is None:
        server_id = ctx.guild.id
    
    print(f"Fetching runner for server {server_id}")
    
    found_runner = None
    
    for runner in runner_list:
        if server_id == runner.server_id:
            found_runner = runner
            break
    
    if found_runner is None:
        found_runner = Runner(server_id, "na1")
        #Print starting information: "This server's region has been set to North America. Use the region command to change it if necessary."
        runner_list.append(found_runner)
        
    print(f"Found runner: {found_runner}")
        
    return found_runner
    
    
@bot.command(name="get")
async def get_player(ctx, *args):
    """
    Checks if the given summoner is in the given server's player list, and if so, returns an embed with their information.
    """
    
    #Need this join so summoner names with spaces are handled
    summoner_name = " ".join(args[:])
    
    retrieved_player = None
    embed = discord.Embed()
    
    runner = get_runner(ctx)
    
    for player in runner.player_list:
        if summoner_name == player.name:
            retrieved_player = player
            break
    
    if retrieved_player is None:
        #Display failure embed - "That player is not in the player list. Add them with the add command!"
        embed = discord.Embed(
            title = "Nobody Found",
            description  = "That player is not in the player list.\nAdd them with the add command!",
            color = discord.Color.red()
            )
        embed.set_author(name = "Error", icon_url = crossURL)
    else:
        #Display player info embed
        #Info to show: name, region, all three rank strings, role preference code, icon
        embed = discord.Embed(
            title = retrieved_player.name,
            color = discord.Color.green()            
            )
        
        embed = create_player_info_embed(retrieved_player)
            
        embed.set_author(name = "Found Player", icon_url = checkURL)
        
        embed.set_footer(text = 'To edit any of this information, use the edit command.')
        
    await ctx.send(embed = embed)
    
@bot.command(name = "add")
async def add_player(ctx, *args):
    """
    Reads summoner name and role preference code, validating both before creating a Player object and adding it to the server's player list.
    Also, if valid, calls get_player to print the info embed from that function.
    """

    #Check if enough inputs were given (1. summoner name, 2. role preference code)
    if len(args) < 2:
        prefixes = await get_prefixes(bot, ctx.message)
        #Display an error message stating the syntax of the command
        embed = discord.Embed(
            title = "Incorrect Command Usage",
            #description = ,
            color = discord.Color.red()
            )
        embed.add_field(name = "Syntax", value = f"{prefixes[0]}add SummonerName 12345\n(but change the numbers to fit your role preferences.)")
        embed.set_author(name = "Error", icon_url = crossURL)
        
        #putting a return here because i think it looks better than indenting the rest of the function and putting it in an else
        await ctx.send(embed = embed)
        return
    
    embed = discord.Embed()
    
    #Turn args into summoner name and role preference code
    args = list(args)
    role_preference_code = args[-1]
    args.pop()
    summoner_name = " ".join(args[:])
    
    #First, fetch region information from the server
    runner = get_runner(ctx)
    region = runner.region
    
    #The region string will be used in all outward-facing information displays
    region_string = utils.get_key(region)
    
    #Check if the summoner is already in the servers
    is_already_added = False
    for player in runner.player_list:
        if summoner_name == player.name:
            is_already_added = True
            break
    
    if is_already_added:
        #Player is already in the server embed
        embed = discord.Embed(
                    title = "Summoner Already Added",
                    description  = f"The player {summoner_name} is already in the player list.\nGet their information with the get command.",
                    color = discord.Color.red()
                    )
        embed.set_author(name = "Error", icon_url = crossURL)
    else:
        #Perform verification check
        verification_report = utils.verify_summoner_name(summoner_name, region)
        
        summoner = None
        
        if verification_report['valid_summoner']:
            summoner = verification_report['summoner']
            
        if summoner is None:
            #Display invalid summoner error
            #"The entered summoner name is invalid"
            embed = discord.Embed(
                    title = "That Summoner Does Not Exist",
                    description  = f"There is no summoner by the name {summoner_name} in the ({region_string}) region.\nTry again, or try changing the region with the region command.",
                    color = discord.Color.red()
                    )
            embed.set_author(name = "Error", icon_url = crossURL)
        else:
            #Check validity of role preference code
            is_valid_code = utils.verify_role_preference_code(role_preference_code)
            if is_valid_code:
                #Get ranked information for the player. (and icon)
                await ctx.send("Grabbing player's rank information from Riot and op.gg. Please wait a few seconds.")
                
                try:
                
                    rank_strings = utils.get_summoner_rank_string(summoner, region)
                    previous_rank_string = utils.get_previous_rank_string(summoner, region)
                    icon = utils.get_summoner_icon(summoner, region)
                    
                    player = Player(summoner['name'], region_string, summoner['id'], 
                                    rank_strings['solo_rank_string'], rank_strings['flex_rank_string'], previous_rank_string['previous_rank_string'],
                                    None, role_preference_code, icon)
                    
                    rank_score = utils.get_rank_score(player.get_rank_strings())['rank_score']
                    
                    player.rank_score = rank_score
                    
                    #Add the player, and call get_player to display the added player's information
                    runner.player_list.append(player)
                    print(f"Added player {player} to {runner}")
                    #print(f"Runner list after appending player to runner: {runner_list}")
                    #Write the updated runner list to file
                    utils.store_runner_list(runner_list, data_directory)
                    
                    embed = create_player_info_embed(player)
                    
                    embed.set_author(name = "Added Player", icon_url = checkURL)
                    
                except:
                    
                    embed = discord.Embed(
                        title = "Failed to Retrieve Player Information",
                        description  = "op.gg is down. Try again later.",
                        color = discord.Color.red()
                        )
                    
                    embed.set_author(name = "Error", icon_url = crossURL)
                
            else:
                #The summoner was valid, but the code was not. Print the syntax for a role preference code.
                embed = discord.Embed(
                    title = "Invalid Role Preference Code",
                    description  = "You entered a valid summoner, but the role preference code was invalid.\nSee rpchelp for more information.",
                    color = discord.Color.red()
                    )
                embed.set_author(name = "Error", icon_url = crossURL)
        
    await ctx.send(embed = embed)
    
@bot.command(name = "remove")
async def remove_player(ctx, *args):
    """
    Checks if the given summoner is in the given server's player list, and if so, removes the player.
    """
    
    #Need this join so summoner names with spaces are handled
    summoner_name = " ".join(args[:])
    
    retrieved_player = None
    embed = discord.Embed()
    
    runner = get_runner(ctx)
    for player in runner.player_list:
        if summoner_name == player.name:
            retrieved_player = player
            runner.player_list.remove(retrieved_player)
            break
    
    if retrieved_player is None:
        #Display failure embed - "That player is not in the player list."
        embed = discord.Embed(
            title = "Nobody Found",
            description  = "That player is not in the player list.\nMaybe you made a typo?",
            color = discord.Color.red()
            )
        embed.set_author(name = "Error", icon_url = crossURL)
    else:
        #Display player info embed
        #Info to show: name, region, all three rank strings, role preference code, icon
        embed = discord.Embed(
            title = retrieved_player.name,
            color = discord.Color.green()            
            )
        
        embed.add_field(name = "Region", value = player.region, inline = True)
        embed.add_field(name = "OP.GG", value = f"[Link]({utils.generate_opgg_link(player.name, utils.regions[player.region])})", inline = True)
        embed.add_field(name = "Role Preference", value = utils.get_role_emote_string(player.role_preference_code), inline = False)
            
        embed.set_author(name = "Removed Player", icon_url = checkURL)
        embed.set_thumbnail(url = player.icon)
        
        embed.set_footer(text = 'To add this player again, use the add command.')
        
    await ctx.send(embed = embed)
    
@bot.command(name = "update")
async def update_player(ctx, *args, server_id = None):
    """
    Finds the player with the given summoner name and tries to update their rank/icon information.
    If there are differences with the stored data and the newly called data, it overwrites the player with the new information.
    """
    
    #Need this join so summoner names with spaces are handled
    summoner_name = " ".join(args[:])
    
    retrieved_player = None
    embed = discord.Embed()
    
    if server_id is None:
        runner = get_runner(ctx)
    else:
        #Shortcut for picking a runner by server id directly
        #This is here for updating all players in the on_ready function
        runner = get_runner(ctx, server_id = server_id)
    for player in runner.player_list:
        if summoner_name == player.name:
            retrieved_player = player
            break
    
    if retrieved_player is None:
        #Display failure embed - "That player is not in the player list."
        embed = discord.Embed(
            title = "Nobody Found",
            description  = "That player is not in the player list.\nMaybe you made a typo?",
            color = discord.Color.red()
            )
        embed.set_author(name = "Error", icon_url = crossURL)
    else:
        update_report = utils.update_player(retrieved_player)
        print(update_report)
        new_player_info = update_report['new_player_info']
        if update_report['not_found']:
            #Display player is no longer in the region. Tell user they moved region.
            #Also remove the player from the runner's list.
            runner.player_list.remove(retrieved_player)
            
            embed = discord.Embed(
                title = "Updated Player",
                description = "That summoner no longer exists.\nThey have been removed from the player list.\nAdd someone new with the add command.",
                color = discord.Color.green()          
                )
            embed.set_author(name = "That Summoner No Longer Exists", icon_url = checkURL)
            
        elif update_report['has_changed'] is False:
            #Display updated but nothing has been changed embed.
            
            embed = discord.Embed(
                title = "Updated Player",
                description = "No new updates are needed.\nThis player's information is up to date.\nIf you believe this is incorrect, refresh this player's [op.gg](https://op.gg) page.",
                color = discord.Color.green()          
                )
            embed.set_author(name = "No Changes Made", icon_url = checkURL)
            
        else:
            #Overwrite the player!
            runner.player_list.remove(retrieved_player)
            
            #Create player object from player_info dict
            new_player = Player(new_player_info['name'], new_player_info['region'], new_player_info['summoner_id'],
                                new_player_info['solo_rank_string'], new_player_info['flex_rank_string'], new_player_info['previous_rank_string'],
                                None, new_player_info['role_preference_code'], new_player_info['icon'])
            
            rank_score = utils.get_rank_score(new_player.get_rank_strings())['rank_score']
            
            new_player.rank_score = rank_score
            
            runner.player_list.append(new_player)
            embed = create_player_info_embed(new_player)
            embed.description = "The player's information has been updated."
                
            embed.set_author(name = "Updated Player", icon_url = checkURL)
        
    #This if is here because of the shortcut I made for 
    if ctx is not None:
        await ctx.send(embed = embed)
    
    
@bot.command(name = "edit")
async def edit_player(ctx, *args):
    """
    Basically just add_player but instead of verifying summoner it just checks if there is a summoner to edit, then changes their role code.
    Also, performs update_player.
    """
    
    #Turn args into summoner name and role preference code
    args = list(args)
    role_preference_code = args[-1]
    args.pop()
    summoner_name = " ".join(args[:])
    
    retrieved_player = None
    embed = discord.Embed()
    
    runner = get_runner(ctx)  
    for player in runner.player_list:
        if summoner_name == player.name:
            retrieved_player = player
            break
    
    if retrieved_player is None:
        #Display failure embed - "That player is not in the player list."        
        embed = discord.Embed(
                title = "Nobody Found",
                description  = f"That player is not in the player list.\nFix any typos, or add them with the add command.",
                color = discord.Color.red()
                )
        embed.set_author(name = "Error", icon_url = crossURL)
    else:
        #Check validity of role preference code
        is_valid_code = utils.verify_role_preference_code(role_preference_code)
        if is_valid_code:
            #Update the player's role preference code
            await ctx.send(f"Changing {retrieved_player.name}'s Role Preference Code to {role_preference_code}")
            
            retrieved_player.role_preference_code = role_preference_code
            
            #Write the updated runner list to file
            utils.store_runner_list(runner_list, data_directory)
            
            embed = create_player_info_embed(player)
            
            embed.set_author(name = "Edited Player", icon_url = checkURL)            
        else:
            #The summoner was valid, but the code was not. Print the syntax for a role preference code.
            embed = discord.Embed(
                title = "Invalid Role Preference Code",
                description  = "You entered a valid player, but the role preference code was invalid.\nSee rpchelp for more information.",
                color = discord.Color.red()
                )
            embed.set_author(name = "Error", icon_url = crossURL)
        
    await ctx.send(embed = embed)
    
    
@bot.command(name = "list")
async def print_player_list(ctx):
    """
    If the player list has players, displays an embed with every player.
    If the player list is empty, displays an embed telling the user to add players with the add command.
    """    
    runner = get_runner(ctx)
    
    embed = discord.Embed()
    
    
    
    if len(runner.player_list) == 0:
        #Print an embed saying that the list is empty and that user should use add command to add players.
        embed = discord.Embed(
            title = "Empty Player List",
            description = "There are no players in the player list.\nAdd them with the add command.",
            color = discord.Color.red()
            )
        embed.set_author(name = "Error", icon_url = crossURL)
    else:
        #separate the list into a group of queued and a group of out of queue queued players
        
        queued_players = []
        out_of_queue_players = []
        
        for player in runner.player_list:
            if player.is_active is True:
                queued_players.append(player)
            else:
                out_of_queue_players.append(player)
        
        #Print an embed with all of the player names, role preference codes, and "main rank".
        embed = discord.Embed(
            color = discord.Color.green()
            )
        embed.set_author(name = "Player List", icon_url = checkURL)
        
        embed.add_field(name = f"In Queue - {len(queued_players)}", value = "These players will be used to create teams when the start command is used.\nDequeue them with the dequeue command.", inline = False)
                
        for player in queued_players:
            description = utils.get_role_emote_string(player.role_preference_code)
            embed.add_field(name = f"{player.name} - {player.rank_score:.0f} Elo", value = description, inline = True)
              
        embed.add_field(name = f"Not In Queue - {len(out_of_queue_players)}", value = "These players can enter the queue with the queue command. Add more with the add command.", inline = False)  
            
        for player in out_of_queue_players:
            description = utils.get_role_emote_string(player.role_preference_code)
            embed.add_field(name = f"{player.name} - {player.rank_score:.0f} Elo", value = description, inline = True)
                
        embed.set_footer(text = 'To edit any of this information, use the edit command.')
        
    await ctx.send(embed = embed)
    
@bot.command(name = "region")
async def set_region(ctx, *args):
    """
    Reads a region and validates it. If invalid, displays valid region strings. Otherwise, sets the server's runner to that region.
    """
    embed = discord.Embed()
    
    region_string = " ".join(args[:])
    
    if region_string not in utils.regions.keys():
        #Print valid region strings
        
        prefixes = await get_prefixes(bot, ctx.message)
        
        embed = discord.Embed(
            title = "Invalid Region",
            description = "That's not a valid region.\nPick one of these LoL servers:",
            color = discord.Color.red()
            )
        for region in utils.regions.keys():
            embed.add_field(name = region, value = utils.regions_to_country.get(region), inline = True)
        embed.add_field(name = "End", value = "Other regions are not supported, sorry.", inline = True)
        embed.add_field(name = "Syntax", value = f"{prefixes[0]}region REGION_CODE")
            
        embed.set_author(name = "Error", icon_url = crossURL)
    else:
        #First, check if the region is different than the current region.
        runner = get_runner(ctx)
        new_region = utils.regions.get(region_string)
        
        if runner.region == new_region:
            #The input region and current region are the same. Don't change anything.
            embed = discord.Embed(
            title = "Region Not Changed",
            description = f"This server's region is already set to {region_string}.\nNothing has been changed.",
            color = discord.Color.red()
            )
            
            embed.set_author(name = "Error", icon_url = crossURL)
        else:
            #Set runner's region to that region.
            #Set runner region to be in the form of Riot API region codes
            runner.region = new_region
            
            embed = discord.Embed(
                title = "Region Updated",
                description = f"This server's region has been set to {region_string}",
                color = discord.Color.green()
                )
            embed.add_field(name = "Resetting Player List", value = "Resetting the player list as to not have players from more than one region in the player list.")
            embed.set_author(name = "Set Region", icon_url = checkURL)
            
            #Resetting player list
            runner.player_list = list()
        
    await ctx.send(embed = embed)
    
@bot.command(name = "queue")
async def activate_player(ctx, *args):
    """
    Set the player's is_active field to True.
    Displays an error embed if no player with that name exists.
    """
    
    runner = get_runner(ctx)
    summoner_name = " ".join(args[:])
    
    retrieved_player = None
    
    for player in runner.player_list:
        if summoner_name == player.name:
            retrieved_player = player
            break
        
    if retrieved_player is None:
        #Display failure embed - "That player is not in the player list."        
        embed = discord.Embed(
                title = "Nobody Found",
                description  = f"That player is not in the player list.\nFix any typos, or add them with the add command.",
                color = discord.Color.red()
                )
        embed.set_author(name = "Error", icon_url = crossURL)
    else:
        #Check if player is already active or not
        if retrieved_player.is_active:
            #Send already active embed
            
            embed = discord.Embed(
                title = f"Player Not Changed",
                description = f"This player is already in queue.\nNothing has been changed.",
                color = discord.Color.red()
                )
            
            embed.set_author(name = "Error", icon_url = crossURL)
            
        else:
            #Activate player!
            retrieved_player.is_active = True
            
            embed = discord.Embed(
                title = f"{retrieved_player.name} is Queued",
                description = f"This player is now in the active Queue.\nRemove them with the dequeue command.",
                color = discord.Color.green()
                )
            embed.set_author(name = "Player Queued", icon_url = checkURL)
            
            #Write the updated runner list to file
            utils.store_runner_list(runner_list, data_directory)
        
        embed.set_footer(text = 'To view the player list, use the list command.')
        
    await ctx.send(embed = embed)
    
@bot.command(name = "dequeue")
async def deactivate_player(ctx, *args):
    """
    Set the player's is_active field to False.
    Displays an error embed if no player with that name exists.
    """
    
    runner = get_runner(ctx)
    summoner_name = " ".join(args[:])
    
    retrieved_player = None
    
    for player in runner.player_list:
        if summoner_name == player.name:
            retrieved_player = player
            break
        
    if retrieved_player is None:
        #Display failure embed - "That player is not in the player list."        
        embed = discord.Embed(
                title = "Nobody Found",
                description  = f"That player is not in the player list.\nFix any typos, or add them with the add command.",
                color = discord.Color.red()
                )
        embed.set_author(name = "Error", icon_url = crossURL)
    else:
        #Check if player is already not active or not
        if retrieved_player.is_active is False:
            #Send already active embed
            
            embed = discord.Embed(
                title = f"Player Not Changed",
                description = f"This player is already not in queue.\nNothing has been changed.",
                color = discord.Color.red()
                )
            
            embed.set_author(name = "Error", icon_url = crossURL)
            
        else:
            #Deactivate player!
            retrieved_player.is_active = False
            
            embed = discord.Embed(
                title = f"{retrieved_player.name} is Dequeued",
                description = f"This player is now out of the active Queue.\nAdd them with the queue command.",
                color = discord.Color.green()
                )
            embed.set_author(name = "Player Dequeued", icon_url = checkURL)
            
            #Write the updated runner list to file
            utils.store_runner_list(runner_list, data_directory)
        
        embed.set_footer(text = 'To view the player list, use the list command.')
        
    await ctx.send(embed = embed)
    
@bot.command(name = "start")
async def start_game(ctx):
    """
    """
    runner = get_runner(ctx)
    
    embed = discord.Embed()
    
    queued_players = []
    
    for player in runner.player_list:
        if player.is_active:
            queued_players.append(player)
    
    if len(queued_players) < 10:
        #Not enough players to start the game
        embed = discord.Embed(
            title = f"Not Enough Queued Players",
            description = f"There need to be at least 10 queued players before starting a game. Add them with the add/queue commands.",
            color = discord.Color.red()
            )
            
        embed.set_author(name = "Error", icon_url = crossURL)
        
        await ctx.send(embed = embed)
    else:
        try:
            #Start matchmaking process
            
            #First, update players
            #for player in queued_players:
                #utils.update_player(player)
            
            print(f"Starting matchmaking process with these players: {queued_players}")
            role_pools = matchmaking.create_role_pools(queued_players)
            
            """
            for role in role_pools:
                print(role)
                for player in role_pools[role]:
                    print(player)
            """
            
            sorted_matchups = matchmaking.generate_matchups(role_pools)
            """
            for role in sorted_matchups:
                for matchup in sorted_matchups[role]:
                    print(matchup)
            """
            
            selected_matchups = matchmaking.select_matchups(sorted_matchups)
            """
            for role in selected_matchups:
                print(role)
                for player in selected_matchups[role]:
                    print(player)
            """
            team_combinations = matchmaking.generate_teams(selected_matchups)
            
            await display_team_combination_embed(ctx, team_combinations)
        except:
            await ctx.send("Uh oh, the bot broke. Go tell Vanea#3158 about it.")
        
async def display_team_combination_embed(ctx, team_combinations, index = 0):
    """
    Displays an embed that displays all 32 possible team combinations (they are navigated through with arrow reactions)
    """
    runner = get_runner(ctx)
    
    embed = discord.Embed(
        title = f"The Matchup! - Option #{index + 1}/32",
        color = discord.Color.green()
        )
    #embed.add_field(name = f"Possibility #{index + 1}", value = "There are 32 possibilities, sorted from most to least balanced.", inline = False)
    
    #embed.set_thumbnail(url = league_logo)
    embed.set_footer(text = "To navigate between the options, react to the arrow icons.")
    
    #storing team combinations in each individual runner so no cross-contamination happens
    runner.latest_team_combinations = team_combinations
    team_combo = runner.latest_team_combinations[index]
    
    #display version 1
    """
    embed.add_field(name = "Top Lane", value = f"{team_combo.team_one.top} <:Top:826682003503316992> {team_combo.team_two.top}", inline = False)
    embed.add_field(name = "Jungle", value = f"{team_combo.team_one.jug} <:Jungle:826682003587727370> {team_combo.team_two.jug}", inline = False)
    embed.add_field(name = "Mid Lane", value = f"{team_combo.team_one.mid} <:Mid:826682003624820736> {team_combo.team_two.mid}", inline = False)
    embed.add_field(name = "Bot Lane", value = f"{team_combo.team_one.bot} <:Bot:826682003339477013> {team_combo.team_two.bot}", inline = False)
    embed.add_field(name = "Support", value = f"{team_combo.team_one.sup} <:Support:826682003435814952> {team_combo.team_two.sup}", inline = False)
    embed.add_field(name = f"Elo Difference - {abs(team_combo.rank_delta):.2f}", value = f"Team One: {team_combo.team_one.total_rank_score:.0f} - Team Two: {team_combo.team_two.total_rank_score:.0f}", inline = False)
    """
    
    #display version 2
    """
    embed.add_field(name = "Blue Side", value = wrap(f"{team_combo.team_one.total_rank_score:.0f} Elo"), inline = True)
    embed.add_field(name = "Elo Difference", value = wrap(f"**{abs(team_combo.rank_delta):.2f}**"), inline = True)
    embed.add_field(name = "Red Side", value = f"{team_combo.team_two.total_rank_score:.0f} Elo", inline = True)
    
    embed.add_field(name = f"{team_combo.team_one.top}", value = wrap(f"{team_combo.team_one.top.rank_score:.0f} Elo"), inline = True)
    embed.add_field(name = "Top Lane", value = wrap(top_icon), inline = True)
    embed.add_field(name = f"{team_combo.team_two.top}", value = f"{team_combo.team_two.top.rank_score:.0f} Elo", inline = True)
    
    embed.add_field(name = f"{team_combo.team_one.jug}", value = wrap(f"{team_combo.team_one.jug.rank_score:.0f} Elo"), inline = True)
    embed.add_field(name = f"Jungle", value = wrap(jug_icon), inline = True)
    embed.add_field(name = f"{team_combo.team_two.jug}", value = f"{team_combo.team_two.jug.rank_score:.0f} Elo", inline = True)
    
    embed.add_field(name = f"{team_combo.team_one.mid}", value = wrap(f"{team_combo.team_one.mid.rank_score:.0f} Elo"), inline = True)
    embed.add_field(name = "Mid Lane", value = wrap(mid_icon), inline = True)
    embed.add_field(name = f"{team_combo.team_two.mid}", value = f"{team_combo.team_two.mid.rank_score:.0f} Elo", inline = True)
    
    embed.add_field(name = f"{team_combo.team_one.bot}", value = wrap(f"{team_combo.team_one.bot.rank_score:.0f} Elo"), inline = True)
    embed.add_field(name = "Bot Lane", value = wrap(bot_icon), inline = True)
    embed.add_field(name = f"{team_combo.team_two.bot}", value = f"{team_combo.team_two.bot.rank_score:.0f} Elo", inline = True)
    
    embed.add_field(name = f"{team_combo.team_one.sup}", value = wrap(f"{team_combo.team_one.sup.rank_score:.0f} Elo"), inline = True)
    embed.add_field(name = "Support", value = wrap(sup_icon), inline = True)
    embed.add_field(name = f"{team_combo.team_two.sup}", value = f"{team_combo.team_two.sup.rank_score:.0f} Elo", inline = True)
    """
    
    displays = create_team_displays(team_combo)
        
    blue_side_padding = displays[0]['longest_length']
    red_side_padding = displays[1]['longest_length']
    
    blue_side_title = "`"+"{title: >{padding}}".format(title = "Blue Side", padding = blue_side_padding)+"`"
    blue_side_elo = f"{team_combo.team_one.total_rank_score:.0f} Elo"
    blue_side_padded_elo = "`"+"{elo: >{padding}}".format(elo = blue_side_elo, padding = blue_side_padding)+"`"
    embed.add_field(name = blue_side_title, value = f"**{blue_side_padded_elo}\n{displays[0]['team_display']}**", inline = True)
    
    embed.add_field(name = "VS", value = f"{spacer_icon}\n{top_icon}\n{jug_icon}\n{mid_icon}\n{bot_icon}\n{sup_icon}", inline = True)
    
    red_side_title = "`"+"{title: <{padding}}".format(title = "Red Side", padding = red_side_padding)+"`"
    red_side_elo = f"{team_combo.team_two.total_rank_score:.0f} Elo"
    red_side_padded_elo = "`"+"{elo: <{padding}}".format(elo = red_side_elo, padding = red_side_padding)+"`"
    embed.add_field(name = red_side_title, value = f"**{red_side_padded_elo}\n{displays[1]['team_display']}**", inline = True)
    
    embed.set_author(name = "Created Game", icon_url = checkURL)
    
    await ctx.send("You have 32 options to choose from, ordered from most (option #1) to least (option #32) balanced teams. GLHF!")
    message = await ctx.send(embed = embed)
    
    #storing the message for future reference
    runner.latest_team_embed = message
    
    emojis = ["⬅️", "➡️"]
    for emoji in emojis:
        await message.add_reaction(emoji)
        
spacer_icon = "<:blank:827117869947027497>"
double_spacer = "<:blank:827117869947027497><:blank:827117869947027497>"
top_icon ="<:Top:826682003503316992>"
jug_icon = "<:Jungle:826682003587727370>"
mid_icon = "<:Mid:826682003624820736>"
bot_icon = "<:Bot:826682003339477013>"
sup_icon = "<:Support:826682003435814952>"

def wrap(text):
    """
    Returns the text wrapped in two spacer icons (one on each end)
    """
    return f"{spacer_icon}{text}{spacer_icon}"

def create_team_displays(team_combo):
    displays = []

    blue_team_players = list(team_combo.team_one.players)
    red_team_players = list(team_combo.team_two.players)
    
    print("Entering display generation loop")
    
    for index, team_players in enumerate((blue_team_players, red_team_players)):
        print(index, team_players)
        longest_name = ""
        for player in team_players:
            #print(f"Checking if {player} has the longest name")
            #print(f"Length of {player.name} is {len(player.name)}")
            if len(player.name) > len(longest_name):
                longest_name = player.name
        longest_length = len(longest_name)
        longest_length = longest_length + longest_length % 6
        
        if index == 0:
            space_padded_names = [f"`{player.name: >{longest_length}}`" for player in team_players]
        else:
            space_padded_names = [f"`{player.name: <{longest_length}}`" for player in team_players]
        
        #print(space_padded_names)
        
        print("Finished padding with spaces")  
                
        team_display = ""
        for name in space_padded_names:
            team_display += f"{name}\n"
        team_display = team_display[:-1]
        display = {"longest_length": longest_length, "team_display": team_display}
        displays.append(display)
    
    return displays

@bot.event
async def on_raw_reaction_add(payload):
    """
    Triggers whenever someone adds a reaction to a message in a server the bot is in.
    """
    await on_raw_reaction(payload)

@bot.event
async def on_raw_reaction_remove(payload):
    """
    Triggers whenever someone removes a reaction to a message in a server the bot is in.
    """
    await on_raw_reaction(payload)
    
async def on_raw_reaction(payload):
    #Check if this is a bot adding a reaction
    if payload.event_type == "REACTION_ADD":
        if payload.member.bot:
            return
    
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    
    #get runner by the server id directly
    runner = get_runner({}, server_id = message.guild.id)
    
    #making sure the bot only does anything on reacts to the team embed
    if str(message) != str(runner.latest_team_embed):
        return
    
    print("Editing embed!")
    
    embed, emojis  = message.embeds[0], ["⬅️", "➡️"]
    directional_input = emojis.index(payload.emoji.name)
    #input = 0 means move left
    #input = 1 means move right
    
    current_option = embed.title[23:]
    current_index = int(current_option.split("/")[0]) - 1
    #current_index = int(embed.to_dict()['fields'][0]['name'][13:]) - 1
    
    print(f"Old team embed index: {current_index}")
    
    #adjust index based on input
    if directional_input == 0:
        current_index -= 1
        if current_index < 0:
            current_index = 31
    elif directional_input == 1:
        current_index += 1
        if current_index > 31:
            current_index = 0
            
    print(f"New team embed index: {current_index}")
    
    team_combinations = runner.latest_team_combinations
    team_combo = team_combinations[current_index]
    
    #embed.set_field_at(0, name = f"Possibility #{current_index + 1}", value = "There are 32 possibilities, sorted from most to least balanced.", inline = False)
    embed.title = f"The Matchup! - Option #{current_index + 1}/32"
    
    displays = create_team_displays(team_combo)
        
    blue_side_padding = displays[0]['longest_length']
    red_side_padding = displays[1]['longest_length']
    
    blue_side_title = "`"+"{title: >{padding}}".format(title = "Blue Side", padding = blue_side_padding)+"`"
    blue_side_elo = f"{team_combo.team_one.total_rank_score:.0f} Elo"
    blue_side_padded_elo = "`"+"{elo: >{padding}}".format(elo = blue_side_elo, padding = blue_side_padding)+"`"
    embed.set_field_at(0, name = blue_side_title, value = f"**{blue_side_padded_elo}\n{displays[0]['team_display']}**", inline = True)
    
    #embed.add_field(name = "VS", value = f"{spacer_icon}\n{top_icon}\n{jug_icon}\n{mid_icon}\n{bot_icon}\n{sup_icon}", inline = True)
    
    red_side_title = "`"+"{title: <{padding}}".format(title = "Red Side", padding = red_side_padding)+"`"
    red_side_elo = f"{team_combo.team_two.total_rank_score:.0f} Elo"
    red_side_padded_elo = "`"+"{elo: <{padding}}".format(elo = red_side_elo, padding = red_side_padding)+"`"
    embed.set_field_at(2, name = red_side_title, value = f"**{red_side_padded_elo}\n{displays[1]['team_display']}**", inline = True)

    await message.edit(embed = embed)
            
@bot.command(name = "help")
async def print_help_message(ctx):
    """
    DM the user a help message.
    """
    help_embed = discord.Embed(
        title = "Help Guide",
        color = discord.Color.blurple()
        )
    help_embed.set_author(name="Help Message", icon_url = checkURL)
    
    prefixes = await get_prefixes(bot, ctx.message)
    prefix = prefixes[0]
    
    #help_embed.add_field(name="*Commands are NOT Case Sensitive*", value = f"{prefix}help and {prefix}HELP do the same thing", inline=False)
    help_embed.add_field(name="__**Basic Commands**__", value = "You don't need anything more than these commands:", inline=False)
    #help_embed.add_field(name=f"{prefix}help", value = "Get this message DM'd to you.", inline=False)
    help_embed.add_field(name=f"{prefix}rpcode", value = "See a description of what the Role Preference Code is.", inline=False)
    help_embed.add_field(name=f"{prefix}add", value = "Add a player to the player list.", inline=False)
    help_embed.add_field(name=f"{prefix}edit", value = "Edit a player's role preference code.", inline=False)
    help_embed.add_field(name=f"{prefix}remove", value = "Remove a player from the player list.", inline=False)
    help_embed.add_field(name=f"{prefix}queue", value = "Enter a player into the active queue for game creation.", inline=False)
    help_embed.add_field(name=f"{prefix}dequeue", value = "Remove a player from the active queue.", inline=False)
    help_embed.add_field(name=f"{prefix}list", value = "List all players, grouped by those in queue and those not in queue.", inline=False)
    help_embed.add_field(name=f"{prefix}start", value = "Create balanced teams and display them (requires 10 people in queue).", inline=False)
    #help_embed.add_field(name="", value = "", inline=False)
    help_embed.add_field(name="__**Advanced Commands**__", value = "You don't need to know these for regular bot usage:", inline=False)
    help_embed.add_field(name=f"{prefix}prefix", value = "Set a custom command prefix for your server.", inline=False)
    #help_embed.add_field(name="", value = "", inline=False)
    
    await ctx.send("Check your DMs for the Help Menu")
    await ctx.author.send(embed=help_embed)

@bot.command(name = "rpcode")
async def print_rpcode_help_message(ctx):
    """
    Display an embed with information about the Role Preference Code.
    """
    
    embed = discord.Embed(
        title = "Role Preference Code Guide",
        color = discord.Color.blurple()
        )
    
    embed.add_field(name="What is the Role Preference Code?", value = f"A 5 digit number that indicates how strongly you prefer to play each role.", inline=False)
    embed.add_field(name="What does it look like?", value = f"Here's an example: 31245", inline=False)
    embed.add_field(name="What does it mean?", value = f"The digits represent each role.\n1 is Top, 2 is Jungle, 3 is Mid, 4 is Bot, 5 is Support..\nThe above example means the player would like to play, in order from most to least:\nMid, Top, Jg, Bot, Sup.", inline=False)
    embed.add_field(name="NEEDS ALL 5 ROLES", value = f"You can't put 1 if you only want to play Top lane. You HAVE to rank order every role.", inline=False)
    embed.add_field(name="What is it for?", value = f"With this code, the team balancing algorithm can place you in the role you'd most like to play.", inline = False)
    embed.add_field(name="Autofill", value = f"However, one or two players will likely be autofilled because not everybody can get the role they want.", inline = False)
    
    await ctx.send(embed = embed)
    
    
def create_player_info_embed(player):
    """
    Use a template to create a player info embed.
    Author is not set.
    """
    embed = discord.Embed(
            title = f"__{player.name}__\n{player.rank_score:.2f} Elo\n{utils.get_role_emote_string(player.role_preference_code)} - `{player.role_preference_code}`",
            color = discord.Color.green()            
            )
        
    embed.add_field(name = "Region", value = player.region, inline = True)
    embed.add_field(name = "OP.GG", value = f"[Link]({utils.generate_opgg_link(player.name, utils.regions[player.region])})", inline = True)
    #embed.add_field(name = "Role Preference", value = f"{utils.get_role_emote_string(player.role_preference_code)} = {player.role_preference_code}", inline = False)
    #embed.add_field(name = "Role Preference Code", value = player.role_preference_code, inline = False)
        #embed.add_field(name = "Solo Queue", value = player.solo_rank_string, inline = True)
        #embed.add_field(name = "Flex Queue", value = player.flex_rank_string, inline = True)
        #embed.add_field(name = "Last Season's Rank", value = player.previous_rank_string, inline = False)
    embed.add_field(name = "Rank", value = f"**Solo/Duo**: {player.solo_rank_string}\n**Flex**: {player.flex_rank_string}\n**Previous Season**: {player.previous_rank_string}", inline = False)
    
    #embed.add_field(name = "Elo Score", value = f"{player.rank_score:.2f}", inline = False)
    
    if player.is_active:
        embed.add_field(name = "In Queue", value = "Leave queue with the dequeue command.", inline = False)
    else:
        embed.add_field(name = "Not In Queue", value = "Enter queue with the queue command.", inline = False)
    
        
    embed.set_thumbnail(url = player.icon)
    
    embed.set_footer(text = 'To edit any of this information, use the edit command.')
    
    return embed
    
"""

A possible way to handle custom prefixes:
    A list of prefixes that the bot is always aware of.
    Also, there is a mapping between prefix and servers that the prefix works for.
    When receiving a command, the bot checks if the server (from context (ctx)) maps to the prefix.
    If not, it drops the command (like dropping a packet).

"""

bot.run(TOKEN)