import pandas as pd
import glob
import os

file_list_dash = glob.glob('data\donor-meta\sex\same-*.xlsx')
file_list_underscore = glob.glob('data\donor-meta\sex\same_*.xlsx')
file_list = file_list_dash + file_list_underscore


if not file_list:
    print("No same-*.xlsx or same_*.xlsx file")
    exit()

merged_df = pd.concat([pd.read_excel(f) for f in file_list], ignore_index=True)
merged_df.to_excel('data\donor-meta\sex\merge-all.xlsx', index=False)
merged_df.to_csv('data\donor-meta\sex\merge-all.csv', index=False)

sex_file = 'sex.csv'
encodings_to_try = ['utf-8', 'ISO-8859-1', 'GBK']

for enc in encodings_to_try:
    try:
        species_df = pd.read_csv(sex_file, encoding=enc)
        break
    except UnicodeDecodeError:
        print(f"Fail to read sex.csv in {enc}, try next one...")
else:
    print("Fail to read sex.csv")
    exit()

merge_all_df = pd.read_excel('data\donor-meta\sex\merge-all.xlsx')

sex_df['tag'] = 'others'

sex_to_json_rs = dict(zip(merge_all_df['sex'], merge_all_df['json_rs']))

sex_df['tag'] = sex_df['sex'].map(sex_to_json_rs).fillna('others')

sex_df.to_csv('data\donor-meta\sex\sex_with_tags.csv', index=False)