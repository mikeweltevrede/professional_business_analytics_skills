import math
import numpy as np
import pandas as pd


def generateData(path, probability={'all': [0.25, 0.5, 0.25]}, bandwidths_tv=[-2, 0, 1],
                 bandwidths_prices=[0.8, 1, 1.2], bandwidths_substrate_prices=[0.9, 1, 1.1],
                 bandwidths_investment=[0.9, 1, 1.1], bandwidths_yield=[-0.15, 0, 0.02],
                 bandwidths_rd=[0.04, 0.05, 0.11], bandwidths_sga=[0.03, 0.04, 0.05],
                 bandwidths_tax=[0.20, 0.25, 0.30], bandwidths_dpo=[35, 45, 55],
                 bandwidths_dso=[35, 45, 55], bandwidths_dio=[20, 30, 40], max_width=1.85,
                 max_height=1.55):
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

    results = {}

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
        tv_selection = np.random.choice(bandwidths_tv, num_products, p=probability['tv'])
    except KeyError:
        tv_selection = np.random.choice(bandwidths_tv, num_products, p=probability['all'])

    # (ProductInches['Market'] == 'Television') is a boolean indicator for whether the product
    # is a television. If multiplied, True is treated as 1 and False is treated as 0. As such,
    # we only add the outcomes of the random selection to the televisions
    ProductInches['New Diagonal (inches)'] = ProductInches['Size (inches)'] + \
        tv_selection * (ProductInches['Market'] == 'Television')

    ProductInches['Angle'] = [math.atan(ProductFormat.loc[0, formt] / ProductFormat.loc[1, formt])
                              for formt in ProductInches['Format']]
    ProductInches['Height (m)'] = np.cos(ProductInches['Angle']) * \
        ProductInches['New Diagonal (inches)'] * 0.0254 + 2*ProductSize['Border_H (in mm)']/1000 + \
        2*ProductSize['Exclusion (in mm)']/1000
    ProductInches['Width (m)'] = np.sin(ProductInches['Angle']) * \
        ProductInches['New Diagonal (inches)'] * 0.0254 + 2*ProductSize['Border_V (in mm)']/1000 + \
        2*ProductSize['Exclusion (in mm)']/1000

    results["tv_selection"] = tv_selection
    results["ProductSize"] = ProductInches

    # Compute area change to update prices
    original_height = np.cos(ProductInches['Angle']) * \
        ProductInches['Size (inches)'] * 0.0254 + 2*ProductSize['Border_H (in mm)']/1000 + \
        2*ProductSize['Exclusion (in mm)']/1000
    original_width = np.sin(ProductInches['Angle']) * \
        ProductInches['Size (inches)'] * 0.0254 + 2*ProductSize['Border_V (in mm)']/1000 + \
        2*ProductSize['Exclusion (in mm)']/1000

    original_area = original_height * original_width
    new_area = ProductInches['Height (m)'] * ProductInches['Width (m)']
    area_change = new_area/original_area

    # Prices per product over time including the uncertainty
    Price = pd.merge(ProductMeta.copy(), pd.read_excel(Data, "Price").drop(
        columns='Unit'), on=['Size (inches)', 'Format', 'Market'])

    try:
        prices_selection = np.random.choice(bandwidths_prices, Price.iloc[:, 3:].shape,
                                            p=probability['prices'])
    except KeyError:
        prices_selection = np.random.choice(bandwidths_prices, Price.iloc[:, 3:].shape,
                                            p=probability['all'])

    Price = pd.concat([Price.iloc[:, :2],
                       (Price.iloc[:, 3:] * prices_selection).multiply(area_change, axis="index")],
                      axis=1)

    results["prices_selection"] = prices_selection
    results["ProductPrice"] = Price

    # Cost substrate per m^2 over time including the uncertainty
    try:
        substrate_prices_selection = np.random.choice(bandwidths_substrate_prices,
                                                      len(CostSubstrate.columns[3:]),
                                                      p=probability['substrate_prices'])
    except KeyError:
        substrate_prices_selection = np.random.choice(bandwidths_substrate_prices,
                                                      len(CostSubstrate.columns[3:]),
                                                      p=probability['all'])

    CostSubstrate = CostSubstrate.iloc[:, 3:] * substrate_prices_selection
    CostSubstrate = CostSubstrate.fillna(0)

    results["substrate_prices_selection"] = substrate_prices_selection
    results["SubstrateCost"] = CostSubstrate

    # Investment costs over time including the uncertainty
    try:
        investment_selection = np.random.choice(bandwidths_investment,
                                                len(CostInvestment.columns[3:]),
                                                p=probability['investment'])
    except KeyError:
        investment_selection = np.random.choice(bandwidths_investment,
                                                len(CostInvestment.columns[3:]),
                                                p=probability['all'])

    CostInvestment = 1e6 * CostInvestment.iloc[:, 3:] * investment_selection
    CostInvestment = CostInvestment.fillna(0)

    results["investment_selection"] = investment_selection
    results["InvestmentCost"] = CostInvestment

    # Yield per market over time including the uncertainty
    Yield = Yield.drop(columns=["Blaco", "Blanco"]).copy()

    try:
        yield_selection = np.random.choice(bandwidths_yield, (Yield.shape[0], Yield.shape[1]-1),
                                           p=probability['yield'])
    except KeyError:
        yield_selection = np.random.choice(bandwidths_yield, (Yield.shape[0], Yield.shape[1]-1),
                                           p=probability['all'])

    Yield = pd.concat([Yield['Yieldpermarket'], Yield.iloc[:, 1:] + yield_selection], axis=1)
    Yield = pd.merge(ProductMeta, Yield, left_on='Market', right_on='Yieldpermarket', how='left')
    Yield = Yield.fillna(0)

    results["yield_selection"] = yield_selection
    results["Yield"] = Yield

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

    results["Depreciation"] = Depreciation

    # Create final random choices
    try:
        results["R&D"] = np.random.choice(bandwidths_rd, 1, p=probability['R&D']).item()
    except KeyError:
        results["R&D"] = np.random.choice(bandwidths_rd, 1, p=probability['all']).item()

    try:
        results["SG&A"] = np.random.choice(bandwidths_sga, 1, p=probability['SG&A']).item()
    except KeyError:
        results["SG&A"] = np.random.choice(bandwidths_sga, 1, p=probability['all']).item()

    try:
        results["TaxRate"] = np.random.choice(bandwidths_tax, 1, p=probability['TaxRate']).item()
    except KeyError:
        results["TaxRate"] = np.random.choice(bandwidths_tax, 1, p=probability['all']).item()

    try:
        results["DPO"] = np.random.choice(bandwidths_dpo, 1, p=probability['DPO']).item()
    except KeyError:
        results["DPO"] = np.random.choice(bandwidths_dpo, 1, p=probability['all']).item()

    try:
        results["DSO"] = np.random.choice(bandwidths_dso, 1, p=probability['DSO']).item()
    except KeyError:
        results["DSO"] = np.random.choice(bandwidths_dso, 1, p=probability['all']).item()

    try:
        results["DIO"] = np.random.choice(bandwidths_dio, 1, p=probability['DIO']).item()
    except KeyError:
        results["DIO"] = np.random.choice(bandwidths_dio, 1, p=probability['all']).item()

    # Final necessary data
    results["MaxCapacity"] = Parameters.loc['Max capacity', 'Cost']
    results["WACC"] = Parameters.loc['WACC', 'Cost']
    results["Max_width"] = max_width
    results["Max_height"] = max_height

    return results
