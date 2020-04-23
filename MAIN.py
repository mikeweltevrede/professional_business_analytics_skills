# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 10:23:51 2020
MAIN script
"""


from DataFunction import generateData
from NPVFunction import NPV_SAA
import numpy as np
import pandas as pd
import time

Scenarios = 10
n_width = 18
n_height = 12

width = np.array([1.85-0.05*i for i in range(n_width)])
height = np.array([1.55-0.05*i for i in range(n_height)])

start_time = time.time()
Data = {}
for i in range(Scenarios):
    Data[i] = generateData("DataPBAS.xlsx")

print(f"Data generation took {time.time()-start_time} seconds")

Products = len(Data[0]['ProductSize'])
Time = len(Data[0]['ProductPrice'].columns)

NPV = pd.DataFrame(np.zeros((n_height, n_width)), index = height, columns = width)
for w in range(len(width)):
    for h in range(len(height)):
        NPV_ = NPV_SAA(Data,width[w],height[h])
        NPV.values[h,w] = NPV_['Average NPV']

NPV.to_csv('NPV Table.csv')
