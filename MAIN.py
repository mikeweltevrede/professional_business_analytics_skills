from tqdm import tqdm
import numpy as np
import pandas as pd
from DataFunction import generateData
from NPVFunction import NPV_SAA
import random

def main(Data, output_path1=None, output_path2=None, output_path3=None, max_height=None, max_width=None,
        num_height=10, num_width=10, stepsize_width=0.01, stepsize_height=0.01, option=1,
         product_thresholds=None, verbose=False):
    
    if max_width is None:
        max_width = 1.85
    widths = [max_width-stepsize_width*i for i in range(num_width)]

    if max_height is None:
        max_height = 1.55
    heights = [max_height-stepsize_height*i for i in range(num_height)]
    
    NPV = pd.DataFrame(np.zeros((num_height, num_width)), index=heights, columns=widths)
    NPVmax = pd.DataFrame(np.zeros((num_height, num_width)), index=heights, columns=widths)
    NPVmin = pd.DataFrame(np.zeros((num_height, num_width)), index=heights, columns=widths)

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
    
    return NPV_

#num_scenarios = 1000
#data_path = "data/DataPBAS.xlsx"
#Data1000 = {i: generateData(data_path) for i in range(num_scenarios)}
#Data500_keys = random.sample(list(Data1000.keys()),500)
#Data500 ={}
#for key in range(len(Data500_keys)):
#    Data500[key] = Data1000[Data500_keys[key]].copy()

if __name__ == "__main__": # This means that running this script will run the function main() above
   
#    # Option 1: Maximise profit
#    print('RUN OPTION 1')
#    NPV_s1_zoom1 = main(Data1000, output_path1="output/NPV Table_option1_zoom1.csv",
#                  output_path2="output/NPVmax Table_option1_zoom1.csv",
#                  output_path3="output/NPVmin Table_option1_zoom1.csv",
#                  num_height=11, num_width=11, stepsize_width=0.01, stepsize_height=0.02,
#                  max_height=1.25, max_width=1.85)
    
    # Option 2: Each market should constitute at least a certain amount of the production
    print('RUN OPTION 2')
    NPV_s2 = main(Data500, output_path1="output/NPV Table_option2_3%.csv",
                  output_path2="output/NPVmax Table_option2_3%.csv",
                  output_path3="output/NPVmin Table_option2_3%.csv",
                  option=2,
                  num_height=12, num_width=5, stepsize_width=0.05, stepsize_height=0.05,
                  max_height=1.55, max_width=1.85,
                  product_thresholds={'notebooks': 0.03, 'monitors': 0.03, 'televisions': 0.03})
    
    # Option 3: Each product should constitute at least a certain amount of the production
    print('RUN OPTION 3')
    NPV_s3 = main(data_path="data/DataPBAS.xlsx", output_path1="output/NPV Table_option3.csv",
                  output_path2="output/NPVmax Table_option3.csv",
                  output_path3="output/NPVmin Table_option3.csv",
                  num_scenarios=num_scenarios, 
                  num_height=12, num_width=5, stepsize_width=0.05, stepsize_height=0.05,
                  option=3, 
                  product_thresholds=0.005)
    