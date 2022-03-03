from gspread import Worksheet


class Configurations:
    def __init__(self, configurations_worksheet: Worksheet):
        self.signatures_of_corrected_products = self.get_extended_signatures_list(configurations_worksheet)

    def get_extended_signatures_list(self, configurations_worksheet: Worksheet) -> list:
        signatures_from_worksheet = self.get_signatures_from_worksheet(configurations_worksheet)
        other_signatures = []
        for signature in signatures_from_worksheet:
            signature_without_dot = signature[:-1]
            other_signatures.append(signature_without_dot)
        return [*signatures_from_worksheet, *other_signatures]

    @staticmethod
    def get_signatures_from_worksheet(worksheet: Worksheet) -> list:
        signatures = []
        row_index = 2
        while True:
            signature = worksheet.cell(row_index, 2).value
            if signature is not None and signature != '':
                signatures.append(signature)
            else:
                break
            row_index += 1
        return signatures


