# coding=utf-8
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ConfigParser
import os
import sys
from scipy.signal import savgol_filter
from QC1 import ConfigSectionMap, read_config
import warnings

Config = ConfigParser.ConfigParser() #initialize the config parser

#Savitsky Golay Filter function
def SGF(df, Params, window = 7, order = 3):
    warnings.simplefilter('ignore', np.RankWarning)
    pd.options.mode.chained_assignment = None  # default='warn'

    for par in Params:
        dfs = savgol_filter(df[par], window, order)
        df[par] = dfs

    return df

def flatten(l, ltypes=(list, tuple)):
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)

#Prepare dataframe for final saving
def finPrep(df, Config_Path):

    ParamDict = read_config('Parameters', Config_Path)
    for key in ParamDict:
        ParamDict[key] = ParamDict[key].split(',')

    #Create final QC Flag
    for Param in ParamDict.keys():
        for para in ParamDict[Param]:
            df.loc[df[para + '_QC1'].str.contains('Good'), para + '_QCfin' ] = 10*1
            df.loc[df[para + '_QC1'].str.contains(r'\(p\)'), para + '_QCfin' ] = 10*2
            df.loc[df[para + '_QC1'].str.contains(r'\(c\)'), para + '_QCfin' ] = 10*3
            df.loc[df[para + '_QC1'].str.contains(r'-m'), para + '_QCfin' ] = 10*8

            #Flag Parameters based on QC2 results
            df.loc[df[para + '_QC2'].str.contains('Good')  & (df[para + '_QC1'].str.contains(r'm') == False) & (df[para + '_QC1'].str.contains(r'\(c\)') == False), para + '_QCfin' ] = df[para + '_QCfin'] + 100*1
            df.loc[df[para + '_QC2'].str.contains(r'\(p\)'), para + '_QCfin' ] = df[para + '_QCfin'] + 100*2
            df.loc[df[para + '_QC2'].str.contains(r'\(c\)'), para + '_QCfin' ] = df[para + '_QCfin'] + 100*3
            df.loc[(df[para + '_QC2'].str.contains(r'Good')) & (df[para + '_QC1'].str.contains(r'\(c\)')), para + '_QCfin' ] = df[para + '_QCfin'] + 100*5
            df.loc[(df[para + '_QC2'].str.contains(r'Good')) & (df[para + '_QC1'].str.contains(r'm')), para + '_QCfin' ] = df[para + '_QCfin'] + 100*5
            df.loc[df[para + '_QC2'].str.contains(r'-m'), para + '_QCfin' ] = df[para + '_QCfin'] + 100*8

            #Flag Paratmeters based on QC0 results
            if para != 'HS':
                df[para + '_QCfin'] = df[para + '_QCfin'] + 1
                df.loc[df[para + '_QC1'].str.contains(r'-m'), para + '_QCfin' ] = df[para + '_QCfin'] + 7

    #Flag Snow Depth Measurments based on QC0
    if 'HS_q' in df.columns:
        df.loc[(df['HS_q'] > 151) & (df['HS_q'] < 211), 'HS_QCfin'] = df['HS_QCfin'] + 1*1
        df.loc[(df['HS_q'] > 210) & (df['HS_q'] < 301), 'HS_QCfin'] = df['HS_QCfin'] + 2*1
        df.loc[(df['HS_q'] > 300), 'HS_QCfin'] = df['HS_QCfin'] + 9*1
        df.loc[(df['HS_q'] < 152), 'HS_QCfin'] = df['HS_QCfin'] + 9*1

    #Drop columns we dont want in the final dataframe
    ParHeads = flatten(ParamDict.values())
    QfHeads = [s + '_QCfin' for s in ParHeads]
    keep = ParHeads + QfHeads
    df = df[keep]

    #run Savitsky Golay filter where defined
    RepDict = read_config('Report Config', Config_Path)
    if RepDict['sgf_pars'] != '':
        sgf_pars = RepDict['sgf_pars'].split(',')
        df = SGF(df, sgf_pars, int(RepDict['sgf_window']), int(RepDict['sgf_order']))

    '''
    #conform snow depth Units to cm
    if 'snow_depth' in read_config('Units', Config_Path).keys():
        snow_unit = read_config('Units', Config_Path)['snow_depth']

        pd.options.mode.chained_assignment = None  # default='warn'
        if snow_unit == 'mm':
            df['HS'] = df['HS']/10
        elif snow_unit == 'cm':
            pass
        elif snow_unit == 'm':
            df['HS'] = df['HS']*100
    '''
    return df

def runme(Config_Path):
    #Read the data paths from the Local Config file
    Config_Path = Config_Path.decode('utf-8')
    PathDict = read_config('Paths', Config_Path)
    QC2_path = PathDict['qc2_path'].decode('utf-8')
    QC3_path = PathDict['qc2_path'].decode('utf-8')
    QCFin_path = PathDict['qcfin_path'].decode('utf-8')

    #Read data
    df = pd.read_csv(QC3_path, header =  [0] , index_col = 0)

    #Prepare the final dataframe
    df_fin = finPrep(df, Config_Path)

    #Save final Quality controled dataframe
    df_fin.to_csv(path_or_buf = QCFin_path, index_label = 'time')

if __name__ == '__main__':
    Config_Path = sys.argv[1]
    runme(Config_Path)
