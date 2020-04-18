# -*- coding: utf-8 -*-
"""
GROUP 6 PBAS
Data import file, incl randomness.
"""
def generateData(path):

    import numpy as np
    import pandas as pd
    import statistics as st
    import math 

    Data = pd.ExcelFile(path)
    
    ProductSize = pd.read_excel(Data,"ProductSize")
    ProductFormat = pd.read_excel(Data,"ProductFormat")
    Price = pd.read_excel(Data,"Price")

    CostSubstrate = pd.read_excel(Data,"CostSubstrate")
    CostInvestment = pd.read_excel(Data,"CostInvestment")
    Yield = pd.read_excel(Data,"Yield")
    Parameters = pd.read_excel(Data,"CostParameters")
    print(Parameters)
    ## ProductInches including the uncertainty for TV screensize
    probability = [0.25,0.5,0.25] # same for all uncertain bandwiths
    outcome = [-2,0,1]
    M = np.zeros((len(ProductSize),5))
    ProductInches = pd.DataFrame(M,index = ProductSize.Format)
    
    for i in range(6):
        ProductInches.values[i,0] = ProductSize.values[i,0]
    for j in range(6,12):
        ProductInches.values[j,0] = ProductSize.values[j,0] + np.random.choice(outcome,1,probability)
    
    for i in range(9,12):
        ProductInches.values[i,1] = math.atan(ProductFormat.values[0,1]/ProductFormat.values[1,1])
    for i in range(6,9):
        ProductInches.values[i,1] = math.atan(ProductFormat.values[0,2]/ProductFormat.values[1,2])
    ProductInches.values[5,1] = math.atan(ProductFormat.values[0,3]/ProductFormat.values[1,3])
    ProductInches.values[4,1] = math.atan(ProductFormat.values[0,6]/ProductFormat.values[1,6])
    ProductInches.values[3,1] = math.atan(ProductFormat.values[0,9]/ProductFormat.values[1,9])
    ProductInches.values[2,1] = math.atan(ProductFormat.values[0,5]/ProductFormat.values[1,5])
    ProductInches.values[1,1] = math.atan(ProductFormat.values[0,8]/ProductFormat.values[1,8])
    ProductInches.values[0,1] = math.atan(ProductFormat.values[0,7]/ProductFormat.values[1,7])
    
    for i in range(12):
        ProductInches.values[i,2]= (math.cos(ProductInches.values[i,1])*ProductInches.values[i,0]*0.0254)+(ProductSize.values[i,3]/1000)
        ProductInches.values[i,3]= (math.sin(ProductInches.values[i,1])*ProductInches.values[i,0]*0.0254)+(ProductSize.values[i,4]/1000)
        ProductInches.values[i,4] = ProductSize.values[i,5]/1000
        
    ProductInches = ProductInches.rename(columns = {4:'Exclusion (m)',0:'Diagonal (inches)',1:'Angle',2:'Height (m)',3:'Width (m)'})
    ## Prices per product over time including the uncertainty
    outcome2 = [0.8,1,1.2] ## Plus or minus 20%
    Price2 = pd.DataFrame(np.zeros((12,15)), index = Price.Format, columns = Price.columns[4:19])
    for i in range(len(Price.columns[4:19])):
        for j in range(len(Price.Format)):
            Price2.values[j,i] = np.random.choice(outcome2,1,probability) * Price.values[j,i+4]
    
    ## Cost substrate per m^2 over time including the uncertainty
    
    outcome3 = [0.9,1,1.1] ##Plus or minus 10%
    CostSubstrate2 = pd.DataFrame(np.zeros((1,len(CostSubstrate.columns[3:18]))), columns = CostSubstrate.columns[3:18])
    for i in range(2,len(CostSubstrate.columns[3:18])):
        CostSubstrate2.values[0,i] = np.random.choice(outcome3,1,probability) * CostSubstrate.values[0,i+3]
    
    ## Investment Cost over time including the uncertainty
    ## Plus or minus 10% so use same outcome as for the cost substrate
    CostInvestment2 = pd.DataFrame(np.zeros((1,len(CostInvestment.columns[3:18]))), columns = CostInvestment.columns[3:18])
    for i in range(len(CostInvestment.columns[3:18])):
        CostInvestment2.values[0,i] = np.random.choice(outcome3,1,probability) * CostInvestment.values[0,i+3]
    
    ## Yield per market over time including the uncertainty
    outcome4 = [0.85,1,1.02] ## 15% down or 2% up   
    Yield2 = pd.DataFrame(np.zeros((len(ProductInches),len(Yield.columns[3:18]))), index = ProductInches.index, columns = Yield.columns[3:18])

    for j in range(2,len(Yield.columns[3:18])):
        Yield2.values[0:2,j] = np.random.choice(outcome4,1,probability) * Yield.values[0,j+3]

    for j in range(2,len(Yield.columns[3:18])):
        Yield2.values[2:5,j] = np.random.choice(outcome4,1,probability) * Yield.values[1,j+3]

    for j in range(2,len(Yield.columns[3:18])):
        Yield2.values[5:len(ProductInches),j] = np.random.choice(outcome4,1,probability) * Yield.values[2,j+3]
           
    MaxCapacity = Parameters.values[0,3]
    RD = np.random.choice([0.04,0.05,0.11],1,probability) ## R&D
    SGA = np.random.choice([0.03,0.04,0.05],1,probability) ##SG&A
    WACC = Parameters.values[3,3]
    Depreciation_years = Parameters.values[4,3]
    maximum_width = 1.55
    maximum_height = 1.85
    TaxRate = np.random.choice([0.20,0.25,0.30],1,probability)
    DPO = np.random.choice([35,45,55],1,probability)
    DSO = np.random.choice([35,45,55],1,probability)
    DIO = np.random.choice([20,30,40],1,probability)
    return {"ProductSize": ProductInches,
            "ProductFormat": ProductFormat,
            "ProductPrice": Price2,
            "SubstrateCost": CostSubstrate2,
            "InvestmentCost": CostInvestment2,
            "Yield": Yield2,
            "MaxCapacity": MaxCapacity,
            "R&D":RD.item(),
            "SG&A":SGA.item(),
            "WACC":WACC,
            "Depreciation_years":Depreciation_years,
            "Max_width": maximum_width,
            "Max_height": maximum_height,
            "TaxRate": TaxRate.item(),
            "DPO":DPO.item(),
            "DSO":DSO.item(),
            "DIO":DIO.item()}
    
