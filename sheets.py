import os
import json
import numpy as np
import pandas as pd
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Connect

# Load the JSON data from the SHEETS_LOGGER_CREDENTIALS environment variable
creds_json = os.getenv('SHEETS_LOGGER_CREDENTIALS')
creds_dict = json.loads(creds_json)
creds_json_str = json.dumps(creds_dict)
creds = Credentials.from_service_account_info(json.loads(creds_json_str))
sheets_spreadsheet_id = os.getenv('BREEDQUEST_SHEETS_ID')
sheets_service = build("sheets", "v4", credentials=creds)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Read Object List from sheets. 
def fetch_table_from_sheets(tab_name, column_name=None):
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=sheets_spreadsheet_id, range=tab_name).execute()
    except:
        print("Could not fetch table from sheets; tab_name: "+tab_name+" column_name: "+column_name+".")
        return None
    
    data = result.get('values', [])
    if column_name is None:
        return data
    else:
        header_row = data[0]
        column_index = header_row.index(column_name)
        column_data = [row[column_index] for row in data[1:] if row[column_index]]
        return column_data

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# Write to Sheets

def write_to_sam_sheets(
        tab_name,
        row_data,
        column_letter="A"
        ):
    # now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Get the last row of data in the sheet
    range_name = f"'{tab_name}'!{column_letter}:{column_letter}"
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheets_spreadsheet_id, range=range_name
    ).execute()
    values = result.get("values", [])
    last_row = len(values) + 1
    
    # Write the data to the next free row
    range_name = f"'{tab_name}'!{column_letter}{last_row}"
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheets_spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": [row_data]}
    ).execute()
    print(f"Sheets: Written to {tab_name}!{column_letter}{last_row}")

def update_sam_sheets(
        tab_name,
        row_id,
        row_data,
        ):
    
    # Identify the row number of the row to update
    range_name = f"'{tab_name}'!A:A"
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheets_spreadsheet_id, range=range_name
    ).execute()
    row_to_change = result.get("values", []).index([row_id]) + 1

    # Write the data to the next free row
    range_name = f"'{tab_name}'!A{row_to_change}"
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheets_spreadsheet_id,
        range=range_name,
        valueInputOption="RAW",
        body={"values": [row_data]}
    ).execute()
    print(f"Sheets: Updated {tab_name}!A{row_to_change}")

def sheet_exists(tab_name):
    sheets = sheets_service.spreadsheets().get(spreadsheetId=sheets_spreadsheet_id).execute().get('sheets', [])
    sheet_names = [sheet['properties']['title'] for sheet in sheets]
    if tab_name in sheet_names:
        return True
    else:
        return False

def instantiate_new_gamestate_sheet(new_sheet_name):
    print(f"Sheets: Creating new tab called: {new_sheet_name}")
    sheet_title = 'gsTemplate'
    service = build('sheets', 'v4', credentials=creds)
    sheet_metadata = service.spreadsheets().get(spreadsheetId=sheets_spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    sheet = None
    for s in sheets:
        if s['properties']['title'] == sheet_title:
            sheet = s
            sheet_id = s['properties']['sheetId']
            break
    if sheet is None:
        raise Exception(f"Sheet with title {sheet_title} not found")
    new_sheet = {
        "properties": {
            "title": new_sheet_name,
            "sheetId": max([s['properties']['sheetId'] for s in sheets]) + 1,
            "index": len(sheets) + 1,
        }
    }
    # Duplicate the sheet
    request = {
        "requests": [
            {
                "duplicateSheet": {
                    "sourceSheetId": sheet_id,
                    "insertSheetIndex": len(sheets),
                    "newSheetName": new_sheet_name,
                }
            },
        ]
    }
    service.spreadsheets().batchUpdate(spreadsheetId=sheets_spreadsheet_id, body=request).execute()



