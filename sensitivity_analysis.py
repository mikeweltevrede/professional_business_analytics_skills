import pickle
import os

from tqdm import tqdm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns; sns.set_style("whitegrid", rc={'grid.color': '.9'})

from DataFunction import generateData
from NPVFunction import NPV_SAA

verbose = False

# Import data
data_path = "data/DataPBAS.xlsx"
Data_baseline = {0: generateData(data_path, probability={'all': [0, 1, 0]})}

# Determined optimal width and height from previous analysis
width = 1.84
height = 1.08

# Set option parameters
option = 2
min_percentage = 0.01
means = Data_baseline[0]['ProductSize'].groupby('Market')['Size (inches)'].agg(np.mean)
means = means/sum(means)
means_scaled = means/(min(means)/min_percentage)

product_thresholds = {'notebooks': means_scaled['Notebook'],
                      'monitors': means_scaled['Monitor'],
                      'televisions': means_scaled['Television']}

baseline_NPV = NPV_SAA(Data_baseline, h=height, w=width, option=option,
                       product_thresholds=product_thresholds,
                       verbose=verbose)['Average NPV']

# Tornado Chart
keys = ['tv', 'prices', 'substrate_prices', 'investment', 'yield', 'R&D', 'SG&A', 'TaxRate', 'DPO',
        'DIO', 'DSO']

NPVs = {'key': [], 'low': [], 'baseline': baseline_NPV, 'high': [], 'diff': [],
        'low_value_selection': [], 'high_value_selection': []}

def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)

for key in keys:
    Data_low = {0: generateData(data_path, probability={'all': [0, 1, 0], key: [1, 0, 0]})}
    Data_high = {0: generateData(data_path, probability={'all': [0, 1, 0], key: [0, 0, 1]})}

    results = [NPV_SAA(Data_low, h=height, w=width, option=option,
                       product_thresholds=product_thresholds, verbose=verbose)['Average NPV'],
               NPV_SAA(Data_high, h=height, w=width, option=option,
                       product_thresholds=product_thresholds, verbose=verbose)['Average NPV']]

    if key in {'yield', 'prices'}:
        selections = [Data_low[0][f"{key}_selection"][0,0], Data_high[0][f"{key}_selection"][0,0]]
    else:
        try:
            selections = [Data_low[0][f"{key}_selection"][0], Data_high[0][f"{key}_selection"][0]]
        except KeyError:
            selections = [Data_low[0][f"{key}"], Data_high[0][f"{key}"]]
        
    selections = [selections[i] for i in argsort(results)]

    results.sort()

    NPVs['key'].append(key)
    NPVs['low'].append(results[0])
    NPVs['high'].append(results[1])
    NPVs['diff'].append(results[1]-results[0])
    NPVs['low_value_selection'].append(selections[0])
    NPVs['high_value_selection'].append(selections[1])

df = pd.DataFrame(NPVs).sort_values('diff')
df.to_csv("output/sensitivity_analysis.csv", index=False)
