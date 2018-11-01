# coding=utf-8
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ConfigParser
from Pysolar.solar import *
from Pysolar.radiation import *
import datetime
from datetime import timedelta
from dateutil import parser
import os
import sys
Config = ConfigParser.ConfigParser() #initialize the config parser

#Map the configurations to a dictionary
def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("Skip: %s" % option)
        except:
            print("exception on %s!" %option)
            dict[option] = SectionOne
    return(dict1)

#Read the global configuration file with the QC test constraints
def read_config(Param, glob_file):
    Config.read(glob_file) #Read the Config ini file
    Config_dict = ConfigSectionMap(Param)
    return Config_dict

def runme(Config_Path):

    #Read the data paths from the Local Config file
    Config_Path = Config_Path.decode('utf-8')
    PathDict = read_config('Paths', Config_Path)
    RAW_path = PathDict['raw_path'].decode('utf-8')
    MET_path = PathDict['met_path'].decode('utf-8')
    QC2_path = PathDict['qc2_path'].decode('utf-8')
    QCFin_path = PathDict['qcfin_path'].decode('utf-8')
    HS_path = PathDict['hs_path_pp'].decode('utf-8')


    #Define the list of columns
    cols = ['doy', 'hr', 't', 'rh', 'sw_in', 'sw_out', 'lw_in', 'lw_out', 'f', 'd']

    #Read the RAW data
    df = pd.read_table(RAW_path, sep = '\s+', header = None)

    df.columns = cols
    print df
    #Modify columns to int
    df[['doy', 'hr']] = df[['doy','hr']].astype(int)
    df['hr'] = df['hr'].replace(2400, 0000)

    df['TIMESTAMP'] = ''
    for index, row in df.iterrows():
        if len(str(row['hr'])) == 4:
            df.loc[index, 'TIMESTAMP'] = datetime.datetime.strptime(read_config('meta', Config_Path)['year'] + str(row['doy']) + ' ' + str(row['hr']), '%Y%j %H%M')
        if len(str(row['hr'])) == 3:
            df.loc[index, 'TIMESTAMP'] = datetime.datetime.strptime(read_config('meta', Config_Path)['year'] + str(row['doy']) + ' ' + '0' + str(row['hr']), '%Y%j %H%M')
        if len(str(row['hr'])) == 2:
            df.loc[index, 'TIMESTAMP'] = datetime.datetime.strptime(read_config('meta', Config_Path)['year'] + str(row['doy']) + ' ' + '00' + str(row['hr']), '%Y%j %H%M')
        if len(str(row['hr'])) == 1:
            df.loc[index, 'TIMESTAMP'] = datetime.datetime.strptime(read_config('meta', Config_Path)['year'] + str(row['doy'] + 1) + ' ' + '000' + str(row['hr']), '%Y%j %H%M')

    df = df.set_index('TIMESTAMP')


    #Add snow depth data where available
    if HS_path != '':
        df_HS = pd.read_table(HS_path, sep = '\s+', header = None)
        #df_HS['TIMESTAMP'] = pd.to_datetime( read_config('meta', Config_Path)['year'] + '-1-1') + pd.to_timedelta(df_HS['doy'], unit = 'D')
        #df_HS['TIMESTAMP'] = df_HS['TIMESTAMP'].dt.round('1h')

        print df_HS
        df_HS.columns = ['doy', 'hr-min', 'HS']
        df_HS['TIMESTAMP'] = ''
        df_HS[['doy', 'hr-min']] = df_HS[['doy','hr-min']].astype(int)
        df_HS['hr-min'] = df_HS['hr-min'].replace(2400, 0000)
        for index, row in df_HS.iterrows():
            if len(str(row['hr-min'])) == 4:
                df_HS.loc[index, 'TIMESTAMP'] = datetime.datetime.strptime(read_config('meta', Config_Path)['year'] + str(row['doy']) + ' ' + str(row['hr-min']), '%Y%j %H%M')
            if len(str(row['hr-min'])) == 3:
                df_HS.loc[index, 'TIMESTAMP'] = datetime.datetime.strptime(read_config('meta', Config_Path)['year'] + str(row['doy']) + ' ' + '0' + str(row['hr-min']), '%Y%j %H%M')
            if len(str(row['hr-min'])) == 2:
                df_HS.loc[index, 'TIMESTAMP'] = datetime.datetime.strptime(read_config('meta', Config_Path)['year'] + str(row['doy']) + ' ' + '00' + str(row['hr-min']), '%Y%j %H%M')
            if len(str(row['hr-min'])) == 1:
                df_HS.loc[index, 'TIMESTAMP'] = datetime.datetime.strptime(read_config('meta', Config_Path)['year'] + str(row['doy'] + 1) + ' ' +  '000' + str(row['hr-min']), '%Y%j %H%M')

        df_HS = df_HS.set_index('TIMESTAMP')
        del df_HS['doy']

        df = df_HS['HS'].to_frame().combine_first(df).dropna()
        #df.loc[df_HS.index.values,'HS'] = df_HS['HS']#df_HS.reindex(df.index.values)['HS']

    del df['hr']
    del df['doy']

    print df
    df = df[~df.index.duplicated(keep = 'first')]
    df.to_csv(MET_path)

if __name__ == '__main__':
    Config_Path = 'F:\Þróunarsvið\Rannsóknir\M-Sameign\GAVEL\GAVEL1\Budir\GAVEL\Config\LocConfig_Budir_1996.ini'

    runme(Config_Path)
