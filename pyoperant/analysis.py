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


class Performance(object):
    # Longer-term performance analysis

    def __init__(self, experiment_folder):
        # Validate input folder
        if not os.path.exists(experiment_folder):
            print "invalid input folder"
            return

        self.data_dir = os.path.join(experiment_folder, 'trialdata')
        if not os.path.exists(self.data_dir):
            print "data folder (%s) not found" % self.data_dir
            return

        self.json_dir = os.path.join(experiment_folder, 'settings_files')
        if not os.path.exists(self.json_dir):
            print "json folder (%s) not found" % self.json_dir
            return

        # Each row in dataDict will be a single
        dataDict = {'File': [],
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
        self.gather_raw_data(dataDict)

    def gather_raw_data(self, data_dict):
        # Pull data from across multiple csv files, keeping notation for phase (which comes from the json file)

        csvList = os.listdir(self.data_dir)
        csvCount = len(csvList)

        # region Read each CSV file
        for i in range(csvCount):
            csvPath = os.path.join(self.data_dir, csvList[i])
            with open(csvPath) as data_file:
                csv_reader = csv.reader(data_file, delimiter=',')
                rowCount = len(list(csv_reader)) - 1  # check if csv has data beyond header
                if rowCount < 1:
                    fileEmpty = True
                else:
                    fileEmpty = False

            if fileEmpty is False:  # Separated from above to allow data_file to close and be reopened for actual 
                # scanning
                with open(csvPath) as data_file:
                    csv_reader = csv.reader(data_file, delimiter=',')
                    currentLine = 0  # resets each time so later we can tell how many lines were imported
                    for row in csv_reader:
                        if currentLine == 0:
                            pass  # ignore first line (headers)
                        else:
                            data_dict['Index'].append(row[1])
                            data_dict['Stimulus'].append(row[3])
                            data_dict['Class'].append(row[4])
                            data_dict['Response'].append(row[5])
                            data_dict['RT'].append(row[7])
                            data_dict['Reward'].append(row[8])
                            data_dict['Punish'].append(row[9])
                            data_dict['Time'].append(row[10])
                            data_dict['Session'].append(i)
                            data_dict['File'].append(csvList[i])
                            data_dict['Subject'].append(csvList[i].partition('_')[0])
                        currentLine += 1

                jsonFile = os.path.splitext(csvList[i])[0].rpartition('_')[2] + '.json'
                jsonPath = os.path.join(self.json_dir, jsonFile)
                with open(jsonPath, 'r') as f:
                    jsonData = json.load(f)
                blockName = jsonData['block_design']['order'][0]
                for j in range(currentLine - 1):
                    data_dict['Block'].append(blockName)
        # endregion

        # Double check that each key in dict has same length
        trial_count = len(data_dict['Index'])  # 'Index' is arbitrary, just need total count of trials
        keyLengths = [len(x) for x in data_dict.values()]
        if not self.dict_len_is_equal(keyLengths):
            raise Exception('Columns are not equal length')

        # region Get result of each trial
        if trial_count < 1:
            print 'No trials found'
        else:
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

            for i in range(trial_count):
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
            self.raw_trial_data = pd.DataFrame.from_dict(data_dict)  # Convert to data frame
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
        # Only takes self.raw_trial_data as input data: unfiltered
        #
        # kwargs are filter type and settings
        parameters = kwargs
        filtered_data = self.raw_trial_data
        if 'startdate' in parameters:
            # Filter sessions prior to start date
            filtered_data = filtered_data[filtered_data['Time'] > parameters['startdate']]
        if 'block' in parameters:
            filtered_data = filtered_data[filtered_data['Block'] == parameters['block']]

        self.filtered_data = filtered_data

    def summarize(self, inputdata='raw'):
        # produces summary dataframe that just contains date, block, and responses
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

        # region Create new dataframe with only relevant fields
        performanceData = pd.DataFrame()
        performanceData['Time'] = trialdata['Time']
        performanceData['Block'] = trialdata['Block']

        performanceData['Hit'] = trialdata['Hit']
        performanceData['Miss'] = trialdata['Miss']
        performanceData['Miss\n(NR)'] = trialdata['Miss\n(NR)']
        performanceData['FA'] = trialdata['FA']
        performanceData['CR'] = trialdata['CR']
        performanceData['CR\n(NR)'] = trialdata['CR\n(NR)']

        performanceData['Trials'] = trialdata['Trial Count']

        performanceData['Probe Hit'] = trialdata['Probe Hit']
        performanceData['Probe Miss'] = trialdata['Probe Miss']
        performanceData['Probe Miss\n(NR)'] = trialdata['Probe Miss\n(NR)']
        performanceData['Probe FA'] = trialdata['Probe FA']
        performanceData['Probe CR'] = trialdata['Probe CR']
        performanceData['Probe CR\n(NR)'] = trialdata['Probe CR\n(NR)']

        performanceData['Probe Trials'] = trialdata['Probe Trials']
        # endregion

        performanceData.sort_values(by='Date')

        self.summaryData = performanceData

    def analyze(self, input_data, **kwargs):
        # Calculate d' scores for summarized data
        # Now have all trials in lists, need to group them in some way (by day, day/hour, etc.)

        # region Summarize input data based on kwargs, or by default (date and block)
        if 'groupBy' in kwargs:
            if kwargs['groupBy'] == 'day':
                groupData = input_data.groupby([input_data['Time'].dt.date, input_data['Block']]).sum()
                groupCount = len(groupData)
            elif kwargs['groupBy'] == 'hour':
                groupData = input_data.groupby([input_data['Time'].dt.date, input_data['Time'].dt.hour,
                                                input_data['Block']]).sum()
                groupCount = len(groupData)
            else:  # catch all other cases, can fill out later
                groupData = input_data.groupby([input_data['Time'].dt.date, input_data['Block']]).sum()
                groupCount = len(groupData)
        else:  # If no grouping specified, use date as default
            groupData = input_data.groupby([input_data['Time'].dt.date, input_data['Block']]).sum()
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
        for k in range(groupCount):
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
                dayProbeBeta = round(Analysis([[probeHitCount, probeMissCount], [probeFACount, probeCRCount]]).bias(),
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
        groupData['β'] = betas
        groupData['β\n(NR)'] = betas_NR
        groupData['S+'] = sPlus_correct
        groupData['S+\n(NR)'] = sPlus_NR_correct
        groupData['S-'] = sMinus_correct
        groupData['S-\n(NR)'] = sMinus_NR_correct
        groupData['Total Corr'] = total_correct
        groupData['Total Corr\n(NR)'] = total_NR_correct
        groupData["Probe d'"] = probeDprimes
        groupData["Probe d'\n(NR)"] = probeDprimes_NR
        groupData['Probe β'] = probeBetas
        groupData['Probe β\n(NR)'] = probeBetas_NR
        groupData['Probe S+'] = probePlus_correct
        groupData['Probe S+\n(NR)'] = probePlus_NR_correct
        groupData['Probe S-'] = probeMinus_correct
        groupData['Probe S-\n(NR)'] = probeMinus_NR_correct
        groupData['Probe Tot Corr'] = total_probe_correct
        groupData['Probe Tot Corr\n(NR)'] = total_probe_NR_correct
        # endregion

        # region Filter out unwanted fields (e.g., NR trials, probe trials)
        # Get list of columns to remove
        dropColumns = []
        if 'NRTrials' in kwargs:
            if kwargs['NRTrials']:
                dropColumns += ["d'", 'β', 'S+', 'S-', 'Total Corr',
                                "Probe d'", 'Probe β', 'Probe S+', 'Probe S-', 'Probe Tot Corr']
            else:
                dropColumns += ["d'\n(NR)", 'β\n(NR)', 'S+\n(NR)', 'S-\n(NR)', 'Total Corr\n(NR)',
                                "Probe d'\n(NR)", 'Probe β\n(NR)', 'Probe S+\n(NR)', 'Probe S-\n(NR)',
                                'Probe Tot Corr\n(NR)']

        if 'probeTrials' in kwargs:
            if not kwargs['probeTrials']:
                dropColumns += ["Probe d'", "Probe d'\n(NR)", 'Probe β', 'Probe β\n(NR)', 'Probe Trials', 'Probe Hit',
                                'Probe Miss', 'Probe Miss\n(NR)', 'Probe FA', 'Probe CR', 'Probe CR\n(NR)', 'Probe S+',
                                'Probe S+\n(NR)', 'Probe S-', 'Probe S-\n(NR)', 'Probe Tot Corr',
                                'Probe Tot Corr\n(NR)']

        if 'rawTrials' in kwargs:
            if not kwargs['rawTrials']:
                dropColumns += ['Hit', 'Miss', 'Miss\n(NR)', 'FA', 'CR', 'CR\n(NR)',
                                'Probe Hit', 'Probe Miss', 'Probe Miss\n(NR)', 'Probe FA', 'Probe CR', 'Probe CR\n(NR)']

        dropColumns = list(set(dropColumns))  # Remove duplicates

        # Set column order

        sortedColumns = ["d'", "d'\n(NR)", 'β', 'β\n(NR)', "Probe d'", "Probe d'\n(NR)", 'Probe β', 'Probe β\n(NR)',
                         'Trials', 'Probe Trials', 'S+', 'S+\n(NR)', 'S-', 'S-\n(NR)',
                         'Total Corr', 'Total Corr\n(NR)', 'Probe S+', 'Probe S+\n(NR)', 'Probe S-', 'Probe S-\n(NR)',
                         'Probe Tot Corr', 'Probe Tot Corr\n(NR)', 'Hit', 'Miss', 'Miss\n(NR)', 'FA', 'CR',
                         'CR\n(NR)', 'Probe Hit', 'Probe Miss', 'Probe Miss\n(NR)', 'Probe FA', 'Probe CR',
                         'Probe CR\n(NR)'
                         ]  # All columns in sorted order

        remainingColumns = list(filter(lambda a: a not in dropColumns, sortedColumns))  # Get list of remaining columns
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
                            if verbose:
                                print 'Record %d does not meet trial count criteria (%d trials vs %d minimum)' % \
                                      (i, ntrials, trialThreshold)

            if criteria_result[i] is not False:  # skip next check if already failed previous criteria
                if 'dprime' in criteria:
                    if use_NR:
                        dprime_actual = row['dPrime_NR']
                        dprime_min = criteria['dPrime_NR']
                    else:
                        dprime_actual = row['dPrime']
                        dprime_min = criteria['dPrime']

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
                            proportion = row['totalNRCorr']
                            stim_type = 'Total_NR'
                        else:
                            proportion = row['totalCorr']
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
