#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import csv
import copy
import datetime as dt
import numpy as np
from scipy.stats import norm
from scipy.stats import beta
import pandas as pd
import re
import string

try:
    import simplejson as json
except ImportError:
    import json


# from matplotlib import mlab

# region Raw stats
# d-prime
def dprime(confusion_matrix):
    """
    Function takes in a 2x2 confusion matrix and returns the d-prime value for the predictions.

    d' = z(hit rate)-z(false alarm rate)

    http://en.wikipedia.org/wiki/D'
    """

    if max(confusion_matrix.shape) > 2:
        return False
    else:
        # Check that hit rate and FA rate can be calculated (i.e. avoid divideByZero error
        if confusion_matrix[0, :].sum() == 0:
            hit_rate = 0
            nudge_hit = 1e-10
        else:
            hit_rate = confusion_matrix[0, 0] / confusion_matrix[0, :].sum()
            nudge_hit = 1.0 / (2.0 * confusion_matrix[0, :].sum())

        if confusion_matrix[1, :].sum() == 0:
            fa_rate = 0
            nudge_fa = 1e-10
        else:
            fa_rate = confusion_matrix[1, 0] / confusion_matrix[1, :].sum()
            nudge_fa = 1.0 / (2.0 * confusion_matrix[1, :].sum())

        # Correction if hit_rate or fa_rate equals 0 or 1 (following suggestion of Macmillan & Kaplan 1985)
        if hit_rate >= 1:
            hit_rate = 1 - nudge_hit
        if hit_rate <= 0:
            hit_rate = 0 + nudge_hit
        if fa_rate >= 1:
            fa_rate = 1 - nudge_fa
        if fa_rate <= 0:
            fa_rate = 0 + nudge_fa

        dp = norm.ppf(hit_rate) - norm.ppf(fa_rate)
        return dp


# bias measurement
def bias(confusion_matrix):
    if max(confusion_matrix.shape) > 2:
        return False
    else:
        if confusion_matrix[0, :].sum() == 0:
            hit_rate = 0
            nudge_hit = 1e-10
        else:
            hit_rate = confusion_matrix[0, 0] / confusion_matrix[0, :].sum()
            nudge_hit = 1.0 / (2.0 * confusion_matrix[0, :].sum())

        if confusion_matrix[1, :].sum() == 0:
            fa_rate = 0
            nudge_fa = 1e-10
        else:
            fa_rate = confusion_matrix[1, 0] / confusion_matrix[1, :].sum()
            nudge_fa = 1.0 / (2.0 * confusion_matrix[1, :].sum())

        # Correction if hit_rate or fa_rate equals 0 or 1 (following suggestion of Macmillan & Kaplan 1985)
        if hit_rate >= 1:
            hit_rate = 1 - nudge_hit
        if hit_rate <= 0:
            hit_rate = 0 + nudge_hit
        if fa_rate >= 1:
            fa_rate = 1 - nudge_fa
        if fa_rate <= 0:
            fa_rate = 0 + nudge_fa

        bias_c = -0.5 * (norm.ppf(hit_rate) + norm.ppf(fa_rate))

        dp = dprime(confusion_matrix)

        bias_beta = np.exp(dp * bias_c)

        return bias_beta


# accuracy (% correct)
def acc(confusion_matrix):
    """Function takes in a NxN confusion matrix
    and returns the fraction of correct predictions"""

    x = confusion_matrix.diagonal().sum()
    N = confusion_matrix.sum()
    p = x / N

    return p


# accuracy (% correct)
def acc_ci(confusion_matrix, alpha=0.05):
    """Function takes in a NxN confusion matrix
    and returns the fraction of correct predictions"""

    x = confusion_matrix.diagonal().sum()
    N = confusion_matrix.sum()

    ci = beta.interval(1 - alpha, x, N - x)
    return ci


# matthew's correlation coefficient
def mcc(confusion_matrix):
    """Function takes in a 2x2 confusion matrix
    and returns the Matthew's Correlation Coefficient for the predictions.

    MCC = (TP*TN-FP*FN)/sqrt((TP+FP)*(TP+FN)*(TN+FP)*(TN+FN))

    http://en.wikipedia.org/wiki/Matthews_correlation_coefficient

    """
    if max(confusion_matrix.shape) > 2:
        return False
    else:
        true_pos = confusion_matrix[0, 0]
        true_neg = confusion_matrix[1, 1]
        false_pos = confusion_matrix[1, 0]
        false_neg = confusion_matrix[0, 1]
        a = (true_pos * true_neg - false_pos * false_neg) / np.sqrt(
            (true_pos + false_pos) * (true_pos + false_neg) * (true_neg + false_pos) * (true_neg + false_neg))
        return a


def create_conf_matrix(expected, observed):
    """
    Function takes in a 1-D array of expected values and a 1-D array of predictions
    and returns a confusion matrix with size corresponding to the number of classes.

    http://en.wikipedia.org/wiki/Confusion_matrix

    Keyword arguments:
    expected  -- list of expected or true values
    observed -- list of observed or response values

    Returns the confusion matrix as a numpy array m[expectation,prediction]

    """
    n_classes = max(len(set(expected)), len(set(observed)), 2)

    m = np.zeros((n_classes, n_classes))
    for exp, pred in zip(expected, observed):
        m[exp, pred] += 1
    return m


def create_conf_matrix_summary(matrix):
    """
    Function takes in a 2-D confusion matrix and converts it to an array.

    http://en.wikipedia.org/wiki/Confusion_matrix

    Keyword arguments:
    expected  -- list of expected or true values
    observed -- list of predicted or response values

    Returns the confusion matrix as a numpy array m[expectation,prediction]

    """

    mArray = np.asarray(matrix)
    m = mArray.astype(float)
    return m


# endregion


class Analysis:
    """ use this to compute performance metrics """

    def __init__(self, matrix):
        self.confusion_matrix = create_conf_matrix_summary(matrix)

    def n_classes(self):
        return max(self.confusion_matrix.shape)

    def dprime(self):
        return dprime(self.confusion_matrix)

    def bias(self):
        return bias(self.confusion_matrix)

    def acc(self):
        return acc(self.confusion_matrix)

    def acc_ci(self):
        return acc_ci(self.confusion_matrix)

    def mcc(self):
        return mcc(self.confusion_matrix)


