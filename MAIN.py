import random
import numpy as np
import pandas as pd
from tqdm import tqdm
from DataFunction import generateData
from NPVFunction import NPV_SAA

def main(Data, output_path1=None, output_path2=None, output_path3=None, max_height=None,
         max_width=None, num_height=10, num_width=10, stepsize_width=0.05, stepsize_height=0.05,
         option=1, product_thresholds=None, verbose=False):
    
    if max_width is None:
        max_width = Data[0]['Max_width']
    widths = [max_width-stepsize_width*i for i in range(num_width)]

    if max_height is None:
        max_height = Data[0]['Max_height']
    heights = [max_height-stepsize_height*i for i in range(num_height)]
    
    NPV = pd.DataFrame(np.zeros((num_height, num_width)), index=heights, columns=widths)
    NPVmax = NPV.copy()
    NPVmin = NPV.copy()

    for h in tqdm(range(num_height)):
        for w in tqdm(range(num_width)):
            NPV_ = NPV_SAA(Data, h=heights[h], w=widths[w], option=option,
                           product_thresholds=product_thresholds, verbose=verbose)
            NPV.values[h, w] = NPV_['Average NPV']
            NPVmax.values[h, w] = NPV_['NPVmax']
            NPVmin.values[h, w] = NPV_['NPVmin']
    
    if output_path1 is not None:
        NPV.to_csv(output_path1)
        NPVmax.to_csv(output_path2)
        NPVmin.to_csv(output_path3)
    
    return NPV, NPVmax, NPVmin


if __name__ == "__main__": # This means that running this script will run the function main() above
   
    num_scenarios = 500
    data_path = "data/DataPBAS.xlsx"
    Data = {i: generateData(data_path) for i in tqdm(range(num_scenarios))}
    
    # Data500_keys = random.sample(list(Data.keys()), 500)
    # Data500 ={}
    # for key in range(len(Data500_keys)):
    #     Data500[key] = Data[Data500_keys[key]].copy()

    # # Option 1: Maximise profit
    print('RUN OPTION 1')
    NPV_s1, NPV_s1_max, NPV_s1_min = main(Data, option=1,
                                          output_path1="output/NPV Table_option1_zoom1.csv",
                                          output_path2="output/NPVmax Table_option1_zoom1.csv",
                                          output_path3="output/NPVmin Table_option1_zoom1.csv",
                                          num_height=11, num_width=11, stepsize_width=0.01,
                                          stepsize_height=0.02, max_height=1.25, max_width=1.85)
    
    # # Option 2: Each market should constitute at least a certain amount of the production
    print('RUN OPTION 2')

    threshold = 0.03
    NPV_s2, NPV_s2_max, NPV_s2_min = main(Data, option=2,
                                          output_path1=f"output/NPV Table_option2_{threshold}.csv",
                                          output_path2=f"output/NPVmax Table_option2_{threshold}.csv",
                                          output_path3=f"output/NPVmin Table_option2_{threshold}.csv",
                                          num_height=12, num_width=5, stepsize_width=0.05,
                                          stepsize_height=0.05, max_height=1.55, max_width=1.85,
                                          product_thresholds={'notebooks': threshold,
                                                              'monitors': threshold,
                                                              'televisions': threshold})
    
    # Option 3: Each product should constitute at least a certain amount of the production
    print('RUN OPTION 3')
    threshold=0.005
    NPV_s3, NPV_s3_max, NPV_s3_max = main(Data, option=3,
                                          output_path1=f"output/NPV Table_option3_{threshold}.csv",
                                          output_path2=f"output/NPVmax Table_option3_{threshold}.csv",
                                          output_path3=f"output/NPVmin Table_option3_{threshold}.csv",
                                          num_height=11, num_width=17, stepsize_width=0.05,
                                          stepsize_height=0.05, product_thresholds=threshold)
    