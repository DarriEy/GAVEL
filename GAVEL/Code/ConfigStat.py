# coding=utf-8
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ConfigParser
import os
import sys
from QC1 import ConfigSectionMap, read_config
Config = ConfigParser.ConfigParser() #initialize the config parser

def read_data(data_dir):

    #Get the paths to the datafiles
    data_paths = [data_dir + '\\' + file for file in os.listdir(data_dir) if '.csv' in file]

    #Setup the dataframe with the total time series
    df = pd.read_csv(data_paths[0], nrows = 0, index_col = 0, parse_dates = True)
    for file in data_paths:
        data = pd.read_csv(file, index_col = 0, parse_dates = True)
        df = df.append(data, sort = True)

    return df

def write_config(df, cols, config_dir):

    #Get the paths to the config files
    config_paths = [config_dir + '\\' + file for file in os.listdir(config_dir) if '.ini' in file]

    #loop over all the configuration files in the config directory
    for conf in config_paths:
        #Open the Configuration File
        with open(conf, 'r') as con_file:
            Lines = con_file.readlines()

        #loop over the lines in the configuration file
        for num, line in enumerate(Lines):

            #loop over the columns in the dataframe
            for col in cols:
                if col + '_max:' == str(line[0:(len(col)+5)]):
                    Lines[num] = col + '_max: ' + str(df[col].max()) + '\n'
                if col + '_min:' == str(line[0:(len(col)+5)]):
                    Lines[num] = col + '_min: ' + str(df[col].min()) + '\n'
                if col + '_avg:' == str(line[0:(len(col)+5)]):
                    Lines[num] = col + '_avg: ' + str(df[col].mean()) + '\n'
                if col + '_std:' == str(line[0:(len(col)+5)]):
                    Lines[num] = col + '_std: ' + str(df[col].std()) + '\n'

        with open(conf, 'w') as con_file:
            con_file.writelines(Lines)

#Fill inn missing obs based on the timedelta
def fill_obs(df):
    first = df.index.values[0]
    second = df.index.values[1]
    last = df.index.values[-1]
    delta = last - df.index.values[-2]

    real_index = pd.date_range(first, last, freq = delta.astype('timedelta64[m]').astype(str).replace(' ', '')[:-4])
    real_df = pd.DataFrame(np.nan, index = real_index, columns = df.columns)

    real_df.loc[df.index.values] = df

    return(real_df)

def runme(Config_Path):
    Config_Path = Config_Path.decode('utf-8')
    PathDict = read_config('Paths', Config_Path)

    #Define directories of data and config files
    data_dir = PathDict['data_dir'].decode('utf-8')
    config_dir = PathDict['config_dir'].decode('utf-8')
    big_df = PathDict['big_df'].decode('utf-8')

    #Read the data
    df = read_data(data_dir)

    #Get the column headers of the parameters we want to analyze
    cols = [c for c in df.columns if '_QCfin' not in c]

    #write the config files
    write_config(df, cols, config_dir)

    #Fill the dataset to 10 min resolution for the entire periods
    df = fill_obs(df)

    #Save the compiled database
    df.to_csv(big_df, index_label = 'time')

if __name__ == '__main__':
    Config_Path = sys.argv[1]
    runme(Config_Path)
