import pandas as pd
import re


df = pd.read_csv(r'data\scale-bar\scale-bar-value-ftu.csv')

# 筛选出 units 为空且 value 不为空的行
mask = df['value'].notnull()

def split_value(x):
    # Remove all digits, spaces, commas, periods, and hyphens from 'value' to get 'value_units'
    value_units = re.sub(r'[\d\s,.\-]+', '', x)
    # Keep digits, commas, periods, hyphens, and spaces, then remove spaces to get 'value_new'
    value_new = re.sub(r'[^ \d,.\-]+', '', x).replace(' ', '')
    return pd.Series({'value_new': value_new, 'value_units': value_units})

df.loc[mask, ['value_new', 'value_units']] = df.loc[mask, 'value'].apply(split_value)

# Define lists of cases to be replaced with empty values
bad_units = ["Not provided", "Not mentioned", "Not applicable", "None mentioned", "Not Found", "Not specified", "Not explicitly mentioned"]
bad_value_units = ["Notprovided", "Notspecified", "Notmentioned", "notavailable", "Nonementioned", "NotFound", "unknown"]
bad_value = ["Not provided", "Not specified", "Not mentioned", "Not explicitly mentioned", "not available", "None mentioned", "Not Found", "unknown"]

bad_units_lower = [s.lower() for s in bad_units]
bad_value_units_lower = [s.lower() for s in bad_value_units]
bad_value_lower = [s.lower() for s in bad_value]

# Check the 'units' column and set to None if it matches any bad case (case-insensitive)
df['units'] = df['units'].apply(lambda x: None if pd.notnull(x) and x.lower() in bad_units_lower else x)

# Check the 'value_units' column and set to None if it matches any bad case (case-insensitive)
df['value_units'] = df['value_units'].apply(lambda x: None if pd.notnull(x) and x.lower() in bad_value_units_lower else x)

# Check the 'value' column and set to None if it matches any bad case (case-insensitive)

df['value'] = df['value'].apply(lambda x: None if pd.notnull(x) and x.lower() in bad_value_lower else x)


df.to_csv(r'scale-bar\scale-bar-value-ftu-clean1.csv', index=False)
