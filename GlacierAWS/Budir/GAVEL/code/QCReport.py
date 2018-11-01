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

plotsz = (11.69, 3)
plotsz2 = (23, 12)

#Read the data
def read_data(read_path, Config_Path):
    ReadDict = read_config('Read_Data', Config_Path) #Get info on the setup of the datafile
    #Read data and create dataframe and parameter dictionaries
    if ReadDict['header'] == 'true':
        if ReadDict['startdata'] != '':
            df = pd.read_csv(read_path, header =  int(ReadDict['headerrow']), skiprows = range(int(ReadDict['headerrow'])+1, int(ReadDict['startdata'])), index_col = 0, parse_dates = True)
        else:
            df = pd.read_csv(read_path, header =  int(ReadDict['headerrow']), index_col = 0, parse_dates = True)

    df = df[df.columns.values].astype(float)

    return df

#Fill inn missing obs based on the timedelta
def fill_obs(df):
    first = df.index.values[0]
    second = df.index.values[1]
    last = df.index.values[-1]
    delta = second - first

    real_index = pd.date_range(first, last, freq = delta.astype('timedelta64[m]').astype(str).replace(' ', '')[:-4])#.format(formatter = lambda x: x.strftime('%Y-%m-%d %H%M%s'))
    real_df = pd.DataFrame(np.nan, index = real_index, columns = df.columns)

    real_df.loc[df.index.values] = df

    #for index, row in df.iterrows():
        #real_df.loc[index] = row

    return(real_df)

#Read the global configuration file with the QC test constraints
def read_config(Param, glob_file):
    Config.read(glob_file) #Read the Config ini file
    Config_dict_glob = ConfigSectionMap(Param)
    return Config_dict_glob

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

# ------------------------- Functions to plot and output into the report -----------------------
def ParamInfo(df, Parameter):

    ParDictQC1 = {}
    ParDictQC1['Observations'] = df.shape[0]
    if 'Good' in df[Parameter + '_QC1'].values:
        ParDictQC1['Num_Good'] = df[Parameter + '_QC1'].value_counts().loc['Good']
    else:
        ParDictQC1['Num_Good'] = '0'

    cert_err = []
    prob_err = []
    missing = []
    for val in df[Parameter + '_QC1'].value_counts().index.values:
        if val != 'Good':
            ParDictQC1[val] = df[Parameter + '_QC1'].value_counts().loc[val]
            if '-m' in val:
                missing.append(val)
            elif '(c)' in val:
                cert_err.append(val)
            elif '(p)' in val:
                prob_err.append(val)

    ParDictQC1['Num Certain Errors'] = df[Parameter + '_QC1'].value_counts().loc[cert_err].sum()
    ParDictQC1['Num Probable Errors'] = df[Parameter + '_QC1'].value_counts().loc[prob_err].sum()
    ParDictQC1['Num Missing Values'] = df[Parameter + '_QC1'].value_counts().loc[missing].sum()

    ParDictQC2 = {}
    if 'Good' in df[Parameter + '_QC2'].values:
        ParDictQC2['Num_fill'] = df[Parameter + '_QC2'].value_counts().loc['Good']-df[Parameter + '_QC1'].value_counts().loc['Good']
        ParDictQC2['Num_Good'] = df[Parameter + '_QC2'].value_counts().loc['Good']
    else:
        ParDictQC2['Num_Good'] = '0'
        ParDictQC2['Num_fill'] = '0'

    cert_err = []
    prob_err = []
    missing = []
    for val in df[Parameter + '_QC2'].value_counts().index.values:
        if val != 'Good':
            ParDictQC2[val] = df[Parameter + '_QC2'].value_counts().loc[val]
            if '-m' in val:
                missing.append(val)
            elif '(c)' in val:
                cert_err.append(val)
            elif '(p)' in val:
                prob_err.append(val)

    ParDictQC2['Num Certain Errors'] = df[Parameter + '_QC2'].value_counts().loc[cert_err].sum()
    ParDictQC2['Num Probable Errors'] = df[Parameter + '_QC2'].value_counts().loc[prob_err].sum()
    ParDictQC2['Num Missing Values'] = df[Parameter + '_QC2'].value_counts().loc[missing].sum()

    return ParDictQC1, ParDictQC2

