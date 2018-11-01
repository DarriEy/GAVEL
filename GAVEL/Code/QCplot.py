# coding=utf-8
import numpy as np
import pandas as pd
import os
import ConfigParser
import matplotlib.pyplot as plt
from windrose import WindroseAxes, plot_windrose
import sys
Config = ConfigParser.ConfigParser() #initialize the config parser
from scipy.signal import savgol_filter
import warnings
import errno
from QC1 import fill_obs, ConfigSectionMap, read_config, read_data
from QCFin import SGF, flatten

'''
Module to plot GAVEL QC results
File name: QC1.py
Author: Darri Eythorsson
Date Created: 26.10.2018
Date Last Modified: 26.10.2018
Python Version: 2.7
Version: 1.0
'''

plotsz = (11.69, 3)
plotsz2 = (23, 12)

def plot_flags(df, param, ax, QC, RepDict):
    #Plot all flagged datapoints in t '''
    prob_color = '#ffa500'
    cert_color = '#ff0000'
    for key in  df.groupby(param + '_' + QC).groups.keys():
        if '(c)' in key:
            #Plot Certain Errors in Red
            dates = df.groupby(param + '_' + QC).groups[key].values
            values = df.loc[df.groupby(param + '_' + QC).groups[key]][param].values
            df.ix[dates, 'Certain Errors' + key] = values

            df['Certain Errors' + key].plot(ax = ax, color = cert_color, linewidth = 5, marker = 'o')
            del df['Certain Errors' + key]
            cert_color = '#' + hex(int(cert_color[1:], 16) - 500000)[2:]

        elif '(p)' in key:
            if RepDict['prob_plot'] == 'true':
                #Plot possible Errors in Orange
                dates = df.groupby(param + '_' + QC).groups[key].values
                values = df.loc[df.groupby(param + '_' + QC).groups[key]][param].values
                df.ix[dates, 'possible Errors' + key] = values

                df['possible Errors' + key].plot(ax = ax, color = prob_color, linewidth = 5, marker = '*')
                del df['possible Errors' + key]
                prob_color = '#' + hex(int(prob_color[1:], 16) - 500000)[2:]

#Functions to plot parameter info
def Temp_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir):

    #Get metadata and report configurations from local config file
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)

    #Run through all the recorded temperature paramters
    for par in read_config('Parameters', Config_Path)['air_temperature'].split(','):
        #Plot temperature with qc1 labels
        fig1, ax1 = plt.subplots()
        ax1.set_title(MetaDict['station_name'] + ': Temperature ' + par + ' QC1')
        ax1.set_ylabel(read_config('Units', Config_Path)['air_temperature'].split(',')[0])
        ax1.set_xlabel('')
        df_q1[par].plot(ax = ax1, color = 'blue')
        #Plot the QC flags from QC1
        plot_flags(df = df_q1, param = par, ax = ax1, QC = 'QC1', RepDict = RepDict)
        ax1.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig1.set_size_inches(plotsz)    #Save the figure
        fig1.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q1.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot temperature with QC2 labels
        fig2, ax2 = plt.subplots()
        ax2.set_title(MetaDict['station_name'] + ': Temperature ' + par + ' QC2 ')
        ax2.set_ylabel(read_config('Units', Config_Path)['air_temperature'].split(',')[0])
        ax2.set_xlabel('')
        df_q2[par].plot(ax = ax2, color = 'blue')
        #plot other temperature variables if available
        plot_flags(df = df_q2, param = par, ax = ax2, QC = 'QC2', RepDict = RepDict)
        ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig2.set_size_inches(plotsz)    #Save the figure
        fig2.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q2.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot temperature with QC3 edits
        fig3, ax3 = plt.subplots()
        ax3.set_title(MetaDict['station_name'] + ': Temperature ' + par + ' QC2 ')
        ax3.set_ylabel(read_config('Units', Config_Path)['air_temperature'].split(',')[0])
        ax3.set_xlabel('')
        df_q3[par].plot(ax = ax3, color = 'red', label = 'QC2 data')
        df_fin[par].plot(ax = ax3, color = 'blue', label = 'Edited (HQC) data')
        #plot other temperature variables if available
        ax3.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig3.set_size_inches(plotsz)    #Save the figure
        fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q3e.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        plt.close('all')

