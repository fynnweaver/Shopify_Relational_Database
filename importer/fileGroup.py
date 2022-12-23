from importer import *
from importer.filesImport import FilesImporter

import os
from collections import Counter
from statistics import median, mean

class FileGrouper:

    def __init__(self, fileDir, rowDataType=ROW_TYPE_DICT, noneStrings=DEFAULT_NONE_STRINGS, rowLimit=None):

        self.dataType = rowDataType

        self.orderPath = None
        self.productPath = None
        self.customerPath = None

        # Load paths and data
        for file in os.listdir(fileDir):
            if 'order' in file:
                self.orderPath = os.path.join(fileDir, file)
                self.orderData = self.getOrderData(self.orderPath, rowDataType=rowDataType)
            elif 'product' in file:
                self.productPath = os.path.join(fileDir, file)
                self.productData = self.getProductData(self.productPath, rowDataType=rowDataType)
            elif 'customer' in file:
                self.customerPath = os.path.join(fileDir, file)
                self.customerData = self.getCustomerData(self.customerPath, rowDataType=rowDataType)
            print('Unknown file in folder')


        # Generate enumerated tables from files or from order
        self.productBase = self.createProductBase()

        self.productAttribute = self.createProductAttribute()
        self.attributeValues = self.createAttributeValues()

        self.orderBase = self.createOrderBase()
        self.transBase = self.createTransBase()

        self.customerBase = self.createCustomerBase()
        self.employeeBase = self.createEmployeeBase()

        #replace IDs using now complete tables
        self.orderBase = self.replaceIds(self.orderBase, ['Customer_Id', 'Email'], self.customerBase)
        self.orderBase = self.replaceIds(self.orderBase, ['Employee_Id', 'Name'], self.employeeBase)
        self.transBase = self.replaceIds(self.transBase, ['Product_Id', 'Title'], self.productBase)
        self.transBase = self.replaceIds(self.transBase, ['Attribute_Id', 'Value'], self.attributeValues)
        print('hi')


    def getOrderData(self, filePath, rowDataType=ROW_TYPE_DICT):
        # Orders
        orderHeaders = ['Name', 'Email', 'Shipping Method', 'Total', 'Paid at', 'Lineitem name', 'Lineitem quantity', 'Lineitem price', 'Billing Name', 'Billing City', 'Billing Province', 'Employee']
        orderTypes = {
            'Total': float,
            'Paid at': safeDateTimeParse,
            'Shipping Method': replaceShop,
            'Lineitem price': float
        }

        if self.orderPath:
            orderData = FilesImporter(filePath, returnColumns=orderHeaders, defaultDataTypes=orderTypes, rowDataType=rowDataType, noneExceptions='Shipping Method')
        else:
            raise Exception('No order file found. Order file is the minimal required for results.')

        return orderData

    def getProductData(self, filePath, rowDataType=ROW_TYPE_DICT):
        # Products
        productHeaders = ['Title', 'Published', 'Option1 Name', 'Option1 Value', 'Variant Price', 'Cost per item', 'Status']
        productTypes = {
            'Variant Price': float,
            'Cost per item': float
        }

        try:
            productData = FilesImporter(filePath, returnColumns=productHeaders, defaultDataTypes=productTypes, rowDataType=rowDataType)
        except:
            productData = None
            print('Warning: no product data given, some results will be limited')

        return productData

    def getCustomerData(self, filePath, rowDataType=ROW_TYPE_DICT):
        # Products
        productHeaders = []
        productTypes = {
            'Variant Price': float,
            'Cost per item': float
        }

        try:
            customerData = FilesImporter(filePath, returnColumns=productHeaders, defaultDataTypes=productTypes, rowDataType=rowDataType)
        except AttributeError():
            customerData = None
            print('Warning: no customer data given, some results will be limited')

        return customerData

    def previewData(self, sheet, numRows):
        if sheet == 'orders':
            self.orderData.printRows(numRows)
        elif sheet == 'products':
            self.productData.printRows(numRows)



    def createProductBase(self):
        productRelation = []
        self.productHeaders = ['Product_Id', 'Title']

        try:
            productList = [row['Title'] for row in self.productData.data]
        except AttributeError:
            productList = [row['Lineitem name'].split('-')[0].strip() for row in self.orderData.data]

        for Id, product in enumerate(set(productList)):
            productRow = [Id, product]

            if self.dataType == ROW_TYPE_DICT:
                productRow = {header: val for header, val in zip(self.productHeaders, productRow)}

            productRelation.append(productRow)

        return productRelation

    def createProductAttribute(self):
        productAttribute = []
        self.productAttributeHeaders = ['Attribute_Id', 'Product_Id', 'Name']

        idx = 0

        for row in self.productData.data:

            if row['Option1 Name']:
                idx += 1
                tempRow = [idx, row['Title'], row['Option1 Name']]

                if self.dataType == ROW_TYPE_DICT:
                    tempRow = {header: val for header, val in zip(self.productAttributeHeaders, tempRow)}

                productAttribute.append(tempRow)



        productAttribute = self.replaceIds(productAttribute, ['Product_Id', 'Title'], self.productBase)

        return productAttribute

    def createAttributeValues(self):
        attributeValues = []
        self.attributeValuesHeaders = ['Value_Id', 'Product_Id', 'Attribute_Id', 'Value']

        idx = 0
        for row in self.productData.data:

            if row['Option1 Value']:

                idx += 1

                if row['Option1 Name'] is None:
                    attribute = previousAttribute
                else:
                    attribute = row['Option1 Name']
                    previousAttribute = row['Option1 Name']

                if row['Title'] is None:
                    title = previousTitle
                else:
                    title = row['Title']
                    previousTitle = row['Title']


                tempRow = [idx, title, attribute, row['Option1 Value']]


                if self.dataType == ROW_TYPE_DICT:
                    tempRow = {header: val for header, val in zip(self.attributeValuesHeaders, tempRow)}

                attributeValues.append(tempRow)

        attributeValues = self.replaceIds(attributeValues, ['Product_Id', 'Title'], self.productBase)

        attributeDict = {}

        for row in self.productAttribute:
            attributeDict[row['Product_Id']] = row['Attribute_Id']

        # Retrieve attribute Id based on product Id
        for row in attributeValues:
            row['Attribute_Id'] = attributeDict[row['Product_Id']]

            del row['Product_Id']

        return attributeValues



    def createOrderBase(self):
        orderRelation = []

        self.orderHeaders = ['Order_Id', 'Customer_Id', 'Shipping_Method', 'Total_Paid', 'Paid_Datetime', 'Employee_Id',
                             'Total_Items']

        numberItems = 0

        for idx, row in enumerate(self.orderData.data):

            # If input is list transform into dict
            if self.dataType == ROW_TYPE_LIST:
                row = {header: val for header, val in zip(self.orderData.headers, row)}

            # Save first row and set start Id
            if idx == 0:
                startID = row['Name']
                rowTemp = [startID, row['Email'], row['Shipping Method'], row['Total'], row['Paid at'], row['Employee']]
                numberItems = int(row['Lineitem quantity'])

            # After first row set current ID and increase number items for every new row
            else:
                currentID = row['Name']
                productQuantity = int(row['Lineitem quantity'])
                numberItems += productQuantity  # [lineitem quantity is corresponding to previous row for some reason making issues what quanitity is over 1]

                # Once ID is no longer equal to start ID append number of items, row and reset for next transaction
                if currentID != startID:
                    rowTemp.append(numberItems)
                    numberItems = 0

                    # Convert back to dict if dict is defined
                    if self.dataType == ROW_TYPE_DICT:
                        rowTemp = {header: val for header, val in zip(self.orderHeaders, rowTemp)}

                    orderRelation.append(rowTemp)
                    rowTemp = [currentID, row['Email'], row['Shipping Method'], row['Total'], row['Paid at'],
                               row['Employee']]
                    startID = currentID

        for row in orderRelation:
            try:
                row['Order_Id'] = int(row['Order_Id'].replace('#', ''))
            except ValueError:
                pass

        return orderRelation

    def createTransBase(self):
        transRelation = []

        self.transHeaders = ['Transaction_Id', 'Order_Id', 'Product_Id', 'Product_Quantity', 'PPU']

        for idx, row in enumerate(self.orderData.data):
            rowTemp = [idx, row['Name'], row['Lineitem name'], row['Lineitem quantity'], row['Lineitem price']]

            if self.dataType == ROW_TYPE_DICT:
                rowTemp = {header: val for header, val in zip(self.transHeaders, rowTemp)}

            transRelation.append(rowTemp)

        for row in transRelation:

            try:
                row['Order_Id'] = int(row['Order_Id'].replace('#', ''))
            except ValueError:
                pass

            try:
                productTitle = row['Product_Id'].split('-')[0].strip()
                productVarient = row['Product_Id'].split('-')[1].strip()
            except:
                productTitle = row['Product_Id']
                productVarient = None

            row['Product_Id'] = productTitle
            row['Attribute_Id'] = productVarient



        print('hi')
        return transRelation



    def createCustomerBase(self):
        customerBase = []
        self.customerHeaders = ['Customer_Id', 'Email', 'First_Name', 'Last_Name', 'City', 'Province', 'Total_Orders']

        # Generate list of unique customers and count frequency (aka number of orders)
        customerList = [row['Customer_Id'] for row in self.orderBase]
        customerOrders = Counter(customerList)

        # Set ID and customerSpent dict
        ID = 0
        customerSpent = {}

        # For each customer + purchase frequency pair create row with ID and customer email
        for customer, totalOrders in customerOrders.items():
            customerRow = [ID, customer]
            ID += 1
            customerSpent[customer] = 0 # set dict item with that customer email to 0

            # For each row in data if the email is that of the current customer then...
            for row in self.orderData.data:

                if row['Email'] == customer:

                    # ...Add order total to the spent dictionary under customer email key
                    try:
                        customerSpent[customer] += row['Total']
                    except TypeError:
                        customerSpent[customer] += 0

                    # ...Split first and last name and append rest of the information
                    try:
                        firstName, lastName = row['Billing Name'].split(' ')
                    except:
                        firstName, lastName = None, None
                    customerRow.append(firstName)
                    customerRow.append(lastName)
                    customerRow.append(row['Billing City'])
                    customerRow.append(row['Billing Province'])
                    customerRow.append(totalOrders)

            # If dict is defined then
            if self.dataType == ROW_TYPE_DICT:
                customerRow = {header: val for header, val in zip(self.customerHeaders, customerRow)}

            customerBase.append(customerRow)

        # Append the total spent using the email key
        for row in customerBase:
            row['Total_Spent'] = round(customerSpent[row['Email']], 2)

        return customerBase

    def createEmployeeBase(self):
        employeeBase = []
        self.employeeHeaders = ['Employee_Id', 'Name', 'Total_Orders']

        employeeList = [row['Employee_Id'] for row in self.orderBase]
        employeeOrders = Counter(employeeList)

        # Set ID and customerSpent dict
        ID = 0
        employeeEarned = {}
        employeePerOrder = {}
        employeeItems = {}

        # For each employee + purchase frequency pair create row with ID and customer email
        for employee, totalOrders in employeeOrders.items():
            employeeRow = [ID, employee, totalOrders]
            ID += 1
            employeeEarned[employee] = 0  # set dict item with that employee email to 0 to track total earned
            employeePerOrder[employee] = []  # set per order as empty list
            employeeItems[employee] = []

            # For each row in data if the email is that of the current employee then...
            for row in self.orderData.data:

                if row['Employee'] == employee:

                    # ...Add order total to the spent dictionary & per order list under employee email key
                    try:
                        employeeEarned[employee] += row['Total']
                        employeePerOrder[employee].append(row['Total'])
                    except TypeError:
                        employeeEarned[employee] += 0


            # Use orderBase table for total items in each order
            for row in self.orderBase:

                if row['Employee_Id'] == employee:

                    employeeItems[employee].append(row['Total_Items'])


            if self.dataType == ROW_TYPE_DICT:
                employeeRow = {header: val for header, val in zip(self.employeeHeaders, employeeRow)}

            employeeBase.append(employeeRow)

        # Round and append total earned, total transactions and average item # per transaction
        for row in employeeBase:
            row['Total_Earned'] = round(employeeEarned[row['Name']], 2)
            row['MedianPerOrder'] = median(employeePerOrder[row['Name']])
            row['MedianItemsPerOrder'] = median(employeeItems[row['Name']])

        return employeeBase






    def replaceIds(self, data, columns, targetIds):

        idDict = {}
        idColumn, nameColumn = columns

        for row in targetIds:
            idDict[row[nameColumn]] = row[idColumn]

        idList = []

        for row in data:
            try:
                currentId = idDict[row[idColumn]]
            except:
                currentId = None
            idList.append(currentId)

        for Id, row in zip(idList, data):
            row[idColumn] = Id

        return data




