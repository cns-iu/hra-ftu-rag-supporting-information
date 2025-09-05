#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import json
import re
import time

import requests
from clickhouse_driver import Client

# Load configuration from environment variables
FASTGPT_API_URL = 'YOUR_FASTGPT_API_URL'
FASTGPT_API_KEY = 'YOUR_FASTGPT_API_KEY'

# Load fixed prompt from file
with open(r'data/scale-bar/selected_prompt.txt', 'r', encoding='utf-8') as f:
    FIXED_PROMPT = f.read().strip()

# Initialize ClickHouse client
client = Client(
    host='your_host', port='your_port',
    user='your_username', password='your_password',
    database='your_database'
)

# Table names and schema definitions
TABLE_INFO = 'scale_bar_all_info'
TABLE_ENT = 'scale_bar_meta_all_info'
PRIMARY_KEYS_INFO = ['pmcid', 'id', 'type']
EXPECTED_COLS_INFO = ['pmcid', 'id', 'content', 'type', 'answer']

# Regex pattern for nested JSON
JSON_PATTERN = r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}"


def create_tables():
    """Create both info and entities tables if they don't exist."""
    ddl_info = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_INFO} (
        pmcid String,
        id String,
        content String,
        type String,
        answer String,
        update_time DateTime DEFAULT now()
    ) ENGINE = ReplacingMergeTree(update_time)
    ORDER BY ({','.join(PRIMARY_KEYS_INFO)});
    """
    ddl_ent = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_ENT} (
        pmcid String,
        id String,
        type String,
        descriptor_type String,
        value String,
        units String,
        notes String,
        panel String,
        update_time DateTime DEFAULT now()
    ) MergeTree()
    ORDER BY (pmcid,id,type);
    """
    client.execute(ddl_info)
    client.execute(ddl_ent)


def import_data():
    """Import source data"""
    client.execute(f"""
        INSERT INTO {TABLE_INFO} (pmcid, id, content, type)
        SELECT pmcid, graphic AS id, caption AS content, 'caption' AS type
        FROM ftu_pub_pmc a
        JOIN vision_llm b ON a.pmcid=b.pmcid AND a.graphic=b.graphic
        WHERE micro='Yes'
    """)
    client.execute(f"""
        INSERT INTO {TABLE_INFO} (pmcid, id, content, type)
        SELECT pmcid, graphic AS id, ref_text AS content, 'ref_text' AS type
        FROM img_ref a
        JOIN vision_llm b ON a.pmcid=b.pmcid AND a.graphic=b.graphic
        WHERE micro='Yes'
    """)


def fetch_pending_info():
    """Fetch rows from info table where answer is empty."""
    cols = ', '.join(PRIMARY_KEYS_INFO + ['content'])
    sql = f"SELECT {cols} FROM {TABLE_INFO} WHERE answer = ''"
    rows = client.execute(sql)
    return [dict(zip(PRIMARY_KEYS_INFO + ['content'], r)) for r in rows]


def extract_json_objects(text):
    """Extract JSON objects from text using nested-brace regex."""
    matches = re.findall(JSON_PATTERN, text)
    objs = []
    for m in matches:
        try:
            objs.append(json.loads(m))
        except json.JSONDecodeError:
            continue
    return objs


def send_request(row, model='llama3.1:70b'):
    """Call LLM, parse answer JSON, and upsert into info table."""
    payload = {
        'messages': [{'role': 'user', 'content': row['content']}],
        'variables': {'model': model, 'prompt': FIXED_PROMPT}
    }
    headers = {'Authorization': f"Bearer {FASTGPT_API_KEY}", 'Content-Type': 'application/json'}

    ans_objs = []
    for _ in range(5):
        resp = requests.post(FASTGPT_API_URL, headers=headers, json=payload)
        text = resp.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        ans_objs = extract_json_objects(text)
        if ans_objs:
            break
    answer_val = json.dumps(ans_objs, ensure_ascii=False) if ans_objs else text

    vals = (row['pmcid'], row['id'], row['type'], row['content'], answer_val)
    sql = f"INSERT INTO {TABLE_INFO} ({', '.join(EXPECTED_COLS_INFO)}) VALUES"
    client.execute(sql, [vals])


def extract_and_insert_entities():
    """Parse scale-bar metadata from answers and insert into scale_bar_meta_all_info."""
    sql = f"SELECT pmcid, id, type, answer FROM {TABLE_INFO} WHERE answer != ''"
    rows = client.execute(sql)
    ent_records = []

    for pmcid, cid, typ, answer in rows:
        try:
            entities = json.loads(answer)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(entities, dict):
            entities = [entities]
        for ent in entities:
            descriptor_type = ent.get('Descriptor Type', '')
            value = ent.get('Value', '')
            units = ent.get('Units', '')
            notes = ent.get('Notes', '')
            panel = ent.get('Panel', '')
            ent_records.append((pmcid, cid, typ,
                                 descriptor_type, value, units, notes, panel))

    if ent_records:
        insert_sql = (
            f"INSERT INTO {TABLE_ENT} "
            "(pmcid, id, type, descriptor_type, value, units, notes, panel) VALUES"
        )
        client.execute(insert_sql, ent_records)


def main():
    # Step 1: Create tables
    create_tables()
    # Step 2: Import source info
    import_data()
    # Step 3: Query LLM and upsert answers
    pending = fetch_pending_info()
    for row in pending:
        send_request(row)
    # Step 4: Extract entities and insert into entities table
    extract_and_insert_entities()


if __name__ == '__main__':
    main()
