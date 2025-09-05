import pandas as pd

df = pd.read_csv(r'data\scale-bar\scale-bar-value-ftu-clean1.csv')

# List of unit filenames to be checked
unit_files = ["m", "cm", "mm", "um", "nm", "angstrom", "pm"]

# Build a dictionary where key is unit name, value is all possible expressions for that unit
# All expressions are converted to lowercase and stripped of leading/trailing whitespace
unit_dict = {}
for unit in unit_files:
    temp_df = pd.read_csv(rf"data\scale-bar\units-expression\{unit}.csv", header=None)
    expressions = temp_df[0].astype(str).str.strip().str.lower().tolist()
    unit_dict[unit] = expressions

# Function to map value to standardized unit
def get_standard_unit(value):
    if pd.isnull(value):
        return None
    val = str(value).strip().lower()
    for unit, expressions in unit_dict.items():
        if val in expressions:
            return unit
    return None

# Step 1: Match the 'units' column and create a new column 'standard_unit'
df['standard_unit'] = df['units'].apply(get_standard_unit)

# Step 2: For rows with null 'standard_unit', try matching 'value_units' column
mask = df['standard_unit'].isnull()
df.loc[mask, 'standard_unit'] = df.loc[mask, 'value_units'].apply(get_standard_unit)

# Step 3: If 'value_new' is null or empty, set it to the value of 'value'
df['value_new'] = df.apply(lambda row: row['value'] if pd.isnull(row['value_new']) or str(row['value_new']).strip() == "" else row['value_new'], axis=1)

# Save the final result
df.to_csv(r'data\scale-bar\sb-cleaned2.csv', index=False)