def Hum_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir):
    #Get metadata and report configurations from local config file
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)

    #loop through all the recorded humidity parameters
    for par in read_config('Parameters', Config_Path)['humidity'].split(','):
        #plot humidity with QC1 labels
        fig1, ax1 = plt.subplots()
        ax1.set_title(MetaDict['station_name'] + ': Humidity ' + par + ' QC1')
        ax1.set_ylabel(read_config('Units', Config_Path)['humidity'].split(',')[0])
        ax1.set_xlabel('')
        df_q1[par].plot(ax = ax1, color = 'blue')
        #Plot qc flags for QC1
        plot_flags(df = df_q1, param = par, ax = ax1, QC ='QC1', RepDict = RepDict)
        ax1.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig1.set_size_inches(plotsz)    #Save the figure
        fig1.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q1.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot humidity with QC2 labels
        fig2, ax2 = plt.subplots()
        ax2.set_title(MetaDict['station_name'] + ': Humidity ' + par + ' QC2"')
        ax2.set_ylabel(read_config('Units', Config_Path)['humidity'].split(',')[0])
        ax2.set_xlabel('')
        df_q2[par].plot(ax = ax2, color = 'blue')
        #Plot qc flags for QC2
        plot_flags(df = df_q2, param = par, ax = ax2, QC ='QC2', RepDict = RepDict)
        ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig2.set_size_inches(plotsz)    #Save the figure
        fig2.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q2.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot temperature with QC3 edits
        fig3, ax3 = plt.subplots()
        ax3.set_title(MetaDict['station_name'] + ': Humidity ' + par + ' QC2 ')
        ax3.set_ylabel(read_config('Units', Config_Path)['humidity'].split(',')[0])
        ax3.set_xlabel('')
        df_q3[par].plot(ax = ax3, color = 'red', label = 'QC2 data')
        df_fin[par].plot(ax = ax3, color = 'blue', label = 'Edited (HQC) data')
        #plot other temperature variables if available
        ax3.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig3.set_size_inches(plotsz)    #Save the figure
        fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q3e.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')


        plt.close('all')

def Press_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir):
    #Get metadata and report configurations from local config file
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)

    #loop through all the recorded Pressure parameters
    for par in read_config('Parameters', Config_Path)['atmospheric_pressure'].split(','):
        #plot humidity with QC1 labels
        fig1, ax1 = plt.subplots()
        ax1.set_title(MetaDict['station_name'] + ': Atmospheric Pressure ' + par + ' QC1')
        ax1.set_ylabel(read_config('Units', Config_Path)['atmospheric_pressure'].split(',')[0])
        ax1.set_xlabel('')
        df_q1[par].plot(ax = ax1, color = 'blue')
        #Plot qc flags for QC1
        plot_flags(df = df_q1, param = par, ax = ax1, QC ='QC1', RepDict = RepDict)
        ax1.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig1.set_size_inches(plotsz)    #Save the figure
        fig1.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q1.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot humidity with QC2 labels
        fig2, ax2 = plt.subplots()
        ax2.set_title(MetaDict['station_name'] + ': Atmospheric Pressure ' + par + ' QC2')
        ax2.set_ylabel(read_config('Units', Config_Path)['atmospheric_pressure'].split(',')[0])
        ax2.set_xlabel('')
        df_q2[par].plot(ax = ax2, color = 'blue')
        #Plot qc flags for QC2
        plot_flags(df = df_q2, param = par, ax = ax2, QC ='QC2', RepDict = RepDict)
        ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig2.set_size_inches(plotsz)    #Save the figure
        fig2.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q2.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot temperature with QC3 edits
        fig3, ax3 = plt.subplots()
        ax3.set_title(MetaDict['station_name'] + ': Atmospheric Pressure ' + par + ' QC2 ')
        ax3.set_ylabel(read_config('Units', Config_Path)['atmospheric_pressure'].split(',')[0])
        ax3.set_xlabel('')
        df_q3[par].plot(ax = ax3, color = 'red', label = 'QC2 data')
        df_fin[par].plot(ax = ax3, color = 'blue', label = 'Edited (HQC) data')
        #plot other temperature variables if available
        ax3.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig3.set_size_inches(plotsz)    #Save the figure
        fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q3e.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        plt.close('all')

