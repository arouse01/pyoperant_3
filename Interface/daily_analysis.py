from pyoperant import analysis
import os
from datetime import datetime, timedelta
import logging, traceback
import sys

"""
Script to analyze bird data and compile into single file per bird
Primarily used to make data more accessible by then moving the output to a Box folder 
"""

# region Error Handling
"""Since this is run through a cron job, need to catch errors and put them somewhere else. Otherwise they get emailed 
every time there's an error, which is annoying since this script runs daily"""


def _log_except_hook(*exc_info):  # How uncaught errors are handled
    text = "".join(traceback.format_exception(*exc_info))
    logging.error("Unhandled exception: {}".format(text))


def log_config():
    # capture all terminal output and send to log file instead
    log_file = os.path.join(os.getcwd(), 'daily_analysis_log.log')
    error_file = os.path.join(os.getcwd(), 'daily_analysis_error.log')
    log_path = os.path.join(os.getcwd())
    if not os.path.exists(log_path):  # Add path if it doesn't exist
        os.makedirs(log_path)

    log_level = logging.INFO

    sys.excepthook = _log_except_hook  # send uncaught exceptions to log file

    logging.basicConfig(filename=log_file,
                        level=log_level,
                        format='"%(asctime)s","%(levelname)s","%(message)s"')
    log = logging.getLogger()
    errorHandler = logging.FileHandler(error_file, mode='a')
    errorHandler.setLevel(logging.ERROR)
    errorHandler.setFormatter(logging.Formatter('"%(asctime)s","%(message)s'))

    log.addHandler(errorHandler)


# endregion


log_config()
dataDir = '/home/rouse/bird/data'
days_prior = 5

folderList = []

# Get list of folders in data directory
targetDateTime = datetime.today() - timedelta(days=days_prior)
for i in os.listdir(dataDir):
    currFolder = os.path.join(dataDir, i)

    # check that current folder is actually a data folder
    currFolderDataPath = os.path.join(currFolder, 'trialdata')
    if os.path.exists(currFolderDataPath):
        if i == 'test':  # skip test folder
            pass
        elif days_prior < 0:  # if days_prior is -1, ignore modification dates and just export all
            folderList.append(i)
        else:  # Retain only folders that have been modified in previous days_prior days
            folderInfo = os.stat(currFolderDataPath)
            folderModTime = datetime.fromtimestamp(folderInfo.st_mtime)
            if folderModTime > targetDateTime:
                folderList.append(i)

outputFolder = '/home/rouse/Desktop/daily_summary'

birdCount = len(folderList)
if birdCount > 0:
    # print("Exporting data for %d birds" % birdCount)
    currNum = 0
    for a in folderList:
        currNum = currNum + 1
        # print("  Exporting %s... (%d/%d)" % (a, currNum, len(folderList)))
        outputPath = os.path.join(outputFolder, a + '.csv')
        dataPath = os.path.join(dataDir, a)
        data = analysis.Performance(dataPath)
        data.raw_trial_data.to_csv(str(outputPath), mode='w+')
