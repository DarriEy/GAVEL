# coding=utf-8
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ConfigParser
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

#Missing Data Test
def QC2_Miss(df, Param, ParamDict, QC = 'QC2'):
    for para in ParamDict[Param]:
        if para in df.columns:
            df[para + '_' + QC] = ''
            df.loc[df[para].isnull(), para + '_' + QC] = '-m'
    return df

#Range Tests
def QC2_Range(df, Param, ParamDict, Config_Path, QC = 'QC2'):
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
            df.loc[df[para] > df['max_diff'].shift(td), para + '_' + QC] = df[para + '_' + QC] + '-r3(p)'
            df.loc[(df['sw_in'] > 50) & (df[para] > df['max_direct'].shift(td)), para + '_' + QC] = df[para + '_' + QC] + '-r4(p)'
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
def QC2_Stat_Range(df, Param, ParamDict, Config_Path, QC = 'QC2'):
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
def QC2_Step(df, Param, ParamDict, Config_Path, QC = 'QC2'):

    Config_dict = read_config(Param, Config_Path)
    for para in ParamDict[Param]:
        if para == 'HS':
            for num in range(1,3):
                df.loc[(abs(df[para].diff(num)) > float(Config_dict['maxdelta10m'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'
                df.loc[(abs(df[para].diff(-num)) > float(Config_dict['maxdelta10m'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'
            for num in range(3,7):
                df.loc[(abs(df[para].diff(num)) > float(Config_dict['maxdelta1h'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'
                df.loc[(abs(df[para].diff(-num)) > float(Config_dict['maxdelta1h'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'

            df[para + '_' + QC] = df[para + '_' + QC].str.replace(r'-s1\(c\)-s1\(c\)', '-s1(c)')
            df[para + '_' + QC] = df[para + '_' + QC].str.replace(r'-s1\(c\)-s1\(c\)', '-s1(c)')

        else:
            #Test for stepsize in 10 min interval
            df.loc[(abs(df[para].diff(1)) > float(Config_dict['maxdelta10m'])), para + '_' + QC] = df[para + '_' + QC] + '-s1(c)'

    return df

#Test for repeating values
def QC2_Rep(df, Param, ParamDict, QC = 'QC2'):
    if Param != 'snow_depth':
        for para in ParamDict[Param]:
            if para in df.columns:
                # Test for repeating values (more than 3 in a row)#
                df.loc[(df[para].diff(1) == 0) & (df[para].diff(2) == 0) & (df[para].diff(3) == 0), para + '_' + QC] = df[para + '_' + QC] + '-s2(p)'
    return df

#Consistency Tests
def QC2_Cons(df, Param, ParamDict, Config_Path, QC = 'QC2'):
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

    if Param == 'short_awve_radiation_out':
        if 'sw_in' and 'sw_out' in df.columns:
            # Compare internal consistency of sw_in and sw_out #
            df.loc[(df['sw_in'] > 50) & (df['sw_in'] < df['sw_out']), 'sw_out_' + QC] = df['sw_out_' + QC] + '-c1(p)'

    if Param == 'short_wave_radiation_in':
        if 'sw_in' and 'sw_out' in df.columns:
            # Compare internal consistency of sw_in and sw_out #
            df.loc[(df['sw_in'] > 50) & (df['sw_in'] < df['sw_out']), 'sw_in_' + QC] = df['sw_in_' + QC] + '-c1(p)'

    if Param == 'long_wave_radiation_in':
        sbc = 0.00000005670367
        if 'lw_in' in df.columns:
            # Compare with theoretical maximum lw emission of blackbody #
            df.loc[df['lw_in'] < float(Config_dict['d1'])*((df['t']+273)**4)*sbc, 'lw_in_' + QC] = df['lw_in_' + QC] + '-c1(c)'
            df.loc[df['lw_in'] > ((df['t'] + 273)**4)*sbc + float(Config_dict['d2']), 'lw_in_' + QC] = df['lw_in_' + QC] + '-c1(c)'
            df.loc[df['lw_in'] < float(Config_dict['c1'])*((df['t']+273)**4)*sbc, 'lw_in_' + QC] = df['lw_in_' + QC] + '-c2(p)'
            df.loc[df['lw_in'] > ((df['t'] + 273)**4)*sbc + float(Config_dict['c2']), 'lw_in_' + QC] = df['lw_in_' + QC] + '-c2(p)'

    if Param == 'long_wave_radiation_out':
        sbc = 0.00000005670367
        if 'lw_out' in df.columns:
            # Compare with theoretical maximum lw emission of blackbody #
            df.loc[df['lw_out'] < sbc*((df['t'] + 273) - float(Config_dict['d3']))**4, 'lw_out_' + QC] = df['lw_out_' + QC] + '-c1(c)'
            df.loc[df['lw_out'] > sbc*((df['t'] + 273) + float(Config_dict['d4']))**4, 'lw_out_' + QC] = df['lw_out_' + QC] + '-c1(c)'
            df.loc[df['lw_out'] < sbc*((df['t'] + 273) - float(Config_dict['c3']))**4, 'lw_out_' + QC] = df['lw_out_' + QC] + '-c2(p)'
            df.loc[df['lw_out'] > sbc*((df['t'] + 273) + float(Config_dict['c4']))**4, 'lw_out_' + QC] = df['lw_out_' + QC] + '-c2(p)'

    if Param == 'snow_depth':
        if 'HS' in df.columns:
            df.loc[(df['t'] > float(Config_dict['certt'])) & (df['HS'].diff(1) > 0), 'HS_' + QC] = df['HS_' + QC] + '-c1(c)'
            df.loc[(df['t'] > float(Config_dict['probt'])) & (df['HS'].diff(1) > 0), 'HS_' + QC] = df['HS_' + QC] + '-c2(p)'

    return df

#Remove errors flagged as certain
def rem_cert(df):
    for col in df.columns:
        if '_QC1' in col:
            df.loc[df[col].str.contains(r'\(c\)'), col[:-4]] = np.nan # replace certain errors
    return df

#interpolate small gaps
def interpol(df, Config_Path, ParamDict):

    Config_dict = read_config('QC2_Parameters', Config_Path)
    method = Config_dict['ipolmtd']

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
def QC2(df, Config_Path):
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
            df = QC2_Miss(df, Param, ParamDict, QC = 'QC2')

        if TestDict['range'] == 'true':
            df = QC2_Range(df, Param, ParamDict, Config_Path, QC = 'QC2')

        if TestDict['stat_range'] == 'true':
            df = QC2_Stat_Range(df, Param, ParamDict, Config_Path, QC = 'QC2')

        if TestDict['consistency'] == 'true':
            df = QC2_Cons(df, Param, ParamDict, Config_Path, QC = 'QC2')

        if TestDict['repeating'] == 'true':
            df = QC2_Rep(df, Param, ParamDict, QC = 'QC2')

        if TestDict['step'] == 'true':
            if Param in Param_Step:
                df = QC2_Step(df, Param, ParamDict, Config_Path, QC = 'QC2')

    #Label good obsevations accordingly
    df = df.replace(to_replace = '', value = 'Good')

    return df

def runme(Config_Path):

    #Read the data paths from the Local Config file
    Config_Path = Config_Path.decode('utf-8')
    PathDict = read_config('Paths', Config_Path)
    QC1_path = PathDict['qc1_path'].decode('utf-8')
    QC2_path = PathDict['qc2_path'].decode('utf-8')

    #Read data
    df = pd.read_csv(QC1_path, header = 0, index_col = 0)

    #Perfrom QC2
    df = QC2(df, Config_Path)

    #Save QC2 data #
    df.to_csv(path_or_buf = QC2_path, index_label = 'time')

if __name__ == '__main__':
    #Config_Path = 'F:\Þróunarsvið\Rannsóknir\M-Sameign\GAVEL\GAVEL1\B13\GAVEL\Config\LocConfig_B13_2016.ini'
    if sys.argv[1] != '':
        Config_Path = sys.argv[1]
    runme(Config_Path)
