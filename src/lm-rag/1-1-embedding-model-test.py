# upload_and_search.py
# -*- coding: utf-8 -*-

import json
import logging
import os
import sys
import time
import urllib.parse
from datetime import datetime
from functools import partial
from multiprocessing import Pool

import pandas as pd
import requests

# =======================
# Logging configuration
# =======================
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(f'{log_dir}/upload_{current_time}.log')
file_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# =======================
# API call functions
# =======================

def searchText(database, datasetId, text, searchMode='mixedRecall', usingReRank=False, rerank_model='bce'):
    api_url = f"{web_url}/api/core/dataset/searchTest"
    payload = {
        "datasetId": datasetId,
        "text": text,
        "limit": 5000,
        "similarity": 0,
        "searchMode": searchMode,
        "usingReRank": usingReRank,
        "datasetSearchUsingExtensionQuery": False,
        "datasetSearchExtensionModel": "Qwen2.5-32B-Instruct",
        "datasetSearchExtensionBg": ""
    }
    kv = {
        'embedding': 'semantic retrieval',
        'fullTextRecall': 'full-text retrieval',
        'mixedRecall': 'hybrid retrieval',
    }
    resp = requests.post(api_url, headers=headers, json=payload)
    data = resp.json().get('data', {})
    if not data:
        logger.info(f"Empty data for payload: {payload}")
        return []

    results = data.get('list', [])
    out = []
    for item in results:
        sourceName = item.get('sourceName', '')
        answer = item.get('q', '')
        scores = item.get('score', [])
        embedding_score = fullText_score = rrf_score = reRank_score = None
        for sc in scores:
            t = sc.get('type')
            v = sc.get('value')
            if t == 'embedding':
                embedding_score = v
            elif t == 'fullText':
                fullText_score = v
            elif t == 'rrf':
                rrf_score = v
            elif t == 'reRank':
                reRank_score = v

        row = [
            database,
            rerank_model if usingReRank else '',
            kv.get(searchMode, searchMode),
            usingReRank,
            sourceName,
            text,
            answer,
            embedding_score,
            reRank_score,
            rrf_score,
            fullText_score
        ]
        out.append(row)
    return out


def create_database(name, vectorModel, agentModel="Qwen2.5-32B-Instruct", parentId=None):
    api_url = f"{web_url}/api/core/dataset/create"
    payload = {
        "parentId": parentId,
        "type": "dataset",
        "name": name,
        "intro": name,
        "avatar": "",
        "vectorModel": vectorModel,
        "agentModel": agentModel
    }
    resp = requests.post(api_url, headers=headers, data=json.dumps(payload))
    logger.info(f"create_database response: {resp.json()}")


def get_database(name, parentId=''):
    api_url = f"{web_url}/api/core/dataset/list?parentId={parentId}"
    resp = requests.post(api_url, headers=headers, data=json.dumps({"parentId": parentId}))
    items = resp.json().get('data', [])
    for it in items:
        if it.get('name') == name:
            return it.get('_id')
    return None


def get_all_database(parentId=''):
    api_url = f"{web_url}/api/core/dataset/list"
    resp = requests.post(api_url, headers=headers, data=json.dumps({"parentId": parentId}))
    items = resp.json().get('data', [])
    results = []
    for it in items:
        if it.get('type') == 'folder':
            results.extend(get_all_database(it.get('_id')))
        else:
            results.append({"name": it.get('name'), "id": it.get('_id')})
    return results


def get_all_collection(database_id, parentId=''):
    api_url = f"{web_url}/api/core/dataset/collection/list"
    payload = {"pageNum": 1, "pageSize": 1000, "datasetId": database_id, "parentId": parentId, "searchText": ""}
    resp = requests.post(api_url, headers=headers, verify=False, data=json.dumps(payload))
    items = resp.json().get('data', {}).get('data', [])
    results = []
    for it in items:
        if it.get('type') == 'folder':
            results.extend(get_all_collection(database_id, it.get('_id')))
        else:
            results.append({'id': it.get('_id'), 'name': it.get('name'), 'parentId': parentId})
    return results


def get_collection(database_id, name, parentId=''):
    cols = get_all_collection(database_id, parentId)
    for c in cols:
        if c['name'] == name:
            return c['id']
    return None


def database_detail(database_id):
    api_url = f"{web_url}/api/core/dataset/detail?id={database_id}"
    resp = requests.get(api_url, headers=headers, verify=False)
    return resp.json()


