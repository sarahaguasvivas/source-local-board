#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv("testData.csv", header=None)

plt.plot(data.iloc[:,0])
plt.plot(data.iloc[:,1])
plt.plot(data.iloc[:,2])

plt.show()


