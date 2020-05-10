import pickle
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns; sns.set()

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

# Make histogram of NPVs
data1000_path = "data/data1000.pkl"
if os.path.isfile(data1000_path):
    # Then this file already exists and can be imported
    with open(data1000_path, "rb") as data:
        Data1000 = pickle.load(data)
else:
    num_scenarios = 1000
    data_path = "data/DataPBAS.xlsx"
    Data1000 = {i: generateData(data_path) for i in tqdm(range(num_scenarios))}

    with open(data1000_path, "wb") as data:
        pickle.dump(Data1000, data)
        
npvs = NPV_SAA(Data1000, h=height, w=width, option=option, product_thresholds=product_thresholds,
               verbose=verbose)['NPVs']

# TODO: Change font to Proxima Nova?
# g = sns.distplot(npvs, color="#4ba173")
# plt.axvline(0, color="#ff5252")
# ax.set(xlabel='Net Present Value')
# frame = plt.gca() 
# frame.axes.get_yaxis().set_visible(False)
# plt.show()

g = sns.distplot(npvs, color="#4ba173", hist=False)
plt.axvline(0, color="#ff5252")
ax = plt.gca()
plt.locator_params(axis='x', nbins=3)
xlabels = ['$'+  '{:,.0f}'.format(x) + 'M' for x in g.get_xticks()/1000000]
g.set_xticklabels(xlabels)
plt.show()
