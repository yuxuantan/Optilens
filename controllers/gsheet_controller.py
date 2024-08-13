import gspread
import pandas as pd
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

# use creds to create a client to interact with the Google Drive API  
class GsheetController():
    def __init__(self, gsheet_name = "Ideal portfolio template"):
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        try:
            gsheet_creds_dict = json.loads(os.environ["GSHEET_CREDENTIALS"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(gsheet_creds_dict, scope)
        except KeyError:
            creds = ServiceAccountCredentials.from_json_keyfile_name('google_creds.json', scope)
        client = gspread.authorize(creds)
        self._sh = client.open(gsheet_name)

    def clearAllDataAndRepopulateHeader(self, sheet_name, headerArr):
        ws = self._sh.worksheet(sheet_name)
        ws.clear()
        ws.append_row(headerArr)

    def writeRow(self, list_of_values, sheet_name):
        """takes in order object and write out the following
        order.contract, order.action, order.filled, order.avg_fill_price
        trade_time = datetime.datetime.fromtimestamp(order.trade_time / 1000)
        """
        ws = self._sh.worksheet(sheet_name)
        
        # Append the row with the JSON serializable contract
        ws.append_row(list_of_values)
        

    
