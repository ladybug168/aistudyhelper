import pdfplumber
import numpy as np
from openai import OpenAI
import os
import json
with open('optiondata.json', 'r') as file:
    # The variable 'data_list' becomes a Python list
    data_list = json.load(file)

print(type(data_list))


names = [d.get('name') for d in data_list]
print(names)

values = [d.get('value') for d in data_list]
print(values)
try:
    element = "Art"
    index_position = names.index(element)
    #print(values[index_position])
    #index_position = my_list.index(element)
    print(f"The index of the first '{element}' is: {index_position}")
    print(values[index_position])
except ValueError:
    print(f"'{element}' is not found in the list.")
    
