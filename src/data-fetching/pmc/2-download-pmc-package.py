import os
import urllib.request
import pandas as pd
from multiprocessing import Pool

# Set the output directory and base URL for downloading
output_dir = r"data\input-data\ftu-pub-pmc"
base_url = "ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/"

# Create the output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Function to download a file for a specific row
def download_file(row):
    pmcid = row['pmcid']
    file_y = row['File']
    file_url = base_url + file_y
    
    # Check if the folder for the given pmcid already exists
    folder_path = os.path.join(output_dir, pmcid)
    if not os.path.exists(folder_path):
        # os.makedirs(folder_path)

        # Download the file
        try:
            print(f"Downloading {file_url} to {folder_path}")
            file_path = os.path.join(output_dir, file_y.split('/')[-1])
            urllib.request.urlretrieve(file_url, file_path)
            print(f"Download completed: {file_path}")
        except Exception as e:
            print(f"Failed to download {file_url}: {e}")
    else:
        print(f"Folder {folder_path} exists. Skipping download.")

# Read the CSV file using pandas
df = pd.read_csv(r'data\input-data\0-1-oa-comm-ftu-pmcid-filepath.csv')

# Create a pool of worker processes to download files in parallel
if __name__ == '__main__':
    # Use a pool of processes to execute the download_file function in parallel
    with Pool(processes=30) as pool:  
        pool.map(download_file, [row for index, row in df.iterrows()])
