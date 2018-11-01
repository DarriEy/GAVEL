# coding=utf-8
import os
import ConfigParser
import logging
import datetime

Config = ConfigParser.ConfigParser() #initialize the config parser

#initialize logger
#logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#Create file handler for logger
now = datetime.datetime.now().strftime("%I%M%p_%d%B%Y")
handler = logging.FileHandler('LogFiles\GAVEL' + now + '.log')
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

# This code runs all the modules of the GAVEL Quality Control system given
# a local configuration file.

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

def run(Config_Paths):
    MetaDict = read_config('meta', Config_Path)

    # Loop through the python files for a given directory
    for Path in Config_Paths:
        logger.info('Running Local Config file: %s' %Path)
        QC1command = 'python ' + 'code\QC1.py' + ' ' + Path
        print QC1command
        os.system(QC1command.encode('utf-8'))
        logger.info('QC1 module executed')

        QC2command = 'python ' + 'code\QC2.py' + ' ' + Path
        os.system(QC2command.encode('utf-8'))
        logger.info('QC2 module executed')

        QCFincommand = 'python ' + 'code\QCFin.py' + ' ' + Path
        os.system(QCFincommand.encode('utf-8'))
        logger.info('QCFin module executed')

        PlotCommand = 'python ' + 'code\QCplot.py' + ' ' + Path
        os.system(PlotCommand.encode('utf-8'))
        logger.info('Plot module executed')

        Reportcommand = 'python ' + 'code\QCReport.py' + ' ' + Path
        os.system(Reportcommand.encode('utf-8'))
        logger.info('Report module executed')

    station = read_config('meta', Path)['station_name']
    # Update long term stats for the
    if MetaDict['update_stats'] == 'true':
        update_command = 'python ' + 'code\ConfigStat.py' + ' ' + Path
        os.system(update_command.encode('utf-8'))
        logger.info('Finished updating long term statistics for station: ' + station)

    logger.info('All config files read')

#Run single directory of config files
def run_sing(Config_Path):
    path = read_config('SingPath',Config_Path)['path']
    MetaDict = read_config('meta', Config_Path)

    os.chdir(MetaDict['gavel_dir'].decode('utf-8'))
    Station_dir = path.decode('utf-8')
    Config_dir = Station_dir + 'GAVEL\Config'
    Config_Paths = [Config_dir + '\\' + file for file in os.listdir(Config_dir) if '.ini' in file]

    run(Config_Paths)

#Run all local config files for all stations specified in Global Config file
def run_all(Config_Path):
    PathDict = read_config('DirPaths', Config_Path)
    MetaDict = read_config('meta', Config_Path)

    #Loop through all stations
    for station in PathDict.keys():
        print('-----------------------------------------------------')
        print('------Running GAVEL for station: %s------' %station)
        print('-----------------------------------------------------')

        logger.info('Running GAVEL for station: %s' %station)
        #Read and define station and config directory paths
        Station_dir = PathDict[station].decode('utf-8')
        Config_dir = Station_dir + 'GAVEL\Config'
        Config_Paths = [Config_dir + '\\' + file for file in os.listdir(Config_dir) if '.ini' in file]

        run(Config_Paths)

#Run list of config files
def run_list(Config_Path):
    ConDict = read_config('ConList', Config_Path)

    station_list = ConDict['station_list'].decode('utf-8').splitlines()

    run(station_list)

def runme(Config_Path):
    #Read the data paths from the Local Config file
    Config_Path = Config_Path.decode('utf-8')
    MetaDict = read_config('meta', Config_Path)

    logger.info('Read Global Configuration file at: %s' %Config_Path)

    #Read from global config whether to run all or specific stations
    if MetaDict['run_all'] == 'true':
        logger.info('Start running GAVEL for all stations')
        run_all(Config_Path)
    elif MetaDict['run_list'] == 'true':
        logger.info('Start running GAVEL for list of Configuration files')
        run_list(Config_Path)
    elif MetaDict['run_sing'] == 'true':
        logger.info('Start running GAVEL for all Configuration files in a directory')
        run_sing(Config_Path)
    else:
        logger.info('Path setting for GAVEL incorrect')
        print 'Specify whether to run all stations or specific instances'


if __name__ == '__main__':
    Config_Path = 'F:\Þróunarsvið\Rannsóknir\M-Sameign\GAVEL\GAVEL1\GAVEL\GloConfig_GAVEL.ini'
    runme(Config_Path)
