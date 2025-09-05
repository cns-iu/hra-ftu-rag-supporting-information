import pandas as pd
import requests

final_results_file = r'data\input-data\0-0-ftu-pmc-total.csv'
oa_comm_use_url = 'https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_comm_use_file_list.csv'
oa_comm_local_file = r'data\input-data\oa_comm_use_file_list.csv'
output_file = r'data\input-data\0-1-oa-comm-ftu-pmcid-filepath.csv'

# download oa_comm_use_file_list.csv
print(f"Downloading {oa_comm_use_url} ...")
response = requests.get(oa_comm_use_url)
with open(oa_comm_local_file, 'wb') as f:
    f.write(response.content)
print("Download complete.")

# load data
final_df = pd.read_csv(final_results_file)
oa_df = pd.read_csv(oa_comm_local_file)


if 'Accession ID' in oa_df.columns:
    oa_df.rename(columns={'Accession ID': 'pmcid'}, inplace=True)

if 'pmcid' not in final_df.columns or 'pmcid' not in oa_df.columns:
    raise ValueError("make sure 'pmcid' in both input files")

# merge
merged_df = pd.merge(final_df, oa_df, on='pmcid', how='inner')
merged_df.to_csv(output_file, index=False)

print(f"Finished. Results saved to: {output_file}")
