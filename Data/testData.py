import matplotlib as pyplot
import numpy as np

f1= open("Data1st.py", "r")

while True:
    line=f1.readline()
    List1=[int(i) for i in f1.split(',') or f1.split('-')]


