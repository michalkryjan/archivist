from datetime import date

import pandas as pd
from gspread import Worksheet

from pandas import DataFrame


class Archive:
    def __init__(self, last_archive_worksheet):
        self.current_data = self.get_current_archive(last_archive_worksheet)

    @staticmethod
    def get_current_archive(last_archive_worksheet: Worksheet):
        archive = pd.DataFrame(data=last_archive_worksheet.get_all_records())
        archive.dropna(how='all', inplace=True)
        print(f'current archive length: {len(archive)}')
        return archive

    def extend_current_archive_with_new_data(self, new_data: DataFrame):
        unified_new_data = self.unify_new_data_structure(new_data)
        return self.current_data.append(unified_new_data, ignore_index=True)

    def unify_new_data_structure(self, new_data: DataFrame) -> DataFrame:
        new_data.insert(loc=0, column='Data dodania do archiwum', value=date.today().strftime('%d.%m.%Y'))
        self.sort_data(new_data)
        return new_data

    @staticmethod
    def sort_data(data: DataFrame):
        labels = data.columns
        data.sort_values(
            by=[labels[0], #'Data dodania do archiwum'
                labels[8], #'Osoba odpowiedzialna za poprawki produktu'
                labels[9], #'Data wykonania poprawek'
                labels[7]], #'Data dodania zlecenia'
            ascending=[True,
                       True,
                       True,
                       True], inplace=True)
