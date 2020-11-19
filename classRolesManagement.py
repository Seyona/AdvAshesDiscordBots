from asyncio import gather

import discord
from discord import TextChannel, Guild, Member, User
import json
from typing import Dict, Union


class AshesRolesManager:
    """
    Class for code specific to the Ashes Roles management system
    """

    def __init__(self, channel: TextChannel, discordIds, spreadsheet):
        """
            Object should be initialized during the onReady function
        """
        self.channel = channel
        self.classNames = []
        self.augmentNames = []
        self.emojiWhiteList = []
        self.primaryClassRoles = []

        self.guildMemberRole = None
        self.newbieRole = None

        self.rosterPrimaryMsg = ""
        self.rosterSecondaryMsg = ""
        self.rosterPlyMsg = ""
        self.rosterAccMsg = ""

        self.summaryDict: Dict[str, AshesUserSummary] = {}
        self.msgIds = {}
        self.classData = {}
        self.spreadsheet = spreadsheet

        summStr = f'❖ Summoner {discordIds["summoner"]}'
        bardStr = f'❖ Bard             {discordIds["bard"]}'
        clericStr = f'❖ Cleric           {discordIds["cleric"]}'
        fighterStr = f'❖ Fighter         {discordIds["fighter"]}'
        mageStr = f'❖ Mage           {discordIds["mage"]}'
        rangerStr = f'❖ Ranger         {discordIds["ranger"]}'
        rogueStr = f'❖ Rogue          {discordIds["rogue"]}'
        tankStr = f'❖ Tank            {discordIds["tank"]}'

        self.cleanLine = "━━━━━━━━━━━━━━━◦❖◦━━━━━━━━━━━━━━━"
        self.classSelectionMsg = f"""
{bardStr}
{clericStr}
{fighterStr}
{mageStr}
{rangerStr}
{rogueStr}
{summStr}
{tankStr}
"""

    async def init(self, discordIds, discGuild: Guild):
        """ Cleans up the roster channel and sets up variables & data that will be needed later """
        await self.channel.purge()

        await self.channel.send(self.cleanLine)
        primClassStr = f'What is your Primary class: {self.classSelectionMsg}'
        updateSecStr = f'What is your Secondary class: {self.classSelectionMsg}'

        self.rosterPrimaryMsg = await self.channel.send(primClassStr)
        await self.channel.send(self.cleanLine)
        self.rosterSecondaryMsg = await self.channel.send(updateSecStr)
        await self.channel.send(self.cleanLine)

        playStyleStr = (f'Select your Main playstyle (Select only 1): \n' +
                        f'❖ PVE:           {discordIds["pve"]} \n' +
                        f'❖ PVP:           {discordIds["pvp"]} \n ' +
                        f'❖ Lifeskiller: {discordIds["lifeskiller"]} \n')

        self.rosterPlyMsg = await self.channel.send(playStyleStr)
        await self.channel.send(self.cleanLine)

        accessStr = (f'Do you have any early access to the game?: \n' +
                     f'❖ Alpha 1:      {discordIds["alpha1"]} \n' +
                     f'❖ Alpha 2:     {discordIds["alpha2"]} \n' +
                     f'❖ Beta 1:         {discordIds["beta1"]} \n' +
                     f'❖ Beta 2:        {discordIds["beta2"]} \n' +
                     f'❖ No Access {discordIds["noaccess"]}')

        self.rosterAccMsg = await self.channel.send(accessStr)
        await self.channel.send(self.cleanLine)

        self.msgIds = {
            "updatePrimaryMsgId": self.rosterPrimaryMsg.id,
            "updateSecondaryMsgId": self.rosterSecondaryMsg.id,
            "updatePlayStyleMsgId": self.rosterPlyMsg.id,
            "updateAccessMsgId": self.rosterAccMsg.id
        }

        # pull classes file into memory
        with open('/discordBot/AdvAshesDiscordBots/classes.json') as json_file:
            self.classData = json.load(json_file)
            self.classNames = self.classData.keys()
            self.augmentNames = [item for innerList in self.classData.values() for item in innerList.values()]

        # Construct the white list of emoji's that users can react with
        for emoji in discGuild.emojis:
            if emoji.name in self.classNames:
                self.emojiWhiteList.append(emoji)
            elif emoji.name in discordIds.keys():
                self.emojiWhiteList.append(emoji)

        self.emojiWhiteList.sort(key=lambda x: x.name, reverse=False)

        # Add the Class emoji's to the messages
        for emoji in self.emojiWhiteList:
            if emoji.name in self.classNames:
                await gather(self.rosterPrimaryMsg.add_reaction(emoji), self.rosterSecondaryMsg.add_reaction(emoji))

        # Get the guild member and Newbie roles
        for role in discGuild.roles:
            if role.id == int(discordIds["guildMemberId"]):
                self.guildMemberRole = role
            if role.id == int(discordIds["newbieId"]):
                self.newbieRole = role

        await gather(self.rosterPlyMsg.add_reaction(discordIds["pve"]),
                     self.rosterPlyMsg.add_reaction(discordIds["pvp"]),
                     self.rosterPlyMsg.add_reaction(discordIds["lifeskiller"]))

        await gather(self.rosterAccMsg.add_reaction(discordIds["alpha1"]), \
                     self.rosterAccMsg.add_reaction(discordIds["alpha2"]), \
                     self.rosterAccMsg.add_reaction(discordIds["beta1"]), \
                     self.rosterAccMsg.add_reaction(discordIds["beta2"]), \
                     self.rosterAccMsg.add_reaction(discordIds["noaccess"]))

    async def ReactionAdded(self, reaction: discord.Reaction, user: Union[Member, User]) -> None:
        """
            Take the reaction ,check the emoji, and update the user's entry
            If the entry is ready for submission it will submit it
        """
        messageId = reaction.message.id
        currentUser = str(user)

        # Check if the user reacted to one of the allowed emojis
        if reaction.emoji not in self.emojiWhiteList:
            await reaction.message.remove_reaction(reaction.emoji, user)
            return  # No need for further evaluation

        if currentUser not in self.summaryDict:
            self.summaryDict[currentUser] = AshesUserSummary()

        # Check if the user has already reacted to this message
        # if they have, remove their prior reaction
        for react in reaction.message.reactions:
            async for reacter in react.users():
                if str(reacter) == str(user) and react.emoji.name != reaction.emoji.name:
                    await reaction.message.remove_reaction(react.emoji, reacter)

        # First Message was clicked
        if messageId == self.msgIds["updatePrimaryMsgId"]:
            self.summaryDict[currentUser].primary = reaction.emoji.name
            self.summaryDict[currentUser].baseClassMsg = reaction

        elif messageId == self.msgIds["updateSecondaryMsgId"]:
            try:
                baseClass: str = self.summaryDict[currentUser].primary

                if baseClass != "":
                    selectedCombo = self.classData[baseClass][reaction.emoji.name]
                    self.summaryDict[currentUser].secondary = selectedCombo
                    self.summaryDict[currentUser].secondaryClassMsg = reaction
                else:
                    await reaction.message.remove_reaction(reaction.emoji, user)

            # For now just print a message to stdout...should covert to actual logging eventually
            except KeyError:
                print(f'{currentUser} is attempting to select a secondary class, but there is no entry in the dictionary.')

        elif messageId == self.msgIds["updatePlayStyleMsgId"]:
            self.summaryDict[currentUser].playstyle = reaction.emoji.name
            self.summaryDict[currentUser].playstyleMsg = reaction

        elif messageId == self.msgIds["updateAccessMsgId"]:
            self.summaryDict[currentUser].alpha = reaction.emoji.name
            self.summaryDict[currentUser].alphaMsg = reaction
            success = await self.summaryDict[currentUser].SubmitSummary(user, self.spreadsheet)
            if success:
                userData = self.summaryDict[currentUser]
                await userData.baseClassMsg.message.remove_reaction(userData.baseClassMsg.emoji, user)
                await userData.secondaryClassMsg.message.remove_reaction(userData.secondaryClassMsg.emoji, user)
                await userData.playstyleMsg.message.remove_reaction(userData.playstyleMsg.emoji, user)
                await userData.alphaMsg.message.remove_reaction(userData.alphaMsg.emoji, user)
                await gather(user.add_roles(self.guildMemberRole), user.remove_roles(self.newbieRole))
                self.summaryDict.pop(currentUser)  # remove their entry from tracking


