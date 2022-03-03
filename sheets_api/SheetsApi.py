import os

import gspread
import numpy as np
from gspread import Worksheet, Client, Spreadsheet
from oauth2client.service_account import ServiceAccountCredentials
from pandas import DataFrame


class SheetsApi:
    def __init__(self):
        self.authorized_client = SheetsApiAuthenticator.authorize_client()
        self.selector = SheetsSelector(self.authorized_client)
        self.modifier = SheetsModifier(self.authorized_client, self.selector.products_worksheet, self.selector.last_archive_worksheet)


class SheetsApiAuthenticator:
    SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    @classmethod
    def authorize_client(cls) -> Client:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(cls.get_service_account_creds_path(), cls.SCOPES)
        return gspread.authorize(credentials)

    @classmethod
    def get_service_account_creds_path(cls):
        return os.path.join(cls.get_current_dir_path(), 'keys', 'service_account_secret.json')

    @staticmethod
    def get_current_dir_path():
        return os.path.dirname(os.path.abspath(__file__))


class SheetsSelector:
    def __init__(self, sheets_client: Client):
        self.client = sheets_client
        self.products_spreadsheet = self.get_products_spreadsheet()
        self.archive_spreadsheet = self.get_archive_spreadsheet()
        self.products_worksheet = self.get_products_worksheet()
        self.configurations_worksheet = self.get_configurations_worksheet()
        self.last_archive_worksheet = self.get_last_archive_worksheet()

    def get_products_spreadsheet(self) -> Spreadsheet:
        return self.client.open_by_key(os.getenv('PRODUCTS_SPREADSHEET_KEY'))

    def get_archive_spreadsheet(self) -> Spreadsheet:
        return self.client.open_by_key(os.getenv('ARCHIVE_SPREADSHEET_KEY'))

    def get_products_worksheet(self) -> Worksheet:
        return self.get_products_spreadsheet().worksheet('produkty do poprawienia')

    def get_configurations_worksheet(self) -> Worksheet:
        return self.get_products_spreadsheet().worksheet('konfiguracja')

    def get_last_archive_worksheet(self) -> Worksheet:
        spreadsheet = self.get_archive_spreadsheet()
        biggest_number = 0
        for worksheet in spreadsheet.worksheets():
            biggest_number = self.get_bigger_number(int(worksheet.title), int(biggest_number))
        return spreadsheet.worksheet(str(biggest_number))

    @staticmethod
    def get_bigger_number(num1: int, num2: int) -> int:
        return num1 if num1 > num2 else num2


class SheetsModifier:
    def __init__(self, sheets_client: Client, products_worksheet: Worksheet, last_archive_worksheet: Worksheet):
        self.client = sheets_client
        self.products_worksheet = products_worksheet
        self.last_archive_worksheet = last_archive_worksheet

    def update_products_worksheet(self, update_data: DataFrame):
        if update_data is not None:
            print(f'products update data length: {len(update_data)}')
            self.overwrite_worksheet_values(update_data, self.products_worksheet, self.overwrite_products_cba_links_column)
            print('Products update done')

    def overwrite_worksheet_values(self, update_data: DataFrame, worksheet: Worksheet, cba_links_correction_void):
        if len(worksheet.get_all_values()) > 0:
            self.clear_worksheet_values(worksheet)
        cba_links_correction_void(update_data)
        self.append_data_to_worksheet(update_data, worksheet)

    def clear_worksheet_values(self, worksheet: Worksheet):
        worksheet.batch_clear(["A2:L50000"])
        self.set_white_background_for_values(worksheet)

    @staticmethod
    def set_white_background_for_values(worksheet: Worksheet):
        worksheet.format("A2:L50000", {
            "backgroundColor": {
                "red": 1.0,
                "green": 1.0,
                "blue": 1.0
            },
        })

    @staticmethod
    def append_data_to_worksheet(data: DataFrame, worksheet: Worksheet):
        params = {'valueInputOption': 'USER_ENTERED'}
        data.replace(np.NaN, '', inplace=True)
        body = {'values': data.values.tolist()}
        worksheet.spreadsheet.values_append(f'{worksheet.title}!A2:L2', params, body)

    def overwrite_products_cba_links_column(self, products_data: DataFrame):
        products_data.drop(labels="Link CBA", axis=1, inplace=True)
        cba_links_correct_values = self.create_list_of_products_correct_formulas(products_data)
        products_data.insert(loc=9, column="Link CBA", value=cba_links_correct_values)

    def create_list_of_products_correct_formulas(self, products_data: DataFrame):
        return self.create_list_of_correct_formulas(products_data, 'B')

    @staticmethod
    def create_list_of_correct_formulas(df, column_letter):
        correct_formulas = []
        for row_number in range(2, len(df.index) + 2, 1):
            formula = f'=HIPERŁĄCZE(CONCAT("HERE GOES PRIVATE URL";{column_letter}{row_number});"CBA")'
            correct_formulas.append(formula)
        return correct_formulas

    def update_archive_worksheet(self, update_data: DataFrame):
        print(f'archive update data length: {len(update_data)}')
        if not self.is_worksheet_data_limit_reached(update_data):
            self.overwrite_worksheet_values(update_data, self.last_archive_worksheet, self.overwrite_archive_cba_links_column)
        else:
            self.make_archive_update_with_splitted_data(update_data)
        print('Archive update done')

    @staticmethod
    def is_worksheet_data_limit_reached(new_data: DataFrame) -> bool:
        return True if len(new_data) > 49999 else False

    def overwrite_archive_cba_links_column(self, archive_data: DataFrame):
        archive_data.drop(labels="Link CBA", axis=1, inplace=True)
        correct_cba_links_values = self.create_list_of_archive_correct_formulas(archive_data)
        archive_data.insert(loc=10, column="Link CBA", value=correct_cba_links_values)

    def create_list_of_archive_correct_formulas(self, archive_data: DataFrame):
        return self.create_list_of_correct_formulas(archive_data, 'C')

    def make_archive_update_with_splitted_data(self, update_data: DataFrame):
        worksheet = self.last_archive_worksheet
        while len(update_data) > 0:
            if len(update_data) > 49999:
                self.overwrite_worksheet_values(update_data[:49999], worksheet, self.overwrite_archive_cba_links_column)
                update_data = update_data[49999:]
                worksheet = worksheet.spreadsheet.add_worksheet(title=str(int(worksheet.title) + 1), rows="50000", cols="12")
                self.overwrite_columns_labels_in_archive_worksheet_to_match_source(worksheet)
            else:
                self.overwrite_worksheet_values(update_data, worksheet, self.overwrite_archive_cba_links_column)
                update_data = ''

    def overwrite_columns_labels_in_archive_worksheet_to_match_source(self, worksheet: Worksheet):
        columns_labels = [['Data dodania do archiwum'] + self.products_worksheet.row_values(1)]
        worksheet.update('A1:M1', columns_labels)