class Session(object):
    """docstring for Session"""

    def __init__(self, arg):
        super(Session, self).__init__()
        self.arg = arg


def field_list():
    fieldList = ['Subject', 'File', 'Session', 'File Count', 'Date', 'Time', 'Block', 'Index', 'Stimulus', 'Class']
    fieldList += ['Response Type', 'Response', 'RT', 'Reward', 'Punish']

    fieldList += ["d'", "d'\n(NR)", u'Beta', u'Beta\n(NR)', 'Trials']
    fieldList += ['S+', 'S+\n(NR)', 'S-', 'S-\n(NR)', 'Total Corr', 'Total Corr\n(NR)']
    fieldList += ['Hit', 'Miss', 'Miss\n(NR)', 'FA', 'CR', 'CR\n(NR)']

    fieldList += ["Probe d'", "Probe d'\n(NR)", u'Probe Beta', u'Probe Beta\n(NR)', 'Probe Trials']
    fieldList += ['Probe S+', 'Probe S+\n(NR)', 'Probe S-', 'Probe S-\n(NR)', 'Probe Tot Corr', 'Probe Tot Corr\n(NR)']
    fieldList += ['Probe Hit', 'Probe Miss', 'Probe Miss\n(NR)', 'Probe FA', 'Probe CR', 'Probe CR\n(NR)']
    return fieldList


