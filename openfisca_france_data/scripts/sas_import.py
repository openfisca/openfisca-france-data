# -*- coding: utf-8 -*-
"""
Created on Tue May  6 15:13:59 2014

@author: pacificoadrien
"""

from sas7bdat import SAS7BDAT
import pandas as pd
import os
import sys



def extract_from_sas(file_to_import):
    f = SAS7BDAT(file_to_import)
    outFile = ("/Users/pacificoadrien/Downloads/help.csv")


    def convertFile(sas7bdat, outFile, delimiter=',', stepSize=100000):
            try:
                if outFile == '-':
                    outF = sys.stdout
                else:
                    outF = open(outFile, 'w')
                    df = pd.DataFrame()

                i = 0
                for i, line in enumerate(sas7bdat.readData(), 1):
                    if not line:
                        i -= 1
                        continue

                    if not i % stepSize:
                        sas7bdat.logger.info('%.1f%% complete',
                                         float(i) / sas7bdat.header.rowcount * 100.0)
                    try:
#                        print(i)
                        if i == 1:

                            df = pd.DataFrame( columns= line )
                        else:
                         df = df.append( dict(zip(df.columns,line)), ignore_index = True)

                    except IOError:
                        sas7bdat.logger.warn('Wrote %d lines before interruption', i)
                        break
                sas7bdat.logger.info('[%s] wrote %d of %d lines',
                                 os.path.basename(outFile), i - 1,
                                 sas7bdat.header.rowcount)
            finally:
                print(df)
                if outF is not None:
                    outF.close()


    convertFile(f, outFile, delimiter=',', stepSize=100000)




if __name__ == '__main__':

    import pkg_resources
    openfisca_france_location = pkg_resources.get_distribution('openfisca-france-data').location
    file_exemple_location = openfisca_france_location + "/openfisca_france_data/scripts/help.sas7bdat"
    extract_from_sas(file_exemple_location)
