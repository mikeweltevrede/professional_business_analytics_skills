import os
from tqdm import tqdm
import pickle

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns; sns.set_style("whitegrid", rc={'grid.color': '.8'})

from DataFunction import generateData
from NPVFunction import NPV_SAA

verbose = False

# Import data
data_path = "data/DataPBAS.xlsx"
data1000_path = "data/data1000.pkl"
Data_baseline = {0: generateData(data_path, probability={'all': [0, 1, 0]})}

if os.path.isfile(data1000_path):
    # Then this file already exists and can be imported
    with open(data1000_path, "rb") as data:
        Data1000 = pickle.load(data)
else:
    num_scenarios = 1000
    Data1000 = {i: generateData(data_path) for i in tqdm(range(num_scenarios))}

    with open(data1000_path, "wb") as data:
        pickle.dump(Data1000, data)

# Determined optimal width and height from previous analysis
width = 1.84
height = 1.08

# Set option parameters
option = 2
min_percentage = 0.01
means = Data1000[0]['ProductSize'].groupby('Market')['Size (inches)'].agg(np.mean)
means = means/sum(means)
means_scaled = means/(min(means)/min_percentage)

product_thresholds = {'notebooks': means_scaled['Notebook'],
                      'monitors': means_scaled['Monitor'],
                      'televisions': means_scaled['Television']}

# Run the model for the baseline data and the 1000 Scenarios Data
baseline_results = NPV_SAA(Data_baseline, h=height, w=width, option=option,
                           product_thresholds=product_thresholds, verbose=verbose)
baseline_NPV = baseline_results['Average NPV']
results_1000 = NPV_SAA(Data1000, h=height, w=width, option=option,
                       product_thresholds=product_thresholds, verbose=verbose)

# Make histogram of NPVs
npvs = results_1000['NPVs']
results_bad = NPV_SAA(Data1000, h=1.85, w=1.06, option=option,
                      product_thresholds=product_thresholds, verbose=verbose)
results_baseline_bad = NPV_SAA(Data_baseline, h=1.85, w=1.06, option=option,
                               product_thresholds=product_thresholds, verbose=verbose)
npvs_bad = results_bad['NPVs']
baseline_bad = results_baseline_bad['Average NPV']

# "Optimal" plot
ax = sns.distplot(npvs, color="#4ba173", label = "Distribution of the NPV")
ax.axvline(0, color='black', alpha=0.5, label = "NPV = 0", linestyle="--")
ax.axvline(np.mean(npvs), color="#ff5252", label = "Average NPV", linestyle="--")
ax.axvline(baseline_NPV, color="#3d85c6", label = "Baseline NPV", linestyle="--")
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
ax.axvline(0, color='black', alpha=0.5, label = "NPV = 0", linestyle="--")
ax.axvline(np.mean(npvs_bad), color="#ff5252", label = "Average NPV", linestyle="--")
ax.axvline(baseline_bad, color="#3d85c6", label = "Baseline NPV", linestyle="--")
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
      f"Probability of negative NPV: {results_1000['#NegativeScenarios']/1000}")
print(f"Mean NPV: {np.mean(pos_npvs_3)}, "
      f"Probability of negative NPV: {results_3['#NegativeScenarios']/1000}")

# NPV versus Number of different products produced
df = pd.DataFrame({'Option': [0,1,2],'Number of different products produced': [2,3,13],
                   'NPVs': [754.961268038783, 720.414809293799, 569.712314425463]})

num_ticks = 9

ax = sns.barplot(x='Option', y='NPVs', data=df, palette=sns.color_palette(['#4ba173']),
                 label='Net Present Value')
lgd1 = ax.legend(bbox_to_anchor=(0.4, -0.15))
ax.set_xticklabels([1,2,3])
plt.ylabel("Net Present Value (million USD)")
ax2 = ax.twinx()
sns.lineplot(x='Option', y='Number of different products produced', data=df, ax=ax2,
             color='#ff5252', marker='o', label='Number of different products produced')
lgd2 = ax2.legend(bbox_to_anchor=(1.05, -0.15))
ax.set_yticks(np.linspace(0, int(np.ceil(ax.get_ybound()[1]/100.0))*100, num_ticks))
ax2.set_yticks(np.linspace(0, np.ceil(ax2.get_ybound()[1]), num_ticks))
plt.savefig("output/NPVs_versus_number_of_products_produced.png", dpi=300,
            bbox_extra_artists=(lgd1,), bbox_inches='tight')
plt.show()

# Check whether orientations are concurrent across scenarios. If not, find the percentage of times
# that it is either orientation.
orientations = {}
for prod in range(12):
    ort = [results_1000['POS'][s][prod]['product_orientation']
           for s in range(len(results_1000['POS']))]
    
    if len(set(ort)) == 1:
        orientations[prod] = set(ort)
    else:
        orientations[prod] = {'vert': sum(o == 'vert' for o in
                                          [results_1000['POS'][s][prod]['product_orientation']
                                           for s in range(len(results_1000['POS']))])/1000,
                              'hor': sum(o == 'hor' for o in
                                         [results_1000['POS'][s][prod]['product_orientation']
                                          for s in range(len(results_1000['POS']))])/1000}
