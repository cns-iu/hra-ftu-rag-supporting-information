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


def send_request(bmi):

    content = f"""
You are a Body mass index(BMI) classification assistant. Using the following BMI categories:

  • Underweight = BMI < 18.5  
  • Normal weight = BMI 18.5–24.9  
  • Overweight = BMI 25–29.9  
  • Obesity = BMI ≥ 30  

### Task: 
Determine the BMI category for the given BMI expression **{bmi}**, based on the following list of BMI categories:

["Underweight", "Normal weight", "Overweight", "Obesity"]

### Rules:
1. Only select one BMI category from the provided list.
2. If **{bmi}** does not fit into any of these BMI categories, output `["others"]`.

### Output format:
Always respond in this format:  
`["BMI category"]`

For example:  
If **{bmi}** is "17.8", output `["Underweight"]`.  
If **{bmi}** is "24.5", output `["Normal weight"]`.  
If **{bmi}** is not in the list, output `["others"]`.
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
                    print(f"[{bmi}] -> {categories}")
                    return bmi, categories
                else:
                    print(f"No JSON found for {bmi} (attempt {attempt+1}).")
            else:
                print(f"Request to {ip_port} failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error contacting {ip_port}: {e}")
    # If all attempts fail, classify as others
    print(f"Defaulting to 'others' for {bmi}")
    return bmi, ['others']


def save_results(results, batch_num, output_dir):
    """
    Save a batch of results to an Excel file in the output directory.
    """
    df = pd.DataFrame(results, columns=['bmi', 'categories'])
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"results_batch_{batch_num}.xlsx")
    df.to_excel(filename, index=False)
    print(f"Batch {batch_num} saved to {filename}")
    return batch_num + 1


def load_processed_bmi(output_dir):
    processed = set()
    if not os.path.isdir(output_dir):
        return processed
    for fname in os.listdir(output_dir):
        if fname.startswith('results_batch_') and fname.endswith('.xlsx'):
            path = os.path.join(output_dir, fname)
            try:
                df = pd.read_excel(path)
                processed.update(df['bmi'].astype(str).tolist())
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

    input_csv = f"data\donor-meta\bmi\bmi_{round_number}.csv"
    output_dir = f"data\donor-meta\bmi\bmi_{round_number}"

    if not os.path.isfile(input_csv):
        print(f"Input file {input_csv} not found.")
        return

    df = pd.read_csv(input_csv, encoding='latin1')
    if 'bmi' not in df.columns:
        print("CSV must have a 'bmi' column.")
        return

    processed = load_processed_bmi(output_dir)
    all_bmi = df['bmi'].astype(str).tolist()
    to_process = [s for s in all_bmi if s not in processed]
    print(f"Total: {len(all_bmi)}, Remaining: {len(to_process)}")
    if not to_process:
        print("No new bmi to process.")
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