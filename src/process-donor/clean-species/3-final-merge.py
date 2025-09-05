import pandas as pd
import glob
import os

file_list_dash = glob.glob('data\donor-meta\species\same-*.xlsx')
file_list_underscore = glob.glob('data\donor-meta\species\same_*.xlsx')
file_list = file_list_dash + file_list_underscore

print("找到的文件：", file_list)

if not file_list:
    print("No same-*.xlsx or same_*.xlsx file")
    exit()

merged_df = pd.concat([pd.read_excel(f) for f in file_list], ignore_index=True)
merged_df.to_excel('data\donor-meta\species\merge-all.xlsx', index=False)
merged_df.to_csv('data\donor-meta\species\merge-all.csv', index=False)

species_file = 'species.csv'
encodings_to_try = ['utf-8', 'ISO-8859-1', 'GBK']

for enc in encodings_to_try:
    try:
        species_df = pd.read_csv(species_file, encoding=enc)
        break
    except UnicodeDecodeError:
        print(f"Fail to read species.csv in {enc}, try next one...")
else:
    print("Fail to read species.csv")
    exit()

merge_all_df = pd.read_excel('data\donor-meta\species\merge-all.xlsx')

species_df['tag'] = 'others'

species_to_json_rs = dict(zip(merge_all_df['species'], merge_all_df['json_rs']))

species_df['tag'] = species_df['species'].map(species_to_json_rs).fillna('others')

species_df.to_csv('data\donor-meta\species\species_with_tags.csv', index=False)