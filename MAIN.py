import time
import numpy as np
import pandas as pd
from DataFunction import generateData
from NPVFunction import NPV_SAA

def main(data_path, output_path=None, num_scenarios=10,  max_height=None, max_width=None,
        num_height=55, num_width=85, stepsize_width=0.01, stepsize_height=0.01, option=1,
         product_thresholds=None, verbose=True):
    
    Data = {i: generateData(data_path) for i in range(num_scenarios)}
    
    if max_width is None:
        max_width = Data[0]['Max_width']
    widths = [max_width-stepsize_width*i for i in range(num_width)]

    if max_height is None:
        max_height = Data[0]['Max_height']
    heights = [max_height-stepsize_height*i for i in range(num_height)]
    
    NPV = pd.DataFrame(np.zeros((num_height, num_width)), index=heights, columns=widths)
    
    for h in range(num_height):
        for w in range(num_width):
            NPV_ = NPV_SAA(Data, h=heights[h], w=widths[w], option=option,
                           product_thresholds=product_thresholds, verbose=verbose)
            NPV.values[h, w] = NPV_['Average NPV']
    
    if output_path is not None:
        NPV.to_csv(output_path)
    
    return NPV

if __name__ == "__main__": # This means that running this script will run the function main() above
    num_scenarios = 500
    
    # Option 1: Maximise profit
    NPV_s1 = main(data_path="data/DataPBAS.xlsx", output_path="output/NPV Table_option1.csv",
                  num_scenarios=num_scenarios,
                  num_height=55, num_width=85, stepsize_width=0.01, stepsize_height=0.01)
    
    # Option 2: Each market should constitute at least a certain amount of the production
    NPV_s2 = main(data_path="data/DataPBAS.xlsx", output_path="output/NPV Table_option2.csv",
                  num_scenarios=num_scenarios,
                  num_height=55, num_width=85, stepsize_width=0.01, stepsize_height=0.01,
                  option=2,
                  product_thresholds={'notebooks': 0.1, 'monitors': 0.1, 'televisions': 0.1})
    
    # Option 3: Each product should constitute at least a certain amount of the production
    NPV_s3 = main(data_path="data/DataPBAS.xlsx", output_path="output/NPV Table_option3.csv",
                  num_scenarios=num_scenarios, 
                  num_height=55, num_width=85, stepsize_width=0.01, stepsize_height=0.01,
                  option=3, 
                  product_thresholds=0.03)
    