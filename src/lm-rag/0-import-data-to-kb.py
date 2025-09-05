import json
import logging
import os
import sys
import time
import urllib
from datetime import datetime
from functools import partial
from multiprocessing import Pool

import pandas as pd
import requests

# API key and base URL for the FastGPT API
key = 'your_api_key_here'
web_url = 'your_web_url'

# HTTP headers for API requests
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {key}'
}

# Proxy settings (if needed)
proxies = {"http": "http://127.0.0.1:18080", "https": "http://127.0.0.1:18080"}

# Get current timestamp for log file naming
current_time = datetime.now()
timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

# Ensure the logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')

# Setup logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)

# File logger
file_handler = logging.FileHandler(f'logs/upload_{timestamp}.log')
file_handler.setLevel(logging.INFO)

# Console logger
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Log format including filename and line number
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ------------------ API Wrappers and Utilities ------------------

# Retrieve a dataset ID by name
def get_database(n, parentId=''):
    api_url = f'{web_url}/api/core/dataset/list?parentId='
    data = {"parentId": parentId}
    r = requests.post(url=api_url, headers=headers, data=json.dumps(data), verify=False)
    data = r.json().get('data', [])
    for i in data:
        if n == i.get('name'):
            return i['_id']
    return None

# Recursively retrieve all datasets under a parent
def get_all_database(parentId=''):
    api_url = f'{web_url}/api/core/dataset/list'
    data = {"parentId": parentId}
    r = requests.post(url=api_url, headers=headers, data=json.dumps(data), verify=False)
    data = r.json().get('data', [])
    results = []
    for i in data:
        if i.get('type') == "folder":
            sub_results = get_all_database(i.get("_id"))
            results.extend(sub_results)
        else:
            results.append({"name": i.get("name"), "id": i.get("_id")})
    return results

# Recursively retrieve all collections within a dataset
def get_all_collection(database_id, parentId=''):
    api_url = f'{web_url}/api/core/dataset/collection/list'
    data = {
        "pageNum": 1,
        "pageSize": 1000,
        "datasetId": database_id,
        "parentId": parentId,
        "searchText": ""
    }
    results = []
    r = requests.post(url=api_url, headers=headers, verify=False, data=json.dumps(data))
    data = r.json().get('data', {}).get('data', {})
    for i in data:
        if i.get('type') == 'folder':
            sub_results = get_all_collection(database_id, parentId=i['_id'])
            results.extend(sub_results)
        else:
            results.append({'id': i['_id'], 'name': i['name'], 'parentId': parentId})
    return results

# Retrieve a specific collection ID by name
def get_collection(database_id, n, parentId=''):
    api_url = f'{web_url}/api/core/dataset/collection/list'
    data = {
        "pageNum": 1,
        "pageSize": 1000,
        "datasetId": database_id,
        "parentId": parentId,
        "searchText": ""
    }
    r = requests.post(url=api_url, headers=headers, verify=False, data=json.dumps(data))
    data = r.json().get('data', {}).get('data', {})
    for i in data:
        if n == i['name']:
            return i['_id']
    return None

# Placeholder for getting database detail
def database_detail(database_id):
    api_url = f'{web_url}/api/core/dataset/detail?id={database_id}'
    r = requests.get(url=api_url, headers=headers, verify=False)
    return r.json()

# Fetch file names in a collection using pagination
def fetch_page(page_num, database_id, parentId, key, web_url, page_size):
    data = {
        "pageNum": page_num,
        "pageSize": page_size,
        "datasetId": database_id,
        "parentId": parentId,
        "searchText": ""
    }
    headers_local = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    }
    api_url = f'{web_url}/api/core/dataset/collection/list'

    while True:
        try:
            response = requests.post(url=api_url, headers=headers_local, json=data, verify=False)
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    names = [item["name"] for item in result["data"]["data"]]
                    return names, result['data']['total'] if page_num == 1 else None
            else:
                logger.error(f"Failed to fetch data: {response.status_code} - {response.text}")
                return [], None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            time.sleep(2)

