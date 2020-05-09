import random
import pickle
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from DataFunction import generateData
from NPVFunction import NPV_SAA


def main(Data, output_path1=None, output_path2=None, output_path3=None, output_path4=None,
         max_height=None, max_width=None, num_height=12, num_width=6, stepsize_width=0.05,
         stepsize_height=0.05, option=1, product_thresholds=None, verbose=False):

    if max_width is None:
        max_width = Data[0]['Max_width']
    widths = [max_width-stepsize_width*i for i in range(num_width)]

    if max_height is None:
        max_height = Data[0]['Max_height']
    heights = [max_height-stepsize_height*i for i in range(num_height)]

    NPV = pd.DataFrame(np.zeros((num_height, num_width)), index=heights, columns=widths)

    if output_path2 is not None:
        NPVmax = NPV.copy()
    if output_path3 is not None:
        NPVmin = NPV.copy()
    if output_path4 is not None:
        NPVpos = NPV.copy()

    for h in tqdm(range(num_height)):
        for w in tqdm(range(num_width)):
            NPV_ = NPV_SAA(Data, h=heights[h], w=widths[w], option=option,
                           product_thresholds=product_thresholds, verbose=verbose)
            NPV.values[h, w] = NPV_['Average NPV']
            if output_path2 is not None:
                NPVmax.values[h, w] = NPV_['NPVmax']
            if output_path3 is not None:
                NPVmin.values[h, w] = NPV_['NPVmin']
            if output_path4 is not None:
                NPVpos.values[h, w] = 1-(NPV_['#NegativeScenarios']/len(Data))

    if output_path1 is not None:
        NPV.to_csv(output_path1)
    if output_path2 is not None:
        NPVmax.to_csv(output_path2)
    if output_path3 is not None:
        NPVmin.to_csv(output_path3)
    if output_path4 is not None:
        NPVpos.to_csv(output_path4)