def Wind_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir):
    #Get metadata and report configurations from local config file
    warnings.simplefilter('ignore', RuntimeWarning)
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)

    #Plot wind speed with qc labels
    for par in read_config('Parameters', Config_Path)['wind_speed'].split(','):
        fig1, ax1 = plt.subplots()
        ax1.set_title(MetaDict['station_name'] + ': Wind Speed ' + par + ' QC1')
        ax1.set_ylabel(read_config('Units', Config_Path)['wind_speed'].split(',')[0])
        ax1.set_xlabel('')
        df_q1[par].plot(ax = ax1, color = 'blue', label = 'Wind Speed')
        #Plot qc flags for QC1
        plot_flags(df = df_q1, param = par, ax = ax1, QC ='QC1', RepDict = RepDict)
        ax1.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig1.set_size_inches(plotsz)    #Save the figure
        fig1.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q1.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot humidity with QC2 labels
        fig2, ax2 = plt.subplots()
        ax2.set_title(MetaDict['station_name'] + ': Wind Speed ' + par + ' QC2"')
        ax2.set_ylabel(read_config('Units', Config_Path)['wind_speed'].split(',')[0])
        ax2.set_xlabel('')
        df_q2[par].plot(ax = ax2, color = 'blue', label = 'Wind Speed')
        #Plot qc flags for QC2
        plot_flags(df = df_q2, param = par, ax = ax2, QC ='QC2', RepDict = RepDict)
        ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig2.set_size_inches(plotsz)    #Save the figure
        fig2.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q2.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot temperature with QC3 edits
        fig3, ax3 = plt.subplots()
        ax3.set_title(MetaDict['station_name'] + ': Wind Speed ' + par + ' QC2 ')
        ax3.set_ylabel(read_config('Units', Config_Path)['wind_speed'].split(',')[0])
        ax3.set_xlabel('')
        df_q3[par].plot(ax = ax3, color = 'red', label = 'QC2 data')
        df_fin[par].plot(ax = ax3, color = 'blue', label = 'Edited (HQC) data')
        #plot other temperature variables if available
        ax3.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig3.set_size_inches(plotsz)    #Save the figure
        fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q3e.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')


        plt.close('all')

    #Plot Wind Rose for QC1 data
    fig3 = plt.figure()
    ax3 = WindroseAxes.from_ax(fig = fig3)
    ax3.bar(df_q1['d'], df_q1['f'], normed=True, opening=0.8, edgecolor='white')
    ax3.set_legend(title = 'Wind speed [m/s]')
    ax3.legend(title = 'Wind Speed')
    fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_wind_rose_' + MetaDict['year'] + '_q1.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    #Plot wind speed with qc1 labels
    for par in read_config('Parameters', Config_Path)['wind_direction'].split(','):
        fig1, ax1 = plt.subplots()
        ax1.set_title(MetaDict['station_name'] + ': Wind Direction ' + par + ' QC1')
        ax1.set_ylabel(read_config('Units', Config_Path)['wind_direction'].split(',')[0])
        ax1.set_xlabel('')
        df_q2[par].plot(ax = ax1, color = 'blue', label = 'Wind Direction')
        #Plot qc flags for QC1
        plot_flags(df = df_q1, param = par, ax = ax1, QC ='QC1', RepDict = RepDict)
        ax1.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig1.set_size_inches(plotsz)    #Save the figure
        fig1.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q1.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot humidity with QC2 labels
        fig2, ax2 = plt.subplots()
        ax2.set_title(MetaDict['station_name'] + ': Wind Direction ' + par + ' QC2"')
        ax2.set_ylabel(read_config('Units', Config_Path)['wind_direction'].split(',')[0])
        ax2.set_xlabel('')
        df_q2[par].plot(ax = ax2, color = 'blue', label = 'Wind Direction')
        #Plot qc flags for QC2
        plot_flags(df = df_q2, param = par, ax = ax2, QC ='QC2', RepDict = RepDict)
        ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig2.set_size_inches(plotsz)    #Save the figure
        fig2.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q2.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot temperature with QC3 edits
        fig3, ax3 = plt.subplots()
        ax3.set_title(MetaDict['station_name'] + ': Wind Direction ' + par + ' QC2 ')
        ax3.set_ylabel(read_config('Units', Config_Path)['wind_direction'].split(',')[0])
        ax3.set_xlabel('')
        df_q3[par].plot(ax = ax3, color = 'red', label = 'QC2 data')
        df_fin[par].plot(ax = ax3, color = 'blue', label = 'Edited (HQC) data')
        #plot other temperature variables if available
        ax3.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig3.set_size_inches(plotsz)    #Save the figure
        fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q3e.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        plt.close('all')

    #Plot wind rose for QC2 data
    fig4 = plt.figure()
    ax4 = WindroseAxes.from_ax(fig = fig4)
    ax4.bar(df_fin['d'], df_fin['f'], normed=True, opening=0.8, edgecolor='white')
    ax4.set_legend(title = 'Wind speed [m/s]')
    ax4.legend(title = 'Wind Speed')
    fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_wind_rose_' + MetaDict['year'] + '_q3.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

