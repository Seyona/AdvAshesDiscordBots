from asyncio import gather

import discord
from discord import TextChannel, Guild, Member, User
from Statics.statics import Static
from Statics.staticsDb import staticsDb
from Statics.staticsData import StaticData
from typing import Dict, Union

class StaticsManagement:
    """ Class to modify data releated to Statics """
    def __init__(self, static_name):
        self.staticRole = None
        self.primaryDiscordRole = None 
        self.leaderRole = None
        self.coleaderRole = None
        self.memberRole = None
        self.discordMemberRole = None

        self.static_name = None
        self.static_lead = None
        self.staticId  = None


    def initRoles(self, discordIds, discGuild: Guild, static_name):
        for role in discGuild.roles:
            if role.id == int(discordIds["cultistId"]):
                self.discordMemberRole = role
            if role.id == int(discordIds["knightId"]):
                self.coleaderRole = role
            if role.id == int(discordIds["captainId"]):
                self.leaderRole = role
            if role.name == static_name: #Role for Static
                self.memberRole = role

    def createStatic(self, static: Static):
        db = staticsDb()
        db.createNewStatic(static)

        self.static_name = static.static_name
        self.static_lead = static.static_lead
        self.staticId  = static.static_id

    async def AddLeaderRole(self, user: User):
        """ Adds Leader role and Static to given user """
        await user.add_roles(self.leaderRole)

    async def MakeNewLeader(self, oldLead: User, newLead: User):
        """ Gives the new lead the leader role and remove the previous role """
        await gather(oldLead.remove_roles(self.leaderRole), self.AddLeaderRole(newLead))

    async def AddColeadRole(self, user: User):
        """ Adds a colead role, coleads are already in the static """
        await user.add_roles(self.coleaderRole)

    async def ReplaceColead(self, oldCoLead: User, newCoLead: User):
        """ Replaces the old colead with the new colead """
        await gather(oldCoLead.remove_roles(self.coleaderRole), self.AddColeadRole(newCoLead))
    
    async def AddStaticRole(self, user: User):
        """ Adds static role to user """
        await user.add_roles(self.memberRole)

    async def RemoveStaticRole(self, user: User):
        """ Removes static role from user """ 
        await user.remove_roles(self.memberRole)

    async def AddDiscordRole(self, user:User):
        """ Adds generic member role to user """
        await user.add_roles(self.discordMemberRole)

