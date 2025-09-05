import pandas as pd
import glob
import os

file_list_dash = glob.glob('data\donor-meta\age\same-*.xlsx')
file_list_underscore = glob.glob('data\donor-meta\age\same_*.xlsx')
file_list = file_list_dash + file_list_underscore

if not file_list:
    print("No same-*.xlsx or same_*.xlsx file")
    exit()

merged_df = pd.concat([pd.read_excel(f) for f in file_list], ignore_index=True)
merged_df.to_excel('data\donor-meta\age\merge-all.xlsx', index=False)
merged_df.to_csv('data\donor-meta\age\merge-all.csv', index=False)

age_file = 'age.csv'
encodings_to_try = ['utf-8', 'ISO-8859-1', 'GBK']

for enc in encodings_to_try:
    try:
        species_df = pd.read_csv(age_file, encoding=enc)
        break
    except UnicodeDecodeError:
        print(f"Fail to read age.csv in {enc}, try next one...")
else:
    print("Fail to read age.csv")
    exit()

merge_all_df = pd.read_excel('data\donor-meta\age\merge-all.xlsx')

age_df['tag'] = 'others'

age_to_json_rs = dict(zip(merge_all_df['age'], merge_all_df['json_rs']))

age_df['tag'] = age_df['age'].map(age_to_json_rs).fillna('others')

age_df.to_csv('data\donor-meta\age\age_with_tags.csv', index=False)