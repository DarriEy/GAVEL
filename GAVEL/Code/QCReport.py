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

plotsz = (11.69, 3)
plotsz2 = (23, 12)

# ------------------------- Functions to produdce tables for the report -----------------------
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
    ParDictQC1['Num possible Errors'] = df[Parameter + '_QC1'].value_counts().loc[prob_err].sum()
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
    ParDictQC2['Num possible Errors'] = df[Parameter + '_QC2'].value_counts().loc[prob_err].sum()
    ParDictQC2['Num Missing Values'] = df[Parameter + '_QC2'].value_counts().loc[missing].sum()

    return ParDictQC1, ParDictQC2

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
    df_FIN = df_FIN.reindex(flatten([['Units'], new_index, ['Mean']]))
    df_FINs = df_FINs.reindex(flatten([['Units'], new_index, ['Std']]))
    df_FINma = df_FINma.reindex(flatten([['Units'], new_index, ['Max']]))
    df_FINmi = df_FINmi.reindex(flatten([['Units'], new_index, ['Min']]))

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

        #Get final statistics of missing values, possible and certain errors
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

def runme(Config_Path):

    #Read the data paths from the Local Config file
    Config_Path = Config_Path.decode('utf-8')
    PathDict = read_config('Paths', Config_Path)
    QC2_path = PathDict['qc2_path'].decode('utf-8')
    MET_path = PathDict['met_path'].decode('utf-8')
    rep_dir = PathDict['rep_dir'].decode('utf-8')
    tab_dir = os.path.join(rep_dir + 'tables\\'+ 'Tables_' + read_config('meta', Config_Path)['year'])
    RepDict = read_config('Report Config', Config_Path)

    #Create directory for saving tables and images
    try:
        os.makedirs(tab_dir)
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
    df = pd.read_csv(QC2_path, index_col = 0, parse_dates = [0])
    df_orig = read_data(MET_path, Config_Path)

    #run Savitsky Golay filter where defined
    if RepDict['sgf_pars'] == 'true':
        sgf_pars = RepDict['sgf_pars'].split(',')
        df = SGF(df, sgf_pars, int(RepDict['sgf_window']), int(RepDict['sgf_order']))


    #Calculate Averages
    AvgTable(df[Parameters], Parameters, tab_dir, Units)

    #Create QC tables
    QCtables(df, Parameters, tab_dir)


if __name__ == '__main__':

    Config_Path = sys.argv[1]
    runme(Config_Path)

#main()
