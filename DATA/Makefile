#
#  Rules for setting up and resetting data
#
#-------------------------------------------------------------------------------

all:	reset

#-------------------------------------------------------------------------------

setup-tst:
	-(cd TST; make setup)

#-------------------------------------------------------------------------------

setup:
	cp Sequence.master             Sequence.dat
	cp Test.master                 Test.dat
	cp Store.master                Store.dat
	cp Address.master              Address.dat
	cp Indexed.master              Indexed.dat
	cp Keyed.master                Keyed.dat

#-------------------------------------------------------------------------------

reset:
	cp Sequence.master             Sequence.dat
	cp Test.master                 Test.dat
	cp Store.master                Store.dat
	cp Address.master              Address.dat
	cp Indexed.master              Indexed.dat
	cp Keyed.master                Keyed.dat
	cp Bkg.new                     Bkg_Doc_AU.dat
	cp Bkg.new                     Bkg_Doc_GB.dat
	cp Bkg.new                     Bkg_Doc_US.dat

#-------------------------------------------------------------------------------

next_week:
	cp 2Postcodes.master           2Postcodes.dat
	cp 3Postcodes.master           3Postcodes.dat
	cp 4Postcodes.master           4Postcodes.dat

#-------------------------------------------------------------------------------

reset_names:
	cp Addresses_10K.master        Addresses_10K.dat
	cp Names_10K.master            Names_10K.dat

#-------------------------------------------------------------------------------

clean:
	-rm tmp/*2011* tmp/*.used tmp/*.stored

#-------------------------------------------------------------------------------

