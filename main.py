from apscheduler.schedulers.blocking import BlockingScheduler
import logging

from sheets_api.SheetsApi import SheetsApi
from core.Products import Products
from core.Archive import Archive


core_scheduler = BlockingScheduler()

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)


@core_scheduler.scheduled_job('cron', timezone='utc', day='1st sun', hour=8, minute=0, second=0)
def move_corrected_products_to_archive():
    sheets_api = SheetsApi()
    sheets_api.modifier.overwrite_columns_labels_in_archive_worksheet_to_match_source(sheets_api.selector.last_archive_worksheet)

    products = Products(sheets_api.selector.products_worksheet, sheets_api.selector.configurations_worksheet)
    sheets_api.modifier.update_products_worksheet(products.not_corrected)

    archive = Archive(sheets_api.selector.last_archive_worksheet)
    extended_archive = archive.extend_current_archive_with_new_data(products.corrected)
    sheets_api.modifier.update_archive_worksheet(extended_archive)


core_scheduler.start()