def SW_info(df, Config_Path, img_dir):
    mks = 5
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)
    #Create figures and plot the actual Short Wave data

    fig8, ax8 = plt.subplots()
    fig9, ax9 = plt.subplots()
    fig10, ax10 = plt.subplots()

    df['sw_in'].plot(ax = ax8, color = 'royalblue', label = 'Incoming SW')

    if 'sw_out' in df.columns:
        df['sw_out'].plot(ax = ax9, color = 'royalblue', label = 'Reflected SW')

    if MetaDict['timedelta'] == '1hr':
        td = 3
    elif MetaDict['timedelta'] == '10min':
        td = 15
    elif MetaDict['timedelta'] == '30min':
        td = 7
    else:
        td = 0

    #Plot the theoretical and measured data
    df['max_direct'].shift(td).plot(ax = ax10, style =  ':', color = 'grey', label = 'Maximum direct SW', linewidth = 0.5)
    df['max_diff'].shift(td).plot(ax = ax10, style =  '--', color = 'grey', label = 'Maximum diffusive SW', linewidth = 0.5)
    df['max_glob'].shift(td).plot(ax = ax10, style =  '-', color = 'grey', label = 'Maximum global SW', linewidth = 0.5)

    df['sw_in'].plot(ax = ax10, color = 'royalblue', label = 'Incoming SW', linewidth = 2)
    ax10.set_title('Short Wave Radiation In')
    if 'sw_out' in df.columns:
        fig11, ax11 = plt.subplots()
        df['max_up'].shift(td).plot(ax = ax11, style = '-', color = 'grey', label = 'Maximum reflected SW', linewidth = 0.5)
        df['sw_in'].plot(ax = ax11, color = 'black', style = '--' , label = 'Incoming SW', linewidth = 1)

        df['sw_out'].plot(ax = ax11, color = 'royalblue', label = 'Reflected SW', linewidth = 2)

        prob_color = '#ffa500'
        cert_color = '#ff0000'
        for key in  df.groupby('sw_out_QC2').groups.keys():
            if key != 'Good':
                if '(c)' in key:
                    #Plot Certain Errors in Red
                    df['Certain Errors'] = np.nan
                    dates = df.groupby('sw_out_QC2').groups[key].values
                    values = df.loc[df.groupby('sw_out_QC2').groups[key]]['sw_in'].values
                    df.ix[dates, 'Certain Errors' + key] = values
                    df['Certain Errors' + key].plot(ax = ax11, color = cert_color, marker = '*', markersize = mks)
                    del df['Certain Errors' + key] #Clean up
                    cert_color = '#' + hex(int(cert_color[1:], 16) - 1000000)[2:]

                elif '(p)' in key:
                    if RepDict['prob_plot'] == 'true':
                        #Plot Probable Errors in Orange
                        df['Probable Errors'] = np.nan
                        dates = df.groupby('sw_out_QC2').groups[key].values
                        values = df.loc[df.groupby('sw_out_QC2').groups[key]]['sw_out'].values
                        df.ix[dates, 'Probable Errors' + key] = values
                        df['Probable Errors' + key].plot(ax = ax11, color = prob_color, marker = 'o', markersize = mks)
                        del df['Probable Errors' + key] #Clean up
                        prob_color = '#' + hex(int(prob_color[1:], 16) - 1000000)[2:]

        ax11.set_title('Short Wave Radiation Out')
        ax11.set_ylabel(read_config('Units', Config_Path)['short_wave_radiation_in'])
        ax11.set_xlabel('')
        ax11.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
        fig11.set_size_inches(plotsz)
        fig11.savefig(img_dir + '\sw_out_QC_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')



    #Plot all flagged datapoints
    prob_color = '#ffa500'
    cert_color = '#ff0000'
    for key in  df.groupby('sw_in_QC2').groups.keys():
        if key != 'Good':
            if '(c)' in key:
                #Plot Certain Errors in Red
                dates = df.groupby('sw_in_QC2').groups[key].values
                values = df.loc[df.groupby('sw_in_QC2').groups[key]]['sw_in'].values
                df.ix[dates, 'Certain Errors' + key] = values

                df['Certain Errors' + key].plot(ax = ax10, color = cert_color, marker = '*', markersize = mks)
                del df['Certain Errors' + key]
                cert_color = '#' + hex(int(cert_color[1:], 16) - 1000000)[2:]

            elif '(p)' in key:
                if RepDict['prob_plot'] == 'true':
                    #Plot Probable Errors in Orange
                    dates = df.groupby('sw_in_QC2').groups[key].values
                    values = df.loc[df.groupby('sw_in_QC2').groups[key]]['sw_in'].values
                    df.ix[dates, 'Probable Errors' + key] = values

                    df['Probable Errors' + key].plot(ax = ax10, color = prob_color, marker = 'o', markersize = mks)
                    del df['Probable Errors' + key]
                    prob_color = '#' + hex(int(prob_color[1:], 16) - 1000000)[2:]


    ax8.set_title(MetaDict['station_name'] + ': Short Wave Radiation In')
    ax9.set_title(MetaDict['station_name']  + ': Short Wave Radiation Out')
    ax8.set_ylabel(read_config('Units', Config_Path)['short_wave_radiation_in'])
    ax9.set_ylabel(read_config('Units', Config_Path)['short_wave_radiation_in'])
    ax10.set_ylabel(read_config('Units', Config_Path)['short_wave_radiation_in'])

    ax8.set_xlabel('')
    ax9.set_xlabel('')
    ax10.set_xlabel('')

    #ax8.legend(loc = 'best')
    #ax9.legend(loc = 'best')
    ax10.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3,
           ncol=4, mode="expand", borderaxespad=0.)

    #Save the data and plots
    fig8.set_size_inches(plotsz)
    fig8.savefig(img_dir + '\sw_in_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')
    fig9.set_size_inches(plotsz)
    fig9.savefig(img_dir + '\sw_out_' + MetaDict['year'] +'.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')
    fig10.set_size_inches(plotsz)
    fig10.savefig(img_dir + '\sw_in_QC_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    #plt.show()
    plt.close('all')

def HumPress_info(df, Config_Path, img_dir):
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)

    #plot for relative humidity
    if 'rh' in df.columns:

        fig7, ax6 = plt.subplots()
        fig9, ax8 = plt.subplots()

        df['rh'].plot(ax = ax6, label = 'Relative_Humidity')
        df['rh'].plot(ax = ax8, label = 'Relative Humidity')

        #Plot all flagged datapoints in rh
        prob_color = '#ffa500'
        cert_color = '#ff0000'
        for key in  df.groupby('rh_QC2').groups.keys():
            if key != 'Good':
                if '(c)' in key:
                    #Plot Certain Errors in Red
                    dates = df.groupby('rh_QC2').groups[key].values
                    values = df.loc[df.groupby('rh_QC2').groups[key]]['rh'].values
                    df.ix[dates, 'Certain Errors'] = values

                    df['Certain Errors'].plot(ax = ax8, color = cert_color, linewidth = 5)
                    del df['Certain Errors']
                    cert_color = '#' + hex(int(cert_color[1:], 16) - 1000000)[2:]

                elif '(p)' in key:
                    if RepDict['prob_plot'] == 'true':
                        #Plot Probable Errors in Orange
                        dates = df.groupby('rh_QC2').groups[key].values
                        values = df.loc[df.groupby('rh_QC2').groups[key]]['rh'].values
                        df.ix[dates, 'Probable Errors' + key] = values

                        df['Probable Errors' + key].plot(ax = ax8, color = prob_color, linewidth = 5)
                        del df['Probable Errors' + key]
                        prob_color = '#' + hex(int(prob_color[1:], 16) - 1000000)[2:]

        if 'rh2' in df.columns:
            fig5, ax5 = plt.subplots()
            df['rh2'].plot(ax = ax5, label = 'Relative Humidity 4m')
            df['rh2'].plot(ax = ax8, label = 'Relative Humidity 4m')
            ax5.set_title(MetaDict['station_name'] + ': Relative Humidity 4m')
            ax5.set_ylabel(read_config('Units', Config_Path)['humidity'])
            ax5.set_xlabel('')
            #Save the data and plots
            fig5.set_size_inches(plotsz)
            fig5.savefig(img_dir + '\\rh2_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        ax6.set_title(MetaDict['station_name'] + ': Relative Humidity')
        ax8.set_title(MetaDict['station_name'] + ': Relative Humidity')
        ax6.set_ylabel(read_config('Units', Config_Path)['humidity'])
        ax8.set_ylabel(read_config('Units', Config_Path)['humidity'])
        ax6.set_xlabel('')
        ax8.set_xlabel('')
        ax8.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)

        #Save the data and plots
        fig7.set_size_inches(plotsz)
        fig7.savefig(img_dir + '\\rh_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        fig9.set_size_inches(plotsz)
        fig9.savefig(img_dir + '\\rh_QC_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    #plot for atmospheric_pressure
    if 'ps' in df.columns:
        fig8, ax7 = plt.subplots()
        fig10, ax9 = plt.subplots()

        df['ps'].plot(ax = ax7, label = 'Atmospheric Pressure')
        df['ps'].plot(ax = ax9, label = 'Atmospheric Pressure')

        prob_color = '#ffa500'
        cert_color = '#ff0000'
        for key in  df.groupby('ps_QC2').groups.keys():
            if key != 'Good':
                if '(c)' in key:
                    #Plot Certain Errors in Red
                    dates = df.groupby('ps_QC2').groups[key].values
                    values = df.loc[df.groupby('ps_QC2').groups[key]]['ps'].values
                    df.ix[dates, 'Certain Errors'] = values

                    df['Certain Errors'].plot(ax = ax9, color = cert_color, linewidth = 5)
                    del df['Certain Errors']
                    cert_color = '#' + hex(int(cert_color[1:], 16) - 1000000)[2:]

                elif '(p)' in key:
                    if RepDict['prob_plot'] == 'true':
                        # Plot Probable Errors in Orange
                        dates = df.groupby('ps_QC2').groups[key].values
                        values = df.loc[df.groupby('ps_QC2').groups[key]]['ps'].values
                        df.ix[dates, 'Probable Errors' + key] = values

                        df['Probable Errors' + key].plot(ax = ax9, color = prob_color, linewidth = 5)
                        del df['Probable Errors' + key]
                        prob_color = '#' + hex(int(prob_color[1:], 16) - 1000000)[2:]

        ax7.set_title(MetaDict['station_name'] + ': Atmospheric Pressure')
        ax9.set_title(MetaDict['station_name'] + ': Atmospheric Pressure')

        ax9.set_ylabel(read_config('Units', Config_Path)['atmospheric_pressure'])
        ax7.set_ylabel(read_config('Units', Config_Path)['atmospheric_pressure'])

        ax9.set_xlabel('')
        ax7.set_xlabel('')

        ax9.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)

        fig8.set_size_inches(plotsz)
        fig8.savefig(img_dir + '\\ps_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

        fig10.set_size_inches(plotsz)
        fig10.savefig(img_dir + '\\ps_QC_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    plt.close('all')

def Wind_info(df, Config_Path, img_dir):
    warnings.simplefilter('ignore', RuntimeWarning)
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)

    #Make the figures and plot
    fig4, ax4 = plt.subplots()
    fig6, ax6 = plt.subplots()

    df['f'].plot(ax = ax6, label = 'wind speed')
    df['f'].plot(ax = ax4, label = 'wind speed')
    #Plot all flagged datapoints in f

    prob_color = '#ffa500'
    cert_color = '#ff0000'
    for key in  df.groupby('f_QC2').groups.keys():
        if key != 'Good':
            if '(c)' in key:
                #Plot Certain Errors in Red
                dates = df.groupby('f_QC2').groups[key].values
                values = df.loc[df.groupby('f_QC2').groups[key]]['f'].values
                df.loc[dates, 'Certain Errors'] = values

                df['Certain Errors'].plot(ax = ax4, color = cert_color, linewidth = 5)
                del df['Certain Errors']
                cert_color = '#' + hex(int(cert_color[1:], 16) - 1000000)[2:]

            elif '(p)' in key:
                if RepDict['prob_plot'] == 'true':
                    #Plot Probable Errors in Orange
                    dates = df.groupby('f_QC2').groups[key].values
                    values = df.loc[df.groupby('f_QC2').groups[key]]['f'].values
                    df.loc[dates, 'Probable Errors' + key] = values

                    df['Probable Errors' + key].plot(ax = ax4, color = prob_color, linewidth = 5)
                    del df['Probable Errors' + key]
                    prob_color = '#' + hex(int(prob_color[1:], 16) - 1000000)[2:]

    ax6.set_title(MetaDict['station_name'] + ': Wind Speed')
    ax6.set_ylabel(read_config('Units', Config_Path)['wind_speed'])

    ax4.set_title(MetaDict['station_name'] + ': Wind Speed')
    ax4.set_ylabel(read_config('Units', Config_Path)['wind_speed'])

    #ax6.legend(loc = 'best')
    ax4.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3,
           ncol=4, mode="expand", borderaxespad=0.)

    ax6.set_xlabel('')
    ax4.set_xlabel('')

    fig6.set_size_inches(plotsz)
    fig6.savefig(img_dir + '\\f_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    fig4.set_size_inches(plotsz)
    fig4.savefig(img_dir + '\\f_QC_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    if 'd' in df.columns:
        fig8 = plt.figure()
        fig5, ax5 = plt.subplots()

        df['d'].plot(ax = ax5, label = 'wind direction')
        prob_color = '#ffa500'
        cert_color = '#ff0000'
        for key in  df.groupby('d_QC2').groups.keys():
            if key != 'Good':
                if '(c)' in key:
                    # Plot Certain Errors in Red
                    dates = df.groupby('d_QC2').groups[key].values
                    values = df.loc[df.groupby('d_QC2').groups[key]]['d'].values
                    df.ix[dates, 'Certain Errors'] = values

                    df['Certain Errors'].plot(ax = ax5, color = cert_color, linewidth = 5)
                    del df['Certain Errors']
                    cert_color = '#' + hex(int(cert_color[1:], 16) - 1000000)[2:]

                elif '(p)' in key:
                    if RepDict['prob_plot'] == 'true':
                        #Plot Probable Errors in Orang
                        dates = df.groupby('d_QC2').groups[key].values
                        values = df.loc[df.groupby('d_QC2').groups[key]]['d'].values
                        df.ix[dates, 'Probable Errors' + key] = values

                        df['Probable Errors' + key].plot(ax = ax5, color = prob_color, linewidth = 5)
                        del df['Probable Errors' + key]
                        prob_color = '#' + hex(int(prob_color[1:], 16) - 1000000)[2:]

        #Plot the Wind Rose
        ax8 = WindroseAxes.from_ax(fig = fig8)
        ax8.bar(df['d'], df['f'], normed=True, opening=0.8, edgecolor='white')
        ax8.set_legend(title = 'Wind speed [m/s]')

        ax5.set_title(MetaDict['station_name'] +': Wind Direction')
        ax8.set_title(MetaDict['station_name'] + ': Wind Rose')
        ax5.set_ylabel(read_config('Units', Config_Path)['wind_direction'])
        ax5.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3,
               ncol=4, mode="expand", borderaxespad=0.)
        ax8.legend(title = 'Wind Speed')
        ax5.set_xlabel('')

        fig5.set_size_inches(plotsz)
        fig5.savefig(img_dir + '\\d_QC_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')
        fig8.savefig(img_dir + '\wind_rose_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    if 'f2' in df.columns:
        fig7, ax7 = plt.subplots()
        df['f2'].plot(ax = ax7, label = 'wind speed 4m')
        df['f2'].plot(ax = ax4, label = 'wind speed 4m')
        ax7.set_title('Wind Speed 4m')
        ax7.set_ylabel(read_config('Units', Config_Path)['wind_speed'])
        ax7.set_xlabel('')

        fig7.set_size_inches(plotsz)
        fig7.savefig(img_dir + '\\f2_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    plt.close('all')

def LW_info(df, Config_Path, img_dir):
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)

    #Calculate max and min long wave radiation based on max and min temps and blackbody assumption
    stbc = 0.00000005670367
    lwmin = ((-40+273)**4)*stbc #read_config('Long_Wave_Radiation')['min']
    lwmax = ((40+273)**4)*stbc #read_config('Long_Wave_Radiation')['max']
    df['lw_theo'] = ((df['t']+273)**4)*stbc
    df['lw_in_theo_lower_1st'] = float(read_config('long_wave_radiation_in', Config_Path)['d1'])*((df['t']+273)**4)*stbc
    df['lw_in_theo_upper_1st'] = ((df['t']+273)**4)*stbc + float(read_config('long_wave_radiation_in', Config_Path)['d2'])
    df['lw_out_theo_lower_1st'] = stbc*((df['t'] + 273) - float(read_config('long_wave_radiation_out', Config_Path)['d3']))**4
    df['lw_out_theo_upper_1st'] = stbc*((df['t'] + 273) + float(read_config('long_wave_radiation_out', Config_Path)['d4']))**4
    df['lw_in_theo_lower_2nd'] = float(read_config('long_wave_radiation_in', Config_Path)['c1'])*((df['t']+273)**4)*stbc
    df['lw_in_theo_upper_2nd'] = ((df['t']+273)**4)*stbc + float(read_config('long_wave_radiation_in', Config_Path)['c2'])
    df['lw_out_theo_lower_2nd'] = stbc*((df['t'] + 273) - float(read_config('long_wave_radiation_out', Config_Path)['c3']))**4
    df['lw_out_theo_upper_2nd'] = stbc*((df['t'] + 273) + float(read_config('long_wave_radiation_out', Config_Path)['c4']))**4

    #Create the figure and plot the measured and theoretical values
    fig4, ax4  = plt.subplots()
    fig5, ax5  = plt.subplots()
    fig6, ax6 = plt.subplots()
    fig7, ax7 = plt.subplots()

    df['lw_in'].plot(ax = ax5, color = 'blue', label = 'LW in')
    df['lw_out'].plot(ax = ax4, color = 'blue', label = 'LW out')
    df['lw_in'].plot(ax = ax6, color = 'blue', label = 'LW in')
    ax6.set_title('Long Wave Radiation In')
    df['lw_out'].plot(ax = ax7, color = 'blue', label = 'LW out')
    ax7.set_title('Long Wave Radiation Out')

    #plot Theoretical QC limits
    df['lw_theo'].plot(ax = ax6, color = 'black', linestyle = '--', label = 'Theoretical lw')
    df['lw_theo'].plot(ax = ax7, color = 'black', linestyle = '--', label = 'Theoretical lw')
    df['lw_in_theo_lower_1st'].plot(ax = ax6, color = 'black', linestyle = ':', label = '1st level')
    df['lw_in_theo_upper_1st'].plot(ax = ax6, color = 'black', linestyle = ':', label = '')
    df['lw_out_theo_lower_1st'].plot(ax = ax7, color = 'black', linestyle = ':', label = '1st level')
    df['lw_out_theo_upper_1st'].plot(ax = ax7, color = 'black', linestyle = ':', label = '')
    df['lw_in_theo_lower_2nd'].plot(ax = ax6, color = 'grey', linestyle = ':', label = '2nd level')
    df['lw_in_theo_upper_2nd'].plot(ax = ax6, color = 'grey', linestyle = ':', label = '')
    df['lw_out_theo_lower_2nd'].plot(ax = ax7, color = 'grey', linestyle = ':', label = '2nd level')
    df['lw_out_theo_upper_2nd'].plot(ax = ax7, color = 'grey', linestyle = ':', label = '')

    #Plot all flagged datapoints in lw_in
    prob_color = '#ffa500'
    cert_color = '#ff0000'
    for key in  df.groupby('lw_in_QC2').groups.keys():
        if key != 'Good':
            if '(c)' in key:
                #Plot Certain Errors in Red
                dates = df.groupby('lw_in_QC2').groups[key].values
                values = df.loc[df.groupby('lw_in_QC2').groups[key]]['lw_in'].values
                df.ix[dates, 'Certain Errors'  + key] = values

                df['Certain Errors' + key].plot(ax = ax6, color = cert_color, marker = '*')
                del df['Certain Errors' + key]
                cert_color = '#' + hex(int(cert_color[1:], 16) - 1000000)[2:]

            elif '(p)' in key:
                if RepDict['prob_plot'] == 'true':
                    #Plot Probable Errors in Orange
                    dates = df.groupby('lw_in_QC2').groups[key].values
                    values = df.loc[df.groupby('lw_in_QC2').groups[key]]['lw_in'].values
                    df.ix[dates, 'Probable Errors' + key] = values

                    df['Probable Errors' + key].plot(ax = ax6, color = prob_color, marker = 'o')
                    del df['Probable Errors' + key]
                    prob_color = '#' + hex(int(prob_color[1:], 16) - 1000000)[2:]

    prob_color = '#ffa500'
    cert_color = '#ff0000'
    for key in  df.groupby('lw_out_QC2').groups.keys():
        if key != 'Good':
            if '(c)' in key:
                #Plot Certain Errors in Red
                dates = df.groupby('lw_out_QC2').groups[key].values
                values = df.loc[df.groupby('lw_out_QC2').groups[key]]['lw_out'].values
                df.ix[dates, 'Certain Errors' + key] = values

                df['Certain Errors' + key].plot(ax = ax7, color = cert_color, marker = '*')
                del df['Certain Errors' + key]
                cert_color = '#' + hex(int(cert_color[1:], 16) - 1000000)[2:]

            elif '(p)' in key:
                if RepDict['prob_plot'] == 'true':
                    #Plot Probable Errors in Orange
                    dates = df.groupby('lw_out_QC2').groups[key].values
                    values = df.loc[df.groupby('lw_out_QC2').groups[key]]['lw_out'].values
                    df.ix[dates, 'Probable Errors' + key] = values

                    df['Probable Errors' + key].plot(ax = ax7, color = prob_color, marker = 'o')
                    del df['Probable Errors' + key]
                    prob_color = '#' + hex(int(prob_color[1:], 16) - 1000000)[2:]

    ax4.set_title(MetaDict['station_name'] + ': Long Wave Radiation Out')
    ax5.set_title(MetaDict['station_name'] + ': Long Wave Radiation In')
    ax4.set_ylabel(read_config('Units', Config_Path)['long_wave_radiation_in'])
    ax5.set_ylabel(read_config('Units', Config_Path)['long_wave_radiation_in'])
    ax6.set_ylabel(read_config('Units', Config_Path)['long_wave_radiation_in'])
    ax7.set_ylabel(read_config('Units', Config_Path)['long_wave_radiation_in'])

    #ax4.legend(loc = 'best')
    #ax5.legend(loc = 'best')
    ax6.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3,
           ncol=4, mode="expand", borderaxespad=0.)
    ax7.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3,
           ncol=4, mode="expand", borderaxespad=0.)

    ax4.set_xlabel('')
    ax5.set_xlabel('')
    ax6.set_xlabel('')
    ax7.set_xlabel('')


    #Save the data and plots
    fig4.set_size_inches(plotsz)
    fig4.savefig(img_dir + '\lw_out_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    fig5.set_size_inches(plotsz)
    fig5.savefig(img_dir + '\lw_in_'  + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    fig6.set_size_inches(plotsz)
    fig6.savefig(img_dir + '\lw_in_QC_'  + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    fig7.set_size_inches(plotsz)
    fig7.savefig(img_dir + '\lw_out_QC_'  + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    plt.close('all')

def Snow_info(df, df_orig, Config_Path, img_dir):
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)
    #Create fig and plot QC controlled snow data
    fig2, ax1 = plt.subplots()
    fig3, ax2 = plt.subplots()

    df_orig['HS'].plot(ax = ax2, color = 'red', label = 'Original Data', linewidth = 0.5)
    df['HS'].plot(ax = ax1, color = 'blue' , label = 'QC2 Data')
    df['HS'].plot(ax = ax2, color = 'green' , label = 'QC Data', linewidth = 4)

    #Add info on manual snow measurements if available
    if 'HSman' in df.columns:
        df['HSman'].plot(ax = ax2, color = 'purple', linewidth = 4, label = '')
        df['HSman'].head(1).plot(ax = ax2, color = 'purple', marker = 'o', markersize = 10, markerfacecolor = 'white', label = 'Manual Measurement')
        df['HSman'].tail(1).plot(ax = ax2, color = 'purple', marker = 'o', markersize = 10, markerfacecolor = 'white', label = '')

    #Add info on QC0, if availalbe
    if 'HS0' in df.columns:
        df['HS0'].plot(ax = ax2, color = 'blue', label = 'QC0 Data', linewidth = 2)


    #Plot all flagged datapoints in HS
    prob_color = '#ffa500'
    cert_color = '#ff0000'
    for key in  df.groupby('HS_QC2').groups.keys():
        if key != 'Good':
            if '(c)' in key:
                #Plot Certain Errors in Red
                dates = df.groupby('HS_QC2').groups[key].values
                values = df.loc[df.groupby('HS_QC2').groups[key]]['HS'].values
                df.ix[dates, 'Certain Errors'  + key] = values

                df['Certain Errors' + key].plot(ax = ax2, color = cert_color, marker = '*')
                del df['Certain Errors' + key]
                cert_color = '#' + hex(int(cert_color[1:], 16) - 1000000)[2:]

            elif '(p)' in key:
                if RepDict['prob_plot'] == 'true':
                    #Plot Probable Errors in Orange
                    dates = df.groupby('HS_QC2').groups[key].values
                    values = df.loc[df.groupby('HS_QC2').groups[key]]['HS'].values
                    df.ix[dates, 'Probable Errors' + key] = values

                    df['Probable Errors' + key].plot(ax = ax2, color = prob_color, marker = 'o')
                    del df['Probable Errors' + key]
                    prob_color = '#' + hex(int(prob_color[1:], 16) - 1000000)[2:]

    df.loc[df['HS_QC2'] == '-m(c)', 'HS'] = -np.nan

    ax1.set_title(MetaDict['station_name'] + ': Snow Depth')
    ax1.set_xlabel('')
    ax1.set_ylabel(read_config('Units', Config_Path)['snow_depth'])

    ax2.set_title(MetaDict['station_name'] + ': Snow Depth')
    ax2.set_xlabel('')
    ax2.set_ylabel(read_config('Units', Config_Path)['snow_depth'])

    #if read_config('Units', Config_Path)['snow_depth'] == 'cm':
        #ax2.set_ylim(-200,500)
    #elif read_config('Units', Config_Path)['snow_depth'] == 'm':
        #ax2.set_ylim(-2,5)

    ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=4,
           ncol=4, mode="expand", borderaxespad=0.)

    #Save the Figs
    fig2.set_size_inches(plotsz)
    fig2.savefig(img_dir + '\HS_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    fig3.set_size_inches(plotsz)
    fig3.savefig(img_dir + '\HS_QC_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    #plt.show()
    plt.close('all')

def Temp_info(df, Config_Path, img_dir):
    MetaDict = read_config('meta', Config_Path)
    RepDict = read_config('Report Config', Config_Path)
    ParamInfo(df, 't')

    fig3, ax1 = plt.subplots()
    fig4, ax2 = plt.subplots()

    ax1.set_title(MetaDict['station_name'] + ': Temperature ')
    ax2.set_title(MetaDict['station_name'] + ': Temperature ')
    df['t'].plot(ax = ax1, color = 'blue')
    df['t'].plot(ax = ax2, color = 'blue')

    #Plot all flagged datapoints in t '''
    prob_color = '#ffa500'
    cert_color = '#ff0000'
    for key in  df.groupby('t_QC2').groups.keys():
        if key != 'Good':
            if '(c)' in key:
                #Plot Certain Errors in Red
                dates = df.groupby('t_QC2').groups[key].values
                values = df.loc[df.groupby('t_QC2').groups[key]]['t'].values
                df.ix[dates, 'Certain Errors' + key] = values

                df['Certain Errors' + key].plot(ax = ax2, color = cert_color, linewidth = 5)
                del df['Certain Errors' + key]
                cert_color = '#' + hex(int(cert_color[1:], 16) - 1000000)[2:]

            elif '(p)' in key:
                if RepDict['prob_plot'] == 'true':
                    #Plot Probable Errors in Orange
                    dates = df.groupby('t_QC2').groups[key].values
                    values = df.loc[df.groupby('t_QC2').groups[key]]['t'].values
                    df.ix[dates, 'Probable Errors' + key] = values

                    df['Probable Errors' + key].plot(ax = ax2, color = prob_color, linewidth = 5)
                    del df['Probable Errors' + key]
                    prob_color = '#' + hex(int(prob_color[1:], 16) - 1000000)[2:]

    #ax1.legend(loc = 'best')
    ax1.set_ylabel(read_config('Units', Config_Path)['air_temperature'])
    ax1.set_xlabel('')

    ax2.set_ylabel(read_config('Units', Config_Path)['air_temperature'])
    ax2.set_xlabel('')

    if 't2' in df.columns:
        fig5, ax5 = plt.subplots()
        ax5.set_title(MetaDict['station_name'] + ': Temperature (Humidity sensor)')
        df['t2'].plot(ax = ax2, color = 'purple')
        df['t2'].plot(ax = ax5, color = 'blue', label = 't2')
        ax5.set_ylabel(read_config('Units', Config_Path)['air_temperature'])
        ax5.set_xlabel('')
        fig5.set_size_inches(plotsz)
        fig5.savefig(img_dir + '\\t2_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    ax2.legend(bbox_to_anchor=(0., 1.15, 1., .102), loc=3,
           ncol=4, mode="expand", borderaxespad=0.)
    #Save the data and plots '''
    fig3.set_size_inches(plotsz)
    fig3.savefig(img_dir + '\\t_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')
    fig4.set_size_inches(plotsz)
    fig4.savefig(img_dir + '\\t_QC_' + MetaDict['year'] + '.png', format = 'png', dpi = 300, pad_inches = None, bbox_inches = 'tight')

    plt.close('all')

def AvgTable(df, Parameters, tab_dir, Units):
    warnings.simplefilter('ignore', RuntimeWarning)

    #Calculate resampled statistics for Monty and Yearly measurment averages
    df_MS = df.resample('M').std().round(1)
    df_MMa = df.resample('M').max().round(1)
    df_MMi = df.resample('M').min().round(1)
    df_MM = df.resample('M').mean().round(1)
    df_YS = df.resample('Y').std().round(1)
    df_YM = df.resample('Y').mean().round(1)
    df_YMMa = df.resample('Y').max().round(1)
    df_YMMi = df.resample('Y').min().round(1)

    #Calculate percentage of valid measurements
    df_MC = df.resample('M').count()#.round(1)
    #get the timedelta
    first = df.index.values[0]
    second = df.index.values[1]
    delta = second - first
    #divide by the number of valid measurements we should have -ish
    if str(delta.astype('timedelta64[m]')) == '10 minutes':
        df_MP = df_MC/4400
    elif str(delta.astype('timedelta64[m]')) == '60 minutes':
        df_MP = df_MC/732
    elif str(delta.astype('timedelta64[m]')) == '30 minutes':
        df_MP = df_MC/1464
    elif str(delta.astype('timedelta64[m]')) == '1440 minutes':
        df_MP = df_MC/30
        
    #Convert dataframe entries to string
    for col in df_MM.columns:
        df_MM[col] = df_MM[col].apply(str)
        df_MS[col] = df_MS[col].apply(str)
        df_MMa[col] = df_MMa[col].apply(str)
        df_MMi[col] = df_MMi[col].apply(str)
        df_YM[col] = df_YM[col].apply(str)
        df_YS[col] = df_YS[col].apply(str)
        df_YMMa[col] = df_YMMa[col].apply(str)
        df_YMMi[col] = df_YMMi[col].apply(str)

    #Create dataframes to orginize the final output tables
    new_index = []
    df_FIN = pd.DataFrame(np.nan, index = df_MM.index, columns = df_MM.columns)
    df_FINs = pd.DataFrame(np.nan, index = df_MM.index, columns = df_MM.columns)
    df_FINma = pd.DataFrame(np.nan, index = df_MM.index, columns = df_MM.columns)
    df_FINmi = pd.DataFrame(np.nan, index = df_MM.index, columns = df_MM.columns)
    for index, row in df_MM.iterrows():
        df_FIN.loc[index] = [m + '' for m,n in zip(list(row),list(df_MS.loc[index]))]
        #Option for adding the std to the mean table
        #df_FIN.loc[index] = [m + '(' + n +')' for m,n in zip(list(row),list(df_MS.loc[index]))]
    for index, row in df_MS.iterrows():
        df_FINs.loc[index] = [m + '' for m,n in zip(list(row),list(df_MS.loc[index]))]
    for index, row in df_MMa.iterrows():
        df_FINma.loc[index] = [m + '' for m,n in zip(list(row),list(df_MS.loc[index]))]
    for index, row in df_MMi.iterrows():
        df_FINmi.loc[index] = [m + '' for m,n in zip(list(row),list(df_MS.loc[index]))]
        new_index.append(index.strftime('%B'))


    #mark observations that have less than 80% of valid observations per month with '*'
    for col in df_MP.columns:
        for val in df_MP[col].iteritems():
            index = val[0]
            item = val[1]
            if item < 0.8:
                df_FIN[col].loc[index] = df_FIN[col].loc[index] + '*'
                df_FINs[col].loc[index] = df_FINs[col].loc[index] + '*'
                df_FINma[col].loc[index] = df_FINma[col].loc[index] + '*'
                df_FINmi[col].loc[index] = df_FINmi[col].loc[index] + '*'

    #Change the index of the final dataframe to be a string with the name of the month
    df_FIN['Month'] = new_index
    df_FINs['Month'] = new_index
    df_FINma['Month'] = new_index
    df_FINmi['Month'] = new_index
    df_FIN = df_FIN.set_index('Month')
    df_FINs = df_FINs.set_index('Month')
    df_FINma = df_FINma.set_index('Month')
    df_FINmi = df_FINmi.set_index('Month')

    #Add Yearly averages to bottom of dataframe
    df_Y = pd.DataFrame(data = {'Mean' : [m + '' for m,n in zip(df_YM.values[0], df_YS.values[0])]}).transpose()
    df_Ys = pd.DataFrame(data = {'Std' : [m + '' for m,n in zip(df_YS.values[0], df_YM.values[0])]}).transpose()
    df_Yma = pd.DataFrame(data = {'Max' : [m + '' for m,n in zip(df_YMMa.values[0], df_YS.values[0])]}).transpose()
    df_Ymi = pd.DataFrame(data = {'Min' : [m + '' for m,n in zip(df_YMMi.values[0], df_YS.values[0])]}).transpose()
    #option for adding the std to the mean table within braces
    #df_Y = pd.DataFrame(data = {'Yearly average' : [m + '(' + n +')' for m,n in zip(df_YM.values[0], df_YS.values[0])]}).transpose()
    df_Y.columns = df_FIN.columns
    df_Ys.columns = df_FIN.columns
    df_Yma.columns = df_FIN.columns
    df_Ymi.columns = df_FIN.columns
    df_FIN = df_FIN.append(df_Y)
    df_FINs = df_FINs.append(df_Ys)
    df_FINma = df_FINma.append(df_Yma)
    df_FINmi = df_FINmi.append(df_Ymi)

    #Add the units of each parameter to the dataframe
    df_U = pd.DataFrame(data = {'Units': Units}).transpose()
    df_U.columns = df_FIN.columns
    df_FIN = df_FIN.append(df_U)
    df_FINs = df_FINs.append(df_U)
    df_FINma = df_FINma.append(df_U)
    df_FINmi = df_FINmi.append(df_U)

    #Organize the rows
    df_FIN = df_FIN.reindex(sum([['Units'], new_index, ['Mean']],[]))
    df_FINs = df_FINs.reindex(sum([['Units'], new_index, ['Std']],[]))
    df_FINma = df_FINma.reindex(sum([['Units'], new_index, ['Max']],[]))
    df_FINmi = df_FINmi.reindex(sum([['Units'], new_index, ['Min']],[]))

    #Write out the tables as LaTeX tables
    with open(os.path.join(tab_dir, 'AvgTable.tex'), 'w') as tf:
        tf.write(df_FIN.to_latex())
    with open(os.path.join(tab_dir, 'StdTable.tex'), 'w') as tf:
        tf.write(df_FINs.to_latex())
    with open(os.path.join(tab_dir, 'MaxTable.tex'), 'w') as tf:
        tf.write(df_FINma.to_latex())
    with open(os.path.join(tab_dir, 'MinTable.tex'), 'w') as tf:
        tf.write(df_FINmi.to_latex())

    '''
    print(df_FIN)
    print(df_FINs)
    print(df_FINma)
    print(df_FINmi)
    '''

def QCtables(df, Parameters, tab_dir):
    #Make tables showing the annual QC statistics for each parameter
    #Loop through the parameters
    for Par in Parameters:
        #Get the statistics from the Parmeters for QC1 and QC2
        PD1, PD2 = ParamInfo(df, Par)

        #Create empty lists to store the statiscs in
        ErrList = [] #name of qc Flagg
        NumList = [] #number of flags in QC1
        NumList2 = [] #number of flags in QC2

        #Get number of observations in eqch module
        for key in PD1.keys():
            if key == 'Observations':
                ErrList.append(key)
                NumList.append(PD1[key])
                NumList2.append(PD1[key])

        #Get number of obs that pass each module
        for key in PD1.keys():
            if key == 'Num_Good':
                ErrList.append(key)
                NumList.append(PD1[key])
                NumList2.append(PD2[key])

        #Calculate the number of obs filled in QC2
        for key in PD2.keys():
            if key == 'Num_fill':
                ErrList.append(key)
                NumList.append(0)
                NumList2.append(PD2[key])

        #Number of specific flags in QC1
        for key in PD1.keys():
            if key[0] == '-':
                ErrList.append(key)
                NumList.append(PD1[key])
                if key in PD2.keys():
                    NumList2.append(PD2[key])
                else:
                    NumList2.append(0)

        #Number of specific flags in QC2 but not QC1 (finish geting all flags)
        for key in PD2.keys():
            if key[0] == '-':
                if key not in PD1.keys():
                    ErrList.append(key)
                    NumList.append(0)
                    NumList2.append(PD2[key])

        #Get final statistics of missing values, probable and certain errors
        for key in PD1.keys():
            if 'Num ' in key:
                ErrList.append(key)
                NumList.append(PD1[key])
                NumList2.append(PD2[key])

        #Calculate precentages for each of the items in the list
        perc = (100*np.array(NumList).astype(float)/float(NumList[0])).round(2)
        perc2 = (100*np.array(NumList2).astype(float)/float(NumList2[0])).round(2)

        #Create dataframe for saving the tables
        df_Par = pd.DataFrame([ErrList, NumList, list(perc), NumList2, list(perc2)]).transpose()
        df_Par.columns = ['QC Flag', 'No. obs QC1', '%  obs QC1', 'No. obs QC2', '%  obs QC2']
        df_Par = df_Par.set_index('QC Flag')
        df_Par = df_Par.rename_axis(Par, axis = 'columns') #add the Parameter name to the table

        #Save the dataframe as a LaTeX table
        with open(os.path.join(tab_dir, Par + '_Table.tex'), 'w') as tf:
            tf.write(df_Par.to_latex())

        #print df_Par

def SGF(df, Params, window = 7, order = 3):
    warnings.simplefilter('ignore', np.RankWarning)

    for par in Params:

        dfs = savgol_filter(df[par], window, order)
        df[par] = dfs


    return df

def runme(Config_Path):

    #Read the data paths from the Local Config file
    Config_Path = Config_Path.decode('utf-8')
    PathDict = read_config('Paths', Config_Path)
    QC2_path = PathDict['qc2_path'].decode('utf-8')
    MET_path = PathDict['met_path'].decode('utf-8')
    rep_dir = PathDict['rep_dir'].decode('utf-8')
    img_dir = os.path.join(rep_dir + 'figures\\' + 'Figs_' + read_config('meta', Config_Path)['year'])
    tab_dir = os.path.join(rep_dir + 'tables\\'+ 'Tables_' + read_config('meta', Config_Path)['year'])
    RepDict = read_config('Report Config', Config_Path)

    #Create directory for saving tables and images
    try:
        os.makedirs(img_dir)
        os.makedirs(tab_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    #Get the Parameters and associated units from the config file
    ParamDict = read_config('Parameters', Config_Path)
    for key in ParamDict:
        ParamDict[key] = ParamDict[key].split(',')
    Parameters = sum(ParamDict.values(),[])
    UnitDict = read_config('Units', Config_Path)
    for key in UnitDict:
        UnitDict[key] = UnitDict[key].split(',')
    Units = sum(UnitDict.values(), [])

    #Read the data
    df = pd.read_csv(QC2_path, index_col = 0, parse_dates = [0])
    df_orig = read_data(MET_path, Config_Path)
    df_orig = fill_obs(df_orig)

    #run Savitsky Golay filter where defined
    if RepDict['sgf_pars'] != '':
        sgf_pars = RepDict['sgf_pars'].split(',')
        df = SGF(df, sgf_pars, int(RepDict['sgf_window']), int(RepDict['sgf_order']))

    #Draw plots for the report
    Temp_info(df, Config_Path, img_dir)
    Wind_info(df, Config_Path, img_dir)
    HumPress_info(df,Config_Path, img_dir)

    if 'lw_in' in df.columns or 'lw_out' in df.columns:
        LW_info(df, Config_Path, img_dir)

    if 'sw_in' in df.columns or 'sw_out' in df.columns:
        SW_info(df, Config_Path, img_dir)

    if 'HS' in df.columns:
        Snow_info(df, df_orig, Config_Path, img_dir)


    #Calculate Averages
    AvgTable(df[Parameters], Parameters, tab_dir, Units)

    #Create QC tables
    QCtables(df, Parameters, tab_dir)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        Config_Path = sys.argv[1]
    #Config_Path = 'F:\Þróunarsvið\Rannsóknir\M-Sameign\GAVEL\GAVEL1\B10\GAVEL\Config\LocConfig_B10_2016.ini'

    runme(Config_Path)

#main()
