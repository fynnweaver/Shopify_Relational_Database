from importer import *
from importer.filesImport import FilesImporter
from importer.fileGroup import FileGrouper

returnColumns = [
    'Name', 'Email', 'Paid at', 'Total', 'Shipping Method', 'Lineitem name', 'Lineitem price', 'Billing Name', 'Billing City', 'Billing Province', 'Employee',
]

defaultHeaders = {
    'Paid at': 'Paid_at',
    'Shipping Method' : 'Shipping_Method',
    'Lineitem name': 'Lineitem_Name',
    'Lineitem price': 'Lineitem_price',

}

defaultDataTypes = {
    'Total': float,
    'Paid at': safeDateTimeParse,
    'Shipping Method': replaceShop

}

noneExceptions = 'Shipping Method'

#fileImport = FilesImporter(f'{DATA_FILE_PATH}orders_export_1.csv', returnColumns=returnColumns, defaultDataTypes=defaultDataTypes, noneExceptions=noneExceptions, rowDataType=ROW_TYPE_LIST)
#fileImport.printRows(4)

# Next step: class that takes dict/list of cleaned data

test = FileGrouper(DATA_FILE_PATH)
test.previewData('orders', 5)