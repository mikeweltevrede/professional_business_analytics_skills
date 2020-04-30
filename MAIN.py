import time
import numpy as np
import pandas as pd
from DataFunction import generateData
from NPVFunction import NPV_SAA

def main(data_path, output_path=None, num_scenarios=10,  max_height=None, max_width=None,
         num_height=10, num_width=10, stepsize_width=0.05, stepsize_height=0.05, option=1,
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
    
    print("Starting on option 1")
    NPV_s1 = main(data_path="data/DataPBAS.xlsx", output_path="output/NPV Table_option1.csv",
                  num_scenarios=10)
    
    print("Starting on option 2")
    NPV_s2 = main(data_path="data/DataPBAS.xlsx", output_path="output/NPV Table_option2.csv",
                  num_scenarios=10, option=2,
                  product_thresholds={key: 0.1 for key in ('notebooks', 'monitors', 'televisions')})
    
    print("Starting on option 3")
    # AttributeError: Unable to retrieve attribute 'x'
    # line 155, in NPV_SAA -> if NPVperScenario[s].getValue() < 0:
    NPV_s3 = main(data_path="data/DataPBAS.xlsx", output_path="output/NPV Table_option3.csv",
                  num_scenarios=10, option=3, product_thresholds=0.03)
    