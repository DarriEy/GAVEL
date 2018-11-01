# GAVEL V1.0

GAVEL is a Quality Control (QC) system developed for meteorological observations on Icelandic glaciers recorded by Automatic Weather Stations (AWS) operated by Landsvirkjun. These observations are, among other applications, used to run hydrological models that predict inflow into the company’s reservoirs. Therefore, the reliability of these measurements is of high importance. The GAVEL system performs several QC tests on meteorological data that identify suspect or incorrect observations. The purpose of the GAVEL project is firstly to prevent data users from using suspect or incorrect data and secondly, to publish long-term records of quality controlled meteorological timeseries from the Icelandic glaciers. These long-term records are of interest for e.g. glaciological and climatological research and for the development of various glaciological and hydrological models.

Overview 
The structure of the GAVEL system is based on automatic quality control methods used at the meteorological institutions in the Nordic countries and are described in the NORDKLIM project (Vejen, o.fl., 2002). In the system quality control is divided in 4 separate levels, depending on the detail of the QC tests. QC0 is performed at the AWS site, QC1 comprises fast testing that can be performed on the data from the sites in real time, QC2 tests data that has been stored in databases with more thorough testing than can be done in real time. Lastly the data that has been evaluated automatically is inspected by trained QC personnel which are the ultimate check on assessing suspect data. In GAVEL QC0 info is acquired from the stations where available, otherwise data from the stations is assumed to have passed QC0. Human Quality Control (HQC) is not a part of the present version of GAVEL, however, a series of analysis plots are produced from the QC2 output which aid in the execution of HQC. 

RAW data is fed into the QC1 module where a series of simple tests are performed. Data is flagged according to reliability based on the test results. The flagged data is then fed into the QC2 module where obviously erroneous data are removed and small gaps are interpolated (length of gap and gap filling method are defined in the local parameter file). The gap filled data is then subjected first to the same tests as in QC1, then to more complicated statistical and spatial tests (NOTE, spatial tests have not been applied to GAVEL v1.0). The data from QC2 is then fed into the results modules. The information from the QC parts is used to provide a final QC flag and the dataset is saved for either HQC or end use. If specified in the global parameter file, long term statistics are updated and analysis plots and tables are produced. 


The GAVEL file structure is split in two sections. All the files necessary to run GAVEL are in the GAVEL folder, these include the GAVEL.py master program and QC1.py, QC2.py and QCplot.py submodules. All files associated with specific AWS site are located in the GlacierAWS folder, where subfolders contain all datafiles for each station. The AWS data is organized in the RAW data folder (including metadata), the Published data folder (including plots and images from the sites) and the GAVEL folder which contains outputs from the QC submodules.

Description of key files:
	GAVEL.py: Python file that runs the entire GAVEL scheme. Initiates other modules according to the configurations defined in the global config file GloConfig.ini
Location: ~\GAVEL\
	QC1.py: Python file that runs the QC1 module of GAVEL. Simple QC tests and functions are defined within and imported into other modules as needed.
Location: ~\GAVEL\Code\
	QC2.py: Python file that runs the QC2 module of GAVEL. Obvious errors are discarded, gaps interpolated and simple tests re-run. More complicated QC tests are defined here.
Location: ~\GAVEL\Code\
	QCFin.py: Python file that complies the information from all the QC tests and produces a final QC code and outputs final dataset.
Location: ~\GAVEL\Code\
	QCplot.py: Python file that produces plots of the raw data and QC data throughout the scheme to illustrate the steps taken and highlights potential errors. 
Location: ~\GAVEL\Code\
	ConfigStat.py: Python file that calculates statistical values for each parameter and updates the local configuration files given new data.
Location: ~\GAVEL\Code\
	GloConfig.ini: Global configuration file. Paths to specific local configuration files are provided to GAVEL.py and options for which GAVEL modules to run. 
Location: ~\GAVEL\
	LocConfig_AWS_YYYY.ini: Local Configuration file, station and year specific. Paths to data files are specified here, and options for running GAVEL are defined.
Location: ~\GAVEL1\GlacierAWS\AWS \GAVEL\Config
GAVELHHMM_DDMMYY.log: Log file for each GAVEL run
Location: ~\GAVEL\LogFiles\
AWS_META.xlx: Excel file with summary of station metadata
Location: ~\GlacierAWS\AWS*\
	VST_AWS_MET.dat: Data file. Preprocessed met data used as input to GAVEL
Location: ~\GlacierAWS\AWS*\RAW\YYYY\
	VST_AWS_QCFin_YYYY.csv: Data file with final QC controlled data with final QC flags, site and year specific.
Location: ~\GlacierAWS\AWS*\Published\data
	VST_AWS_QCFin_ALL.dat: Data file. Final output from GAVEL. All years on record for specific site with final QC flags.
Location: ~\GlacierAWS\AWS*\Published\data

Future Work:
The structure and key QC tests of GAVEL V1.0 have been developed and bug tested on most glacial AWS data available. Full time series of quality controlled data are being produced for all the glacial AWS sites operated by Landsvirkjun. Further work could be undertaken to improve and expand the functionality of the GAVEL system, as well as to apply it to a wider range of data, including land based AWS data, reservoir level data and other hydro-meteorological data. Among the potential improvements to the current system are: 

•	Calculate icing probability
•	Clean up snow depth data and incorporate manual snow depth measurements
•	Apply GAVEL to real time data acquisition
•	Develop HQC module
•	More detailed analysis of AWS data, including energy balance analysis
•	Apply spatial tests and comparison with weather models
•	Apply GAVEL to land based AWS and other hydro-meteorological data 
•	Correct precipitation data for land based AWS
