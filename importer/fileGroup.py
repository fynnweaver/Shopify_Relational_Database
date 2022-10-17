from importer import *
from importer.filesImport import FilesImporter

import os

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
        self.productRelation = self.createProductRelational()
        self.customerRelation = self.createCustomerRelational()
        self.employeeRelation = self.createEmployeeRelational()

        self.orderRelation = self.createOrderRelational()
        self.transRelation = self.createTransRelational()

        # Populate enumerated tables with data from orders

        #self.orderRelational = self.createOrderRelational()



    def getOrderData(self, filePath, rowDataType=ROW_TYPE_DICT):
        # Orders
        orderHeaders = ['Name', 'Email', 'Shipping Method', 'Total', 'Paid at', 'Lineitem name', 'Lineitem price', 'Billing Name', 'Billing City', 'Billing Province', 'Employee']
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



    def createProductRelational(self):
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
        self.productAttributeHeaders = ['Product_Id', 'Attribute_Id', 'Name']

        for row in enumerate(self.productData.data):
            tempRow = [row['Title'], row['Option1 Name'], row['Option1 Name']]

            productAttribute.append(tempRow)


    def createVariantRelational(self):
        variantRelation = []
        self.variantHeaders = ['']


    def createCustomerRelational(self):
        customerRelation = []
        self.customerHeaders = ['Customer_Id', 'Email', 'Name', 'City', 'Province']

        try:
            customerList = [row['Email'] for row in self.customerData.data]
        except AttributeError:
            customerList = [row['Email'] for row in self.orderData.data]

        for Id, customer in enumerate(set(customerList)):
            customerRow = [Id, customer]

            for row in self.orderData.data:
                if row['Email'] == customer:
                    customerRow.append(row['Billing Name'])
                    customerRow.append(row['Billing City'])
                    customerRow.append(row['Billing Province'])

            if self.dataType == ROW_TYPE_DICT:
                customerRow = {header: val for header, val in zip(self.customerHeaders, customerRow)}

            customerRelation.append(customerRow)

        return customerRelation

    def createEmployeeRelational(self):
        employeeRelation = []
        self.employeeHeaders = ['Employee_Id', 'Name']

        employeeList = [row['Employee'] for row in self.orderData.data]

        for Id, customer in enumerate(set(employeeList)):
            employeeRow = [Id, customer]

            if self.dataType == ROW_TYPE_DICT:
                employeeRow = {header: val for header, val in zip(self.employeeHeaders, employeeRow)}

            employeeRelation.append(employeeRow)

        return employeeRelation



    def createOrderRelational(self):
        orderRelation = []

        self.orderHeaders = ['Order_Id', 'Customer_Id', 'Shipping_Method', 'Total_Paid', 'Paid_Datetime', 'Employee_Id', 'Total_Items']

        numberItems = 0

        for idx, row in enumerate(self.orderData.data):

            # If input is list transform into dict
            if self.dataType == ROW_TYPE_LIST:
                row = {header: val for header, val in zip(self.orderData.headers, row)}

            # Save first row and set start Id
            if idx == 0:
                startID = row['Name']
                rowTemp = [startID, row['Email'], row['Shipping Method'], row['Total'], row['Paid at'], row['Employee']]


            # After first row set current ID and increase number items for every new row
            else:
                currentID = row['Name']
                numberItems += 1

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

        orderRelation = self.replaceIds(orderRelation, ['Customer_Id', 'Email'], self.customerRelation)
        orderRelation = self.replaceIds(orderRelation, ['Employee_Id', 'Name'], self.employeeRelation)


        return orderRelation



    def replaceIds(self, data, columns, targetIds):

        idDict = {}
        idColumn, nameColumn = columns

        for row in targetIds:
            idDict[row[idColumn]] = row[nameColumn]


        valueList = [row[idColumn] for row in data]

        for key, value in idDict.items():
            if value not in valueList:
                continue

            index = valueList.index(value)
            valueList[index] = key

        for Id, row in zip(valueList, data):
            row[idColumn] = Id

        return data



    def createTransRelational(self):
        transRelation = []

        self.transHeaders = ['Transaction_Id', 'Order_Id', 'Product_Id', 'Price_Paid']

        for idx, row in enumerate(self.orderData.data):
            rowTemp = [idx, row['Name'], row['Lineitem name'], row['Lineitem price']]

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
            row['Variant_Id'] = productVarient

        transRelation = self.replaceIds(transRelation, ['Product_Id', 'Title'], self.productRelation)
        transRelation = self.replaceIds(transRelation, ['Variant_Id', 'Variant'])

        print('hi')
        return transRelation


