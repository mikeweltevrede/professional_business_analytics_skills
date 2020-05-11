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

results = NPV_SAA(Data1000, h=height, w=width, option=option, product_thresholds=product_thresholds,
               verbose=verbose)
npvs = results['NPVs']
npvs_bad = NPV_SAA(Data1000, h=1.85, w=1.06, option=option, product_thresholds=product_thresholds,
                   verbose=verbose)['NPVs']

# "Optimal" plot
ax = sns.distplot(npvs, color="#4ba173", label = "Distribution of the NPV")
ax.axvline(0, color='black', alpha=0.5, label = "NPV = 0")
ax.axvline(np.mean(npvs), color="#ff5252", label = "Average NPV")
ax.set_xticklabels(['{:,.0f}'.format(x) for x in ax.get_xticks()/1e9])
ax.set_yticklabels([int(round(y*1e10)) for y in ax.get_yticks()])
ax.set(ylim=(0, 6.5e-10))
plt.xlabel("Net Present Value (billions $) for 1000 possible scenarios")
plt.ylabel("Probability of occuring ($10^{-7}$%)")
ax.legend(loc='upper left')
sns.despine()
plt.tight_layout()
plt.savefig("output/distplot_optimal.png", dpi=300)
plt.show()

# "Bad" plot
ax = sns.distplot(npvs_bad, color="#4ba173", label = "Distribution of the NPV")
ax.axvline(0, color='black', alpha=0.5, label = "NPV = 0")
ax.axvline(np.mean(npvs_bad), color="#ff5252", label = "Average NPV")
ax.set_xticklabels(['{:,.1f}'.format(x) for x in ax.get_xticks()/1e9])
ax.set_yticklabels([int(round(y*1e10)) for y in ax.get_yticks()])
ax.set(ylim=(0, 9e-10))
plt.xlabel("Net Present Value (billions \$) for 1000 possible scenarios")
plt.ylabel("Probability of occuring ($10^{-7}$%)")
ax.legend(loc='upper left')
sns.despine()
plt.tight_layout()
plt.savefig("output/distplot_bad.png", dpi=300)
plt.show()

# Determine NPVs for the other options
results_1 = NPV_SAA(Data1000, h=height, w=width, option=1, verbose=verbose)
results_3 = NPV_SAA(Data1000, h=height, w=width, option=3, product_thresholds=0.005,
                 verbose=verbose)

pos_npvs_1 = [npv for npv in results_1['NPVs'] if npv > 0]
pos_npvs_2 = [npv for npv in npvs if npv > 0]
pos_npvs_3 = [npv for npv in results_3['NPVs'] if npv > 0]

print(f"Mean NPV: {np.mean(pos_npvs_1)}, "
      f"Probability of negative NPV: {results_1['#NegativeScenarios']/1000}")
print(f"Mean NPV: {np.mean(pos_npvs_2)}, "
      f"Probability of negative NPV: {results['#NegativeScenarios']/1000}")
print(f"Mean NPV: {np.mean(pos_npvs_3)}, "
      f"Probability of negative NPV: {results_3['#NegativeScenarios']/1000}")
