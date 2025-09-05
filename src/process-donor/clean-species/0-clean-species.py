import json
import os
import re
import requests
import pandas as pd
import random

ip_port_list = [
    "your_ip_port_list" # add more addresses as needed
]

SPECIES_CATEGORIES = [
    "Homo sapiens", "Mus musculus", "Rattus norvegicus", "Sus scrofa", "Gadus morhua"
]


def extract_json_text(text):
    """
    Extract the first JSON array found in the model response.
    """
    pattern = r"\[.*?\]"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
    return []


def send_request(species):
    """
    Send a classification request for a given species and return the result.
    """
    content = f"""
### Task:
Determine which species category the given organism **{species}** belongs to, based on the provided categories.

Categories: {SPECIES_CATEGORIES}

Rules:
1. Select exactly one category from the list.
2. If no match, return ['others'].

Output format:
Always respond as a JSON array, e.g. ["Homo sapiens"].
"""
    data = {
        "model": "gemma2:27b",
        "messages": [{"role": "user", "content": content}],
        "stream": False
    }

    for attempt in range(3):
        ip_port = random.choice(ip_port_list)
        url = f"http://{ip_port}/api/chat"
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                res_json = response.json()
                reply = res_json.get('message', {}).get('content', '')
                categories = extract_json_text(reply)
                if categories:
                    print(f"[{species}] -> {categories}")
                    return species, categories
                else:
                    print(f"No JSON found for {species} (attempt {attempt+1}).")
            else:
                print(f"Request to {ip_port} failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error contacting {ip_port}: {e}")
    # If all attempts fail, classify as others
    print(f"Defaulting to 'others' for {species}")
    return species, ['others']


def save_results(results, batch_num, output_dir):
    """
    Save a batch of results to an Excel file in the output directory.
    """
    df = pd.DataFrame(results, columns=['species', 'categories'])
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"results_batch_{batch_num}.xlsx")
    df.to_excel(filename, index=False)
    print(f"Batch {batch_num} saved to {filename}")
    return batch_num + 1


def load_processed_species(output_dir):
    """
    Load the set of already processed species from existing result files.
    """
    processed = set()
    if not os.path.isdir(output_dir):
        return processed
    for fname in os.listdir(output_dir):
        if fname.startswith('results_batch_') and fname.endswith('.xlsx'):
            path = os.path.join(output_dir, fname)
            try:
                df = pd.read_excel(path)
                processed.update(df['species'].astype(str).tolist())
            except Exception as e:
                print(f"Failed to read {path}: {e}")
    return processed


def main():
    # Determine round number
    round_file = 'round.csv'
    if not os.path.isfile(round_file):
        print("round.csv not found. Exiting.")
        return
    try:
        round_number = int(pd.read_csv(round_file, header=None).iloc[0, 0])
    except Exception as e:
        print(f"Error reading round.csv: {e}")
        return

    input_csv = f"data\donor-meta\species\species_{round_number}.csv"
    output_dir = f"data\donor-meta\species\species_{round_number}"

    if not os.path.isfile(input_csv):
        print(f"Input file {input_csv} not found.")
        return

    df = pd.read_csv(input_csv, encoding='latin1')
    if 'species' not in df.columns:
        print("CSV must have a 'species' column.")
        return

    processed = load_processed_species(output_dir)
    all_species = df['species'].astype(str).tolist()
    to_process = [s for s in all_species if s not in processed]
    print(f"Total: {len(all_species)}, Remaining: {len(to_process)}")
    if not to_process:
        print("No new species to process.")
        return

    batch_size = 100
    batch_num = 1
    results = []

    for sp in to_process:
        results.append(send_request(sp))
        if len(results) >= batch_size:
            batch_num = save_results(results, batch_num, output_dir)
            results.clear()

    if results:
        save_results(results, batch_num, output_dir)

if __name__ == '__main__':
    main()
