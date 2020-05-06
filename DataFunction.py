import numpy as np
import pandas as pd
import statistics as st
import math


def generateData(path, probability = {'all': [0.25, 0.5, 0.25]}, bandwidths_tv = [-2, 0, 1],
                 bandwidths_prices = [0.8, 1, 1.2], bandwidths_substrate_prices = [0.9, 1, 1.1],
                 bandwidths_investment = [0.9, 1, 1.1], bandwidths_yield = [-0.15, 0, 0.02],
                 bandwidths_rd = [0.04, 0.05, 0.11], bandwidths_sga = [0.03, 0.04, 0.05],
                 bandwidths_tax = [0.20, 0.25, 0.30], bandwidths_dpo = [35, 45, 55],
                 bandwidths_dso = [35, 45, 55], bandwidths_dio = [20, 30, 40], max_width = 1.85,
                 max_height = 1.55):
    """
    Imports the data and constructs a random instance

    Parameters
    ----------
    path : str
        Path to the data
    probability : dict
        Dictionary of probabilities for each of the bandwidths. If not specified for all bandwidths,
        this should include a key called 'all' that will be used for all bandwidths that are not
        assigned a custom probability.
    bandwidths_tv : list
        List of bandwidths for the television diagonal size. Length must match that of `probability`
    bandwidths_prices : list
        List of bandwidths for the selling prices. Length must match that of `probability`
    bandwidths_substrate_prices : list
        List of bandwidths for the substrate purchase costs. Length must match that of `probability`
    bandwidths_investment : list
        List of bandwidths for the investment costs. Length must match that of `probability`
    bandwidths_yield : list
        List of bandwidths for the yields. Note, these are in percentage points added/subtracted
        rather than multiplicative factors. Length must match that of `probability`
    bandwidths_rd : list
        List of bandwidths for the R&D costs. Length must match that of `probability`
    bandwidths_sga : list
        List of bandwidths for the SG&A costs. Length must match that of `probability`
    bandwidths_tax : list
        List of bandwidths for the tax rate. Length must match that of `probability`
    bandwidths_dpo : list
        List of bandwidths for the DPO. Length must match that of `probability`
    bandwidths_dso : list
        List of bandwidths for the DSO. Length must match that of `probability`
    bandwidths_dio : list
        List of bandwidths for the DIO. Length must match that of `probability`
    max_width : float
        Maximum width of the substrate
    max_height: float
        Maximum height of the substrate

    Returns
    -------
    dict
        Dictionary of all needed values and randomized data

    Yields
    -------
    KeyError
        When the year for depreciation is not yet initialized, create it
    """ 

    Data = pd.ExcelFile(path)
    ProductSize = pd.read_excel(Data, "ProductSize")
    ProductFormat = pd.read_excel(Data, "ProductFormat")

    CostSubstrate = pd.read_excel(Data, "CostSubstrate")
    CostInvestment = pd.read_excel(Data, "CostInvestment")
    Yield = pd.read_excel(Data, "Yield")
    Parameters = pd.read_excel(Data, "CostParameters").set_index('Cost Type')

    num_products = len(ProductSize)
    ProductMeta = ProductSize[['Size (inches)', 'Format', 'Market']].copy()

    # ProductInches including the uncertainty for TV screen size
    ProductInches = ProductMeta.copy()
    
    try:
        # (ProductInches['Market'] == 'Television') is a boolean indicator for whether the product
        # is a television. If multiplied, True is treated as 1 and False is treated as 0. As such,
        # we only add the outcomes of the random selection to the televisions
        ProductInches['New Diagonal (inches)'] = ProductInches['Size (inches)'] + \
            np.random.choice(bandwidths_tv, num_products, p=probability['tv']) * \
                (ProductInches['Market'] == 'Television')
    except KeyError:
        ProductInches['New Diagonal (inches)'] = ProductInches['Size (inches)'] + \
            np.random.choice(bandwidths_tv, num_products, p=probability['all']) * \
                (ProductInches['Market'] == 'Television')
    
    ProductInches['Angle'] = [math.atan(ProductFormat.loc[0, formt] / ProductFormat.loc[1, formt])
                              for formt in ProductInches['Format']]
    ProductInches['Height (m)'] = np.cos(ProductInches['Angle']) * \
        ProductInches['New Diagonal (inches)'] * 0.0254 + 2*ProductSize['Border_H (in mm)']/1000 + \
        2*ProductSize['Exclusion (in mm)']/1000
    ProductInches['Width (m)'] = np.sin(ProductInches['Angle']) * \
        ProductInches['New Diagonal (inches)'] * 0.0254 + 2*ProductSize['Border_V (in mm)']/1000 + \
        2*ProductSize['Exclusion (in mm)']/1000

    # Prices per product over time including the uncertainty
    Price = pd.merge(ProductMeta.copy(), pd.read_excel(Data, "Price").drop(
        columns='Unit'), on=['Size (inches)', 'Format', 'Market'])
    
    try:
        Price = pd.concat([Price.iloc[:, :2], Price.iloc[:, 3:] * np.random.choice(
            bandwidths_prices, Price.iloc[:, 3:].shape, p=probability['prices'])], axis=1)
    except KeyError:
        Price = pd.concat([Price.iloc[:, :2], Price.iloc[:, 3:] * np.random.choice(
            bandwidths_prices, Price.iloc[:, 3:].shape, p=probability['all'])], axis=1)

    # Cost substrate per m^2 over time including the uncertainty
    try:
        CostSubstrate = CostSubstrate.iloc[:, 3:] * np.random.choice(
            bandwidths_substrate_prices, len(CostSubstrate.columns[3:]),
            p=probability['substrate_prices'])
    except KeyError:
        CostSubstrate = CostSubstrate.iloc[:, 3:] * np.random.choice(
            bandwidths_substrate_prices, len(CostSubstrate.columns[3:]), p=probability['all'])
        
    CostSubstrate = CostSubstrate.fillna(0)
    
    # Investment costs over time including the uncertainty
    try:
        CostInvestment = 1e6 * CostInvestment.iloc[:, 3:] * np.random.choice(
            bandwidths_investment, len(CostInvestment.columns[3:]), p=probability['investment'])
    except KeyError:
        CostInvestment = 1e6 * CostInvestment.iloc[:, 3:] * np.random.choice(
            bandwidths_investment, len(CostInvestment.columns[3:]), p=probability['all'])
        
    CostInvestment = CostInvestment.fillna(0)

    # Yield per market over time including the uncertainty
    Yield = Yield.drop(columns=["Blaco", "Blanco"]).copy()
    
    try:
        Yield = pd.concat([Yield['Yieldpermarket'], Yield.iloc[:, 1:] + np.random.choice(
            bandwidths_yield, (Yield.shape[0], Yield.shape[1]-1), p=probability['yield'])], axis=1)
    except KeyError:
        Yield = pd.concat([Yield['Yieldpermarket'], Yield.iloc[:, 1:] + np.random.choice(
            bandwidths_yield, (Yield.shape[0], Yield.shape[1]-1), p=probability['all'])], axis=1)
        
    Yield = pd.merge(ProductMeta, Yield, left_on='Market', right_on='Yieldpermarket', how='left')
    Yield = Yield.fillna(0)
    
    # Depreciation over time
    Depreciation = {}
    depreciation_period = int(Parameters.loc['Depreciation years', 'Cost'])

    for i in range(CostInvestment.shape[1]):
        investment = CostInvestment.iloc[:, i] / depreciation_period
        for j in range(depreciation_period):
            year = investment.name + j
            try:
                Depreciation[year] = Depreciation[year] + investment[0]
            except KeyError:
                Depreciation[year] = investment[0]

    Depreciation = pd.DataFrame(Depreciation, index=[0])

    # Create final random choices
    try:
        rd = np.random.choice(bandwidths_rd, 1, p=probability['rd']).item()
    except KeyError:
        rd = np.random.choice(bandwidths_rd, 1, p=probability['all']).item()

    try:
        sga = np.random.choice(bandwidths_sga, 1, p=probability['sga']).item()
    except KeyError:
        sga = np.random.choice(bandwidths_sga, 1, p=probability['all']).item()
        
    try:
        tax = np.random.choice(bandwidths_tax, 1, p=probability['tax']).item()
    except KeyError:
        tax = np.random.choice(bandwidths_tax, 1, p=probability['all']).item()
        
    try:
        dpo = np.random.choice(bandwidths_dpo, 1, p=probability['dpo']).item()
    except KeyError:
        dpo = np.random.choice(bandwidths_dpo, 1, p=probability['all']).item()

    try:
        dso = np.random.choice(bandwidths_dso, 1, p=probability['dso']).item()
    except KeyError:
        dso = np.random.choice(bandwidths_dso, 1, p=probability['all']).item()
        
    try:
        dio = np.random.choice(bandwidths_dio, 1, p=probability['dio']).item()
    except KeyError:
        dio = np.random.choice(bandwidths_dio, 1, p=probability['all']).item()

    return {"ProductSize": ProductInches,
            "ProductFormat": ProductFormat,
            "ProductPrice": Price,
            "SubstrateCost": CostSubstrate,
            "InvestmentCost": CostInvestment,
            "Yield": Yield,
            "Depreciation": Depreciation,
            "MaxCapacity": Parameters.loc['Max capacity', 'Cost'],
            "R&D": rd,
            "SG&A": sga,
            "WACC": Parameters.loc['WACC', 'Cost'],
            "Depreciation_years": depreciation_period,
            "Max_width": max_width,
            "Max_height": max_height,
            "TaxRate": tax,
            "DPO": dpo,
            "DSO": dso,
            "DIO": dio}
