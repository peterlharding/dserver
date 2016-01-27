Overview
========

The dserver.ini is used to configure the data to be delivered by the data server.

A sample file - dserver_ini - is provided.  Copy this file to dserver.ini:
 
    $ cp -i dserver_ini dserver.ini

    $ cat dserver.ini

	#----- Example Data Server configuration file ----------------------------------

	[Config]
	Port=9578
	Environment=SVT

	#-------------------------------------------------------------------------------

	[Data]
	Description=VUserIdx:Indexer:{'start':0}
	Description=RunNo:Counter:
	Description=Globals:Hashed:
	Description=Profiles:Indexed:
	Description=SerialNo:Sequence:
	Description=Sequence:Sequence:,
	Description=Indexed:Indexed:,
	Description=Keyed:Keyed:,
	Description=KeyedSequence:KeyedSequence:
	Description=Test:Indexed:
	Description=Store:CSV:|

	#-------------------------------------------------------------------------------

The INI file specified the port the data server will operate on which allows multiple
data servers to operat concurrently

The data set to be used is specified by Environment.  This is the name of the sub-folder
contining the data files - in this case DATA/SVT.  Each data set sub-folder needs to
contain a .dat file for each data source specified in the INI file.

A model Makefile is provided to show rules for settng up and resetting data sets or
components of them.

Each data set directory contains a 'tmp' sub-directory into which .used and .store
files are written along with 'point in time' backups of the data set files




