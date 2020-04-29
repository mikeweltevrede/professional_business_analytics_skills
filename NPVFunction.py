# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 12:05:05 2020
PBAS function for Expected value NPV by using SAA (Sample Average Approximation)
"""

import gurobipy as gb
from gurobipy import quicksum
import numpy as np
import collections


def NPV_SAA(Data, w, h):
    
    Scenarios = len(Data)
    Products = len(Data[0]['ProductSize'])
    Time = len(Data[0]['ProductPrice'].columns) - 2

    # Products Per Substrate
    PoS = {}
    for s in range(Scenarios):
        PoS[s] = {}

        for p in range(Products):
            # Note: In our data Height<Width for all products, i.e. all products are oriented to be
            # horizontal.

            # Compute how many products fit if the screen is placed horizontally
            num_width_hor = np.floor(w/Data[s]['ProductSize'].loc[p, 'Width (m)'])
            num_height_hor = np.floor(h/Data[s]['ProductSize'].loc[p, 'Height (m)'])
            num_products_hor = num_width_hor*num_height_hor

            # Compute how many products fit if the screen is placed vertically
            num_width_vert = np.floor(w/Data[s]['ProductSize'].loc[p, 'Height (m)'])
            num_height_vert = np.floor(h/Data[s]['ProductSize'].loc[p, 'Width (m)'])
            num_products_vert = num_width_vert*num_height_vert

            if num_products_hor >= num_products_vert:
                # Products are placed horizontally
                PoS[s][p] = {'num_width': num_width_hor,
                             'num_height': num_height_hor,
                             'num_products': num_products_hor,
                             'product_orientation': 'hor'}
            else:
                # Products are placed vertically
                PoS[s][p] = {'num_width': num_width_vert,
                             'num_height': num_height_vert,
                             'num_products': num_products_vert,
                             'product_orientation': 'vert'}

    # INITIALIZE MODEL
    m = gb.Model('PBAS')

    # VARIABLES
    x = m.addVars(Products, Time, vtype=gb.GRB.INTEGER, lb=0,
                  name='Substrate per product over time')
    GM = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='GrossMargin')
    OM = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Operating Margin')
    Sales = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Sales')
    CostofSales = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Cost of Sales')
    COS2 = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Cost of Sales without depreciation')
    NI = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Net Income')
    NCF = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Net Cash Flow')
    NPV = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Net Present Value')
    CCC = m.addVars(Scenarios, vtype=gb.GRB.CONTINUOUS, name='Cash Conversion Cycle')
    WC = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Working Capital')
    DWC = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Delta Working Capital')
    NPVperScenario = m.addVars(Scenarios, vtype=gb.GRB.CONTINUOUS, name='NPV per Scenario')

    # CONSTRAINTS
    for t in range(Time):
        m.addConstr(quicksum(x[p, t] for p in range(Products)) <= Data[0]
                    ['MaxCapacity']*12, name='Yearly Substrate Capacity')

    for s in range(Scenarios):
        for t in range(Time):
            m.addConstr(Sales[s, t] == quicksum(
                Data[s]['ProductPrice'].iloc[p, t+2] *
                Data[s]['Yield'].iloc[p, t+4]*PoS[s][p]['num_products']*x[p, t]
                for p in range(Products)), name='Sales constraint')

            m.addConstr(CostofSales[s, t] == quicksum(
                Data[s]['SubstrateCost'].iloc[0, t]*(w*h)*x[p, t] for p in range(Products)) +
                Data[s]['Depreciation'].iloc[0, t], name='Cost of Sales constraint')
            
            # Cost of sales without depreciation (needed for P&L)
            m.addConstr(COS2[s, t] == quicksum(
                Data[s]['SubstrateCost'].iloc[0, t]*(w*h)*x[p, t] for p in range(Products)), 
                name='Cost of Sales without depreciation')

            GM[s, t] = Sales[s, t]-CostofSales[s, t]
            OM[s, t] = GM[s, t] - Sales[s, t]*(Data[s]['R&D']+Data[s]['SG&A'])
            NI[s, t] = (1-Data[s]['TaxRate'])*OM[s, t]
            WC[s, t] = Sales[s, t]*CCC[s]
            NCF[s, t] = (NI[s, t] + Data[s]['Depreciation'].iloc[0, t] - DWC[s, t] -
                         Data[s]['InvestmentCost'].iloc[0, t])
            NPV[s, t] = NCF[s, t]/((1+Data[s]['WACC'])**t) # TODO: Check whether this should be **(t+1)

        # These constraints are only made for every s
        CCC[s] = (Data[s]['DIO']+Data[s]['DSO']-Data[s]['DPO'])/365
        NPVperScenario[s] = quicksum(NPV[s, t] for t in range(Time))
        DWC[s, 0] = WC[s, 0]
        
        for t in range(1, Time):
            DWC[s, t] = WC[s, t-1]-WC[s, t]

    # OBJECTIVE
    obj = (1/Scenarios)*quicksum(quicksum(NPV[s, t] for s in range(Scenarios)) for t in range(Time))
    m.setObjective(obj, gb.GRB.MAXIMIZE)

    # RUN OPTIMIZATION
    m.optimize()

    # Count negative scenarios
    NegativeScenario = 0
    for s in range(Scenarios):
        if NPVperScenario[s].getValue() < 0:
            NegativeScenario = NegativeScenario + 1
    
    # ELEMENTS PROFIT AND LOSS STATEMENT
    PL = collections.defaultdict(dict)
    for t in range(Time):
        PL[t]['SALES'] = ((1/Scenarios)*quicksum(Sales[s, t].X for s in range(Scenarios))).getValue()
        PL[t]['COS'] = ((1/Scenarios)*quicksum(COS2[s, t].X for s in range(Scenarios))).getValue()
        PL[t]['GM'] = ((1/Scenarios)*quicksum(GM[s, t].getValue() for s in range(Scenarios))).getValue()
        PL[t]['RD'] = ((1/Scenarios)*quicksum(Data[s]['R&D'] for s in range(Scenarios))).getValue()
        PL[t]['SG&A'] = ((1/Scenarios)*quicksum(Data[s]['SG&A'] for s in range(Scenarios))).getValue()
        PL[t]['Depreciation'] = Data[s]['Depreciation'].iloc[0, t]
        PL[t]['OM'] = ((1/Scenarios)*quicksum(OM[s, t].getValue() for s in range(Scenarios))).getValue()
        PL[t]['TAX'] = ((1/Scenarios)*quicksum(Data[s]['TaxRate'] for s in range(Scenarios))).getValue()
        PL[t]['NI'] = ((1/Scenarios)*quicksum(NI[s, t].getValue() for s in range(Scenarios))).getValue()
        
    return {'Average NPV': obj.getValue(),
            'Width': w,
            'Height': h,
            '#NegativeScenarios': NegativeScenario,
            'PL': PL}
