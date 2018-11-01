# coding=utf-8
import os

# This code runs all the modules of the GAVEL Quality Control system given
# a local configuration file.

def runme():
    # Define the paths to the configuration files
    #Config_Paths = [u'F:\Þróunarsvið\Rannsóknir\M-Sameign\GAVEL\GAVEL1\Budir\GAVEL\Config\LocConfig_Budir_1996.ini']
    Config_dir = u'F:\Þróunarsvið\Rannsóknir\M-Sameign\GAVEL\GAVEL1\Budir\GAVEL\Config'
    Config_Paths = [Config_dir + '\\' + file for file in os.listdir(Config_dir) if '.ini' in file]


    # Loop through the python files
    for Path in Config_Paths:
        QC1command = 'python ' + 'code\QC1.py' + ' ' + Path
        print(QC1command)
        QC2command = 'python ' + 'code\QC2.py' + ' ' + Path
        QCFincommand = 'python ' + 'code\QCFin.py' + ' ' + Path
        Reportcommand = 'python ' + 'code\QCReport.py' + ' ' + Path
        Commands = [QC1command, QC2command, QCFincommand, Reportcommand]
        for command in Commands:
            os.system(command.encode('utf-8'))

    # Update long term stats for the
    update_command = 'python ' + 'code\ConfigStat.py' + ' ' + Path
    os.system(update_command.encode('utf-8'))

    #Produce summary of long term statistics
    summary_command = 'python ' + 'code\TotStat.py' + ' ' + Path
    os.system(summary_command.encode('utf-8'))


if __name__ == '__main__':
    runme()
