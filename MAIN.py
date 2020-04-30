import time
import numpy as np
import pandas as pd
from DataFunction import generateData
from NPVFunction import NPV_SAA

def main(data_path, num_scenarios, output_path, max_height=None, max_width=None, num_height=10,
         num_width=10, stepsize_width=0.05, stepsize_height=0.05):
    
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
            NPV_ = NPV_SAA(Data, heights[h], widths[w])
            NPV.values[h, w] = NPV_['Average NPV']
    
    NPV.to_csv(output_path)
    
    return NPV

if __name__ == "__main__":
    # This means that running this script will run the function main()
    NPV_s1 = main(data_path = "data/DataPBAS.xlsx", num_scenarios = 10,
                  output_path = "output/NPV Table.csv")
    