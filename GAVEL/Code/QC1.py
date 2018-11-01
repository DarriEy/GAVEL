# coding=utf-8
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ConfigParser
from Pysolar.solar import *
from Pysolar.radiation import *
import datetime
from datetime import timedelta
import os
import sys
Config = ConfigParser.ConfigParser() #initialize the config parser

'''
File name: QC1.py
Author: Darri Eyþórsson
Date Created: 15.08.2018
Date Last Modified: 2.10.2018
Python Version: 2.7
Version: 1.0
'''

#Read the data
def read_data(read_path, Config_Path):

    #Read data and create dataframe and parameter dictionaries
    ReadDict = read_config('Read_Data', Config_Path) #Get info on the setup of the datafile
    if ReadDict['header'] == 'true':
        if ReadDict['startdata'] != '':
            df = pd.read_csv(read_path, header =  int(ReadDict['headerrow']), skiprows = range(int(ReadDict['headerrow'])+1, int(ReadDict['startdata'])), index_col = 0, parse_dates = True, low_memory = False)
        else:
            df = pd.read_csv(read_path, header =  int(ReadDict['headerrow']), index_col = 0, parse_dates = True, low_memory = False)

    #Modify dataframe
    df = df[df.columns.values].astype(float)
    df = fill_obs(df, Config_Path) #Fill in dataframe with potential missing observations
    df = df.astype(float)
    if 'lw_in_c' in df.columns:
        df = df.rename({'lw_in_c': 'lw_in', 'lw_out_c': 'lw_out'}, axis = 'columns')

    return df

#Fill inn missing obs based on the timedelta
def fill_obs(df,Config_Path):

    MetaDict = read_config('meta', Config_Path)
    if MetaDict['timedelta'] == '10min':
        delta = np.timedelta64(10,'m')
    elif MetaDict['timedelta'] == '30min':
        delta = np.timedelta64(30,'m')
    elif MetaDict['timedelta'] == '1hr':
        delta = np.timedelta64(1,'h')
    elif MetaDict['timedelta'] == '1d':
        delta = np.timedelta64(24,'h')

    first = df.index.values[0]
    last = df.index.values[-1]

    real_index = pd.date_range(first, last, freq = delta.astype(str).replace(' ', '')[:-4])#.format(formatter = lambda x: x.strftime('%Y-%m-%d %H%M%s'))
    real_df = pd.DataFrame(np.nan, index = real_index, columns = df.columns)

    real_df.loc[df.index.values] = df

    return(real_df)

#Import QC0 data
def QC0Snow(df, HS_path, Config_Path):
    SnowDict = read_config('snow_depth', Config_Path)

    #Check if the snow measurements are in a seperate file, then read the data
    if HS_path != '':
        df_HS = pd.read_csv(HS_path, header =  int(SnowDict['headerrow']), skiprows = range(int(SnowDict['headerrow'])+1, int(SnowDict['startdata'])), index_col = 0, parse_dates = True)

        real_index = pd.date_range(df_HS.index.values[0], df_HS.index.values[-1], freq = '1T')
        real_df = pd.DataFrame(np.nan, index = real_index, columns = df_HS.columns)
        real_df.loc[df_HS.index.values] = df_HS
        real_df =  real_df['HS_q'].loc[df.index.values]
        df['HS_q'] = real_df.values


    #Remove all observations with QC0 results defined in the local parameter file
    if 'HS_q' in df.columns:
        df.loc[(df['HS_q'] > float(SnowDict['qc0lo'])) & (df['HS_q'] < float(SnowDict['qc0up'])), 'HS0'] = df['HS']
        df['HS'] = df['HS0']

    return df