def LW_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir):
        MetaDict = read_config('meta', Config_Path)
        RepDict = read_config('Report Config', Config_Path)

        #Calculate max and min long wave radiation based on max and min temps and blackbody assumption
        stbc = 0.00000005670367
        lwmin = ((-40+273)**4)*stbc #read_config('Long_Wave_Radiation')['min']
        lwmax = ((40+273)**4)*stbc #read_config('Long_Wave_Radiation')['max']
        df_q1['lw_theo'] = ((df_q1['t']+273)**4)*stbc
        df_q1['lw_in_theo_lower_1st'] = float(read_config('long_wave_radiation_in', Config_Path)['d1'])*((df_q1['t']+273)**4)*stbc
        df_q1['lw_in_theo_upper_1st'] = ((df_q1['t']+273)**4)*stbc + float(read_config('long_wave_radiation_in', Config_Path)['d2'])
        df_q1['lw_out_theo_lower_1st'] = stbc*((df_q1['t'] + 273) - float(read_config('long_wave_radiation_out', Config_Path)['d3']))**4
        df_q1['lw_out_theo_upper_1st'] = stbc*((df_q1['t'] + 273) + float(read_config('long_wave_radiation_out', Config_Path)['d4']))**4
        df_q1['lw_in_theo_lower_2nd'] = float(read_config('long_wave_radiation_in', Config_Path)['c1'])*((df_q1['t']+273)**4)*stbc
        df_q1['lw_in_theo_upper_2nd'] = ((df_q1['t']+273)**4)*stbc + float(read_config('long_wave_radiation_in', Config_Path)['c2'])
        df_q1['lw_out_theo_lower_2nd'] = stbc*((df_q1['t'] + 273) - float(read_config('long_wave_radiation_out', Config_Path)['c3']))**4
        df_q1['lw_out_theo_upper_2nd'] = stbc*((df_q1['t'] + 273) + float(read_config('long_wave_radiation_out', Config_Path)['c4']))**4

        #Run through all the recorded temperature paramters
        for par in read_config('Parameters', Config_Path)['long_wave_radiation_in'].split(','):
            #Plot temperature with qc1 labels
            fig1, ax1 = plt.subplots()
            ax1.set_title(MetaDict['station_name'] + ': Long Wave Radiation In ' + par + ' QC1')
            ax1.set_ylabel(read_config('Units', Config_Path)['long_wave_radiation_in'].split(',')[0])
            ax1.set_xlabel('')
            df_q1[par].plot(ax = ax1, color = 'blue', label = 'Long Wave Radiation In')
            df_q1['lw_theo'].plot(ax = ax1, color = 'black', linestyle = '--', label = 'Theoretical lw')
            df_q1['lw_in_theo_lower_1st'].plot(ax = ax1, color = 'black', linestyle = ':', label = '1st level')
            df_q1['lw_in_theo_upper_1st'].plot(ax = ax1, color = 'black', linestyle = ':', label = '')
            df_q1['lw_in_theo_lower_2nd'].plot(ax = ax1, color = 'grey', linestyle = ':', label = '2nd level')
            df_q1['lw_in_theo_upper_2nd'].plot(ax = ax1, color = 'grey', linestyle = ':', label = '')
            #Plot the QC flags from QC1
            plot_flags(df = df_q1, param = par, ax = ax1, QC = 'QC1', RepDict = RepDict)
            ax1.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
            fig1.set_size_inches(plotsz)    #Save the figure
            fig1.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q1.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

            #plot data with QC2 labels
            #plot temperature with QC2 labels
            fig2, ax2 = plt.subplots()
            ax2.set_title(MetaDict['station_name'] + ': Long Wave Radiation In ' + par + ' QC2 ')
            ax2.set_ylabel(read_config('Units', Config_Path)['long_wave_radiation_in'].split(',')[0])
            ax2.set_xlabel('')
            df_q2[par].plot(ax = ax2, color = 'blue', label = 'Long Wave Radiation In')
            df_q1['lw_theo'].plot(ax = ax2, color = 'black', linestyle = '--', label = 'Theoretical lw')
            df_q1['lw_in_theo_lower_1st'].plot(ax = ax2, color = 'black', linestyle = ':', label = '1st level')
            df_q1['lw_in_theo_upper_1st'].plot(ax = ax2, color = 'black', linestyle = ':', label = '')
            df_q1['lw_in_theo_lower_2nd'].plot(ax = ax2, color = 'grey', linestyle = ':', label = '2nd level')
            df_q1['lw_in_theo_upper_2nd'].plot(ax = ax2, color = 'grey', linestyle = ':', label = '')
            #plot other temperature variables if available
            plot_flags(df = df_q2, param = par, ax = ax2, QC = 'QC2', RepDict = RepDict)
            ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
            fig2.set_size_inches(plotsz)    #Save the figure
            fig2.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q2.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

            #plot temperature with QC3 edits
            fig3, ax3 = plt.subplots()
            ax3.set_title(MetaDict['station_name'] + ': Long Wave Radiation In ' + par + ' QC2 ')
            ax3.set_ylabel(read_config('Units', Config_Path)['long_wave_radiation_in'].split(',')[0])
            ax3.set_xlabel('')
            df_q3[par].plot(ax = ax3, color = 'red', label = 'QC2 data')
            df_fin[par].plot(ax = ax3, color = 'blue', label = 'Edited (HQC) data')
            #plot other temperature variables if available
            ax3.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
            fig3.set_size_inches(plotsz)    #Save the figure
            fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q3e.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')


            plt.close('all')

        #Run through all the recorded temperature paramters
        for par in read_config('Parameters', Config_Path)['long_wave_radiation_out'].split(','):
            #Plot temperature with qc1 labels
            fig1, ax1 = plt.subplots()
            ax1.set_title(MetaDict['station_name'] + ': Long Wave Radiation Out ' + par + ' QC1')
            ax1.set_ylabel(read_config('Units', Config_Path)['long_wave_radiation_out'].split(',')[0])
            ax1.set_xlabel('')
            df_q1[par].plot(ax = ax1, color = 'blue', label = 'Long Wave Radiation Out')
            df_q1['lw_theo'].plot(ax = ax1, color = 'black', linestyle = '--', label = 'Theoretical lw')
            df_q1['lw_in_theo_lower_1st'].plot(ax = ax1, color = 'black', linestyle = ':', label = '1st level')
            df_q1['lw_in_theo_upper_1st'].plot(ax = ax1, color = 'black', linestyle = ':', label = '')
            df_q1['lw_in_theo_lower_2nd'].plot(ax = ax1, color = 'grey', linestyle = ':', label = '2nd level')
            df_q1['lw_in_theo_upper_2nd'].plot(ax = ax1, color = 'grey', linestyle = ':', label = '')
            #Plot the QC flags from QC1
            plot_flags(df = df_q1, param = par, ax = ax1, QC = 'QC1', RepDict = RepDict)
            ax1.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
            fig1.set_size_inches(plotsz)    #Save the figure
            fig1.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q1.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

            #plot data with QC2 labels
            #plot temperature with QC2 labels
            fig2, ax2 = plt.subplots()
            ax2.set_title(MetaDict['station_name'] + ': Long Wave Radiation Out ' + par + ' QC2 ')
            ax2.set_ylabel(read_config('Units', Config_Path)['long_wave_radiation_out'].split(',')[0])
            ax2.set_xlabel('')
            df_q2[par].plot(ax = ax2, color = 'blue', label = 'Long Wave Radiation Out')
            df_q1['lw_theo'].plot(ax = ax2, color = 'black', linestyle = '--', label = 'Theoretical lw')
            df_q1['lw_in_theo_lower_1st'].plot(ax = ax2, color = 'black', linestyle = ':', label = '1st level')
            df_q1['lw_in_theo_upper_1st'].plot(ax = ax2, color = 'black', linestyle = ':', label = '')
            df_q1['lw_in_theo_lower_2nd'].plot(ax = ax2, color = 'grey', linestyle = ':', label = '2nd level')
            df_q1['lw_in_theo_upper_2nd'].plot(ax = ax2, color = 'grey', linestyle = ':', label = '')
            #plot other temperature variables if available
            plot_flags(df = df_q2, param = par, ax = ax2, QC = 'QC2', RepDict = RepDict)
            ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
            fig2.set_size_inches(plotsz)    #Save the figure
            fig2.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q2.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

            #plot temperature with QC3 edits
            fig3, ax3 = plt.subplots()
            ax3.set_title(MetaDict['station_name'] + ': Long Wave Radiation Out ' + par + ' QC2 ')
            ax3.set_ylabel(read_config('Units', Config_Path)['long_wave_radiation_out'].split(',')[0])
            ax3.set_xlabel('')
            df_q3[par].plot(ax = ax3, color = 'red', label = 'QC2 data')
            df_fin[par].plot(ax = ax3, color = 'blue', label = 'Edited (HQC) data')
            #plot other temperature variables if available
            ax3.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
            fig3.set_size_inches(plotsz)    #Save the figure
            fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q3e.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

            plt.close('all')

