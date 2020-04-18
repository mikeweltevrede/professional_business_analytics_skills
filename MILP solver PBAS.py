# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 11:40:46 2020
PBAS
"""
import gurobipy as gb
from gurobipy import quicksum   
from DataFunction import generateData
import numpy as np

Scenarios = 10

Data = {}
for i in range(Scenarios):
    Data[i] = generateData("DataPBAS.xlsx")
    
Products = len(Data[1]['ProductSize'])
Time = len(Data[1]['ProductPrice'].columns)
w = 1.799
h = 1.348

W = np.zeros((Products,Scenarios))
H = np.zeros((Products,Scenarios))
## CONSTRAINTS
for p in range(Products):
    for s in range(Scenarios):
        W[p,s] = np.floor(w/(Data[s]['ProductSize'].values[p,3]+Data[s]['ProductSize'].values[p,4]))
        H[p,s] = np.floor(h/(Data[s]['ProductSize'].values[p,2]+Data[s]['ProductSize'].values[p,4]))



m = gb.Model('PBAS')

## VARIABLES
x = m.addVars(Products,Time,vtype=gb.GRB.INTEGER, lb= 0, name='Substrate per product over time')

#W = m.addVars(Products,Scenarios,vtype = gb.GRB.INTEGER, lb=0,name = 'Products on Horizontal')
#H = m.addVars(Products,Scenarios,vtype = gb.GRB.INTEGER, lb=0,name = 'Products on Vertical')
ApS = m.addVars(Products,Scenarios,vtype = gb.GRB.INTEGER, lb=0,name = 'Products on Substrate')
Profit = m.addVars(Products,Time,Scenarios,vtype=gb.GRB.CONTINUOUS,name='Profit per Substrate per product')


#m.addConstr(w <= 1.55,name='Capacity Constraint Width')
#m.addConstr(h <= 1.85,name='Capacity Constraint Height')

#for p in range(Products):
#    for s in range(Scenarios):
#        m.addQConstr(ApS[p,s] == W[p,s]*H[p,s], name='Products on substrate')
#for p in range(Products):
#    for s in range(Scenarios):
#        ApS[p,s] = W[p,s]*H[p,s]
#
ApS = {s: {p: W[p,s]*H[p,s] for p in range(Products)} for s in range(Scenarios)}        

for t in range(Time):
    m.addConstr(quicksum(x[p,t] for p in range(Products)) <= Data[0]['MaxCapacity']*12,name='Yearly Substrate Capacity')

#for p in range(Products):
#    for t in range(Time):
#        for s in range(Scenarios):
#            m.addQConstr(Profit[p,t,s] == (Data[s]['ProductPrice'].values[p,t]*Data[s]['Yield'].values[p,t]*ApS[s][p])-(Data[s]['SubstrateCost'].values[0,t]*(w*h)),name='Profit per substrate for each product')

Profit = {s: {p: {t: (Data[s]['ProductPrice'].values[p,t]*Data[s]['Yield'].values[p,t]*ApS[s][p])-(Data[s]['SubstrateCost'].values[0,t]*(w*h)) for t in range(Time) } for p in range(Products)} for s in range(Scenarios)}
## OBJECTIVE


obj = gb.LinExpr()
obj = quicksum(quicksum(quicksum(Profit[s][p][t]*x[p,t] for s in range(Scenarios)) for t in range(Time)) for p in range(Products))

m.setObjective(obj, gb.GRB.MAXIMIZE)

m.optimize()



