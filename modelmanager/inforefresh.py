#!/usr/bin/env python

# call this script to check for missing models (folders)
# and refresh modelsinfo.csv removing the non-existing
# models.

import pandas as pd
import os

modelsinfo = pd.read_csv("modelsinfo.csv")

drop_indexes = []
for i, data in modelsinfo.iterrows():
    if not os.path.isdir(data["id"]):
        drop_indexes += [i] 
        print(f"Found non-existing model {data['id']}")
        
modelsinfo.drop(drop_indexes, inplace=True)
modelsinfo.to_csv("modelsinfo.csv", index=False)
