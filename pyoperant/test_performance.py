import csv

csvPath = '/home/rouse/bird/data/g98o15/trialdata/g98o15_trialdata_20250630124047.csv'
data_file = open(csvPath, 'rb')
csv_reader = csv.reader(data_file, delimiter = ',')
print("hi")