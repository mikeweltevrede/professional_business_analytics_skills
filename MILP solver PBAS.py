# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 11:40:46 2020
PBAS
"""
import gurobipy as gb
from gurobipy import quicksum   
from DataFunction import generateData
import numpy as np

Scenarios = 2
w = 1.799
h = 1.348


Data = {}
for i in range(Scenarios):
    Data[i] = generateData("DataPBAS.xlsx")
    
Products = len(Data[0]['ProductSize'])
Time = len(Data[0]['ProductPrice'].columns)


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
ApS = m.addVars(Products,Scenarios,vtype = gb.GRB.INTEGER, lb=0,name = 'Products on Substrate')
GM = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS,name='GrossMargin')
OM = m.addVars(Scenarios, Time,vtype=gb.GRB.CONTINUOUS, name = 'Operating Margin')
Sales = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name = 'Sales')
CostofSales = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name = 'Cost of Sales')
NI = m.addVars(Scenarios, Time,vtype=gb.GRB.CONTINUOUS, name = 'Net Income')
NCF = m.addVars(Scenarios, Time,vtype=gb.GRB.CONTINUOUS, name = 'Net Cash Flow')
NPV = m.addVars(Scenarios,Time,vtype=gb.GRB.CONTINUOUS, name = 'Net Present Value')



ApS = {s: {p: W[p,s]*H[p,s] for p in range(Products)} for s in range(Scenarios)}        

for t in range(Time):
    m.addConstr(quicksum(x[p,t] for p in range(Products)) <= Data[0]['MaxCapacity']*12,name='Yearly Substrate Capacity')



for s in range(Scenarios):
    for t in range(Time):
        m.addConstr(Sales[s,t] == quicksum(Data[s]['ProductPrice'].values[p,t]*Data[s]['Yield'].values[p,t]*ApS[s][p]*x[p,t] for p in range(Products)),name='Sales constraint')
            
for s in range(Scenarios):
    for t in range(Time):         
        m.addConstr(CostofSales[s,t] == quicksum(Data[s]['SubstrateCost'].values[0,t]*(w*h)*x[p,t]    for p in range(Products)) + Data[s]['Depreciation'].values[0,t],name='Cost of Sales constraint')
# + Data[s]['Depreciation'].values[0,t]
for s in range(Scenarios):
    for t in range(Time):
        GM[s,t] = Sales[s,t]-CostofSales[s,t]
    
for s in range(Scenarios):
    for t in range(Time):
        OM[s,t] = GM[s,t] - Sales[s,t]*(Data[s]['R&D']+Data[s]['SG&A'])

for s in range(Scenarios):
    for t in range(Time):
        NI[s,t] = (1-Data[s]['TaxRate'])*OM[s,t]
        
for s in range(Scenarios): ## DWC moet er nog bij.
    for t in range(Time):
        NCF[s,t] = NI[s,t] + Data[s]['Depreciation'].values[0,t] - Data[s]['InvestmentCost'].values[0,t]

for s in range(Scenarios): 
    for t in range(Time):
        NPV[s,t] = NCF[s,t]/((1+Data[s]['WACC'])**t)




## OBJECTIVE

obj = gb.LinExpr()
obj = (1/Scenarios)*quicksum(quicksum(NPV[s,t] for s in range(Scenarios))for t in range(Time))

m.setObjective(obj, gb.GRB.MAXIMIZE)

m.optimize()

for var in [CostofSales]:
    for k in var:
        if var[k].x != 0:
            print(k,var[k].x)

for t in range(Time):
    print(t)
    print('NPV:%g' %NPV[0,t].getValue())
    print('GM:%g' %GM[0,t].getValue())
    print('OM:%g' %OM[0,t].getValue())
    print('NI:%g' %NI[0,t].getValue())
    print('NCF:%g' %NCF[0,t].getValue())