#Get manual snow measurements
def SnoMan(df, df_Sno, Config_Path):

    df_Sno['year'] = read_config('meta', Config_Path)['year']
    df_Sno['date'] = pd.to_datetime(df_Sno['year'] + df_Sno['doy'].astype(int).astype(str), format = '%Y%j')

    df_Sno = df_Sno.set_index('date')
    del df_Sno['doy']
    del df_Sno['year']
    df['HSman'] = np.nan

    for index, row in df_Sno.iterrows():
        df_ReSno = pd.DataFrame([row[0], row[0]], index = [index, index + timedelta(days = 1)], columns = df_Sno.columns).resample('10Min').pad()
        for sno_index, sno_row in df_ReSno.iterrows():
            if sno_index in df.index:
                df['HSman'].loc[sno_index] = sno_row[0]
    return df

#Calculate the precip for each timestep if there is precip data
def calc_precip(df):
    if 'r' in df.columns:
        df['rt'] = df['r'].diff(1)
        df['rt'][df['rt'] < -10] = 0    # remove obs where gauge is emptied
    return df

#Calculate the theoretical solar radiation at given point in time
def sw_lims(df, lat, lon):

    S0 = 1368   #define average solar constant
    Sa = []
    mu0 = []

    for row in df.itertuples():
        Sa.append(S0/(1-0.01672*np.cos(np.deg2rad(0.9856*(row[0].timetuple().tm_yday-4))))**2)
        sza = float(90) - GetAltitude(lat , lon, row[0].to_pydatetime())
        if sza > 90:
            mu0.append(0)
            #mu0sza.append(0)
        else:
            mu0.append(np.cos(np.deg2rad(sza)))
            #mu0sza.append(np.cos(np.deg2rad(szasens)))

    #df['SZA'] = SZA
    df['Sa'] = Sa
    df['mu0'] = mu0
    df['max_glob'] = df['Sa']*1.5*df['mu0']**1.2+100
    df['max_diff'] = df['Sa']*0.95*df['mu0']**1.2+50
    df['max_direct'] = df['Sa']*df['mu0']
    df['max_up'] = df['Sa']*1.2*df['mu0']**1.2+50
    df['Diff_ratio'] = df['max_diff']/df['max_glob']

    if 'sw_in' and 'sw_out' in df.columns:
        df['Glob_sum_ratio'] = df['max_glob']/(df['sw_in']-df['sw_out'])

    del df['Sa']
    del df['mu0']

    return df

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
def read_config(Param, conf_file):
    Config.read(conf_file) #Read the Config ini file
    Config_dict = ConfigSectionMap(Param)
    return Config_dict

#Missing Data Test
def QC_Miss(df, Param, ParamDict, QC = 'QC1'):
    for para in ParamDict[Param]:
        df[para + '_' + QC] = ''
        df.loc[df[para].isnull(), para + '_' + QC] = '-m'
    return df

#Range Tests
def QC_Range(df, Param, ParamDict, Config_Path, QC = 'QC1'):
    # Read the config for Parameter specific info and metadata
    Config_dict = read_config(Param, Config_Path)
    Meta_dict = read_config('meta', Config_Path)

    if Meta_dict['timedelta'] == '1hr':
        td = 3
    elif Meta_dict['timedelta'] == '10min':
        td = 15
    elif Meta_dict['timedelta'] == '30min':
        td = 7
    else:
        td = 0

    if Param == 'short_wave_radiation_in':
        for para in ParamDict[Param]:
            df.loc[df[para] > df['max_glob'].shift(td), para + '_' + QC] = df[para + '_' + QC] + '-r1(c)'
            df.loc[(df['sw_in'] > 100) & (df[para] > df['max_diff'].shift(td)), para + '_' + QC] = df[para + '_' + QC] + '-r3(p)'
            df.loc[(df['sw_in'] > 100) & (df[para] > df['max_direct'].shift(td)), para + '_' + QC] = df[para + '_' + QC] + '-r4(p)'
            df.loc[df[para] < float(Config_dict['min']), para + '_' + QC] = df[para + '_' + QC] + '-r2(c)'

    elif Param == 'short_wave_radiation_out':
        for para in ParamDict[Param]:
            df.loc[df[para] > df['max_up'].shift(td), para + '_' + QC] = df[para + '_' + QC] + '-r1(c)'
            df.loc[df[para] < float(Config_dict['min']), para + '_' + QC] = df[para + '_' + QC] + '-r2(c)'

    elif Param == 'air_temperature':
        for para in ParamDict[Param]:
            df.loc[df[para] > (float(Config_dict['max']) - float(Config_dict['lapse'])*float(Meta_dict['elevation'])/1000), para + '_' + QC] = df[para + '_' + QC] + '-r1(c)'
            df.loc[df[para] < (float(Config_dict['min']) - float(Config_dict['lapse'])*float(Meta_dict['elevation'])/1000), para + '_' + QC] = df[para + '_' + QC] + '-r2(c)'

    elif Param == 'atmospheric_pressure':
        for para in ParamDict[Param]:
            baro_drop = 11.3 #drop in pressure by altitude Pa/m
            df.loc[df[para] > (float(Config_dict['max']) - baro_drop*float(Meta_dict['elevation'])/100), para + '_' + QC] = df[para + '_' + QC] + '-r1(c)'
            df.loc[df[para] < (float(Config_dict['min']) - baro_drop*float(Meta_dict['elevation'])/100), para + '_' + QC] = df[para + '_' + QC] + '-r2(c)'

    else:
        for para in ParamDict[Param]:
            df.loc[df[para] > float(Config_dict['max']), para + '_' + QC] = df[para + '_' + QC] + '-r1(c)'
            df.loc[df[para] < float(Config_dict['min']), para + '_' + QC] = df[para + '_' + QC] + '-r2(c)'

    return df

