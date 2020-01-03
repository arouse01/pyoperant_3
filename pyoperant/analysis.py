#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import csv
# import copy
import datetime as dt  # Pycharm thinks this is unused but it does get used in the filter building section
import numpy as np
from scipy.stats import norm
from scipy.stats import beta
import pandas as pd
import re
import logging, traceback
# import string
import collections  # for orderedDict

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


class FieldList:
    """
    Creates list of fields related to analysis, and optionally creates dict with field-specific info
    Could be replaced with an external json file with the same info

    To add an analysis field:
        Define the field
        -Add field name to the list in FieldList.__init__
        -If field will be filterable, add the name to the appropriate list in the filter section in FieldList.build_dict
        -Add the field name to the appropriate groupby list in the groupby section in FieldList.build_dict (types are
        explained within the function)

        Define field's value
        -If the field is something pulled directly from the trial data (not 'group' columns which have to be
        calculated later), add a blank list to dataDict in either Performance.__init__ or Performance.gather_raw_data
            -Add the correct line so the field gets properly defined for each trial in the 'Actually read csv and pull
            data' region
                -If pulling from json file, the value(s) can be defined in the 'Get data from json settings file' region
        -Otherwise, if field is a 'group' column, it gets calculated in Performance.analyze
        and added to the summary dataframe in the 'Add calculated stats to summarized dataframe' region

        Don't forget to test that it all works properly!

    """
    def __init__(self):
        # Item order is resulting sort order
        fieldList = ['Subject', 'File', 'Session', 'File Count', 'Date', 'Time', 'Hour', 'Block', 'Block Number',
                     'Trials', 'S+ Trials', 'S- Trials', 'S+ (NR) Trials', 'S- (NR) Trials', 'Index', 'Stimulus',
                     'Tempo', 'Trial Type', 'Class', 'Response Type', 'Response', 'RT', 'Reward', 'Punish', 'Timeout']

        fieldList += ["d'", "d' (NR)", u'Beta', u'Beta (NR)', 'S+ Rate', 'S+ (NR) Rate', 'S- Rate', 'S- (NR) Rate',
                      'Total Corr', 'Total Corr (NR)']
        fieldList += ['Hit', 'Miss', 'Miss (NR)', 'FA', 'CR', 'CR (NR)', 'Prop CR Resets']

        fieldList += ["Probe d'", "Probe d' (NR)", u'Probe Beta', u'Probe Beta (NR)', 'Probe Trials', 'Probe S+ Trials',
                      'Probe S+ (NR) Trials', 'Probe S- Trials', 'Probe S- (NR) Trials']
        fieldList += ['Probe S+ Rate', 'Probe S+ (NR) Rate', 'Probe S- Rate', 'Probe S- (NR) Rate', 'Probe Tot Corr',
                      'Probe Tot Corr (NR)']
        fieldList += ['Probe Hit', 'Probe Miss', 'Probe Miss (NR)', 'Probe FA', 'Probe CR', 'Probe CR (NR)']

        self.fieldList = fieldList

    def build_dict(self):
        fieldDict = collections.OrderedDict()
        for column in self.fieldList:
            # column = column.decode('utf-8')
            columnDict = {'visible': True, 'filter': {}, 'name': column.replace('\n(NR)', ' (NR)')}

            # Define field filter type
            if columnDict['name'] in ['Subject', 'Block', 'Block Number', 'Response Type', 'Tempo', 'Stimulus',
                                      'Trial Type', 'Class', 'Response']:
                columnDict['filter']['type'] = 'list'
            elif columnDict['name'] in ['Date']:
                columnDict['filter']['type'] = 'range'
            else:
                columnDict['filter']['type'] = 'None'

            # Define field groupby type - give each field a type to indicate what functions can be performed
            if columnDict['name'] in ['File', 'Session', 'File Count', 'Index', 'Time']:
                # 'raw' columns can't be grouped easily because values are often unique per trial, or it doesn't make
                # sense to group by those fields (e.g., grouping by 'File' for continuous-running birds)
                columnDict['type'] = 'raw'
            elif columnDict['name'] in ['Subject', 'Block', 'Block Number', 'Date', 'Hour', 'Response Type', 'Stimulus',
                                        'Tempo', 'Trial Type', 'Class', 'Response']:
                # 'index' columns are those that could be used as an index for grouping
                columnDict['type'] = 'index'  # groupby enabled
            elif columnDict['name'] in ['RT', 'Timeout']:
                # 'mean' columns are those that should/can be averaged when trials are grouped
                columnDict['type'] = 'mean'
            elif columnDict['name'] in ['Reward', 'Punish', 'S+ Trials', 'S+ (NR) Trials', 'S- Trials',
                                        'S- (NR) Trials', 'Trials',
                                        'Hit', 'FA', 'Miss', 'CR', 'Miss (NR)', 'CR (NR)',
                                        'Probe S+ Trials', 'Probe S+ (NR) Trials', 'Probe S- Trials',
                                        'Probe S- (NR) Trials',
                                        'Probe Trials', 'Probe Hit', 'Probe FA', 'Probe Miss',
                                        'Probe CR', 'Probe Miss (NR)', 'Probe CR (NR)', ]:
                # 'sum' columns are those that should simply be summed when trials are grouped (most columns are
                # indicators of trial/response type, in effect acting as a 'count' column')
                columnDict['type'] = 'sum'
            elif columnDict['name'] in ["d'", "d' (NR)", 'Beta', 'Beta (NR)', 'S+ Rate', 'S+ (NR) Rate',
                                        'S- Rate', 'S- (NR) Rate', 'Total Corr', 'Total Corr (NR)',
                                        "Probe d'", "Probe d' (NR)", 'Probe Beta', 'Probe Beta (NR)',
                                        'Probe S+ Rate', 'Probe S+ (NR) Rate', 'Probe S- Rate', 'Probe S- (NR) Rate',
                                        'Probe Tot Corr', 'Probe Tot Corr (NR)', 'Prop CR Resets']:
                # 'group' columns are those that are calculated based strictly on grouped data - calculations that
                # can't be performed on a single trial (e.g. proportion correct)
                columnDict['type'] = 'group'

            fieldDict[column] = columnDict
        return fieldDict