class Performance(object):
    # Longer-term performance analysis

    def __init__(self, experiment_folder):
        # convert experiment_folder to list if single item
        if type(experiment_folder) is not 'list':
            experiment_folder = [experiment_folder]
        self.data_dir = []
        self.json_dir = []
        for singleDir in experiment_folder:
            # Validate input folder(s)
            if not os.path.exists(singleDir):
                print "invalid input folder"
                return

            singleData = os.path.join(singleDir, 'trialdata')
            if not os.path.exists(singleData):
                print "data folder (%s) not found" % singleDir
                return
            else:
                self.data_dir.append(singleData)

                singleJson = os.path.join(singleDir, 'settings_files')
                if not os.path.exists(singleJson):
                    print "json folder (%s) not found" % singleJson
                    return
                else:
                    self.json_dir.append(os.path.join(singleDir, 'settings_files'))

        # Each row in dataDict will be a single
        dataDict = {'File': [],
                    'Subject': [],
                    'Session': [],
                    'File Count': [],
                    # 'Type': [],
                    'Block': [],
                    'Index': [],
                    'Time': [],
                    'Response Type': [],
                    'Stimulus': [],
                    'Class': [],
                    'Response': [],
                    'RT': [],
                    'Reward': [],
                    'Punish': []
                    }
        self.gather_raw_data(dataDict)

    def classify_response(self, response=None, trial_class=None):
        # Preset so the variables don't arrive to the return section with no value

        trial_type = None

        if response == 'ERR':
            pass
        elif trial_class == 'probePlus':
            if response == 'sPlus':
                trial_type = 'probe_hit'
            elif response == 'sMinus':
                trial_type = 'probe_Miss'
            else:
                # No response
                trial_type = 'probe_Miss_NR'

        elif trial_class == 'probeMinus':
            if response == 'sPlus':
                trial_type = 'probe_FA'
            elif response == 'sMinus':
                trial_type = 'probe_CR'
            else:
                # No response
                trial_type = 'probe_CR_NR'

        elif trial_class == 'sPlus':
            if response == 'sPlus':
                trial_type = 'response_hit'
            elif response == 'sMinus':
                trial_type = 'response_Miss'
            else:
                # No response
                trial_type = 'response_Miss_NR'

        elif trial_class == 'sMinus':
            if response == 'sPlus':
                trial_type = 'response_FA'
            elif response == 'sMinus':
                trial_type = 'response_CR'
            else:
                # No response
                trial_type = 'response_CR_NR'

        return trial_type

    def classify_trial_binary(self, row, match_trial_type):
        # Preset so the variables don't arrive to the return section with no value
        trial_class = None
        trial_type = None

        if response == 'ERR':
            return 0
        elif trial_class == 'probePlus':
            trial_class = 'probe'
            if response == 'sPlus':
                trial_type = 'probe_hit'
            elif response == 'sMinus':
                trial_type = 'probe_Miss'
            else:
                # No response
                trial_type = 'probe_Miss_NR'

        elif trial_class == 'probeMinus':
            trial_class = 'probe'
            if response == 'sPlus':
                trial_type = 'probe_FA'
            elif response == 'sMinus':
                trial_type = 'probe_CR'
            else:
                # No response
                trial_type = 'probe_CR_NR'

        elif trial_class == 'sPlus':
            trial_class = 'training'
            if response == 'sPlus':
                trial_type = 'response_hit'
            elif response == 'sMinus':
                trial_type = 'response_Miss'
            else:
                # No response
                trial_type = 'response_Miss_NR'

        elif trial_class == 'sMinus':
            trial_class = 'training'
            if response == 'sPlus':
                trial_type = 'response_FA'
            elif response == 'sMinus':
                trial_type = 'response_CR'
            else:
                # No response
                trial_type = 'response_CR_NR'

        if match_trial_type == trial_class:
            return 1
        elif match_trial_type == trial_type:
            return 1
        else:
            return 0

    def gather_raw_data(self, data_dict):
        # Pull data from across multiple csv files, keeping notation for phase (which comes from the json file)

        # region Read each CSV file
        for dir_index, curr_dir in enumerate(self.data_dir):
            csvList = os.listdir(curr_dir)
            readMethod = 3
            if readMethod == 1:
                pass
            #     data_dict_group = []
            #     # import as DataFrames, slow
            #     for curr_csv in csvList:
            #         csvPath = os.path.join(curr_dir, curr_csv)
            #
            #         raw_dict = pd.read_csv(csvPath)
            #         # Add other columns, if missing
            #         if 'subject' not in raw_dict:
            #             raw_dict['Subject'] = curr_csv.partition('_')[0]
            #         if 'file count' not in raw_dict:
            #             raw_dict['File_count'] = i
            #         if 'file' not in raw_dict:
            #             raw_dict['File'] = curr_csv
            #         if 'block' not in raw_dict:
            #
            #             # jsonFile = os.path.splitext(curr_csv)[0].rpartition('_')[2] + '.json'
            #             jsonFile = os.path.splitext(curr_csv.replace('trialdata', 'settings'))[0] + '.json'
            #             jsonPath = os.path.join(self.json_dir[dir_index], jsonFile)
            #             with open(jsonPath, 'r') as f:
            #                 jsonData = json.load(f)
            #             block = jsonData['block_design']['order'][0]
            #             # update for old names (before blocks had more descriptive names)
            #             if block == 'training 1':
            #                 block = 'training 125'
            #             elif block == 'training 2':
            #                 block = 'training 150'
            #             elif block == 'training 3':
            #                 block = 'training 125/150'
            #             elif block == 'training 4':
            #                 block = 'training 100'
            #             elif block == 'training 4b':
            #                 block = 'training 175'
            #             elif block == 'training 5':
            #                 block = 'training 100/125/150'
            #             elif block == 'training 5b':
            #                 block = 'training 125/150/175'
            #
            #             raw_dict['block'] = block
            #
            #         data_dict_group.append(raw_dict)
            #         data_dict = pd.concat(data_dict_group, ignore_index=True)
            #         column_names = [x.capitalize() for x in data_dict.columns]
            #         column_names = [x.translate(string.maketrans("", ""), string.punctuation) for x in column_names]
            #         data_dict.columns = column_names
            #         data_dict.Rt.rename('RT')

            elif readMethod == 2:
                pass
            #     # alternate import method, directly as csv
            #     for curr_csv in csvList:
            #         csvPath = os.path.join(curr_dir, curr_csv)
            #         with open(csvPath, 'rb') as data_file:
            #             csv_reader = csv.reader(data_file, delimiter=',')
            #             rowCount = len(list(csv_reader)) - 1  # check if csv has data beyond header
            #             if rowCount < 1:
            #                 fileEmpty = True
            #             else:
            #                 fileEmpty = False
            #
            #         if fileEmpty is False:  # Separated from above to allow data_file to close and be reopened
            #             # for actual scanning
            #             with open(csvPath) as data_file:
            #                 csv_reader = csv.reader(data_file, delimiter=',')
            #                 currentLine = 0  # resets each time so later we can tell how many lines were imported
            #                 column_names = []
            #                 for row in csv_reader:
            #                     # Get block names just in case it's not included in data file
            #                     jsonFile = os.path.splitext(curr_csv.replace('trialdata', 'settings'))[
            #                                    0] + '.json'
            #                     jsonPath = os.path.join(dir_index, jsonFile)
            #                     with open(jsonPath, 'r') as f:
            #                         jsonData = json.load(f)
            #                     blockList = jsonData['block_design']['order']
            #                     # update for old names (before blocks had more descriptive names)
            #                     if type(blockList) is not 'list':
            #                         blockList = [blockList]
            #                     for k in xrange(len(blockList)):
            #                         if blockList[k] == 'training 1':
            #                             blockList[k] = 'training 125'
            #                         elif blockList[k] == 'training 2':
            #                             blockList[k] = 'training 150'
            #                         elif blockList[k] == 'training 3':
            #                             blockList[k] = 'training 125/150'
            #                         elif blockList[k] == 'training 4':
            #                             blockList[k] = 'training 100'
            #                         elif blockList[k] == 'training 4b':
            #                             blockList[k] = 'training 175'
            #                         elif blockList[k] == 'training 5':
            #                             blockList[k] = 'training 100/125/150'
            #                         elif blockList[k] == 'training 5b':
            #                             blockList[k] = 'training 125/150/175'
            #
            #                     if currentLine == 0:
            #                         # Get column names from first row
            #                         for column in row:
            #                             if column == 'rt':
            #                                 col_name = 'RT'
            #                             else:
            #                                 col_name = column.capitalize()
            #                                 col_name = col_name.translate(string.maketrans("", ""), string.punctuation)
            #                             column_names.append(col_name)  # ignore first line (headers)
            #
            #                     else:
            #                         # Rather than manually coding which column is which, match to name from first row
            #                         for column in xrange(len(row)):
            #                             if column_names[column] == 'Stimulus':
            #                                 stim_name = re.split('/', row[3])
            #                                 data_dict['Stimulus'].append(stim_name[-1])
            #                             else:
            #                                 # col_name = column_names[column].capitalize()
            #                                 # col_name = col_name.translate(string.maketrans("",""), string.punctuation)
            #                                 data_dict[column_names[column]].append(row[column])
            #                         if 'Subject' not in column_names:
            #                             data_dict['Subject'].append(curr_csv.partition('_')[0])
            #                         if 'File Count' not in column_names:
            #                             data_dict['File_Count'].append(dir_index)
            #                         if 'File' not in column_names:
            #                             data_dict['File'].append(curr_csv)
            #                         if 'Block' not in column_names:
            #                             block_number = int(data_dict['Session'][-1]) - 1
            #                             data_dict['Block'].append(blockList[block_number])
            #                         # data_dict['File_Count'].append(dir_index)
            #                         # data_dict['File'].append(curr_csv)
            #                         # data_dict['Subject'].append(curr_csv.partition('_')[0])
            #                     currentLine += 1
            #
            #             # jsonFile = os.path.splitext(curr_csv)[0].rpartition('_')[2] + '.json'
            #             # jsonPath = os.path.join(self.json_dir, jsonFile)
            #             # with open(jsonPath, 'r') as f:
            #             #     jsonData = json.load(f)
            #             # block = jsonData['block_design']['order'][0]
            #             # # update for old names (before blocks had more descriptive names)
            #             # if block == 'training 1':
            #             #     block = 'training 125'
            #             # elif block == 'training 2':
            #             #     block = 'training 150'
            #             # elif block == 'training 3':
            #             #     block = 'training 125/150'
            #             # elif block == 'training 4':
            #             #     block = 'training 100'
            #             # elif block == 'training 4b':
            #             #     block = 'training 175'
            #             # elif block == 'training 5':
            #             #     block = 'training 100/125/150'
            #             # elif block == 'training 5b':
            #             #     block = 'training 125/150/175'
            #             #
            #             # for curr_dir in xrange(currentLine - 1):
            #             #     data_dict['Block'].append(block)
            #     data_dict = pd.DataFrame.from_dict(data_dict)  # Convert to data frame
            #

            elif readMethod == 3:
                # Modification of method 5: Adding block name based on session number
                # a little slower but with flexibility of files with more than one block

                # Add specific response columns to data_dict
                data_dict['Hit'] = []
                data_dict['FA'] = []
                data_dict['Miss'] = []
                data_dict['CR'] = []
                data_dict['Miss\n(NR)'] = []
                data_dict['CR\n(NR)'] = []
                data_dict['Trials'] = []
                data_dict['Probe Hit'] = []
                data_dict['Probe FA'] = []
                data_dict['Probe Miss'] = []
                data_dict['Probe CR'] = []
                data_dict['Probe Miss\n(NR)'] = []
                data_dict['Probe CR\n(NR)'] = []
                data_dict['Probe Trials'] = []

                for curr_csv in csvList:
                    csvPath = os.path.join(curr_dir, curr_csv)
                    with open(csvPath, 'rb') as data_file:
                        csv_reader = csv.reader(data_file, delimiter=',')
                        rowCount = len(list(csv_reader)) - 1  # check if csv has data beyond header
                        if rowCount < 1:
                            fileEmpty = True
                        else:
                            fileEmpty = False

                    if fileEmpty is False:  # Separated from above to allow data_file to close and be reopened
                        # for actual scanning
                        jsonFile = os.path.splitext(curr_csv.replace('trialdata', 'settings'))[0] + '.json'
                        jsonPath = os.path.join(self.json_dir[dir_index], jsonFile)
                        with open(jsonPath, 'r') as f:
                            jsonData = json.load(f)
                        blocks = jsonData['block_design']['order']
                        # update for old names (before blocks had more descriptive names)
                        for block in xrange(len(blocks)):
                            if blocks[block] == 'training 1':
                                blocks[block] = 'training 125'
                            elif blocks[block] == 'training 2':
                                blocks[block] = 'training 150'
                            elif blocks[block] == 'training 3':
                                blocks[block] = 'training 125/150'
                            elif blocks[block] == 'training 4':
                                blocks[block] = 'training 100'
                            elif blocks[block] == 'training 4b':
                                blocks[block] = 'training 175'
                            elif blocks[block] == 'training 5':
                                blocks[block] = 'training 100/125/150'
                            elif blocks[block] == 'training 5b':
                                blocks[block] = 'training 125/150/175'

                        with open(csvPath, 'rb') as data_file:
                            csv_reader = csv.reader(data_file, delimiter=',')
                            currentLine = 0  # resets each time so later we can tell how many lines were imported
                            for row in csv_reader:
                                if currentLine == 0:
                                    pass  # ignore first line (headers)
                                else:
                                    data_dict['Index'].append(int(row[1]))
                                    data_dict['Class'].append(row[4])
                                    data_dict['Response'].append(row[5])
                                    data_dict['RT'].append(float(row[7]) if len(row[7]) > 0 else float('nan'))
                                    data_dict['Reward'].append(1 if row[8] == 'True' else 0)
                                    data_dict['Punish'].append(1 if row[9] == 'True' else 0)
                                    data_dict['Time'].append(row[10])
                                    data_dict['Session'].append(row[0])
                                    data_dict['File'].append(curr_csv)
                                    stim_name = re.split('/', row[3])
                                    data_dict['Stimulus'].append(stim_name[-1])
                                    data_dict['Subject'].append(curr_csv.partition('_')[0])
                                    data_dict['File Count'].append(1)

                                    data_dict['Block'].append(blocks[int(row[0]) - 1])

                                    response_type = self.classify_response(row[5], row[4])
                                    data_dict['Response Type'].append(response_type)

                                    data_dict['Hit'].append(1 if response_type == 'response_hit' else 0)
                                    data_dict['FA'].append(1 if response_type == 'response_FA' else 0)
                                    data_dict['Miss'].append(1 if response_type == 'response_Miss' else 0)
                                    data_dict['CR'].append(1 if response_type == 'response_CR' else 0)
                                    data_dict['Miss\n(NR)'].append(1 if response_type == 'response_Miss_NR' else 0)
                                    data_dict['CR\n(NR)'].append(1 if response_type == 'response_CR_NR' else 0)
                                    data_dict['Trials'].append(1 if response_type[0:4] == 'resp' else 0)
                                    data_dict['Probe Hit'].append(1 if response_type == 'probe_hit' else 0)
                                    data_dict['Probe FA'].append(1 if response_type == 'probe_FA' else 0)
                                    data_dict['Probe Miss'].append(1 if response_type == 'probe_Miss' else 0)
                                    data_dict['Probe CR'].append(1 if response_type == 'probe_CR' else 0)
                                    data_dict['Probe Miss\n(NR)'].append(1 if response_type == 'probe_Miss_NR' else 0)
                                    data_dict['Probe CR\n(NR)'].append(1 if response_type == 'probe_CR_NR' else 0)
                                    data_dict['Probe Trials'].append(1 if response_type[0:4] == 'prob' else 0)

                                currentLine += 1

                data_dict = pd.DataFrame.from_dict(data_dict)  # Convert to data frame

        # endregion
        self.raw_trial_data = data_dict
        self.raw_trial_data['Time'] = pd.to_datetime(self.raw_trial_data['Time'], format='%Y-%m-%d %H:%M:%S')
        self.raw_trial_data['Date'] = self.raw_trial_data['Time'].dt.date

        self.raw_trial_data.set_index('Date', inplace=True)  # inplace so change is saved to same variable
        self.raw_trial_data.sort_index(inplace=True)  # inplace so change is saved to same variable
        # self.trial_types(data_dict)

    def trial_types(self, data_dict):
        # Defunct, not used any more (defs that used this were way too slow in the first place)

        # Double check that each key in dict has same length
        trial_count = len(data_dict)  # 'Index' is arbitrary, just need total count of trials
        # keyLengths = [len(x) for x in data_dict.values()]
        # if not self.dict_len_is_equal(keyLengths):
        #     raise Exception('Columns are not equal length')

        # region Get result of each trial
        if trial_count < 1:
            print 'No trials found'
        else:
            a = 1
            if a == 1:
                response_hit = [0] * trial_count
                response_FA = [0] * trial_count
                response_Miss = [0] * trial_count
                response_CR = [0] * trial_count
                response_Miss_NR = [0] * trial_count
                response_CR_NR = [0] * trial_count
                response_tot = [0] * trial_count  # To end up being the trials/day field
                probe_hit = [0] * trial_count
                probe_FA = [0] * trial_count
                probe_Miss = [0] * trial_count
                probe_CR = [0] * trial_count
                probe_Miss_NR = [0] * trial_count
                probe_CR_NR = [0] * trial_count
                probe_tot = [0] * trial_count  # To end up being the probe trials/day field

                for i in xrange(trial_count):
                    if data_dict['Response'][i] == "ERR":
                        pass
                    elif data_dict['Class'][i] == "probePlus":
                        probe_tot[i] = 1
                        if data_dict['Response'][i] == "sPlus":
                            probe_hit[i] = 1
                        elif data_dict['Response'][i] == "sMinus":
                            probe_Miss[i] = 1
                        else:
                            # No response
                            probe_Miss_NR[i] = 1

                    elif data_dict['Class'][i] == "probeMinus":
                        probe_tot[i] = 1
                        if data_dict['Response'][i] == "sPlus":
                            probe_FA[i] = 1
                        elif data_dict['Response'][i] == "sMinus":
                            probe_CR[i] = 1
                        else:
                            # No response
                            probe_CR_NR[i] = 1

                    elif data_dict['Class'][i] == "sPlus":
                        response_tot[i] = 1
                        if data_dict['Response'][i] == "sPlus":
                            response_hit[i] = 1
                        elif data_dict['Response'][i] == "sMinus":
                            response_Miss[i] = 1
                        else:
                            # No response
                            response_Miss_NR[i] = 1

                    elif data_dict['Class'][i] == "sMinus":
                        response_tot[i] = 1
                        if data_dict['Response'][i] == "sPlus":
                            response_FA[i] = 1
                        elif data_dict['Response'][i] == "sMinus":
                            response_CR[i] = 1
                        else:
                            # No response
                            response_CR_NR[i] = 1

                data_dict['Hit'] = response_hit
                data_dict['FA'] = response_FA
                data_dict['Miss'] = response_Miss
                data_dict['CR'] = response_CR
                data_dict['Miss\n(NR)'] = response_Miss_NR
                data_dict['CR\n(NR)'] = response_CR_NR
                data_dict['Trial Count'] = response_tot
                data_dict['Probe Hit'] = probe_hit
                data_dict['Probe FA'] = probe_FA
                data_dict['Probe Miss'] = probe_Miss
                data_dict['Probe CR'] = probe_CR
                data_dict['Probe Miss\n(NR)'] = probe_Miss_NR
                data_dict['Probe CR\n(NR)'] = probe_CR_NR
                data_dict['Probe Trials'] = probe_tot
            elif a == 2:
                # Too slow!
                data_dict['Hit'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_hit'), axis=1)
                data_dict['FA'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_FA'), axis=1)
                data_dict['Miss'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_Miss'), axis=1)
                data_dict['CR'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_CR'), axis=1)
                data_dict['Miss\n(NR)'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_Miss_NR'), axis=1)
                data_dict['CR\n(NR)'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_CR_NR'), axis=1)
                data_dict['Trial Count'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'training'), axis=1)
                data_dict['Probe Hit'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_hit'), axis=1)
                data_dict['Probe FA'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_FA'), axis=1)
                data_dict['Probe Miss'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_Miss'), axis=1)
                data_dict['Probe CR'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_CR'), axis=1)
                data_dict['Probe Miss\n(NR)'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_Miss_NR'), axis=1)
                data_dict['Probe CR\n(NR)'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_CR_NR'), axis=1)
                data_dict['Probe Trials'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe'), axis=1)
            elif a == 4:
                response_hit = [0] * trial_count
                response_FA = [0] * trial_count
                response_Miss = [0] * trial_count
                response_CR = [0] * trial_count
                response_Miss_NR = [0] * trial_count
                response_CR_NR = [0] * trial_count
                response_tot = [0] * trial_count  # To end up being the trials/day field
                probe_hit = [0] * trial_count
                probe_FA = [0] * trial_count
                probe_Miss = [0] * trial_count
                probe_CR = [0] * trial_count
                probe_Miss_NR = [0] * trial_count
                probe_CR_NR = [0] * trial_count
                probe_tot = [0] * trial_count  # To end up being the probe trials/day field

                for i in xrange(trial_count):
                    response_hit[i] = self.classify_trial_binary(data_dict[i], 'response_hit')
                    response_FA[i] = self.classify_trial_binary(data_dict[i], 'response_FA')
                    response_Miss[i] = self.classify_trial_binary(data_dict[i], 'response_Miss')
                    response_CR[i] = self.classify_trial_binary(data_dict[i], 'response_CR')
                    response_Miss_NR[i] = self.classify_trial_binary(data_dict[i], 'response_Miss_NR')
                    response_CR_NR[i] = self.classify_trial_binary(data_dict[i], 'response_CR_NR')
                    response_tot[i] = self.classify_trial_binary(data_dict[i], 'response_tot')  # Trials/day field
                    probe_hit[i] = self.classify_trial_binary(data_dict[i], 'probe_hit')
                    probe_FA[i] = self.classify_trial_binary(data_dict[i], 'probe_FA')
                    probe_Miss[i] = self.classify_trial_binary(data_dict[i], 'probe_Miss')
                    probe_CR[i] = self.classify_trial_binary(data_dict[i], 'probe_CR')
                    probe_Miss_NR[i] = self.classify_trial_binary(data_dict[i], 'probe_Miss_NR')
                    probe_CR_NR[i] = self.classify_trial_binary(data_dict[i], 'probe_CR_NR')
                    probe_tot[i] = self.classify_trial_binary(data_dict[i], 'probe_tot')  # Probe trials/day field

                data_dict['Hit'] = response_hit
                data_dict['FA'] = response_FA
                data_dict['Miss'] = response_Miss
                data_dict['CR'] = response_CR
                data_dict['Miss\n(NR)'] = response_Miss_NR
                data_dict['CR\n(NR)'] = response_CR_NR
                data_dict['Trial Count'] = response_tot
                data_dict['Probe Hit'] = probe_hit
                data_dict['Probe FA'] = probe_FA
                data_dict['Probe Miss'] = probe_Miss
                data_dict['Probe CR'] = probe_CR
                data_dict['Probe Miss\n(NR)'] = probe_Miss_NR
                data_dict['Probe CR\n(NR)'] = probe_CR_NR
                data_dict['Probe Trials'] = probe_tot
            elif a == 3:
                # Too slow!
                data_dict['Hit'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_hit'), axis=1)
                data_dict['FA'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_FA'), axis=1)
                data_dict['Miss'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_Miss'), axis=1)
                data_dict['CR'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_CR'), axis=1)
                data_dict['Miss\n(NR)'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_Miss_NR'), axis=1)
                data_dict['CR\n(NR)'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'response_CR_NR'), axis=1)
                data_dict['Trial Count'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'training'), axis=1)
                data_dict['Probe Hit'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_hit'), axis=1)
                data_dict['Probe FA'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_FA'), axis=1)
                data_dict['Probe Miss'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_Miss'), axis=1)
                data_dict['Probe CR'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_CR'), axis=1)
                data_dict['Probe Miss\n(NR)'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_Miss_NR'), axis=1)
                data_dict['Probe CR\n(NR)'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe_CR_NR'), axis=1)
                data_dict['Probe Trials'] = data_dict.apply(
                    lambda row: self.classify_trial_binary(row, 'probe'), axis=1)

            self.raw_trial_data = data_dict
            self.raw_trial_data['Date'] = pd.to_datetime(self.raw_trial_data['Time'], format='%Y/%m/%d')
            self.raw_trial_data['Time'] = pd.to_datetime(self.raw_trial_data['Time'], format='%Y-%m-%d %H:%M:%S')
            self.raw_trial_data.set_index('Date', inplace=True)  # inplace so change is saved to same variable
            self.raw_trial_data.sort_index(inplace=True)  # inplace so change is saved to same variable
        # endregion

    def dict_len_is_equal(self, list_to_check):
        # Quick function to validate that each item in a list has the same length
        return not list_to_check or list_to_check.count(list_to_check[0]) == len(list_to_check)

    def divide_by_zero(self, numerator, denominator, roundto=3):
        # error catching for ZeroDivisionError so I don't have to catch the exception every single time manually
        try:
            result = round(float(numerator) / float(denominator), roundto)
        except ZeroDivisionError:
            result = None
        return result

    def filter_data(self, **kwargs):
        # Filter the raw data, like restrict to date range or specific block
        # Only takes self.raw_trial_data as input data (i.e., unfiltered)
        #
        # kwarg is either single keyword or a dict
        # dict contains columns as keys, and the values are a list of strs to filter for (so any values not passed
        # will be omitted from output

        parameters = kwargs
        filtered_data = self.raw_trial_data
        # startdate filter
        if 'startdate' in parameters:
            # Filter sessions prior to start date
            filtered_data = filtered_data[filtered_data['Time'] > parameters['startdate']]

        if 'filters' in parameters and len(parameters['filters']) > 0:
            filterList = []
            for column in parameters['filters'].keys():
                if column == 'Date':
                    # Build date this way because the resulting eval can't handle if date is in string format
                    inputDate = parameters['filters'][column][1]
                    inputYear = inputDate.year
                    inputMonth = inputDate.month
                    inputDay = inputDate.day
                    filterList.append('(filtered_data.Time.dt.date {} dt.date({}, {}, {}))'.format(
                        parameters['filters'][column][0], inputYear, inputMonth, inputDay))
                    # filterList.append('(input_data.Time.dt.date {} {})'.format(
                    #     parameters['filters'][column][0], parameters['filters'][column][1]))
                elif parameters['filters'][column]:
                    filterList.append('filtered_data.{}.isin({})'.format(column, (kwargs['filters'][column])))
            filterString = ' & '.join(filterList)
            filtered_data = filtered_data[eval(filterString)]

        self.filtered_data = filtered_data

    def summarize(self, inputdata='raw'):
        # produces summary dataframe that just contains relevant data
        # Can accept raw (unfiltered) data or the filtered data returned from self.filter_data
        # parameter is string

        # region Parse input parameter to choose correct data to summarize
        if inputdata == 'raw':  # Summarize raw data
            trialdata = self.raw_trial_data
        elif inputdata == 'filtered' or inputdata == 'filt':  # If using filtered data
            trialdata = self.filtered_data
        elif isinstance(inputdata, pd.DataFrame):  # If inputting different dataframe than preprocessed
            trialdata = inputdata
        else:
            return
        # endregion

        # region Create new dataframe with only relevant fields by dropping unused fields
        # performanceData = trialdata
        dropFields = ['Reward', 'Punish', 'Session', 'File Count']
        outputData = trialdata.drop(dropFields, axis=1)
        outputData.reset_index()
        # endregion

        outputData.sort_values(by='Date')

        self.summaryData = outputData

    def analyze(self, input_data, **kwargs):
        # Calculate d' scores for summarized data

        # region Summarize input data based on kwargs, or by default (date and block)
        if 'groupBy' in kwargs and len(kwargs['groupBy']) > 0:
            input_data.sort_values(by='Date')
            groupData = input_data.groupby(kwargs['groupBy']).sum()
            # if kwargs['groupBy'] == 'day':
            #     groupData = input_data.groupby([input_data['Day'], input_data['Block']]).sum()
            #     groupCount = len(groupData)
            # elif kwargs['groupBy'] == 'hour':
            #     groupData = input_data.groupby([input_data['Day'], input_data['Time'].dt.hour,
            #                                     input_data['Block']]).sum()
            #     groupCount = len(groupData)
            # elif kwargs['groupBy'] == 'stimulus':
            #     groupData = input_data.groupby([input_data['Day'], input_data['Block'],
            #                                     input_data['Stimulus']]).sum()
            #     groupCount = len(groupData)
            # else:  # catch all other cases, can fill out later
            #     groupData = input_data.groupby([input_data['Day'], input_data['Block']]).sum()
            #     groupCount = len(groupData)
            groupCount = len(groupData)
            # endregion

            # region Variable init
            dprimes = []
            dprimes_NR = []
            betas = []
            betas_NR = []
            sPlus_correct = []
            sPlus_NR_correct = []
            sMinus_correct = []
            sMinus_NR_correct = []
            total_correct = []
            total_NR_correct = []
            probeDprimes = []
            probeDprimes_NR = []
            probeBetas = []
            probeBetas_NR = []
            probePlus_correct = []
            probePlus_NR_correct = []
            probeMinus_correct = []
            probeMinus_NR_correct = []
            total_probe_correct = []
            total_probe_NR_correct = []
            # endregion

            # region Calculate stats for each summary group
            for k in xrange(groupCount):
                hitCount = float(groupData['Hit'][k])
                missCount = float(groupData['Miss'][k])
                missNRCount = float(groupData['Miss\n(NR)'][k])
                FACount = float(groupData['FA'][k])
                CRCount = float(groupData['CR'][k])
                CRNRCount = float(groupData['CR\n(NR)'][k])
                totalTrials = float(groupData['Trials'][k])
                probeHitCount = float(groupData['Probe Hit'][k])
                probeMissCount = float(groupData['Probe Miss'][k])
                probeMissNRCount = float(groupData['Probe Miss\n(NR)'][k])
                probeFACount = float(groupData['Probe FA'][k])
                probeCRCount = float(groupData['Probe CR'][k])
                probeCRNRCount = float(groupData['Probe CR\n(NR)'][k])
                probeTotalTrials = float(groupData['Probe Trials'][k])

                dayDprime = round(Analysis([[hitCount, missCount], [FACount, CRCount]]).dprime(), 3)
                dprimes.append(dayDprime)

                # region Training trial stats
                dayDprime_NR = round(Analysis([[hitCount, (missCount + missNRCount)],
                                               [FACount, (CRCount + CRNRCount)]]).dprime(), 3)
                dprimes_NR.append(dayDprime_NR)

                if totalTrials < 10:
                    dayBeta = 'n/a'
                else:
                    dayBeta = round(Analysis([[hitCount, missCount], [FACount, CRCount]]).bias(), 3)
                betas.append(dayBeta)

                if totalTrials < 10:
                    dayBeta_NR = 'n/a'
                else:
                    dayBeta_NR = round(Analysis([[hitCount, (missCount + missNRCount)],
                                                 [FACount, (CRCount + CRNRCount)]]).bias(), 3)
                betas_NR.append(dayBeta_NR)
                # endregion

                # region Probe trial stats
                dayProbeDprime = round(Analysis([[probeHitCount, probeMissCount],
                                                 [probeFACount, probeCRCount]]).dprime(), 3)
                probeDprimes.append(dayProbeDprime)

                dayProbeDprime_NR = round(Analysis([[probeHitCount, (probeMissCount + probeMissNRCount)],
                                                    [probeFACount, (probeCRCount + probeCRNRCount)]]).dprime(), 3)
                probeDprimes_NR.append(dayProbeDprime_NR)

                if probeTotalTrials < 10:
                    dayProbeBeta = 'n/a'
                else:
                    dayProbeBeta = round(
                        Analysis([[probeHitCount, probeMissCount], [probeFACount, probeCRCount]]).bias(),
                        3)
                probeBetas.append(dayProbeBeta)

                if probeTotalTrials < 10:
                    dayProbeBeta_NR = 'n/a'
                else:
                    dayProbeBeta_NR = round(Analysis([[probeHitCount, (probeMissCount + probeMissNRCount)],
                                                      [probeFACount, (probeCRCount + probeCRNRCount)]]).bias(), 3)
                probeBetas_NR.append(dayProbeBeta_NR)
                # endregion

                if missCount == float(0):
                    missCount = 0.001
                if missNRCount == float(0):
                    missNRCount = 0.001
                if FACount == float(0):
                    FACount = 0.001

                sPlus_correct.append(self.divide_by_zero(hitCount, (hitCount + missCount), 5))
                sPlus_NR_correct.append(self.divide_by_zero(hitCount, (hitCount + missCount + missNRCount), 5))
                sMinus_correct.append(self.divide_by_zero(CRCount, (CRCount + FACount), 5))
                sMinus_NR_correct.append(self.divide_by_zero((CRCount + CRNRCount), (FACount + CRCount + CRNRCount), 5))
                total_correct.append(self.divide_by_zero((hitCount + CRCount),
                                                         (hitCount + CRCount + missCount + FACount), 5))
                total_NR_correct.append(self.divide_by_zero((hitCount + CRCount + CRNRCount), totalTrials, 5))

                probePlus_correct.append(self.divide_by_zero(probeHitCount, (probeHitCount + probeMissCount), 5))
                probePlus_NR_correct.append(self.divide_by_zero(probeHitCount,
                                                                (probeHitCount + probeMissCount + probeMissNRCount), 5))
                probeMinus_correct.append(self.divide_by_zero(probeCRCount, (probeCRCount + probeFACount), 5))
                probeMinus_NR_correct.append(self.divide_by_zero((probeCRCount + probeCRNRCount),
                                                                 (probeFACount + probeCRCount + probeCRNRCount), 5))
                total_probe_correct.append(
                    self.divide_by_zero((probeHitCount + probeCRCount),
                                        (probeHitCount + probeCRCount + probeMissCount + probeFACount), 5))
                total_probe_NR_correct.append(self.divide_by_zero((probeHitCount + probeCRCount + probeCRNRCount),
                                                                  probeTotalTrials, 5))
            # endregion

            # region Add calculated stats to summarized dataframe
            groupData["d'"] = dprimes
            groupData["d'\n(NR)"] = dprimes_NR
            groupData['Beta'] = betas
            groupData['Beta\n(NR)'] = betas_NR
            groupData['S+'] = sPlus_correct
            groupData['S+\n(NR)'] = sPlus_NR_correct
            groupData['S-'] = sMinus_correct
            groupData['S-\n(NR)'] = sMinus_NR_correct
            groupData['Total Corr'] = total_correct
            groupData['Total Corr\n(NR)'] = total_NR_correct
            groupData["Probe d'"] = probeDprimes
            groupData["Probe d'\n(NR)"] = probeDprimes_NR
            groupData['Probe Beta'] = probeBetas
            groupData['Probe Beta\n(NR)'] = probeBetas_NR
            groupData['Probe S+'] = probePlus_correct
            groupData['Probe S+\n(NR)'] = probePlus_NR_correct
            groupData['Probe S-'] = probeMinus_correct
            groupData['Probe S-\n(NR)'] = probeMinus_NR_correct
            groupData['Probe Tot Corr'] = total_probe_correct
            groupData['Probe Tot Corr\n(NR)'] = total_probe_NR_correct
            # endregion

        else:  # If no grouping specified, return raw data
            groupData = input_data
            # groupData = groupData.drop(['Date'], axis=1)
            groupData.reset_index()
            # region Filter out unwanted fields (e.g., NR trials, probe trials)
            # Get list of columns to remove

        dropColumns = []

        if 'dropCols' in kwargs and len(kwargs['dropCols']) > 0:
            dropColumns += kwargs['dropCols']

        # Set column order

        sortedColumns = field_list()

        # Compare all column names to those in groupData (that were returned after processing) and add all columns
        # not in groupData to dropList to make sure that remainingColumns only contains columns that were present in
        # groupData (avoiding a "missing index" error)
        missingColumns = list(filter(lambda a: a not in groupData, sortedColumns))

        dropColumns += missingColumns
        dropColumns = list(set(dropColumns))  # Remove duplicates

        remainingColumns = list(
            filter(lambda a: a not in dropColumns, sortedColumns))  # Get list of remaining columns

        # endregion

        outputData = groupData[remainingColumns]  # Pull remaining columns from groupData

        if 'sortBy' in kwargs and len(kwargs['sortBy']) > 0:
            outputData.sort_values(by=kwargs['sortBy'])

        return outputData

    def append_math(self, input_list, value):
        pass

    def check_criteria(self, trialdata, criteria=None, verbose=False):
        # parse criteria for: number of days prior to check, which block, dprime threshold, etc
        # returns True if criteria met on all days, otherwise False
        # trialdata = dataframe of summarized, filtered, analyzed data to check
        # criteria = dict of criteria settings
        # Start with assumption that each day is True, then reject if any criteria are not met
        if not isinstance(trialdata, pd.DataFrame):
            return 'Error: not dataframe'
        if criteria is None:
            return False

        rowcount = len(trialdata.index)
        criteria_result = [True] * rowcount  # List of whether each row meets criteria
        i = 0

        if 'NR' in criteria:
            use_NR = criteria['NR']
        else:
            use_NR = True

        for index, row in trialdata.iterrows():
            if criteria_result[i] is not False:  # skip next check if already failed previous criteria
                if 'trialcount' in criteria:  # minimum trial count of specific trial type or overall
                    if 'mintrials' in criteria['trialcount']:
                        trialThreshold = criteria['trialcount']['mintrials']
                        if 'type' in criteria['trialcount']:
                            ntrials = row[criteria['trialcount']['type']]
                        elif use_NR:
                            ntrials = row['Trials']  # if type not specified, just compare to total trialcount
                        else:
                            ntrials = row['Trials']  # if type not specified, just compare to total trialcount

                        if ntrials < trialThreshold:
                            criteria_result[i] = False
                            if verbose:
                                print 'Record %d does not meet trial count criteria (%d trials vs %d minimum)' % \
                                      (i, ntrials, trialThreshold)

            if criteria_result[i] is not False:  # skip next check if already failed previous criteria
                if 'dprime' in criteria:
                    if use_NR:
                        dprime_actual = row["d'\n(NR)"]
                        dprime_min = criteria["d'\n(NR)"]
                    else:
                        dprime_actual = row["d'"]
                        dprime_min = criteria["d'"]

                    if dprime_actual < dprime_min:
                        criteria_result[i] = False
                        if verbose:
                            print "Record %d failed d' criteria (%d actual vs %d minimum)" % \
                                  (i, dprime_actual, dprime_min)

            if criteria_result[i] is not False:  # skip next check if already failed previous criteria
                if 'propCorrect' in criteria:
                    for category in criteria['propCorrect']:
                        if 'type' in category:
                            proportion = row[category['type']]
                            stim_type = category['type']
                        elif use_NR:
                            proportion = row['Total Corr\n(NR)']
                            stim_type = 'Total_NR'
                        else:
                            proportion = row['Total Corr']
                            stim_type = 'Total'

                        if proportion < category['minimum']:
                            criteria_result[i] = False
                            if verbose:
                                print "Category %s failed proportion correct criteria (%0.3f actual vs %0.3f " \
                                      "minimum)" % (stim_type, proportion, category['minimum'])

            i += 1

        if 'days' in criteria:  # criteria not met on at least 'days' days
            num_days = sum(criteria_result)
            min_days = criteria['days']
        else:  # otherwise if ANY days don't meet criteria,
            num_days = sum(criteria_result)
            min_days = len(criteria_result)
            # return false
        if num_days < min_days:
            if verbose:
                print "Not enough days meeting criteria (%d days, %d min)" % (num_days, min_days)
            return False

        # Otherwise, return true
        if verbose:
            print "Meets all criteria!"
        return True

# datapath = '/home/rouse/bird/data/y18r8'
# perform = Performance(datapath).gather_raw_data()
# stats = perform.analyze('raw')
# stats.to_csv(os.path.join(datapath,'test.csv'))
# print stats
