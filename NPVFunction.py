import collections
import numpy as np
import pandas as pd
import gurobipy as gb
from gurobipy import quicksum


def NPV_SAA(Data, h, w, option=1, product_thresholds=None, verbose=True):

    assert option in {1, 2, 3}, "Option should be 1, 2, or 3"

    if option == 2:
        assert isinstance(product_thresholds, dict), \
            "product_thresholds should be a dict when option is 2"

        product_thresholds_keys = {'notebooks', 'monitors', 'televisions'}
        assert product_thresholds_keys <= product_thresholds.keys(), \
            f"product_thresholds should have keys {product_thresholds_keys}"
        assert all (0 <= product_thresholds[key] <= 1 for key in product_thresholds_keys), \
            (f"The values in product_thresholds for {product_thresholds_keys} should be a number "
            "between 0 and 1 when option is 2")

    if option == 3:
        assert isinstance(product_thresholds, float), \
            "product_thresholds should be a number when option is 3"
        assert 0 <= product_thresholds <= 1, \
            "product_thresholds should be a number between 0 and 1 when option is 3"


    Scenarios = len(Data)
    Products = len(Data[0]['ProductSize'])
    Time = len(Data[0]['ProductPrice'].columns) - 2

    if option == 2:
        Notebook = Data[0]['ProductSize'].loc[
            Data[0]['ProductSize']['Market'] == 'Notebook'].index.values
        Monitor = Data[0]['ProductSize'].loc[
            Data[0]['ProductSize']['Market'] == 'Monitor'].index.values
        Television = Data[0]['ProductSize'].loc[
            Data[0]['ProductSize']['Market'] == 'Television'].index.values

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
    # Profit Table
    COS11 = {} #Costs per substate per time (cost for alle products equal)
    Sales11 = {} #Sales per substrate per product per time
    Profit1 = {} # Is product profitable?
    
    for t in range(Time):
        for p in range(Products):
            COS11[t] = (1/Scenarios)*sum(Data[s]['SubstrateCost'].iloc[0, t]*(w*h)
                                         for s in range(Scenarios))
            Sales11[p ,t] = (1/Scenarios)*sum(Data[s]['ProductPrice'].iloc[p, t+2] * \
                                              Data[s]['Yield'].iloc[p, t+4] * \
                                                  PoS[s][p]['num_products']
                                                  for s in range(Scenarios))
            Profit1[p, t] = Sales11[p, t] - COS11[t]
    
    # INITIALIZE MODEL
    m = gb.Model('PBAS')
    if not verbose:
        m.setParam('OutputFlag', False)
    
    # VARIABLES
    x = m.addVars(Products, Time, vtype=gb.GRB.INTEGER, lb=0,
                  name='Substrate per product over time')
    GM = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='GrossMargin')
    OM = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Operating Margin')
    Sales = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Sales')
    CostofSales = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS, name='Cost of Sales')
    COS2 = m.addVars(Scenarios, Time, vtype=gb.GRB.CONTINUOUS,
                     name='Cost of Sales without depreciation')
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

    if option == 2:
        # Per market, check if there is any positive profitability. If so, require that at least a
        # certain percentage of the production is in that market. In effect, this means that the
        # most profitable product in that market gets produced.
        for t in range(Time):
            for p in Notebook:
                if Profit1[p, t] > 0:
                    m.addConstr(quicksum(x[p, t] for p in Notebook) >=
                        product_thresholds['notebooks']*Data[0]['MaxCapacity']*12)
                    break # We only need one product to be profitable to add this constraint
            for p in Monitor:
                if Profit1[p, t] > 0:
                    m.addConstr(quicksum(x[p, t] for p in Monitor) >=
                        product_thresholds['monitors']*Data[0]['MaxCapacity']*12)
                    break # Dito
            for p in Television:
                if Profit1[p, t] > 0:
                    m.addConstr(quicksum(x[p, t] for p in Television) >=
                        product_thresholds['televisions']*Data[0]['MaxCapacity']*12)
                    break # Dito

    if option == 3:
        for p in range(Products):
            for t in range(2, Time):
                m.addConstr(x[p, t] >= product_thresholds*Data[0]['MaxCapacity']*12)

    for s in range(Scenarios):
        CCC[s] = (Data[s]['DIO']+Data[s]['DSO']-Data[s]['DPO'])/365
        DWC[s, 0] = WC[s, 0]
        
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

            NPV[s, t] = NCF[s, t]/((1+Data[s]['WACC'])**t) 

        for t in range(1, Time):
            DWC[s, t] = WC[s, t-1]-WC[s, t]

        NPVperScenario[s] = quicksum(NPV[s, t] for t in range(Time))
        
    # OBJECTIVE
    obj = (1/Scenarios)*quicksum(quicksum(NPV[s, t] for s in range(Scenarios)) for t in range(Time))
    m.setObjective(obj, gb.GRB.MAXIMIZE)

    # RUN OPTIMIZATION
    m.optimize()
    
    NPVs = [NPVperScenario[s].getValue() for s in range(Scenarios)]
    NPVmax = max(NPVs)
    NPVmin = min(NPVs)
    
    # Count negative scenarios
    NegativeScenario = 0
    for s in range(Scenarios):
        if NPVperScenario[s].getValue() < 0:
            NegativeScenario = NegativeScenario + 1

    # Production Table        
    ProductProduction = pd.DataFrame(np.zeros((Products,Time)), index=Data[0]['Yield']['Format'],
                                     columns=Data[0]['InvestmentCost'].columns)
    TotalProduction = pd.DataFrame(np.zeros((1,Time)), index=['Total Production'], 
                                   columns=Data[0]['InvestmentCost'].columns)
    
    for p in range(Products):
        for t in range(Time):
            ProductProduction.iloc[p, t] = int(x[p, t].x)
            
    for t in range(Time):
        TotalProduction.iloc[0, t] = int(quicksum(x[p, t].x for p in range(Products)).getValue())
        
    Production = pd.concat([ProductProduction, TotalProduction])

    # ELEMENTS PROFIT AND LOSS STATEMENT
    PL = collections.defaultdict(dict)
    for t in range(Time):
        PL[t]['ProductPrice'] = [((1/Scenarios)*quicksum(Data[s]['ProductPrice'].iloc[p, t+2]
                                             for s in range(Scenarios))).getValue() 
                                                 for p in range(Products)]# Price per product
        PL[t]['NumberofProducts'] = [((1/Scenarios)*quicksum(PoS[s][p]['num_products']
                                            for s in range(Scenarios))).getValue()
                                                for p in range(Products)]
        PL[t]['SubstrateCost'] = ((1/Scenarios)*sum(Data[s]['SubstrateCost'].iloc[0, t]*(w*h) 
                                            for s in range(Scenarios)))
        PL[t]['SALES'] = ((1/Scenarios)*quicksum(Sales[s, t].X
                                                 for s in range(Scenarios))).getValue()
        PL[t]['COS'] = ((1/Scenarios)*quicksum(COS2[s, t].X
                                               for s in range(Scenarios))).getValue()
        PL[t]['CostofSales'] = ((1/Scenarios)*quicksum(CostofSales[s, t].X
                                               for s in range(Scenarios))).getValue()
        PL[t]['GM'] = ((1/Scenarios)*quicksum(GM[s, t].getValue()
                                              for s in range(Scenarios))).getValue()
        PL[t]['RD'] = ((1/Scenarios)*quicksum(Data[s]['R&D']
                                              for s in range(Scenarios))).getValue()
        PL[t]['SG&A'] = ((1/Scenarios)*quicksum(Data[s]['SG&A']
                                                for s in range(Scenarios))).getValue()
        PL[t]['OM'] = ((1/Scenarios)*quicksum(OM[s, t].getValue()
                                              for s in range(Scenarios))).getValue()
        PL[t]['TAX'] = ((1/Scenarios)*quicksum(Data[s]['TaxRate']
                                               for s in range(Scenarios))).getValue()
        PL[t]['NI'] = ((1/Scenarios)*quicksum(NI[s, t].getValue()
                                              for s in range(Scenarios))).getValue()
        PL[t]['DWC'] = (1/Scenarios)*(quicksum(DWC[s, t] for s in range(Scenarios))).getValue()
        PL[t]['WC'] = ((1/Scenarios)*quicksum(WC[s, t].getValue()
                                              for s in range(Scenarios))).getValue()
        PL[t]['Depreciation'] = ((1/Scenarios)*quicksum(Data[s]['Depreciation'].iloc[0, t]
                                                        for s in range(Scenarios))).getValue()
        PL[t]['CAPEX'] = ((1/Scenarios)*quicksum(Data[s]['InvestmentCost'].iloc[0, t]
                                                for s in range(Scenarios))).getValue()
        PL[t]['NCF'] = ((1/Scenarios)*quicksum(NCF[s, t].getValue()
                                              for s in range(Scenarios))).getValue()
        PL[t]['CCC'] = (1/Scenarios)*(quicksum(CCC[s] for s in range(Scenarios))).getValue()
        PL[t]['NPV'] = ((1/Scenarios)*quicksum(NPV[s, t].getValue()
                                              for s in range(Scenarios))).getValue()
        
    return {'Average NPV': obj.getValue(),
            'NPVmax': NPVmax,
            'NPVmin': NPVmin,
            'NPVs': NPVs,
            'Width': w,
            'Height': h,
            '#NegativeScenarios': NegativeScenario,
            'PL': PL,
            'Production':Production}
