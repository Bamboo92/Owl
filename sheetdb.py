from dotenv import load_dotenv
from typing import Final
import os

#from google.auth.transport.requests import Request
#from google.oauth2.credentials import Credentials
#from google_auth_oauthlib.flow import InstalledAppFlow
#from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

import manage_time

# Pfad zur Service Account Schlüsseldatei
SERVICE_ACCOUNT_FILE = 'service_account.json'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

load_dotenv()
SPREADSHEET_ID: Final[str] = os.getenv('SPREADSHEET_ID')

sheet = None


"""
def get_credentials():
    credentials = None
    if os.path.exists('token.json'):
        credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())

    try:
        service = build('sheets', 'v4', credentials=credentials)
        global sheet
        sheet = service.spreadsheets()
    except HttpError as error:
        print(error)"""


def get_credentials():
    try:
        # Lade die Credentials aus der Service Account Datei
        credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        print(manage_time.get_time(), ' Service Account File geladen.')
        try:
            # Initialisiere den Google Sheets Service
            print(manage_time.get_time(), ' Trying service')
            service = build('sheets', 'v4', credentials=credentials)
            print(manage_time.get_time(), ' Got service')
            try:
                print(manage_time.get_time(), ' Trying sheet')
                global sheet
                sheet = service.spreadsheets()
                print(manage_time.get_time(), ' Got sheet')
            except Exception as e:
                print(f'Fehler mit service.spreadsheets(): {e}')
        except Exception as e:
            print(f'Fehler beim build: {e}')
    except FileNotFoundError:
        print(f"Service Account Datei nicht gefunden: {SERVICE_ACCOUNT_FILE}")
    except Exception as e:
        print(f"Fehler beim Laden der Service Account Credentials: {e}")
    return None


def get_row_by_date(date, sheet_name='Working_times'):
    date_str = manage_time.format_date_to_str(date)
    range_name = f'{sheet_name}!C:C'

    if sheet is None:
        print("Could not execute [get_row_id_by_date]: No sheet found")
    else:
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        rows = result.get('values', [])

        for i, row in enumerate(rows):
            if row and row[0] == date_str:
                return i + 1  # Die API indiziert bei 1, nicht bei 0
        return None


def index_to_column_letter(index):
    """Konvertiert einen numerischen Spaltenindex in einen Buchstabenindex."""
    letter = ''
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letter = chr(65 + remainder) + letter
    return letter


def get_column_index_by_name(column_name, sheet_name='Working_times'):
    range_name = f'{sheet_name}!1:1'  # Erste Zeile für Spaltenüberschriften

    if sheet is None:
        print("Could not execute [get_column_index_by_name]: No sheet found")
        return None

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    columns = result.get('values', [])[0]  # Erste Zeile mit Spaltennamen

    try:
        # Erhalte den numerischen Index der Spalte
        column_index = columns.index(column_name) + 1
        # Konvertiere den numerischen Index in einen Buchstabenindex
        column_letter = index_to_column_letter(column_index)
        return column_letter
    except ValueError:
        print(f"Column name '{column_name}' not found.")
        return None


def get_row_data_by_date(date, display_name, column_name, sheet_name='Working_times'):
    # Formatiere das Datum als String, um es mit dem Format im Sheet abzugleichen
    date_str = manage_time.format_date_to_str(date)
    # Generiere den Spaltennamen
    full_column_name = connect_names(display_name, column_name)

    # Hole die Zeilennummer für das gegebene Datum
    row_id = get_row_by_date(date, sheet_name)
    # Hole den Buchstabenindex für die gegebene Spalte
    column_letter = get_column_index_by_name(full_column_name, sheet_name)

    if sheet is None or row_id is None or column_letter is None:
        print("Could not execute [get_row_data_by_date]: Missing data or no sheet found")
        return None

    # Konstruiere den Bereich in 'A1' Notation für die spezifische Zelle
    cell_range = f'{sheet_name}!{column_letter}{row_id}'

    try:
        # Hole den Wert aus der spezifizierten Zelle
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=cell_range).execute()
        values = result.get('values', [])

        if not values:
            print(f"No data found in cell {cell_range}.")
            return None
        return values[0][0]  # Rückgabe des Wertes in der gefundenen Zelle
    except HttpError as error:
        print(f"An error occurred while retrieving data from cell {cell_range}: {error}")
        return None


def connect_names(display_name, column_name):
    # Verbindet den Display-Namen eines Mitglieds mit einer anderen Variable zu einem neuen String.
    members_column_name = f"{display_name} {column_name}"
    return members_column_name


def sheet_add_time(display_name, channel, date, input_value, sheet_name='Working_times'):
    if channel == 'Worked for':
        date_str = input_value
    else:
        date_str = manage_time.format_time_to_str(input_value)

    row_id = get_row_by_date(date, sheet_name)  # Findet die Zeilennummer basierend auf dem Datum
    column_name = connect_names(display_name, channel)  # Zusammengesetzter Spaltenname
    column_index = get_column_index_by_name(column_name, sheet_name)  # Findet den Spaltenindex basierend auf dem Spaltennamen
    if row_id is not None and column_index is not None:
        # Konstruiere den Bereich in 'A1' Notation
        range_name = f"{sheet_name}!{column_index}{row_id}"
        # Vorbereiten der Werte, die aktualisiert werden sollen
        values = [[date_str]]
        body = {'values': values}

        try:
            result = sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body).execute()
            print(f"Cell {range_name} updated successfully.")
        except HttpError as error:
            print(f"An error occurred: {error}")
    else:
        print("Error: Invalid row or column index.")