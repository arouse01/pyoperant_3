import os
import csv
import copy
import datetime as dt
import numpy as np
from scipy.stats import norm
from scipy.stats import beta
import pandas as pd
from pyoperant import analysis

try:
    import simplejson as json
except ImportError:
    import json


class Performance(object):

    def __init__(self, experiment_folder):
        if not os.path.exists(experiment_folder):
            print "invalid input folder"
            return
        self.data_dir = os.path.join(experiment_folder, 'trialdata')
        self.json_dir = os.path.join(experiment_folder, 'settings_files')
        # error check
        if not os.path.exists(self.data_dir):
            print "data folder (%s) not found" % self.data_dir
            return
        elif not os.path.exists(self.json_dir):
            print "json folder (%s) not found" % self.json_dir
            return

        self.startDate = '01/01/2018'

        self.data_dict = {'File': [],
                          'Subject': [],
                          'Session': [],
                          'Block': [],
                          'Index': [],
                          'Time': [],
                          'Stimulus': [],
                          'Class': [],
                          'Response': [],
                          'RT': [],
                          'Reward': [],
                          'Punish': []
                          }

    def checkequal(self, list_to_check):
        return not list_to_check or list_to_check.count(list_to_check[0]) == len(list_to_check)

    def analyze(self, option='day'):

        csvList = os.listdir(self.data_dir)
        # Filter list here, if needed

        csvCount = len(csvList)
        for i in range(csvCount):
            csvPath = os.path.join(self.data_dir, csvList[i])
            with open(csvPath) as data_file:
                csv_reader = csv.reader(data_file, delimiter=',')

                rowCount = sum(1 for row in csv_reader) - 1  # check if csv only has 1 line

                if rowCount < 1:
                    fileEmpty = True
                else:
                    fileEmpty = False

            if fileEmpty is False:
                with open(csvPath) as data_file:
                    csv_reader = csv.reader(data_file,
                                            delimiter=',')  # reinitialize so the 'current line count' is reset
                    currentLine = 0
                    for row in csv_reader:
                        if currentLine == 0:
                            pass
                        else:
                            self.data_dict['Index'].append(row[1])
                            self.data_dict['Stimulus'].append(row[3])
                            self.data_dict['Class'].append(row[4])
                            self.data_dict['Response'].append(row[5])
                            self.data_dict['RT'].append(row[7])
                            self.data_dict['Reward'].append(row[8])
                            self.data_dict['Punish'].append(row[9])
                            self.data_dict['Time'].append(row[10])
                            self.data_dict['Session'].append(i)
                            self.data_dict['File'].append(csvList[i])
                            self.data_dict['Subject'].append(csvList[i].partition('_')[0])
                        currentLine += 1

                jsonFile = os.path.splitext(csvList[i])[0].rpartition('_')[2] + '.json'
                jsonPath = os.path.join(self.json_dir, jsonFile)
                with open(jsonPath, 'r') as f:
                    jsonData = json.load(f)
                blockName = jsonData['block_design']['order'][0]
                for j in range(currentLine - 1):
                    self.data_dict['Block'].append(blockName)
        # Double check that each key in dict has same length
        trialCount = len(self.data_dict['Index'])  # 'Index' is arbitrary, just need total count of trials
        keyLengths = [len(x) for x in self.data_dict.values()]
        if not self.checkequal(keyLengths):
            raise Exception('Columns are not equal length')

        if trialCount < 1:
            print 'No trials found'
        else:
            self.response_hit = [0] * trialCount
            self.response_FA = [0] * trialCount
            self.response_Miss = [0] * trialCount
            self.response_CR = [0] * trialCount
            self.response_Miss_NR = [0] * trialCount
            self.response_CR_NR = [0] * trialCount
            self.response = [1] * trialCount  # To end up being the trials/day field

            for i in range(trialCount):
                if self.data_dict['Response'][i] == "ERR":
                    pass
                elif self.data_dict['Class'][i] == "probePlus" or self.data_dict['Class'][i] == "sPlus":
                    if self.data_dict['Response'][i] == "sPlus":
                        self.response_hit[i] = 1
                    elif self.data_dict['Response'][i] == "sMinus":
                        self.response_Miss[i] = 1
                    else:
                        # No response
                        self.response_Miss_NR[i] = 1

                elif self.data_dict['Class'][i] == "probeMinus" or self.data_dict['Class'][i] == "sMinus":
                    if self.data_dict['Response'][i] == "sPlus":
                        self.response_FA[i] = 1
                    elif self.data_dict['Response'][i] == "sMinus":
                        self.response_CR[i] = 1
                    else:
                        # No response
                        self.response_CR_NR[i] = 1

            self.data_dict['Hit'] = self.response_hit
            self.data_dict['False_Alarm'] = self.response_FA
            self.data_dict['Miss'] = self.response_Miss
            self.data_dict['CR'] = self.response_CR
            self.data_dict['Miss_NR'] = self.response_Miss_NR
            self.data_dict['CR_NR'] = self.response_CR_NR
            self.data_dict['Trial_Count'] = self.response
            self.trialData = pd.DataFrame.from_dict(self.data_dict)  # Convert to data frame
            self.trialData['Date'] = pd.to_datetime(self.trialData['Time'], format='%Y/%m/%d')

            self.performanceData = pd.DataFrame()
            self.performanceData['Date'] = pd.to_datetime(self.trialData['Time'], format='%Y/%m/%d')
            self.performanceData['Block'] = self.data_dict['Block']
            self.performanceData['Hit'] = self.response_hit
            self.performanceData['False_Alarm'] = self.response_FA
            self.performanceData['Miss'] = self.response_Miss
            self.performanceData['CR'] = self.response_CR
            self.performanceData['Miss_NR'] = self.response_Miss_NR
            self.performanceData['CR_NR'] = self.response_CR_NR
            self.performanceData['Trials'] = self.response

            if option == 'day':
                # Now have all trials in lists, need to group them
                groupData = self.performanceData.groupby([self.performanceData['Date'].dt.date, self.performanceData[
                    'Block']]).sum()
                groupCount = len(groupData)
                dprimes = []
                dprimes_NR = []
                for k in range(groupCount):
                    hitCount = groupData['Hit'][k]
                    missCount = groupData['Miss'][k]
                    missNRCount = groupData['Miss_NR'][k]
                    FACount = groupData['False_Alarm'][k]
                    CRCount = groupData['CR'][k]
                    CRNRCount = groupData['CR_NR'][k]
                    dayDprime = analysis.Analysis([[hitCount, missCount], [FACount, CRCount]]).dprime()
                    dprimes.append(dayDprime)
                    dayDprime_NR = analysis.Analysis([[hitCount, (missCount + missNRCount)],
                                                      [FACount, (CRCount + CRNRCount)]]).dprime()
                    dprimes_NR.append(dayDprime_NR)
                groupData['dPrime'] = dprimes
                groupData['dPrime_NR'] = dprimes_NR
                return groupData

            elif option == 'raw':
                self.trialData = pd.DataFrame.from_dict(self.data_dict)  # Convert to data frame
                self.trialData['Date'] = pd.to_datetime(self.trialData['Time'], format='%Y/%m/%d')
                return self.trialData
    # Get date range?
    # Loop:
    # import first data csv
    # if csv is empty
    # pass
    # else:
    # append columns index(2), stimulus(4), class(5), response(6), rt(8), reward(9), punish(10), time(11)
    # open json that matches csv name
    # extract block order, append to data (to add which block each line came from)
    # i++
    # Remove any erroneous lines (class_ of ERR)
    # Split data array by date (or other criteria)
    # for each group:
    # calculate d' across whole group
    # Average rt for trials with one
    # other stats

# datapath = '/home/rouse/bird/data/y18r8'
# perform = Performance(datapath)
# stats = perform.analyze('raw')
# stats.to_csv(os.path.join(datapath,'test.csv'))
# print stats
