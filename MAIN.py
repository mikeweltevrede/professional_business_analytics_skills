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

start_time = time.time()
Data = {}
for i in range(Scenarios):
    Data[i] = generateData("DataPBAS.xlsx")
 
end_time = time.time()    
Products = len(Data[0]['ProductSize'])
Time = len(Data[0]['ProductPrice'].columns)

width = np.array([1+0.05*i for i in range(18)])
height = np.array([1+0.05*i for i in range(12)])



NPV = pd.DataFrame(np.zeros((len(height),len(width))), index = height, columns = width)
for w in range(len(width)):
    for h in range(len(height)):
        NPV_ = NPV_SAA(Data,width[w],height[h])
        NPV.values[h,w] = NPV_['Average NPV']

NPV.to_csv('NPV Table')