class AshesUserSummary:
    """ Class for the Ashes User Summary Information """

    def __init__(self):
        self.primary = ""
        self.baseClassMsg = None

        self.secondary = ""
        self.secondaryClassMsg = None

        self.playstyle = ""
        self.playstyleMsg = None

        self.alpha = ""
        self.alphaMsg = None

    async def SubmitSummary(self, user: Union[Member, User], spreadsheet) -> bool:
        """ Submits the summary information to a spreadsheet (eventually a database?) """

        success = False
        missingItems = []
        errors = ""

        classStr = self.secondary.capitalize()
        baseClass = self.primary.capitalize()
        playStyle = self.playstyle.capitalize()
        alpha = self.playstyle.capitalize()

        response = f'Summary for <@{user.id}: \n'

        if classStr == "":
            missingItems.append("Secondary Class")
        if baseClass == '':
            missingItems.append("Primary class")
        if playStyle == '':
            missingItems.append("Play style")
        if alpha == '':
            missingItems.append("Access level")

        response += (f'Class: {classStr} \n' +
                     f'Base Class: {baseClass} \n' +
                     f'Playstyle: {playStyle} \n' +
                     f'Access: {alpha} \n\n')

        if len(missingItems) != 0:
            errors = "Missing: " + ', '.join(missingItems)
            # Should programmatically pull out information for URL, but this is a one guild operation.
            response = (response + errors +
                        '\n This request is Incomplete. Please go back to the channel to and react to the sections that were missed.' +
                        '\n Direct link to channel : https://discord.com/channels/379498643721420800/735729573865586708/')

        if errors == "":  # No problem run spreadsheet update
            spreadsheet.SendDictToRosterSheet(self, user)
            success = True  # maybe new respond message depending what channel they are in

        await user.send(response)
        return success