class Performance(object):
    # Longer-term performance analysis

    def __init__(self, experiment_folder):
        self.log = logging.getLogger(__name__)

        # convert experiment_folder to list if single item
        if not isinstance(experiment_folder, list):
            experiment_folder = [experiment_folder]
        self.data_dir = []
        self.json_dir = []
        for singleDir in experiment_folder:
            # Validate input folder(s)
            if not os.path.exists(singleDir):
                self.log.error("invalid input folder: {}".format(singleDir))
                continue

            singleData = os.path.join(singleDir, 'trialdata')
            if not os.path.exists(singleData):
                self.log.error("data folder ({}) not found".format(singleData))
                continue
            else:
                # make sure both json and trialdata folders are present before appending
                singleJson = os.path.join(singleDir, 'settings_files')
                if not os.path.exists(singleJson):
                    self.log.error("json folder ({}) not found".format(singleJson))
                    continue
                else:
                    self.data_dir.append(singleData)
                    self.json_dir.append(os.path.join(singleDir, 'settings_files'))

        # Each row in dataDict will be a single
        dataDict = {'File': [],
                    'Subject': [],
                    'Session': [],
                    'File Count': [],
                    'Trial Type': [],
                    'Block': [],
                    # 'Block Number': [],
                    'Index': [],
                    'Time': [],
                    'Response Type': [],
                    'Stimulus': [],
                    'Class': [],
                    'Response': [],
                    'RT': [],
                    'Reward': [],
                    'Punish': [],
                    'Timeout': []
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

    def gather_raw_data(self, data_dict):
        # Pull data from across multiple csv files, keeping notation for phase (which comes from the json file)

        # empty vars to start
        data_dict['Hit'] = []
        data_dict['FA'] = []
        data_dict['Miss'] = []
        data_dict['CR'] = []
        data_dict['Miss (NR)'] = []
        data_dict['CR (NR)'] = []
        data_dict['Trials'] = []
        data_dict['S+ Trials'] = []
        data_dict['S- Trials'] = []
        data_dict['S+ (NR) Trials'] = []
        data_dict['S- (NR) Trials'] = []
        data_dict['Probe Hit'] = []
        data_dict['Probe FA'] = []
        data_dict['Probe Miss'] = []
        data_dict['Probe CR'] = []
        data_dict['Probe Miss (NR)'] = []
        data_dict['Probe CR (NR)'] = []
        data_dict['Probe Trials'] = []
        data_dict['Probe S+ Trials'] = []
        data_dict['Probe S- Trials'] = []
        data_dict['Probe S+ (NR) Trials'] = []
        data_dict['Probe S- (NR) Trials'] = []
        data_dict['Tempo'] = []

        # region Read each CSV file
        for dir_index, curr_dir in enumerate(self.data_dir):
            # - importing csv files as dataframes directly and then concatenating with pandas was way too slow,
            # so went with importing csv data directly into a dict line by line
            # - Dynamically getting column names from first row of each csv and then matching column number to name for
            # all subsequent rows was also way too slow
            # - Fastest method was to hardcode column names and indices, which is not ideal (if column order ever
            # changes), but it's WAY faster than the other two approaches
            csvList = os.listdir(curr_dir)

            # Add specific response columns to data_dict
            for curr_csv in csvList:
                csvPath = os.path.join(curr_dir, curr_csv)
                with open(csvPath, 'rb') as data_file:
                    csv_reader = csv.reader(data_file, delimiter=',')
                    rowCount = len(list(csv_reader)) - 1  # check if csv has data beyond header
                    if rowCount < 1:
                        fileEmpty = True
                    else:
                        fileEmpty = False

                if fileEmpty is False:
                    # Separated from above to allow data_file to close and be reopened for actual scanning

                    # region Get data from json settings file
                    # get short dict of block names and update old names to match new naming convention
                    jsonFile = os.path.splitext(curr_csv.replace('trialdata', 'settings'))[0] + '.json'
                    jsonPath = os.path.join(self.json_dir[dir_index], jsonFile)
                    if not os.path.exists(jsonPath):
                        self.log.error('json file does not exist: {}'.format(jsonPath))
                        continue
                    with open(jsonPath, 'r') as f:
                        jsonData = json.load(f)

                    blocks = jsonData['block_design']['order']
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
                        elif blocks[block] == 'shaping phase 0':
                            blocks[block] = 'shaping 1'

                    # Get timeout setting (stored in json file)
                    timeout = jsonData['classes']['sMinus']['punish_value']
                    # endregion

                    # region Actually read csv and pull data
                    with open(csvPath, 'rb') as data_file:
                        csv_reader = csv.reader(data_file, delimiter=',')
                        currentLine = 0  # resets each time so later we can tell how many lines were imported
                        for row in csv_reader:
                            if currentLine == 0:
                                # ignore first line (headers) because we're assuming the order is the same for all files
                                pass
                            else:
                                data_dict['Index'].append(int(row[1]))
                                data_dict['Class'].append(row[4])
                                data_dict['Response'].append(row[5])

                                data_dict['RT'].append(float(row[7]) if len(row[7]) > 0 else float('nan'))
                                data_dict['Reward'].append(1 if row[8] == 'True' else 0)
                                data_dict['Punish'].append(1 if row[9] == 'True' else 0)
                                data_dict['Timeout'].append(timeout)
                                data_dict['Time'].append(row[10])
                                data_dict['Session'].append(row[0])
                                data_dict['File'].append(curr_csv)

                                stim_name = re.split('/', row[3])
                                stim_name = stim_name[-1]

                                data_dict['Stimulus'].append(stim_name)
                                data_dict['Subject'].append(curr_csv.partition('_')[0])
                                data_dict['File Count'].append(1)

                                # categorize shaping stimuli (which contain 'song' in the name)separately (they don't
                                # have a tempo)
                                if stim_name[-8:] == 'song.wav':
                                    stim_tempo = 'Shaping'
                                    trialType = 'Shaping'
                                else:
                                    try:
                                        stim_tempo = float(stim_name[5:9]) / 10
                                    except ValueError:
                                        # Old stim name format only had tempo as three-digit number, which is caught
                                        # by ValueError (since ###_ can't be converted to float)
                                        stim_tempo = float(stim_name[5:8])
                                    if row[5] == 'probePlus' or row[5] == 'probeMinus':
                                        trialType = 'Probe'
                                    else:
                                        trialType = 'Training'

                                data_dict['Trial Type'].append(trialType)
                                data_dict['Tempo'].append(stim_tempo)

                                # block number in data file is indexed from 1
                                data_dict['Block'].append(blocks[int(row[0]) - 1])

                                response_type = self.classify_response(row[5], row[4])
                                data_dict['Response Type'].append(response_type)

                                data_dict['Hit'].append(1 if response_type == 'response_hit' else 0)
                                data_dict['FA'].append(1 if response_type == 'response_FA' else 0)
                                data_dict['Miss'].append(1 if response_type == 'response_Miss' else 0)
                                data_dict['CR'].append(1 if response_type == 'response_CR' else 0)
                                data_dict['Miss (NR)'].append(1 if response_type == 'response_Miss_NR' else 0)
                                data_dict['CR (NR)'].append(1 if response_type == 'response_CR_NR' else 0)
                                data_dict['Trials'].append(1 if response_type[0:4] == 'resp' else 0)
                                data_dict['Probe Hit'].append(1 if response_type == 'probe_hit' else 0)
                                data_dict['Probe FA'].append(1 if response_type == 'probe_FA' else 0)
                                data_dict['Probe Miss'].append(1 if response_type == 'probe_Miss' else 0)
                                data_dict['Probe CR'].append(1 if response_type == 'probe_CR' else 0)
                                data_dict['Probe Miss (NR)'].append(1 if response_type == 'probe_Miss_NR' else 0)
                                data_dict['Probe CR (NR)'].append(1 if response_type == 'probe_CR_NR' else 0)
                                data_dict['Probe Trials'].append(1 if response_type[0:4] == 'prob' else 0)

                                data_dict['S+ Trials'].append(
                                    1 if response_type in ['response_hit', 'response_Miss'] else 0)
                                data_dict['S+ (NR) Trials'].append(
                                    1 if response_type in ['response_hit', 'response_Miss', 'response_Miss_NR'] else 0)
                                data_dict['S- Trials'].append(
                                    1 if response_type in ['response_FA', 'response_CR'] else 0)
                                data_dict['S- (NR) Trials'].append(
                                    1 if response_type in ['response_FA', 'response_CR', 'response_CR_NR'] else 0)
                                data_dict['Probe S+ Trials'].append(
                                    1 if response_type in ['probe_hit', 'probe_Miss'] else 0)
                                data_dict['Probe S+ (NR) Trials'].append(
                                    1 if response_type in ['probe_hit', 'probe_Miss', 'probe_Miss_NR'] else 0)
                                data_dict['Probe S- Trials'].append(
                                    1 if response_type in ['probe_FA', 'probe_CR'] else 0)
                                data_dict['Probe S- (NR) Trials'].append(
                                    1 if response_type in ['probe_FA', 'probe_CR', 'probe_CR_NR'] else 0)

                            currentLine += 1
                    # endregion
        data_dict = pd.DataFrame.from_dict(data_dict)  # Convert to data frame

        # endregion

        # Turn constructed dict into self var
        self.raw_trial_data = data_dict

        # region Create indexable fields for groupby functions

        # Create actual datetime value from string
        self.raw_trial_data['Time'] = pd.to_datetime(self.raw_trial_data['Time'], format='%Y-%m-%d %H:%M:%S')

        self.raw_trial_data['Hour'] = pd.DatetimeIndex(self.raw_trial_data['Time']).hour
        self.raw_trial_data['Date'] = self.raw_trial_data['Time'].dt.date

        # endregion Create indexable fields for groupby functions

        # region Block numbers
        # sort first
        self.raw_trial_data.sort_values(by=['Subject', 'Time'], inplace=True)

        # Using temporary field, indicate (as bool) rows where block changes from previous to current (Returns series)
        self.raw_trial_data['tempGroup'] = self.raw_trial_data['Block'] != self.raw_trial_data['Block'].shift()

        # group by subject, then get cumsum of True values (i.e. how many times block changed so far)
        tempGroupBy = self.raw_trial_data.groupby(self.raw_trial_data.Subject, sort=False)
        self.raw_trial_data['Block Number'] = tempGroupBy.tempGroup.apply(lambda x: x.cumsum())

        # remove temporary field
        self.raw_trial_data.drop('tempGroup', axis=1, inplace=True)
        # endregion

        # Later code depends on the output of this function being indexed (otherwise it returns 'index' as the name
        # of the index. Other parts of the code read all of the column and index names, and there's no field called
        # 'index' which confuses the code)
        self.raw_trial_data.set_index(['Subject', 'Date'], inplace=True)  # inplace so change is saved to same variable
        self.raw_trial_data.sort_index(inplace=True)  # inplace so change is saved to same variable

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
        filtered_data = self.raw_trial_data.reset_index()  # need to reset index because otherwise the filter won't
        # recognize the field 'Subject' (since it's an index, as passed from gather_raw_data())

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
                    filterList.append('filtered_data[\'{}\'].isin({})'.format(column, (kwargs['filters'][column])))
            filterString = ' & '.join(filterList)
            filtered_data = filtered_data[eval(filterString)]

        self.filtered_data = filtered_data.set_index(['Subject', 'Date'])  # restore index that was set by

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

            groupFieldList = kwargs['groupBy']
            rangeGroup = []
            for itemIndex, groupField in enumerate(groupFieldList):
                if isinstance(groupField, list):
                    # remove any lists in kwargs, because those are only used for range grouping (rather than a dict
                    # of included values)
                    rangeGroup = groupFieldList.pop(itemIndex)

            # Sort and reset index so numeric index of dataframe is trial number

            input_data = input_data.sort_values(by=['Subject', 'Time'] + groupFieldList)  # Add Subject and Time so
            # values are at least sorted by those first (to avoid incorrect date sorting)

            input_data = input_data.reset_index()
            if len(rangeGroup) > 0:
                tempGroupBy = input_data.groupby(groupFieldList, sort=False)  # get groupBy without the row 'collapse'
                # add to the groupBy term: series that gives each row a 'group number', based on dividing its
                # cumcount() (cumulative row count within group) by the break number
                groupFieldList.append(np.floor(tempGroupBy.cumcount() / rangeGroup[1]).astype(int))

            # create groupby object, then specify desired calculations for each column
            groupData = input_data.groupby(groupFieldList, sort=False)

            groupHeaders = groupData.obj.columns
            groupingDict = {}
            fieldDict = FieldList().build_dict()
            # reaction time should be mean, not sum, time should be minimum (so groups with matching dates can still
            # be sorted in chronological order), and string fields shouldn't be aggregated at all.
            for column in groupHeaders:

                if column == 'Time':
                    groupingDict[column] = 'min'
                elif fieldDict[column]['type'] == 'mean' or fieldDict[column]['type'] == 'sum':
                    groupingDict[column] = fieldDict[column]['type']
                else:
                    pass
                    
            # applying this .agg() transforms the groupBy object back into a regular dataframe
            groupData = groupData.agg(groupingDict)

            # Give actual name to Bin column since it was created within analysis.py and is initially nameless
            if len(rangeGroup) > 0:
                indexNames = list(groupData.index.names)
                rangeColumnIndex = len(indexNames) - 1
                indexNames[rangeColumnIndex] = 'Bin'
                groupData.index.rename(indexNames, inplace=True)
            # groupData = groupData.sort_values(by='Time')
            groupCount = len(groupData)

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
            resetRatio = []
            # endregion

            # region Calculate stats for each summary group
            for k in xrange(groupCount):
                hitCount = float(groupData['Hit'][k])
                missCount = float(groupData['Miss'][k])
                missNRCount = float(groupData['Miss (NR)'][k])
                FACount = float(groupData['FA'][k])
                CRCount = float(groupData['CR'][k])
                CRNRCount = float(groupData['CR (NR)'][k])
                totalTrials = float(groupData['Trials'][k])
                probeHitCount = float(groupData['Probe Hit'][k])
                probeMissCount = float(groupData['Probe Miss'][k])
                probeMissNRCount = float(groupData['Probe Miss (NR)'][k])
                probeFACount = float(groupData['Probe FA'][k])
                probeCRCount = float(groupData['Probe CR'][k])
                probeCRNRCount = float(groupData['Probe CR (NR)'][k])
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

                resetRatio.append(self.divide_by_zero(CRCount, (CRCount + CRNRCount), 5))

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
            groupData["d' (NR)"] = dprimes_NR
            groupData['Beta'] = betas
            groupData['Beta (NR)'] = betas_NR
            groupData['S+ Rate'] = sPlus_correct
            groupData['S+ (NR) Rate'] = sPlus_NR_correct
            groupData['S- Rate'] = sMinus_correct
            groupData['S- (NR) Rate'] = sMinus_NR_correct
            groupData['Total Corr'] = total_correct
            groupData['Total Corr (NR)'] = total_NR_correct
            groupData["Probe d'"] = probeDprimes
            groupData["Probe d' (NR)"] = probeDprimes_NR
            groupData['Probe Beta'] = probeBetas
            groupData['Probe Beta (NR)'] = probeBetas_NR
            groupData['Probe S+ Rate'] = probePlus_correct
            groupData['Probe S+ (NR) Rate'] = probePlus_NR_correct
            groupData['Probe S- Rate'] = probeMinus_correct
            groupData['Probe S- (NR) Rate'] = probeMinus_NR_correct
            groupData['Probe Tot Corr'] = total_probe_correct
            groupData['Probe Tot Corr (NR)'] = total_probe_NR_correct
            groupData['Prop CR Resets'] = resetRatio

            # endregion

            # if len(rangeGroup) > 0:
            #     groupData.index[''].drop()

        else:  # If no grouping specified, return raw data
            groupData = input_data
            # groupData = groupData.drop(['Date'], axis=1)
            groupData.reset_index()

        # Get list of columns to remove
        dropColumns = []

        if 'dropCols' in kwargs and len(kwargs['dropCols']) > 0:
            dropColumns += kwargs['dropCols']

        # Set column order

        sortedColumns = FieldList().fieldList

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

                            message = 'Record {:d} does not meet trial count criteria ({:d} trials vs {:d} minimum)' \
                                .format(i, ntrials, trialThreshold)
                            if verbose:
                                print message
                            self.log.debug(message)

            if criteria_result[i] is not False:  # skip next check if already failed previous criteria
                if 'dprime' in criteria:
                    if use_NR:
                        dprime_actual = row["d' (NR)"]
                        dprime_min = criteria["d' (NR)"]
                    else:
                        dprime_actual = row["d'"]
                        dprime_min = criteria["d'"]

                    if dprime_actual < dprime_min:
                        criteria_result[i] = False

                        message = "Record {:d} failed d' criteria ({:d} actual vs {:d} minimum)" \
                            .format(i, dprime_actual, dprime_min)
                        if verbose:
                            print message
                        self.log.debug(message)

            if criteria_result[i] is not False:  # skip next check if already failed previous criteria
                if 'propCorrect' in criteria:
                    for category in criteria['propCorrect']:
                        if 'type' in category:
                            proportion = row[category['type']]
                            stim_type = category['type']
                        elif use_NR:
                            proportion = row['Total Corr (NR)']
                            stim_type = 'Total_NR'
                        else:
                            proportion = row['Total Corr']
                            stim_type = 'Total'

                        if proportion < category['minimum']:
                            criteria_result[i] = False

                            message = "Category {} failed proportion correct criteria ({:0.3f} actual vs {:0.3f} " \
                                      "minimum)".format(stim_type, proportion, category['minimum'])
                            if verbose:
                                print message
                            self.log.debug(message)

            i += 1

        if 'days' in criteria:  # criteria not met on at least 'days' days
            num_days = sum(criteria_result)
            min_days = criteria['days']
        else:  # otherwise if ANY days don't meet criteria,
            num_days = sum(criteria_result)
            min_days = len(criteria_result)
            # return false
        if num_days < min_days:
            message = "Not enough days meeting criteria ({:d} days, {:d} min)".format(num_days, min_days)
            if verbose:
                print message
            self.log.debug(message)
            return False

        # Otherwise, return true

        message = "Meets all criteria!"
        if verbose:
            print message
        self.log.debug(message)
        return True

# datapath = '/home/rouse/bird/data/y18r8'
# perform = Performance(datapath).gather_raw_data()
# stats = perform.analyze('raw')
# stats.to_csv(os.path.join(datapath,'test.csv'))
# print stats
