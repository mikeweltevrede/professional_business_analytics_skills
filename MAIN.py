# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 10:23:51 2020
MAIN script
"""


import numpy as np
import pandas as pd
from DataFunction import generateData
from NPVFunction import NPV_SAA

Scenarios = 10
n_width = 5
n_height = 5

Data = {i: generateData("data/DataPBAS.xlsx") for i in range(Scenarios)}

widths = [Data[0]['Max_width']-0.05*i for i in range(n_width)]
heights = [Data[0]['Max_height']-0.05*i for i in range(n_height)]

Products = len(Data[0]['ProductSize'])
Time = len(Data[0]['ProductPrice'].columns)

NPV = pd.DataFrame(np.zeros((n_width, n_height)), index=widths,
                   columns=heights)
for w in range(n_width):
    for h in range(n_height):
        NPV_ = NPV_SAA(Data, widths[w], heights[h])
        NPV.values[w, h] = NPV_['Average NPV']

NPV.to_csv('output/NPV Table.csv')
