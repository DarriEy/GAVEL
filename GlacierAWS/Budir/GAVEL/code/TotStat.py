# coding=utf-8
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import ConfigParser
Config = ConfigParser.ConfigParser() #initialize the config parser

#Define name of station and path to the complete database
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

    Config_Path = Config_Path.decode('utf-8')
    PathDict = read_config('Paths', Config_Path)

    #Define directories of data and config files
    station_name =  read_config('meta', Config_Path)['station_name']
    Fin_DB = PathDict['qcfin_path'].decode('utf-8')
    sum_dir = PathDict['sum_dir'].decode('utf-8')
    #Fin_DB = u'F:\\Þróunarsvið\Rannsóknir\M-Sameign\GAVEL\GAVEL1\Mariutungur\Published\data\VST_Mariutungur_QCfin_ALL.dat'

    #Read the database and select parameters to investigate
    df = pd.read_csv(Fin_DB, index_col = 0, parse_dates = True)
    params = ['t', 'HS', 'd', 'f', 'sw_in', 'sw_out', 'rh', 'lw_in', 'lw_out']
    ParNames = ['Air_Temperature','Snow_Depth', 'Wind_Direction', 'Wind_Speed'
                , 'Short_Wave_Radiation_in', 'Short_Wave_Radiation_out', 'Relative_Humidity'
                , 'Long_Wave_Radiation_in', 'Long_Wave_Radiation_out']
    ParDict = dict(zip(params,ParNames))

    #Create summary directory
    #sum_dir = u'F:\\Þróunarsvið\Rannsóknir\M-Sameign\GAVEL\GAVEL1\Mariutungur\Published\\figures\Summary\\'
    try:
        os.makedirs(sum_dir)
    except:
        pass

    #loop through the paramters, get stats and plot figs
    for par in ParDict.keys():
        fig, ax = plt.subplots()
        df.resample('M').mean()[par].plot(ax = ax)
        ax.set_title(station_name + ': ' + ParDict[par])

        fig.savefig(sum_dir + '\\' + station_name + '_' + par + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

if __name__ == '__main__':
    Config_Path = sys.argv[1]
    runme(Config_Path)
