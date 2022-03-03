import pandas as pd
from gspread import Worksheet
from pandas import DataFrame

from core.Configurations import Configurations


class Products:
    def __init__(self, products_worksheet: Worksheet, configurations_worksheet: Worksheet):
        configurations = Configurations(configurations_worksheet)
        self.all = self.get_all_products(products_worksheet)
        self.corrected = self.get_corrected_products(configurations.signatures_of_corrected_products)
        self.not_corrected = self.get_not_corrected_products(configurations.signatures_of_corrected_products)

    @staticmethod
    def get_all_products(products_worksheet):
        products = pd.DataFrame(data=products_worksheet.get_all_records())
        products.dropna(how='all', inplace=True)
        print(f'current products length: {len(products)}')
        return products

    def get_corrected_products(self, signatures_of_corrected_products) -> DataFrame:
        corrected_products = self.all[self.create_corrected_products_mask(signatures_of_corrected_products)]
        corrected_products.dropna(how='all', inplace=True)
        return corrected_products

    def create_corrected_products_mask(self, signatures_of_corrected_products):
        column_with_signatures = self.all.columns[7]
        return self.all[column_with_signatures].isin(signatures_of_corrected_products)

    def get_not_corrected_products(self, signatures_of_corrected_products) -> DataFrame:
        not_corrected_products = self.all[~self.create_corrected_products_mask(signatures_of_corrected_products)]
        not_corrected_products.dropna(how='all', inplace=True)
        return not_corrected_products
