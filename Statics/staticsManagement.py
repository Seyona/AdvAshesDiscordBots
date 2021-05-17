from asyncio import gather

import discord
from discord import TextChannel, Guild, Member, User
from Statics.statics import Static
from Statics.staticsDb import staticsDb
from Statics.staticsData import StaticData
from typing import Dict, Union

class StaticsManagement:
    """ Class to modify data releated to Statics """
    def __init__(self):
        self.staticRole = None
        self.primaryDiscordRole = None 
        self.leaderRole = None
        self.coleaderRole = None
        self.memberRole = None
        self.discordMemberRole = None
        self.basicRole = None

        self.static_name = None
        self.static_lead = None
        self.staticId  = None


    def initRoles(self, discordIds, discGuild: Guild, role_tag, static_name):
        for role in discGuild.roles:
            if role.id == int(discordIds["cultistId"]):
                self.discordMemberRole = role
            if role.id == int(discordIds["knightId"]):
                self.coleaderRole = role
            if role.id == int(discordIds["captainId"]):
                self.leaderRole = role
            if role.id == int(discordIds["ritualistId"]):
                self.basicRole = role

        self.static_name = static_name
        self.memberRole = role_tag  

    def setStaticInfo(self, static: Static):
        self.static_name = static.static_name
        self.static_lead = static.static_lead
        self.staticId  = static.id

    async def AddLeaderRole(self, user: User):
        """ Adds Leader role to given user """
        await user.add_roles(self.leaderRole)

    async def RemoveLeaderRole(self, user: User):
        """ Removes Leader role to given user """
        await user.remove_roles(self.leaderRole)

    async def MakeNewLeader(self, oldLead: User, newLead: User):
        """ Gives the new lead the leader role and remove the previous role """
        await gather(oldLead.remove_roles(self.leaderRole), self.AddLeaderRole(newLead))

    async def AddColeadRole(self, user: User):
        """ Adds the colead role, coleads are already in the static """
        await user.add_roles(self.coleaderRole)
    
    async def RemoveColeadRole(self, user: User):
        """ Removes the colead role, coleads are already in the static """
        await user.remove_roles(self.coleaderRole)

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

    async def RemoveDiscordRole(self, user:User):
        """ Remove generic member role to user """
        await user.remove_roles(self.discordMemberRole)

    async def RemoveBasicTag(self, user:User):
        """ Removes basic tag from user 
            4/1 : This is currently the ritualist tag
        """
        await user.remove_roles(self.basicRole)

    async def AddBasicTag(self, user:User):
        """ Adds basic tag to user 
            4/1: This is currently the ritualist tag
        """
        await user.add_roles(self.basicRole)

