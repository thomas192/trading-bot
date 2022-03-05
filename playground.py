import numpy as np
import pandas as pd

var = None

if pd.isnull(var):
    print("var is null")
else:
    print("var is not null")

var = 500.56789

if not pd.isnull(var):
    print("var is not null")
else:
    print("var is null")

var = None

if pd.isnull(var):
    print("var is null")
else:
    print("var is not null")
