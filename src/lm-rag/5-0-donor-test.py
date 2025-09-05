#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import functools
import json
import multiprocessing
import re
import time
import uuid

import pandas as pd
import requests
from clickhouse_driver import Client

# File paths and table name configuration
file1 = r"data\donor-meta\donor-test-answer.csv"
file2 = r"data\donor-meta\prompt-donor.csv"
table_name = "donor_test"

# ClickHouse client configuration
client = Client(
    host='your_host', port='your_port',
    user='your_username', password='your_password',
    database='your_database'
)

# Expected columns and primary key order fields
expected_cols = [
    'text_type', 'num', 'itype', 'pmcid',
    'content', 'llama31_runtime', 'llama32_runtime', 'gemma_runtime', 'qwen_runtime',
    'llama31_jaccard', 'llama32_jaccard', 'qwen_jaccard', 'gemma_jaccard',
    'answer', 'prompt', 'llama31', 'llama32', 'qwen', 'gemma'
]
order_columds = ['text_type', 'num', 'itype', 'pmcid', 'content', 'prompt']

# FastGPT API key
Authorization = 'your_fastgpt_key'


def create_table():
    """Create the ClickHouse table if it does not already exist."""
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {' String, '.join(expected_cols)} String,
        update_time DateTime DEFAULT now()
    ) ENGINE = ReplacingMergeTree(update_time)
    ORDER BY ({', '.join(order_columds)});
    """
    client.execute(create_table_query)


def import_data():
    """Import data from CSV files into ClickHouse."""
    df_A = pd.read_csv(file1)
    df_B = pd.read_csv(file2)
    df_A.rename(columns={'type': 'text_type'}, inplace=True)
    df_A['key'] = 1
    df_B['key'] = 1
    merged = pd.merge(df_A, df_B, on='key').drop('key', axis=1)
    for col in expected_cols:
        if col not in merged.columns:
            merged[col] = ''
    merged[expected_cols] = merged[expected_cols].astype(str)
    merged['update_time'] = datetime.datetime.now()
    all_cols = expected_cols + ['update_time']
    data = [tuple(row) for row in merged[all_cols].to_numpy()]
    client.execute(f'INSERT INTO {table_name} VALUES', data)


def fetch_data_from_clickhouse(condition):
    """Fetch rows from ClickHouse matching the given SQL condition."""
    query = f"SELECT {', '.join(expected_cols)} FROM {table_name} {condition}"
    rows = client.execute(query)
    return [dict(zip(expected_cols, row)) for row in rows]


def extrac_json_text(text):
    """Extract JSON objects from the model response text."""
    pattern = r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}'
    json_strings = re.findall(pattern, text)
    objs = []
    for js in json_strings:
        try:
            objs.append(json.loads(js))
        except json.JSONDecodeError:
            continue
    return objs


def jaccard_similarity(dict1, dict2, compare_values=True):
    """Compute the Jaccard similarity between two dicts (by items or keys)."""
    try:
        if compare_values:
            set1 = set(dict1.items())
            set2 = set(dict2.items())
        else:
            set1 = set(dict1.keys())
            set2 = set(dict2.keys())
    except:
        return 0
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union) if union else 0


def average_jaccard_similarity(list1, list2, compare_values=True):
    """Compute average Jaccard over all pairs between two lists of dicts."""
    if isinstance(list1, dict):
        list1 = [list1]
    if isinstance(list2, dict):
        list2 = [list2]
    similarities = []
    for d1 in list1:
        for d2 in list2:
            similarities.append(jaccard_similarity(d1, d2, compare_values))
    return sum(similarities) / len(similarities) if similarities else 0


def process_jaccard(result, column_name):
    """Compute and store the Jaccard similarity for a given response column."""
    answer = result.get('answer', '')
    rs = result.get(column_name, '')
    try:
        json_rs = json.loads(rs)
    except:
        json_rs = []
    try:
        answer_json = json.loads(answer)
    except:
        answer_json = {}
    sim = average_jaccard_similarity(answer_json, json_rs)
    result[f'{column_name}_jaccard'] = str(sim)
    insert_data(result)


def insert_data(data):
    """Insert or update a single row in ClickHouse."""
    row = [data.get(col, '') for col in expected_cols]
    client.execute(
        f"INSERT INTO {table_name} ({', '.join(expected_cols)}) VALUES",
        [tuple(row)]
    )


def send_request(result, model_name, col_name):
    """Query the FastGPT API for a model, save the response and latency."""
    question = result.get('content', '')
    prompt = result.get('prompt', '')
    url = 'your_fastgpt_url'
    headers = {
        'Authorization': f"Bearer {Authorization}",
        'Content-Type': 'application/json'
    }
    payload = {
        'messages': [{'content': question, 'role': 'user'}],
        'variables': {'model': model_name, 'prompt': prompt}
    }
    start = time.time()
    json_rs = []
    for _ in range(10):
        res = requests.post(url, headers=headers, data=json.dumps(payload))
        content = res.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        json_rs = extrac_json_text(content)
        if json_rs:
            break
    runtime = time.time() - start
    result[f'{col_name}_runtime'] = str(round(runtime, 2))
    result[col_name] = json.dumps(json_rs)
    insert_data(result)

if __name__ == '__main__':
    # Step 1: Create table and import data
    create_table()
    import_data()

    # Step 2: Iterate over models, query and save responses/latencies
    model_map = {
        'qwen': 'qwen2.5:72b',
        'llama32': 'llama3.2:latest',
        'gemma': 'gemma2:27b',
        'llama31': 'llama3.1:70b'
    }
    for col, model in model_map.items():
        condition = f"WHERE {col} = '' AND prompt != ''"
        tasks = fetch_data_from_clickhouse(condition)
        for task in tasks:
            send_request(task, model, col)

    # Step 3: Parallel computation of record-level Jaccard similarity
    for col in model_map:
        condition = f"WHERE {col} != '' AND {col}_jaccard = ''"
        tasks = fetch_data_from_clickhouse(condition)
        worker = functools.partial(process_jaccard, column_name=col)
        with multiprocessing.Pool(processes=20) as pool:
            pool.map(worker, tasks)