if __name__ == "__main__":  # This means that running this script will run the code below

    # Run baseline case
    Data_baseline = {0: generateData("data/DataPBAS.xlsx", probability={'all': [0, 1, 0]})}

    # Create data
    seed = 42
    data1000_path = "data/data1000.pkl"
    data500_path = f"data/data500_seed{seed}.pkl"
    if os.path.isfile(data1000_path):
        # Then this file already exists and can be imported
        with open(data1000_path, "rb") as data:
            Data1000 = pickle.load(data)

        if os.path.isfile(data500_path):
            # Then this file already exists and can be imported - we assume they are concurrent
            with open(data500_path, "rb") as data:
                Data500 = pickle.load(data)
        else:
            # This file needs to be created
            random.seed(seed)
            keys = random.sample(list(Data1000.keys()), num_scenarios//2)
            Data500 = {i: Data1000[keys[i]] for i in range(len(keys))}

            with open(data500_path, "wb") as data:
                pickle.dump(Data500, data)

    else:
        num_scenarios = 1000
        data_path = "data/DataPBAS.xlsx"
        Data1000 = {i: generateData(data_path) for i in tqdm(range(num_scenarios))}

        with open(data1000_path, "wb") as data:
            pickle.dump(Data1000, data)

        # Then also the subsample needs to be recreated
        random.seed(seed)
        keys = random.sample(list(Data1000.keys()), num_scenarios//2)
        Data500 = {i: Data1000[keys[i]] for i in range(len(keys))}

        with open(data500_path, "wb") as data:
            pickle.dump(Data500, data)

    #### Run the models ####
    # For option 1 and 3, we only run the full grid on the baseline case and on a dataset comprising
    # of 500 scenarios. For option 2, we zoom in on the most promising areas using a larger dataset
    # of 1000 scenarios.

    # # Option 1: Maximise profit
    # print('RUN OPTION 1')

    # # Run full grid (1.60-1.85 (0.05) x 1.00-1.55 (0.05))
    # main(Data_baseline, option=1, output_path1="output/NPV_baseline_option1_fullgrid.csv")
    # main(Data500, option=1,
    #      output_path1="output/NPV_option1_fullgrid.csv",
    #      output_path2="output/NPVmax_option1_fullgrid.csv",
    #      output_path3="output/NPVmin_option1_fullgrid.csv",
    #      output_path4="output/NPVpos_option1_fullgrid.csv")

    # Option 2: Each market should constitute at least a certain amount of the production
    print('RUN OPTION 2')

    # Construct the thresholds based on  product size, i.e. smaller products should have a
    # lower percentage because more of these fit on a substrate.
    min_percentage = 0.01
    means = Data_baseline[0]['ProductSize'].groupby('Market')['Size (inches)'].agg(np.mean)
    means = means/sum(means)

    # Scale such that minimum is min_percentage%
    means_scaled = means/(min(means)/min_percentage)

    # # Run baseline case
    # main(Data_baseline, option=2,
    #      output_path1=f"output/NPV_baseline_option2_{min_percentage}_fullgrid.csv",
    #      product_thresholds={'notebooks': means_scaled['Notebook'],
    #                          'monitors': means_scaled['Monitor'],
    #                          'televisions': means_scaled['Television']})

    # # Run full grid (1.60-1.85 (0.05) x 1.00-1.55 (0.05))
    # main(Data500, option=2,
    #      output_path1=f"output/NPV_option2_{min_percentage}_fullgrid.csv",
    #      output_path2=f"output/NPVmax_option2_{min_percentage}_fullgrid.csv",
    #      output_path3=f"output/NPVmin_option2_{min_percentage}_fullgrid.csv",
    #      output_path4=f"output/NPVpos_option2_{min_percentage}_fullgrid.csv",
    #      product_thresholds={'notebooks': means_scaled['Notebook'],
    #                          'monitors': means_scaled['Monitor'],
    #                          'televisions': means_scaled['Television']})

    # Run zoomed-in on most profitable for more scenarios
    main(Data1000, option=2,
         output_path1=f"output/NPV_option2_{min_percentage}_mostprofit.csv",
         output_path2=f"output/NPVmax_option2_{min_percentage}_mostprofit.csv",
         output_path3=f"output/NPVmin_option2_{min_percentage}_mostprofit.csv",
         output_path4=f"output/NPVpos_option2_{min_percentage}_mostprofit.csv",
         max_height=1.55, max_width=1.85, stepsize_height=0.01, stepsize_width=0.01, num_height=5,
         num_width=5, product_thresholds={'notebooks': means_scaled['Notebook'],
                                          'monitors': means_scaled['Monitor'],
                                          'televisions': means_scaled['Television']})

    # Run zoomed-in on 2nd most profitable for more scenarios
    main(Data1000, option=2,
         output_path1=f"output/NPV_option2_{min_percentage}_2ndmostprofit.csv",
         output_path2=f"output/NPVmax_option2_{min_percentage}_2ndmostprofit.csv",
         output_path3=f"output/NPVmin_option2_{min_percentage}_2ndmostprofit.csv",
         output_path4=f"output/NPVpos_option2_{min_percentage}_2ndmostprofit.csv",
         max_height=1.15, max_width=1.85, stepsize_height=0.01, stepsize_width=0.01, num_height=11,
         num_width=5, product_thresholds={'notebooks': means_scaled['Notebook'],
                                          'monitors': means_scaled['Monitor'],
                                          'televisions': means_scaled['Television']})

    # Run zoomed-in on least costly () for more scenarios
    main(Data1000, option=2,
         output_path1=f"output/NPV_option2_{min_percentage}_leastcost.csv",
         output_path2=f"output/NPVmax_option2_{min_percentage}_leastcost.csv",
         output_path3=f"output/NPVmin_option2_{min_percentage}_leastcost.csv",
         output_path4=f"output/NPVpos_option2_{min_percentage}_leastcost.csv",
         max_height=1.1, max_width=1.8, stepsize_height=0.01, stepsize_width=0.01, num_height=7,
         num_width=7, product_thresholds={'notebooks': means_scaled['Notebook'],
                                          'monitors': means_scaled['Monitor'],
                                          'televisions': means_scaled['Television']})

    # # Option 3: Each product should constitute at least a certain amount of the production
    # print('RUN OPTION 3')
    # threshold = 0.005

    # # Run baseline case
    # main(Data_baseline, option=3,
    #      output_path1=f"output/NPV_baseline_option3_{threshold}_fullgrid.csv",
    #      product_thresholds=threshold)

    # # Run full grid (1.60-1.85 (0.05) x 1.00-1.55 (0.05))
    # main(Data500, option=3,
    #      output_path1=f"output/NPV_option3_{threshold}_fullgrid.csv",
    #      output_path2=f"output/NPVmax_option3_{threshold}_fullgrid.csv",
    #      output_path3=f"output/NPVmin_option3_{threshold}_fullgrid.csv",
    #      output_path4=f"output/NPVpos_option3_{threshold}_fullgrid.csv",
    #      product_thresholds=threshold)
