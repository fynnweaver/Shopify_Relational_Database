from datetime import datetime
from dateutil.parser import parse

DATA_FILE_PATH = r'C:/Users/fynn/Documents/Code_Projects/Shopify_Relational_Database/files/'

ROW_TYPE_DICT = 'dict'
ROW_TYPE_LIST = 'list'
ROW_TYPE_TUPLE = 'tuple'

FILE_TYPE_CSV = 'csv'
FILE_TYPE_XLS = 'xls'

DEFAULT_NONE_STRINGS = ('null', 'na', 'n/a', '')

def safeDateTimeParse(val):
    if isinstance(val, datetime):
        return val
    return parse(val)

def replaceShop(val):
    if val == '':
        return 'Store_Purchase'
    elif val == 'Local Delivery':
        return 'Local_Delivery'
    elif val[0].isnumeric():
        return 'Local_Pickup'
    return val