import ijson
import pandas as pd
import os
import requests
import gzip
import shutil

# Step 1: Download the file
def download_ontology_file(url, output_path):
    print(f"Downloading file from: {url}")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        print(f"Downloaded to: {output_path}")
    else:
        raise Exception(f"Failed to download file. Status code: {response.status_code}")

# Step 2: Unzip the .gz file
def unzip_gz_file(gz_path, output_path):
    print(f"Unzipping file: {gz_path}")
    with gzip.open(gz_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f"Unzipped to: {output_path}")

# Step 3: Save DataFrame in Excel chunks
def save_dataframe_in_chunks(df, base_filename, chunk_size=500):
    num_chunks = len(df) // chunk_size + (1 if len(df) % chunk_size else 0)
    for i in range(num_chunks):
        chunk = df[i*chunk_size:(i+1)*chunk_size]
        chunk_filename = f"{base_filename}_part_{i+1}.xlsx"
        chunk.to_excel(chunk_filename, index=False)
        print(f"Chunk saved to: {chunk_filename}")

# Step 4: Process JSON and export to Excel
def process_ontologies_json(json_path, start_index=0, end_index=50, output_dir="./output"):
    with open(json_path, 'r') as file:
        parser = ijson.items(file, 'ontologies.item')
        for index, ontology in enumerate(parser):
            if index < start_index:
                continue
            if end_index is not None and index >= end_index:
                break
            classes_data = ontology.get('classes', [])
            if classes_data:
                df = pd.json_normalize(classes_data)
                base_filename = os.path.join(output_dir, f"classes_output_ontology_{index}")
                save_dataframe_in_chunks(df, base_filename)
            else:
                print(f"Ontology {index} has no 'classes' data")
    print("All Excel files generated for the given range!")

# ---- Main Execution Flow ----

# Configuration
download_url = 'https://ftp.ebi.ac.uk/pub/databases/spot/ols/latest/ontologies.json.gz'
gz_file = r'data\input-data\ontologies.json.gz'
json_file = r'data\input-data\ontologies.json'
output_directory = r'data\input-data\ols'
os.makedirs(output_directory, exist_ok=True)

# Run steps
download_ontology_file(download_url, gz_file)
unzip_gz_file(gz_file, json_file)
process_ontologies_json(json_file, start_index=0, end_index=50, output_dir=output_directory)
