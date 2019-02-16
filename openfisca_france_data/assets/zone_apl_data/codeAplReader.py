# -*- coding: utf-8 -*-


import csv
import pickle

if __name__ == '__main__':

    codeDict = {}
    fileName = 'zone_apl.csv'

    code = csv.reader(open(fileName), delimiter = ";")

    for row in code:
        codeDict.update({row[2]: (row[1], row[4])})

    # print(codeDict['75017'])

    outputFile = open("code_apl", 'wb')
    pickle.dump(codeDict, outputFile)
    outputFile.close()
