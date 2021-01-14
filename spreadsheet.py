import gspread
from datetime import date, datetime
import os

from classRolesManagement import AshesUserSummary


class Spreadsheet:

    def __init__(self, sheetId):
        self.spreadsheetId = sheetId
        self.gc = gspread.service_account()
        self.sheet = self.gc.open_by_key(self.spreadsheetId)
        self.rosterSheet = self.sheet.worksheet("Roster")

    def SendDictToRosterSheet(self, info: AshesUserSummary, user):
        """ Sends the passed dictionary to the roster worksheet """
        nameWithTag = str(user)
        cells = self.rosterSheet.findall(nameWithTag)

        if len(cells) == 0:  # new entry
            row = self.GetNextAvailableRow()
            self.rosterSheet.update(f'A{row}', user.name)
            self.rosterSheet.update(f'G{row}', nameWithTag)
            self.rosterSheet.update(f'H{row}', str(date.today()))  # Join Date
        else:
            row = cells[0].row

        if info.secondary != '':
            self.rosterSheet.update(f'B{row}', info.secondary)

        if info.primary != '':
            self.rosterSheet.update(f'C{row}', info.primary)

        if info.playstyle != '':
            self.rosterSheet.update(f'E{row}', info.playstyle)

        if info.alpha != '':
            self.rosterSheet.update(f'F{row}', info.alpha)

        self.rosterSheet.update(f'I{row}', str(datetime.now()))  # Last modification date

    def GetNextAvailableRow(self):
        """ Gets the next row number that is free """
        str_list = list(filter(None, self.rosterSheet.col_values(1)))
        return str(len(str_list) + 1)