def SW_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir):
    #Get metadata and report configurations from local config file
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)

    #Define time to shift theoretical time series due to time zone difference
    if MetaDict['timedelta'] == '1hr':
        td = 3
    elif MetaDict['timedelta'] == '10min':
        td = 15
    elif MetaDict['timedelta'] == '30min':
        td = 7
    else:
        td = 0

    for par in read_config('Parameters', Config_Path)['short_wave_radiation_in'].split(','):
        #Plot temperature with qc1 labels
        fig1, ax1 = plt.subplots()
        ax1.set_title(MetaDict['station_name'] + ': Short Wave Radiation In ' + par + ' QC1')
        ax1.set_ylabel(read_config('Units', Config_Path)['short_wave_radiation_in'].split(',')[0])
        ax1.set_xlabel('')
        df_q1[par].plot(ax = ax1, color = 'blue')
        df_q1['max_direct'].shift(td).plot(ax = ax1, style =  ':', color = 'grey', label = 'Maximum direct SW', linewidth = 0.5)
        df_q1['max_diff'].shift(td).plot(ax = ax1, style =  '--', color = 'grey', label = 'Maximum diffusive SW', linewidth = 0.5)
        df_q1['max_glob'].shift(td).plot(ax = ax1, style =  '-', color = 'grey', label = 'Maximum global SW', linewidth = 0.5)

        #Plot the QC flags from QC1
        plot_flags(df = df_q1, param = par, ax = ax1, QC = 'QC1', RepDict = RepDict)
        ax1.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig1.set_size_inches(plotsz)    #Save the figure
        fig1.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q1.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot temperature with QC2 labels
        fig2, ax2 = plt.subplots()
        ax2.set_title(MetaDict['station_name'] + ': Short Wave Radiation In ' + par + ' QC2 ')
        ax2.set_ylabel(read_config('Units', Config_Path)['short_wave_radiation_in'].split(',')[0])
        ax2.set_xlabel('')
        df_q2[par].plot(ax = ax2, color = 'blue')
        df_q1['max_direct'].shift(td).plot(ax = ax2, style =  ':', color = 'grey', label = 'Maximum direct SW', linewidth = 0.5)
        df_q1['max_diff'].shift(td).plot(ax = ax2, style =  '--', color = 'grey', label = 'Maximum diffusive SW', linewidth = 0.5)
        df_q1['max_glob'].shift(td).plot(ax = ax2, style =  '-', color = 'grey', label = 'Maximum global SW', linewidth = 0.5)

        #plot other temperature variables if available
        plot_flags(df = df_q2, param = par, ax = ax2, QC = 'QC2', RepDict = RepDict)
        ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig2.set_size_inches(plotsz)    #Save the figure
        fig2.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q2.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot temperature with QC3 edits
        fig3, ax3 = plt.subplots()
        ax3.set_title(MetaDict['station_name'] + ': Short Wave Radiation In ' + par + ' QC2 ')
        ax3.set_ylabel(read_config('Units', Config_Path)['short_wave_radiation_in'].split(',')[0])
        ax3.set_xlabel('')
        df_q3[par].plot(ax = ax3, color = 'red', label = 'QC2 data')
        df_fin[par].plot(ax = ax3, color = 'blue', label = 'Edited (HQC) data')
        #plot other temperature variables if available
        ax3.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig3.set_size_inches(plotsz)    #Save the figure
        fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q3e.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        plt.close('all')

    if 'sw_out' in df_q1.columns:

        for par in read_config('Parameters', Config_Path)['short_wave_radiation_out'].split(','):
            #Plot temperature with qc1 labels
            fig1, ax1 = plt.subplots()
            ax1.set_title(MetaDict['station_name'] + ': Short Wave Radiation Out ' + par + ' QC1')
            ax1.set_ylabel(read_config('Units', Config_Path)['short_wave_radiation_out'].split(',')[0])
            ax1.set_xlabel('')
            df_q1[par].plot(ax = ax1, color = 'blue', label = 'Short Wave Radiation Out')
            df_q1['sw_in'].plot(ax = ax1, label = 'Short Wave Radiation In')
            df_q1['max_direct'].shift(td).plot(ax = ax1, style =  ':', color = 'grey', label = 'Maximum direct SW', linewidth = 0.5)
            df_q1['max_diff'].shift(td).plot(ax = ax1, style =  '--', color = 'grey', label = 'Maximum diffusive SW', linewidth = 0.5)
            df_q1['max_glob'].shift(td).plot(ax = ax1, style =  '-', color = 'grey', label = 'Maximum global SW', linewidth = 0.5)

            #Plot the QC flags from QC1
            plot_flags(df = df_q1, param = par, ax = ax1, QC = 'QC1', RepDict = RepDict)
            ax1.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
            fig1.set_size_inches(plotsz)    #Save the figure
            fig1.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q1.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

            #plot temperature with QC2 labels
            fig2, ax2 = plt.subplots()
            ax2.set_title(MetaDict['station_name'] + ': Short Wave Radiation Out ' + par + ' QC2 ')
            ax2.set_ylabel(read_config('Units', Config_Path)['short_wave_radiation_out'].split(',')[0])
            ax2.set_xlabel('')
            df_q2[par].plot(ax = ax2, color = 'blue', label = 'Short Wave Radiation Out')
            df_q2['sw_in'].plot(ax = ax1, label = 'Short Wave Radiation In')
            df_q2['max_direct'].shift(td).plot(ax = ax2, style =  ':', color = 'grey', label = 'Maximum direct SW', linewidth = 0.5)
            df_q2['max_diff'].shift(td).plot(ax = ax2, style =  '--', color = 'grey', label = 'Maximum diffusive SW', linewidth = 0.5)
            df_q2['max_glob'].shift(td).plot(ax = ax2, style =  '-', color = 'grey', label = 'Maximum global SW', linewidth = 0.5)

            #plot other temperature variables if available
            plot_flags(df = df_q2, param = par, ax = ax2, QC = 'QC2', RepDict = RepDict)
            ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
            fig2.set_size_inches(plotsz)    #Save the figure
            fig2.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q2.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

            #plot temperature with QC3 edits
            fig3, ax3 = plt.subplots()
            ax3.set_title(MetaDict['station_name'] + ': Short Wave Radiation Out' + par + ' QC2 ')
            ax3.set_ylabel(read_config('Units', Config_Path)['short_wave_radiation_out'].split(',')[0])
            ax3.set_xlabel('')
            df_q3[par].plot(ax = ax3, color = 'red', label = 'QC2 data')
            df_fin[par].plot(ax = ax3, color = 'blue', label = 'Edited (HQC) data')
            #plot other temperature variables if available
            ax3.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
            fig3.set_size_inches(plotsz)    #Save the figure
            fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q3e.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

            plt.close('all')

