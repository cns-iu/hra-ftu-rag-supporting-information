import pandas as pd
import glob
import os

file_list_dash = glob.glob('data\donor-meta\bmi\same-*.xlsx')
file_list_underscore = glob.glob('data\donor-meta\bmi\same_*.xlsx')
file_list = file_list_dash + file_list_underscore

if not file_list:
    print("No same-*.xlsx or same_*.xlsx file")
    exit()

merged_df = pd.concat([pd.read_excel(f) for f in file_list], ignore_index=True)
merged_df.to_excel('data\donor-meta\bmi\merge-all.xlsx', index=False)
merged_df.to_csv('data\donor-meta\bmi\merge-all.csv', index=False)

bmi_file = 'bmi.csv'
encodings_to_try = ['utf-8', 'ISO-8859-1', 'GBK']

for enc in encodings_to_try:
    try:
        species_df = pd.read_csv(bmi_file, encoding=enc)
        break
    except UnicodeDecodeError:
        print(f"Fail to read bmi.csv in {enc}, try next one...")
else:
    print("Fail to read bmi.csv")
    exit()

merge_all_df = pd.read_excel('data\donor-meta\bmi\merge-all.xlsx')

bmi_df['tag'] = 'others'

bmi_to_json_rs = dict(zip(merge_all_df['bmi'], merge_all_df['json_rs']))

bmi_df['tag'] = bmi_df['bmi'].map(bmi_to_json_rs).fillna('others')

bmi_df.to_csv('data\donor-meta\bmi\bmi_with_tags.csv', index=False)