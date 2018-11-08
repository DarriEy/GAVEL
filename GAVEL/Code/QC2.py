# coding=utf-8
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ConfigParser
import os
import sys
from QC1 import *
Config = ConfigParser.ConfigParser() #initialize the config parser

'''
QC2 module of GAVEL quality control software, second part of automatic quality
control, remove obvious errors, interpolate and re-run QC1 tests

File name: QC2.py
Author: Darri Eythorsson
Date Created: 15.08.2018
Date Last Modified: 2.11.2018
Python Version: 2.7
Version: 1.0
'''
#Remove errors flagged as certain
def rem_cert(df):
    for col in df.columns:
        if '_QC1' in col:
            df.loc[df[col].str.contains(r'\(c\)'), col[:-4]] = np.nan # replace certain errors
    return df

#interpolate small gaps
def interpol(df, Config_Path, ParamDict):

    Config_dict = read_config('QC2_Parameters', Config_Path)
    method = Config_dict['ipolmtd'] #read which method to use for interpolation

    #go through all the parameters and interpolate
    for Param in ParamDict.keys():
        for para in ParamDict[Param]:
            if para in df.columns:
                if para == 'HS':
                    df[para] = df[para].interpolate(method,  limit = int(Config_dict['filllimitsnow']))
                    df[para] = df[para].bfill(limit = 1)
                    df[para] = df[para].ffill(limit = 1)
                else:
                    df[para] = df[para].interpolate(method,  limit = int(Config_dict['filllimit']))
                    df[para] = df[para].bfill(limit = 1)
                    df[para] = df[para].ffill(limit = 1)
    return df

#----------  QC2 Module - Gap filling etc ----------
def QC2(df, Config_Path, QC = 'QC2'):
    #Get list of parameters
    ParamDict = read_config('Parameters', Config_Path)
    for key in ParamDict:
        ParamDict[key] = ParamDict[key].split(',')

    #List of Parameters to perform the QC tests on
    Param_Range = ParamDict.keys() #Get the parameter names to perform Range, Missing value tests on
    Param_Step = ['air_temperature', 'wind_speed', 'atmospheric_pressure', 'snow_depth'] #Define list of parameters to do step test on

    #Remove certain error flags
    df = rem_cert(df)

    #Interpolate small gaps of max 6h
    df = interpol(df, Config_Path, ParamDict)

    #Get dictionary of which tests to apply
    TestDict = read_config('QC Tests', Config_Path)

    #Perform consistency and missing values tests
    for Param in Param_Range:
        #Run the test functions
        if TestDict['missing'] == 'true':
            df = QC_Miss(df, Param, ParamDict, QC = QC)

        if TestDict['range'] == 'true':
            df = QC_Range(df, Param, ParamDict, Config_Path, QC = QC)

        if TestDict['stat_range'] == 'true':
            df = QC_Stat_Range(df, Param, ParamDict, Config_Path, QC = QC)

        if TestDict['consistency'] == 'true':
            df = QC_Cons(df, Param, ParamDict, Config_Path, QC = QC)

        if TestDict['repeating'] == 'true':
            df = QC_Rep(df, Param, ParamDict, QC = QC)

        if TestDict['step'] == 'true':
            if Param in Param_Step:
                df = QC_Step(df, Param, ParamDict, Config_Path, QC = QC)

    #Label good obsevations accordingly
    df = df.replace(to_replace = '', value = 'Good')

    return df

def runme(Config_Path):

    #Read the data paths from the Local Config file
    Config_Path = Config_Path.decode('utf-8')
    PathDict = read_config('Paths', Config_Path)
    QC1_path = PathDict['qc1_path'].decode('utf-8')
    QC2_path = PathDict['qc2_path'].decode('utf-8')
    QC3_path = PathDict['qc3_path'].decode('utf-8')

    #Read data
    df = pd.read_csv(QC1_path, header = 0, index_col = 0)

    #Perfrom QC2
    df = QC2(df, Config_Path, QC = 'QC2')

    #Save QC2 data 
    df.to_csv(path_or_buf = QC2_path, index_label = 'time')

if __name__ == '__main__':
    Config_Path = sys.argv[1]
    runme(Config_Path)