#Statistical Range Tests
def QC_Stat_Range(df, Param, ParamDict, Config_Path, QC = 'QC1'):
    # Read the config for Parameter specific info and metadata
    Config_dict = read_config(Param, Config_Path)
    StatsDict = read_config('QC Stats', Config_Path)

    if Param == 'wind_direction':
        pass
    elif Param == 'snow_depth':
        pass
    else:
        for para in ParamDict[Param]:
            #if para in df.columns:
            df.loc[df[para] > float(Config_dict[para.lower() + '_avg']) + float(StatsDict['stds'])*float(Config_dict[para.lower() + '_std']), para + '_' + QC] = df[para + '_' + QC] + '-r5(p)'
            df.loc[df[para] < float(Config_dict[para.lower() + '_avg']) - float(StatsDict['stds'])*float(Config_dict[para.lower() + '_std']), para + '_' + QC] = df[para + '_' + QC] + '-r6(p)'

    return df

#Step Tests
def QC_Step(df, Param, ParamDict, Config_Path, QC = 'QC1'):

    Config_dict = read_config(Param, Config_Path)
    for para in ParamDict[Param]:
        if para == 'HS':
            for num in range(1,3):
                df.loc[(abs(df[para].diff(num)) > float(Config_dict['maxdelta10m'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'
                df.loc[(abs(df[para].diff(-num)) > float(Config_dict['maxdelta10m'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'
            for num in range(3,9):
                df.loc[(abs(df[para].diff(num)) > float(Config_dict['maxdelta1h'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'
                df.loc[(abs(df[para].diff(-num)) > float(Config_dict['maxdelta1h'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'
            for num in range(9,15):
                df.loc[(abs(df[para].diff(num)) > float(Config_dict['maxdelta1h'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'
                df.loc[(abs(df[para].diff(-num)) > float(Config_dict['maxdelta1h'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'
            for num in range(15,25):
                df.loc[(abs(df[para].diff(num)) > float(Config_dict['maxdelta1h'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'
                df.loc[(abs(df[para].diff(-num)) > float(Config_dict['maxdelta1h'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'

            for num in range(1,10):
                df[para + '_' + QC] = df[para + '_' + QC].str.replace(r'-s1\(c\)-s1\(c\)', '-s1(c)')
                df[para + '_' + QC] = df[para + '_' + QC].str.replace(r'-s1\(c\)-s1\(c\)', '-s1(c)')

        else:
            #Test for stepsize in 10 min interval
            if read_config('meta', Config_Path)['timedelta'] == '10min':
                delta = Config_dict['maxdelta10m']
            else:
                delta = Config_dict['maxdelta1h']

            df.loc[(abs(df[para].diff(1)) > float(delta)), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'

    return df

#Test for repeating values
def QC_Rep(df, Param, ParamDict, QC = 'QC1'):
    if Param != 'snow_depth':
        for para in ParamDict[Param]:
            # Test for repeating values (more than 3 in a row)#
            df.loc[(df[para].diff(1) == 0) & (df[para].diff(2) == 0) & (df[para].diff(3) == 0), para + '_' + QC] = df[para + '_' + QC] + '-s2(p)'
    return df

#Consistency Tests
def QC_Cons(df, Param, ParamDict, Config_Path, QC = 'QC1'):
    # Read the config for Parameter specific info and metadata
    Config_dict = read_config(Param, Config_Path)
    Meta_dict = read_config('meta', Config_Path)

    if Param == 'air_temperature':
        if 'tx' and 'tn' in df.columns:
            df.loc[df['t'] > df['tx'], 't_' + QC] = df['t' + '_' + QC] + '-c1(c)'
            df.loc[df['t'] < df['tn'], 't_'+ QC] = df['t' + '_' + QC] + '-c2(c)'
            df.loc[df['tx'] < df['tn'], 't_'+ QC] = df['t' + '_' + QC] + '-c3(c)'
            df.loc[df['tx'] - df['t'] > float(Config_dict['k4']), 't_' + QC] = df['t' + '_' + QC] + '-c4(p)'
            df.loc[df['t'] - df['tn'] > float(Config_dict['k5']), 't_' + QC] = df['t' + '_' + QC] + '-c5(p)'
        if 't2' in df.columns:
            df.loc[abs(df['t'] - df['t2']) > float(Config_dict['k6']), 't_' + QC] = df['t' + '_' + QC] + '-c6(p)'

    elif Param == 'short_wave_radiation_out':
        if 'sw_in' and 'sw_out' in df.columns:
            #Compare internal consistency of sw_in and sw_out
            df.loc[(df['sw_in'] > 50) & (df['sw_in'] < df['sw_out']), 'sw_out_' + QC] = df['sw_out_' + QC] + '-c1(p)'

    elif Param == 'short_wave_radiation_in':
        if 'sw_in' and 'sw_out' in df.columns:
            #Compare internal consistency of sw_in and sw_out #
            df.loc[(df['sw_in'] > 50) & (df['sw_in'] < df['sw_out']), 'sw_in_' + QC] = df['sw_in_' + QC] + '-c1(p)'

    elif Param == 'long_wave_radiation_in':
        sbc = 0.00000005670367
        if 'lw_in' in df.columns:
            #Compare with theoretical maximum lw emission of blackbody #
            df.loc[df['lw_in'] < float(Config_dict['d1'])*((df['t']+273)**4)*sbc, 'lw_in_' + QC] = df['lw_in_' + QC] + '-c1(c)'
            df.loc[df['lw_in'] > ((df['t'] + 273)**4)*sbc + float(Config_dict['d2']), 'lw_in_' + QC] = df['lw_in_' + QC] + '-c1(c)'
            df.loc[df['lw_in'] < float(Config_dict['c1'])*((df['t']+273)**4)*sbc, 'lw_in_' + QC] = df['lw_in_' + QC] + '-c2(p)'
            df.loc[df['lw_in'] > ((df['t'] + 273)**4)*sbc + float(Config_dict['c2']), 'lw_in_' + QC] = df['lw_in_' + QC] + '-c2(p)'

    elif Param == 'long_wave_radiation_out':
        sbc = 0.00000005670367
        if 'lw_out' in df.columns:
            #Compare with theoretical maximum lw emission of blackbody
            df.loc[df['lw_out'] < sbc*((df['t'] + 273) - float(Config_dict['d3']))**4, 'lw_out_' + QC] = df['lw_out_' + QC] + '-c1(c)'
            df.loc[df['lw_out'] > sbc*((df['t'] + 273) + float(Config_dict['d4']))**4, 'lw_out_' + QC] = df['lw_out_' + QC] + '-c1(c)'
            df.loc[df['lw_out'] < sbc*((df['t'] + 273) - float(Config_dict['c3']))**4, 'lw_out_' + QC] = df['lw_out_' + QC] + '-c2(p)'
            df.loc[df['lw_out'] > sbc*((df['t'] + 273) + float(Config_dict['c4']))**4, 'lw_out_' + QC] = df['lw_out_' + QC] + '-c2(p)'

    elif Param == 'snow_depth':
        df.loc[(df['t'] > float(Config_dict['certt'])) & (df['HS'].diff(1) < 0), 'HS_' + QC] = df['HS_' + QC] + '-c1(c)'
        df.loc[(df['t'] > float(Config_dict['probt'])) & (df['HS'].diff(1) < 0), 'HS_' + QC] = df['HS_' + QC] + '-c2(p)'
    return df

# ---------  QC1 Module - Automated simple tests  ----------
def QC1(df, Config_Path, QC = 'QC1'):

    #Lists of Parameters to perform the QC tests on
    ParamDict = read_config('Parameters', Config_Path)
    for key in ParamDict:
        ParamDict[key] = ParamDict[key].split(',')
    Param_Range = ParamDict.keys() #Get the parameter names to perform Range, Missing value tests on
    Param_Step = ['air_temperature', 'wind_speed', 'atmospheric_pressure', 'snow_depth'] #Define list of parameters to do step test on

    # Calculate SW limits
    Meta_dict = read_config('meta', Config_Path)
    df = sw_lims(df, lat = float(Meta_dict['lat']), lon = float(Meta_dict['lon']))
    #Get dictionary of which tests to apply
    TestDict = read_config('QC Tests', Config_Path)
    #Perform consistency and missing values tests
    for Param in Param_Range:
        #Run the test functions
        if TestDict['missing'] == 'true':
            df = QC_Miss(df, Param, ParamDict)

        if TestDict['range'] == 'true':
            df = QC_Range(df, Param, ParamDict, Config_Path, QC = QC)

        '''
        if TestDict['stat_range'] == 'true':
            df = QC_Stat_Range(df, Param, ParamDict, Config_Path, QC = QC)
        '''

        if TestDict['consistency'] == 'true':
            df = QC_Cons(df, Param, ParamDict, Config_Path, QC = QC)

        if TestDict['repeating'] == 'true':
            df = QC_Rep(df, Param, ParamDict, QC = QC)

        if TestDict['step'] == 'true':
            if Param in Param_Step:
                df = QC_Step(df, Param, ParamDict, Config_Path, QC = QC)

    #Label good obsevations accordingly and print dataframe
    df = df.replace(to_replace = '', value = 'Good')

    return df

#Save the data
def save_data(df, save_path):
    df.to_csv(path_or_buf = save_path, index_label = 'time')

def runme(Config_Path):

    #Read the data paths from the Local Config file
    Config_Path = Config_Path.decode('utf-8')
    PathDict = read_config('Paths', Config_Path)

    #Extract the paths to use from the config file
    MET_path = PathDict['met_path'].decode('utf-8')
    HS_path = PathDict['hs_path'].decode('utf-8')
    SnoMan_path = PathDict['snoman_path'].decode('utf-8')
    QC1_path = PathDict['qc1_path'].decode('utf-8')

    #Read data
    df = read_data(MET_path, Config_Path)

    #Get QC0 and manual info for snow measurements
    df = QC0Snow(df, HS_path, Config_Path)

    #Module for working with manual snow measurements
    if SnoMan_path != '':
        df_Sno = pd.read_excel(SnoMan_path)
        df = SnoMan(df, df_Sno, Config_Path)

    #Perform QC1
    df = QC1(df, Config_Path, QC = 'QC1')

    #Save QC1 data
    save_data(df, QC1_path)

if __name__ == '__main__':
    Config_Path = sys.argv[1]
    runme(Config_Path)
