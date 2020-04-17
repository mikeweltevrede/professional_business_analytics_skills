# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 11:40:46 2020
PBAS
"""
import gurobipy as gb
from gurobipy import quicksum   


Scenarios = 10

Data = {}
for i in range(Scenarios):
    Data[i] = generateData("C:/Users/sybra/Documents/BAOR/PBAS/DataPBAS.xlsx")
    
Products = len(Data[1]['ProductSize'])
Time = len(Data[1]['ProductPrice'].columns)

m = gb.Model('PBAS')

## VARIABLES
x = m.addVars(Products,Time,vtype=gb.GRB.INTEGER, lb= 0, name='Substrate per product over time')
w = m.addVar(vtype=gb.GRB.CONTINUOUS, lb = 0, name= 'Width Substrate')
h = m.addVar(vtype=gb.GRB.CONTINUOUS, lb = 0, name= 'Height Substrate')
W = m.addVars(Products,Scenarios,vtype = gb.GRB.INTEGER, lb=0,name = 'Products on Horizontal')
H = m.addVars(Products,Scenarios,vtype = gb.GRB.INTEGER, lb=0,name = 'Products on Vertical')
ApS = m.addVars(Products,Scenarios,vtype = gb.GRB.INTEGER, lb=0,name = 'Products on Substrate')
Profit = m.addVars(Products,Time,Scenarios,vtype=gb.GRB.CONTINUOUS,name='Profit per Substrate per product')

## CONSTRAINTS
for p in range(Products):
    for s in range(Scenarios):
        m.addConstr(W[p,s] <= w/(Data[s]['ProductSize'].values[p,3]+Data[s]['ProductSize'].values[p,4]),name='Number on horizontal')
        m.addConstr(H[p,s] <= h/(Data[s]['ProductSize'].values[p,2]+Data[s]['ProductSize'].values[p,4]),name='Number on vertical')

m.addConstr(w <= 1.55,name='Capacity Constraint Width')
m.addConstr(h <= 1.85,name='Capacity Constraint Height')

for p in range(Products):
    for s in range(Scenarios):
        m.addQConstr(ApS[p,s] == W[p,s]*H[p,s], name='Products on substrate')

for t in range(Time):
    m.addConstr(quicksum(x[p,t] for p in range(Products)) <= Data[0]['MaxCapacity']*12,name='Yearly Substrate Capacity')

for p in range(Products):
    for t in range(Time):
        for s in range(Scenarios):
            m.addQConstr(Profit[p,t,s] == (Data[s]['ProductPrice'].values[p,t]*Data[s]['Yield'].values[p,t]*ApS[p,s])-(Data[s]['SubstrateCost'].values[0,t]*(w*h)),name='Profit per substrate for each product')

## OBJECTIVE

obj = quicksum(quicksum(quicksum(Profit[p,t,s]*x[p,t] for s in range(Scenarios)) for t in range(Time)) for p in range(Products))

m.setObjective(obj, gb.GRB.MAXIMIZE)

m.optimize()



