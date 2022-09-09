# The OFF ERFS-FPR Pipeline

## Installation of Windows Subsystem for Linux (WSL)

- from the admin (!) console, launch wsl --install, then reboot, then wsl –update (also from admin console), after update run wsl --shutdown to reboot WSL, then wsl --list --online to see available distributions, then install a distribution (here standard option Ubuntu, which works fine) with wsl --install -d Ubuntu
- after installation of distribution, will have to enter a username and password combination for Linux. after this step, the installation is complete. You should be able to directly access the Ubuntu console from a shortcut in the Windows menu (and you should change to this instead of the Windows command prompt now)
- . Admin rights should no longer be necessary from this point on onwards.
- You should be able to access the Linux folders from Windows, they are available as a network drive under \\wsl$\Ubuntu
- optional intermediary step (not documented): use of virtualenv
- Python should already be downloaded and ready-to-use (as python3). I recommend using the python-is-python3 package (sudo apt-get install python-is-python3). Afterwards, you can use Python with the python command only. Before launching this command, it is best to launch sudo apt-get update to update the list of packages.
- One can also install sudo apt-get install python3-pip to better manage Python packages. (after the update command).
- I then created a subfolder "Git" in the user directory for the git repositories, but you can store them wherever you like. Then install all the packages using git clone [URL]. I installed OF-Code, OFF, OFF-SM from GitHub, and OFF-Data from LexImpact's Git (access given by Mahdi). For this particular repository, it may be necessary to set up an SSH key for your account (ssh-keygen, then add public key to Git online).
- For managing Python packages, I use pip. Make sure to use versions compatible with OFF (see setup).
- Then install the OFF packages using pip. Go to each folder, run pip install -e .
- Pro tip: setting up a .wslconfig file to control memory/swap and processor usage

## Set-up of the configuration

- raw\_data.ini and config.ini, as explained in the [OF-SM ReadMe](https://github.com/openfisca/openfisca-survey-manager#getting-the-configuration-directory-path)
- the raw\_data.ini contains the paths to the folders (one for each year) containing the raw ERFS-FPR .dta files

## Building the collections from the raw data

- using the command build-collection -c erfs\_fpr -d -m -v
- this will create the .h5 files in the folder specified in the configuration, one for each year, which are the basis for creating the survey scenario afterwards
- for all years from 1996 to 2017, this can take 2-3 hours
- in principle, this step should not need a lot of verification, since it doesn't alter the tables, it just puts them together; however, it might still be a good idea to check an example.
- also, it may be a good idea to exclude all the non-essential tables (ie. other than fpr\_indiv/irf/menage/mrf\*) because it is likely that they too will be included, inflating the size of the .h5 files

## Building the data

- from the console, launch build-erfs-fpr -y 2016 to launch for a given year, 2016 in this example
- to launch for multiple years, launch build-erfs-fpr -c path/to/raw\_data.ini, where raw\_data.ini can also be another config file that contains an [erfs\_fpr] collection; the path to the standard config file is .config/openfisca-survey-manager/raw\_config.ini, the input.h5 mentioned below will then contain data bases for all the years
- launching these commands will load and transform the raw data, the final data will then be stored in a file named input.h5 in the same folder as the raw .h5 files
- this input.h5 will then be the starting point of the actual analyses

## Producing the results

- for the moment I am using the test\_aggregates.py function to produce some test results
- it can also take as an argument either a year with -y 2016 or a config file with -c path/to/raw\_data.ini, so to launch the calculation for all the results in the input.h5 (assuming it has been produced using the same .ini file), just run python Git/openfisca-france-data/tests/erfs\_fpr/integration/test\_aggregates.py -c .config/openfisca-survey-manager/raw\_data.ini

# Other stuff

- survey\_scenario.create\_data\_frame\_by\_entity(["revenue\_disponible"])["menage"] works for "baseline" -\> maybe can be easily adapted to also produce results for modified simulation
- survey\_scenario.memory\_usage() gives overview of all variables cached and not cached
- survey\_scenario.summarize\_variable("variable\_name") displays summary stats for all periods the variable is calculated for

# Old stuff

## Quick start: How to reproduce the pipeline results on the local machine?

- install all the repositories, see GitHub/Lab for details
  - that also includes the set-up of the .ini configuration files
  - there, in the raw\_data.ini, define a collection named "erfs\_fpr" and supply the paths of all the ERFS data you have (one line = path for each year)
- launch the build-collection -c erfs\_fpr -d -m -v, where erfs\_fpr stands for the collection defined above. this will take the raw data (Stata files) and transform them into raw .h5 files that will be stored in the folder specified in the config (SMCollections \> OutputH5 in my case). These intermediary .h5 files will be used by the survey manager during the next step.
  - I've run this for all the ERFS-FPR years, the (raw) data is ready
- Next, you need to build the ERFS-FPR data. To do this, launch build-erfs-fpr -y 2016 finalh5.h5 where you can replace 2016 with any year you have built in your collection.
  - the .h5 you specify here is where the final data will be stored.
- Finally, to get the end results, you need to launch the script /path\_to\_git/openfisca-france-data/tests/erfs\_fpr/integration/test\_aggregates.py. This will create some aggregate summary stats and save them in CSV/HTML format.

But, what's going on in the background?

there are basically three things to do:

1. make sure the code knows how to handle the data of each year.
2. make sure the tax and benefit system is valid for each of these years.
3. create a script similar to the one for the aggregates with the output we need.