# Get all file names in a collection
def get_file_names(database_id, parentId=''):
    page_num = 1
    page_size = 30
    first_page_names, total = fetch_page(page_num, database_id, parentId, key, web_url, page_size)

    if not total or total <= 0:
        logger.error("No data found.")
        return []

    total_pages = (total + page_size - 1) // page_size
    if total_pages == 1:
        return first_page_names

    with Pool(processes=10) as pool:
        fetch_page_partial = partial(fetch_page, database_id=database_id, parentId=parentId, key=key, web_url=web_url, page_size=page_size)
        results = pool.map(fetch_page_partial, range(2, total_pages + 1))

    all_names = first_page_names + [name for result, _ in results for name in result]
    return all_names

# Get data size from a collection
def get_file_data(collectionId):
    url = f'{web_url}/api/core/dataset/data/list'
    data = {
        "offset": 0,
        "pageSize": 10,
        "collectionId": collectionId,
        "searchText": ""
    }
    req = requests.post(url=url, headers=headers, data=json.dumps(data), verify=False).json()
    return req.get('data', {}).get('total')

# Delete a file collection
def delete_file_data(collectionId):
    url = f'{web_url}/api/core/dataset/collection/delete?id={collectionId}'
    req = requests.delete(url=url, headers=headers).json()
    if req.get('code') != 200:
        logger.info(req)

# Upload a single file to the server
def upload_file(database_id, parentId=None, file_path=None, filename=None, max_retries=3):
    filename_encoded = urllib.parse.quote(filename)
    headers_local = {'Authorization': f'Bearer {key}'}
    data = {
        'datasetId': database_id,
        'parentId': parentId,
        'trainingType': 'chunk',
        'chunkSize': 256,
        'chunkSplitter': '',
        'qaPrompt': '',
    }
    api_url = f'{web_url}/api/core/dataset/collection/create/localFile'

    for attempt in range(max_retries):
        try:
            with open(file_path, 'rb') as file_obj:
                files = {'file': (filename_encoded, file_obj)}
                response = requests.post(api_url, headers=headers_local, verify=False, files=files, data={"data": json.dumps(data)})

            if response.status_code == 200:
                logger.info(f"Uploaded {filename} successfully")
                break
            else:
                logger.info(f"Upload failed for {filename}, status: {response.status_code}")
                if response.status_code == 500:
                    logger.info(f"Retrying upload ({attempt + 1}/{max_retries})...")
                    time.sleep(2)
                else:
                    break
        except Exception as e:
            logger.error(f"Upload exception for {filename}: {e}")
    else:
        logger.info(f"Max retries exceeded for {filename}")

# Process a single file for uploading
def process_file(args):
    database_id, collection_id, file_path, filename = args
    upload_file(database_id=database_id, parentId=collection_id, file_path=file_path, filename=filename)

# Placeholder for processing file IDs (delete/update)
def process_file_ids(database_id, collection_id, parm=None):
    logger.info("process_file_ids function is not implemented.")

# Main upload function for a folder
def upload_files(database, collect_name='', parm='', parentId='', directory_path=''):
    database_id = get_database(database, parentId)
    if not database_id:
        logger.error(f"Database '{database}' not found.")
        return

    collection_id = get_collection(database_id, collect_name, parentId)

    if parm == 'del':
        process_file_ids(database_id, collection_id, parm)
        logger.info("Deletion complete")
        sys.exit(1)
    elif parm == 'update':
        process_file_ids(database_id, collection_id)
        logger.info("Update deletion complete")

    all_names = get_file_names(database_id, collection_id)
    logger.info(f"Total files: {len(all_names)}, Unique: {len(set(all_names))}")

    files_to_upload = []
    for dirpath, dirnames, filenames in os.walk(directory_path):
        for fname in filenames:
            if fname not in all_names:
                file_path = os.path.join(dirpath, fname)
                files_to_upload.append((database_id, collection_id, file_path, fname))

    if files_to_upload:
        with Pool(processes=10) as pool:
            pool.map(process_file, files_to_upload)

if __name__ == "__main__":
    # Modify the following variables before running the script
    directory_path = ''  # Directory containing files to upload
    database = ''        # Name of the database
    collect_name = ''    # Name of the collection
    # You can set parm to 'del' or 'update' if needed
    parm = ''
    parentId = ''
    upload_files(database=database, collect_name=collect_name, parm=parm, parentId=parentId, directory_path=directory_path)