def Snow_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir):
    #Get metadata and report configurations from local config file
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)

    for par in read_config('Parameters', Config_Path)['snow_depth'].split(','):
        #Plot Snow Depth with qc1 labels
        fig1, ax1 = plt.subplots()
        ax1.set_title(MetaDict['station_name'] + ':  Snow Depth ' + par + ' QC1')
        ax1.set_ylabel(read_config('Units', Config_Path)['snow_depth'].split(',')[0])
        ax1.set_xlabel('')
        df_q1[par].plot(ax = ax1, color = 'blue', label = 'Snow Depth')
        if 'HS0' in df_q1.columns:
            df_q1['HS0'].plot(ax = ax1, color = 'blue', label = 'QC0 Data', linewidth = 2)

        #Plot the QC flags from QC1
        plot_flags(df = df_q1, param = par, ax = ax1, QC = 'QC1', RepDict = RepDict)
        ax1.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig1.set_size_inches(plotsz)    #Save the figure
        fig1.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q1.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot  Snow Depth with QC2 labels
        fig2, ax2 = plt.subplots()
        ax2.set_title(MetaDict['station_name'] + ':  Snow Depth ' + par + ' QC2 ')
        ax2.set_ylabel(read_config('Units', Config_Path)['snow_depth'].split(',')[0])
        ax2.set_xlabel('')
        df_q2[par].plot(ax = ax2, color = 'blue', label = 'Snow Depth')
        if 'HS0' in df_q2.columns:
            df_q2['HS0'].plot(ax = ax2, color = 'blue', label = 'QC0 Data', linewidth = 2)

        #plot other  Snow Depth variables if available
        plot_flags(df = df_q2, param = par, ax = ax2, QC = 'QC2', RepDict = RepDict)
        ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig2.set_size_inches(plotsz)    #Save the figure
        fig2.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q2.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        #plot temperature with QC3 edits
        fig3, ax3 = plt.subplots()
        ax3.set_title(MetaDict['station_name'] + ': Snow Depth ' + par + ' QC2 ')
        ax3.set_ylabel(read_config('Units', Config_Path)['snow_depth'].split(',')[0])
        ax3.set_xlabel('')
        df_q3[par].plot(ax = ax3, color = 'red', label = 'QC2 data')
        df_fin[par].plot(ax = ax3, color = 'blue', label = 'Edited (HQC) data')
        #plot other temperature variables if available
        ax3.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3, ncol=4, mode="expand", borderaxespad=0.)
        fig3.set_size_inches(plotsz)    #Save the figure
        fig3.savefig(img_dir + '\\' + MetaDict['station_code'] + '_' + par + '_' + MetaDict['year'] + '_q3e.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        plt.close('all')

def QC0plot(df_q0, Config_Path, img_dir):

    #plot all columns in original dataset
    for col in df_q0.columns:
        fig, ax = plt.subplots()
        df_q0[col].plot(ax = ax)
        ax.set_title(read_config('meta', Config_Path)['station_name'] + ': ' + col)
        fig.set_size_inches(plotsz)
        fig.savefig(img_dir + '\\' + read_config('meta', Config_Path)['station_code'] + '_' + col + '_' + read_config('meta', Config_Path)['year'] + '_q0.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')
        plt.close('all')

def QCFinplot(df_fin, Config_Path, img_dir):
    ParamDict = read_config('Parameters', Config_Path)
    Params = flatten(ParamDict.values())
    #plot all columns in original dataset
    for col in Params:
        for par in col.split(','):
            fig, ax = plt.subplots()
            df_fin[par].plot(ax = ax)
            ax.set_title(read_config('meta', Config_Path)['station_name'] + ': ' + par)
            fig.set_size_inches(plotsz)
            fig.savefig(img_dir + '\\' + read_config('meta', Config_Path)['station_code'] + '_' + par + '_' + read_config('meta', Config_Path)['year'] + '_q3.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')
            plt.close('all')

def TotStat(Config_Path, img_dir):
        PathDict = read_config('Paths', Config_Path)

        #Define directories of data and config files
        station_name =  read_config('meta', Config_Path)['station_code']
        Fin_DB = PathDict['big_df'].decode('utf-8')
        sum_dir = PathDict['sum_dir'].decode('utf-8')

        #Read the database and select parameters to investigate
        df = pd.read_csv(Fin_DB, index_col = 0, parse_dates = True)
        ParDict = read_config('Parameters', Config_Path)

        #Create summary directory
        try:
            os.makedirs(sum_dir)
        except:
            pass

        #loop through the paramters, get stats and plot figs
        for par in flatten(ParDict.values()):
            if ',' in par:
                pars = par.split(',')
                for pa in pars:

                    fig, ax = plt.subplots()
                    df.resample('M').mean()[pa].plot(ax = ax)
                    ax.set_title(station_name + ': ' + ParDict.keys()[ParDict.values().index(par)])
                    fig.savefig(sum_dir + '\\' + station_name + '_' + pa + '_Monthly.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

                    fig2, ax2 = plt.subplots()
                    df.resample('D').mean()[pa].plot(ax = ax2)
                    ax2.set_title(station_name + ': ' + ParDict.keys()[ParDict.values().index(par)])
                    fig2.savefig(sum_dir + '\\' + station_name + '_' + pa + '_Daily.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')
                    plt.close('all')

            else:
                fig, ax = plt.subplots()
                df.resample('M').mean()[par].plot(ax = ax)
                ax.set_title(station_name + ': ' + ParDict.keys()[ParDict.values().index(par)])
                fig.savefig(sum_dir + '\\' + station_name + '_' + par + '_Monthly.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

                fig2, ax2 = plt.subplots()
                df.resample('D').mean()[par].plot(ax = ax2)
                ax2.set_title(station_name + ': ' + ParDict.keys()[ParDict.values().index(par)])
                fig2.savefig(sum_dir + '\\' + station_name + '_' + par + '_Daily.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')
                plt.close('all')

        if 'sw_in' in df.columns and 'sw_out' in df.columns:

            fig2, ax2 = plt.subplots()
            (df['sw_in'].resample('D').mean()/df['sw_out'].resample('D').mean()).plot(ax = ax2)
            ax2.set_title(station_name + ': SW_IN/SW_OUT')
            fig2.savefig(sum_dir + '\\' + station_name + '_sw_in-sw_out.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

            fig3, ax3 = plt.subplots()
            (df['sw_out'].resample('D').mean()/df['sw_in'].resample('D').mean()).plot(ax = ax3)
            ax3.set_title(station_name + ': Albedo')
            ax3.set_ylim(0,1.5)
            fig3.savefig(sum_dir + '\\' + station_name + '_Albedo.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

def runme(Config_Path):

        #Read the data paths from the Local Config file
        Config_Path = Config_Path.decode('utf-8')
        PathDict = read_config('Paths', Config_Path)
        QC2_path = PathDict['qc2_path'].decode('utf-8')
        QC1_path = PathDict['qc1_path'].decode('utf-8')
        QC3_path = PathDict['qc3_path'].decode('utf-8')
        QCFin_path = PathDict['qcfin_path'].decode('utf-8')
        MET_path = PathDict['met_path'].decode('utf-8')
        rep_dir = PathDict['rep_dir'].decode('utf-8')
        img_dir = os.path.join(rep_dir + 'figures\\' + 'Figs_' + read_config('meta', Config_Path)['year'])
        RepDict = read_config('Report Config', Config_Path)

        #Create directory for saving tables and images
        try:
            os.makedirs(img_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        #Get the Parameters and associated units from the config file
        ParamDict = read_config('Parameters', Config_Path)
        for key in ParamDict:
            ParamDict[key] = ParamDict[key].split(',')
        Parameters = flatten(ParamDict.values())

        UnitDict = read_config('Units', Config_Path)
        for key in UnitDict:
            UnitDict[key] = UnitDict[key].split(',')
        Units = flatten(UnitDict.values())

        #Read the data
        df_q0 = read_data(MET_path, Config_Path)
        df_q1 = pd.read_csv(QC1_path, index_col = 0, parse_dates = [0])
        df_q2 = pd.read_csv(QC2_path, index_col = 0, parse_dates = [0])
        df_q3 = pd.read_csv(QC3_path, index_col = 0, parse_dates = [0])
        df_fin = pd.read_csv(QCFin_path, index_col = 0, parse_dates = [0])

        #Flot QC0 and final data
        QC0plot(df_q0, Config_Path, img_dir)
        QCFinplot(df_fin, Config_Path, img_dir)

        #Draw plots for each group of variables
        if 't' in df_q2.columns:
            Temp_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir)

        if 'rh' in df_q2.columns:
            Hum_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir)

        if 'ps' in df_q2.columns:
            Press_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir)

        if 'f' in df_q2.columns and 'd' in df_q2.columns:
            Wind_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir)

        if 'lw_in' in df_q2.columns or 'lw_out' in df_q2.columns:
            LW_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir)

        if 'sw_in' in df_q2.columns or 'sw_out' in df_q2.columns:
            SW_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir)

        if 'HS' in df_q2.columns:
            Snow_info(df_q1, df_q2, df_q3, df_fin, Config_Path, img_dir)

        #plot long term summary figs
        TotStat(Config_Path, img_dir)


if __name__ == '__main__':

    Config_Path = sys.argv[1]
    runme(Config_Path)