def fetch_page(page_num, database_id, parentId, key, web_url, page_size):
    api_url = f"{web_url}/api/core/dataset/collection/list"
    payload = {"pageNum": page_num, "pageSize": page_size, "datasetId": database_id, "parentId": parentId, "searchText": ''}
    hdr = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    while True:
        try:
            resp = requests.post(api_url, headers=hdr, json=payload, verify=False)
            if resp.status_code == 200 and resp.json().get('code') == 200:
                data = resp.json().get('data', {})
                names = [it['name'] for it in data.get('data', [])]
                total = data.get('total') if page_num == 1 else None
                return names, total
            else:
                logger.error(f"fetch_page failed: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"fetch_page exception: {e}")


def get_file_names(database_id, parentId=''):
    first, total = fetch_page(1, database_id, parentId, key, web_url, 30)
    if not total or total <= 0:
        return []
    pages = (total + 29) // 30
    names = first.copy()
    if pages > 1:
        with Pool(processes=10) as pool:
            args = [(pg, database_id, parentId, key, web_url, 30) for pg in range(2, pages+1)]
            results = pool.starmap(fetch_page, args)
        for r, _ in results:
            names.extend(r)
    return names


def get_file_data(collectionId):
    api_url = f"{web_url}/api/core/dataset/data/list"
    payload = {"offset": 0, "pageSize": 10, "collectionId": collectionId, "searchText": ''}
    resp = requests.post(api_url, headers=headers, data=json.dumps(payload))
    return resp.json().get('data', {}).get('total')


def delete_file_data(collectionId):
    api_url = f"{web_url}/api/core/dataset/collection/delete?id={collectionId}"
    requests.delete(api_url, headers=headers)


def fetch_page_id(page_num, database_id, parentId, key, web_url, page_size):
    names, total = fetch_page(page_num, database_id, parentId, key, web_url, page_size)
    # reuse fetch_page logic but return ids when implemented similarly
    # ...
    return [], total


def get_file_ids(database_id, parentId=None):
    first_ids, total = fetch_page_id(1, database_id, parentId, key, web_url, 30)
    if not total or total <= 0:
        return []
    pages = (total + 29) // 30
    ids = first_ids.copy()
    if pages > 1:
        with Pool(processes=10) as pool:
            args = [(pg, database_id, parentId, key, web_url, 30) for pg in range(2, pages+1)]
            results = pool.starmap(fetch_page_id, args)
        for r, _ in results:
            ids.extend(r)
    return ids


def delete_collection_file(collectionId, parm):
    total = 0 if parm == 'del' else get_file_data(collectionId)
    if total < del_file_length:
        delete_file_data(collectionId)
    else:
        logger.info(f"skip delete collection {collectionId}, total {total}")


def process_file_ids(database_id, parentId=None, parm=None):
    ids = get_file_ids(database_id, parentId)
    with Pool(processes=10) as pool:
        pool.starmap(delete_collection_file, [(cid, parm) for cid in ids])


def process_file(args):
    database_id, collection_id, file_path, filename = args
    upload_file(database_id, collection_id, file_path, filename)


def upload_file(database_id, parentId=None, file_path=None, filename=None, max_retries=3):
    fname = urllib.parse.quote(filename)
    data = {'datasetId': database_id, 'parentId': parentId, 'trainingType': 'chunk', 'chunkSize': 256, 'chunkSplitter': '', 'qaPrompt': ''}
    api_url = f"{web_url}/api/core/dataset/collection/create/localFile"
    hdr = {'Authorization': f'Bearer {key}'}
    for i in range(max_retries):
        with open(file_path, 'rb') as f:
            files = {'file': (fname, f)}
            resp = requests.post(api_url, headers=hdr, verify=False, files=files, data={"data": json.dumps(data)})
        if resp.status_code == 200:
            logger.info(f"Uploaded {filename}")
            return
        elif resp.status_code == 500:
            time.sleep(2)
    logger.info(f"Failed upload {filename}")


def upload_files(database, collect_name='', parm='', parentId=''):
    db_id = get_database(database, parentId)
    col_id = get_collection(db_id, collect_name, parentId)
    if parm in ('del', 'update'):
        process_file_ids(db_id, col_id, parm)
        if parm == 'del': sys.exit(0)
    names = get_file_names(db_id, col_id)
    to_upload = []
    for root, _, files in os.walk(directory_path):
        for fn in files:
            if fn not in names:
                to_upload.append((db_id, col_id, os.path.join(root, fn), fn))
    if to_upload:
        with Pool(processes=10) as pool:
            pool.map(process_file, to_upload)


def search_total(database, parentId, text):
    db_id = get_database(database, parentId)
    if not db_id:
        create_database(database, database, parentId=parentId)
        db_id = get_database(database, parentId)
    out = []
    for mode in ['embedding', 'fullTextRecall', 'mixedRecall']:
        out.extend(searchText(database, db_id, text, searchMode=mode, usingReRank=False))
    return out


def search_worker(args):
    return search_total(*args)


if __name__ == '__main__':
    # ===== Configuration =====
    key = 'fastgpt-'
    web_url = 'http://ip:3000'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'}
    directory_path = '/tmp/files/'
    databases = ['bce-embedding-base_v1']
    del_file_length = 10000  # threshold for deleting

    # Read questions
    with open(r'data\emb\test_questions.csv', encoding='utf-8') as f:
        texts = [l.strip() for l in f.readlines()[1:] if l.strip()]

    # Ensure databases exist
    for db in databases:
        if not get_database(db, ''):
            create_database(db, db, parentId='')

    # Upload files
    for db in databases:
        upload_files(db, parentId='')

    # Search tasks
    columns = [
        'embedding_model_name', 'reRank_model_name', 'searchMode', 'usingReRank',
        'sourceName', 'question', 'answer', 'embedding_score', 'reRank_score', 'rrf_score', 'fullText_score'
    ]
    all_results = []
    tasks = [(db, '', txt) for db in databases for txt in texts]
    with Pool(processes=1) as pool:
        for res in pool.map(search_worker, tasks):
            all_results.extend(res)

    df = pd.DataFrame(all_results, columns=columns)
    df.to_excel(r'data\emb\emb_test_output.xlsx', index=False, engine='openpyxl')