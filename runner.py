'''
Created on Mar 28, 2021

@author: ssmup
'''
#For creating the directory to write
import os

#For writing/reading the player_list
#import pickle

class Runner(object):
    """
    Contains the server_id of the server this Runner is for, also holds the player_list of LoL players used in that server.
    """

    def __init__(self, server_id, region):
        
        self.server_id = int(server_id)
        #region must be in the form of Riot API Region Codes
        self.region = region
        self.player_list = list()
    
    def __str__(self):
        return "Runner for Server %d; Region %s; Player List: %s" % (self.server_id, self.region, str(self.player_list))