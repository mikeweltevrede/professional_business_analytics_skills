from DataFunction import generateData
from NPVFunction import NPV_SAA

import numpy as np
import pandas as pd

# Determined optimal width and height from previous analysis
width = 1.85
height = 1.08

# Import data
data_path = "data/DataPBAS.xlsx"
Data_baseline = {0: generateData(data_path, probability={'all': [0, 1, 0]})}

verbose = False

# Set option parameters
option = 2
min_percentage = 0.01
means = Data_baseline[0]['ProductSize'].groupby('Market')['Size (inches)'].agg(np.mean)
reversemeans = (1 - means/sum(means))
# Scale such that minimum is min_percentage%
reversemeans = reversemeans/(min(reversemeans)/min_percentage)

product_thresholds = {'notebooks': reversemeans['Notebook'],
                      'monitors': reversemeans['Monitor'],
                      'televisions': reversemeans['Television']}

baseline_NPV = NPV_SAA(Data_baseline, h=height, w=width, option=option,
                       product_thresholds=product_thresholds, verbose=verbose)['Average NPV']

# Start sensitivity analysis: two per bandwidth possibility
keys = ['tv', 'prices', 'substrate_prices', 'investment', 'yield', 'rd', 'sga', 'tax', 'dpo', 'dio',
        'dso']

NPVs = {'key': [], 'low': [], 'baseline': baseline_NPV, 'high': [], 'diff': []}

for key in keys:
    Data_low = {0: generateData(data_path, probability={'all': [0, 1, 0], key: [1, 0, 0]})}
    Data_high = {0: generateData(data_path, probability={'all': [0, 1, 0], key: [0, 0, 1]})}

    results = [NPV_SAA(Data_low, h=height, w=width, option=option,
                       product_thresholds=product_thresholds, verbose=verbose)['Average NPV'],
               NPV_SAA(Data_high, h=height, w=width, option=option,
                       product_thresholds=product_thresholds, verbose=verbose)['Average NPV']]

    NPVs['key'].append(key)
    NPVs['low'].append(min(results))
    NPVs['high'].append(max(results))
    NPVs['diff'].append(max(results)-min(results))

df = pd.DataFrame(NPVs).sort_values('diff')
df.to_csv("output/sensitivity_analysis.csv", index=False)
