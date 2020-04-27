"""
GROUP 6 PBAS
Data import file, incl randomness.
"""


def generateData(path):
    """
    Imports the data and constructs a random instance

    Parameters
    ----------
    path : str
        Path to the data

    Returns
    -------
    dict
        Dictionary of all needed values and randomized data

    Yields
    -------
    KeyError
        When the year for depreciation is not yet initialized, create it
    """

    import numpy as np
    import pandas as pd
    import statistics as st
    import math

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
    probability = [0.25, 0.5, 0.25]
    bandwidths_tv = [-2, 0, 1]

    ProductInches = ProductMeta.copy()
    ProductInches['New Diagonal (inches)'] = ProductInches['Size (inches)'] + \
        np.random.choice(bandwidths_tv, num_products, probability)
    ProductInches['Angle'] = [math.atan(ProductFormat.loc[0, formt] / ProductFormat.loc[1, formt])
                              for formt in ProductInches['Format']]
    ProductInches['Height (m)'] = np.cos(ProductInches['Angle']) * ProductInches['New Diagonal (inches)'] * \
        0.0254 + ProductSize['Border_H (in mm)']/1000 + ProductSize['Exclusion (in mm)']/1000
    ProductInches['Width (m)'] = np.sin(ProductInches['Angle']) * ProductInches['New Diagonal (inches)'] * \
        0.0254 + ProductSize['Border_V (in mm)']/1000 + ProductSize['Exclusion (in mm)']/1000

    # Prices per product over time including the uncertainty
    bandwidths_prices = [0.8, 1, 1.2]
    Price = pd.merge(ProductMeta.copy(), pd.read_excel(Data, "Price").drop(
        columns='Unit'), on=['Size (inches)', 'Format', 'Market'])
    Price = pd.concat([Price.iloc[:, :2], Price.iloc[:, 3:] * np.random.choice(
        bandwidths_prices, Price.iloc[:, 3:].shape, probability)], axis=1)

    # Cost substrate per m^2 over time including the uncertainty
    bandwidths_substrate_prices = [0.9, 1, 1.1]
    CostSubstrate = CostSubstrate.iloc[:, 3:] * np.random.choice(
        bandwidths_substrate_prices, len(CostSubstrate.columns[3:]), probability)

    # Investment costs over time including the uncertainty
    bandwidths_investment = [0.9, 1, 1.1]
    CostInvestment = 10e6 * CostInvestment.iloc[:, 3:] * np.random.choice(
        bandwidths_investment, len(CostInvestment.columns[3:]), probability)
    CostInvestment = CostInvestment.dropna(axis=1)

    # Yield per market over time including the uncertainty
    bandwidths_yield = [0.85, 1, 1.02]  # 15% down or 2% up
    Yield = Yield.drop(columns=["Blaco", "Blanco"]).copy()
    Yield = pd.concat([Yield['Yieldpermarket'], Yield.iloc[:, 1:] * np.random.choice(
        bandwidths_yield, (Yield.shape[0], Yield.shape[1]-1), probability)], axis=1)
    Yield = pd.merge(ProductMeta, Yield, left_on='Market', right_on='Yieldpermarket', how='left')

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

    # Construct results
    return {"ProductSize": ProductInches,
            "ProductFormat": ProductFormat,
            "ProductPrice": Price,
            "SubstrateCost": CostSubstrate,
            "InvestmentCost": CostInvestment,
            "Yield": Yield,
            "Depreciation": Depreciation,
            "MaxCapacity": Parameters.loc['Max capacity', 'Cost'],
            "R&D": np.random.choice([0.04, 0.05, 0.11], 1, probability).item(),
            "SG&A": np.random.choice([0.03, 0.04, 0.05], 1, probability).item(),
            "WACC": Parameters.loc['WACC', 'Cost'],
            "Depreciation_years": depreciation_period,
            "Max_width": 1.55,
            "Max_height": 1.85,
            "TaxRate": np.random.choice([0.20, 0.25, 0.30], 1, probability).item(),
            "DPO": np.random.choice([35, 45, 55], 1, probability).item(),
            "DSO": np.random.choice([35, 45, 55], 1, probability).item(),
            "DIO": np.random.choice([20, 30, 40], 1, probability).item()}
