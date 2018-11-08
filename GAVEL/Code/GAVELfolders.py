# coding=utf-8
import os
import sys
import datetime

'''
Module which creates folder structure for a new AWS site in the GAVEL quality
control system

File name: GAVELfolders.py
Author: Darri Eythorsson
Date Created: 26.10.2018
Date Last Modified: 02.11.2018
Python Version: 2.7
Version: 1.0
'''

def runme(Root_Path):
    #Read the data paths from the Local Config file
    year = datetime.datetime.now().year
    Root_Path = Root_Path.decode('utf-8')

    #Make AWS base direcotry
    os.makedirs(Root_Path)

    #Make directories in RAW folder
    os.makedirs(Root_Path + 'RAW')
    os.makedirs(Root_Path + 'RAW\\year')
    os.makedirs(Root_Path + 'RAW\\META')

    #Make directories in Published folder
    os.makedirs(Root_Path + 'Published')
    os.makedirs(Root_Path + 'Published\\data')
    os.makedirs(Root_Path + 'Published\\figures')
    os.makedirs(Root_Path + 'Published\\img')
    os.makedirs(Root_Path + 'Published\\report')
    os.makedirs(Root_Path + 'Published\\report\\tex')
    os.makedirs(Root_Path + 'Published\\tables')

    #Make Directories in GAVEL folder
    os.makedirs(Root_Path + 'GAVEL')
    os.makedirs(Root_Path + 'GAVEL\\Code')
    os.makedirs(Root_Path + 'GAVEL\\Config')
    os.makedirs(Root_Path + 'GAVEL\\QC')
    os.makedirs(Root_Path + 'GAVEL\\QC\\QC1')
    os.makedirs(Root_Path + 'GAVEL\\QC\\QC2')
    os.makedirs(Root_Path + 'GAVEL\\QC\\QC3')

if __name__ == '__main__':
    Root_Path = 'F:\\Þróunarsvið\\Rannsóknir\\M-Sameign\\GAVEL\GAVEL1\\GlacierAWS\\TEST\\'
    Root_Path = sys.argv[1]
    runme(Root_Path)
