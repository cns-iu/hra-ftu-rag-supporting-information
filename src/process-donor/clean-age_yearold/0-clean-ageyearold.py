import json
import os
import re
import requests
import pandas as pd
import random

ip_port_list = [
    "your_ip_port_list" # add more addresses as needed
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


def send_request(age):

    content = f"""
    ### Task: 
    Determine the age category for the given age expression **{age}**, based on the following list of age categories:

    ["<1 year old", "[1 year old, 5 years old)", "[5 years old, 10 years old)", "[10 years old, 15 years old)", "[15 years old, 20 years old)", "[20 years old, 25 years old)","[25 years old, 30 years old)", "[30 years old, 35 years old)","[35 years old, 40 years old)", "[40 years old, 45 years old)","[45 years old, 50 years old)", "[50 years old, 55 years old)","[55 years old, 60 years old)", "[60 years old, 65 years old)","[65 years old, 70 years old)", "[70 years old, 75 years old)","[75 years old, 80 years old)", "[80 years old, 85 years old)","[85 years old, 90 years old)", "[90 years old, 95 years old)","[95 years old, 100 years old)", ">=100 years old"]

    ### Age Range Interpretation:
    - All age ranges use **left-closed, right-open intervals**: **[x years old, y years old)**
    - Meaning:
    - **Include** the left boundary (age ≥ x years)
    - **Exclude** the right boundary (age < y years)
    - Special cases:
    - `<1 year old` includes any age **less than 1 year** (e.g., infants, newborns, months).
    - `>100 years old` includes any age **strictly greater than 100 years**.

    ### Rules:
    1. Only select one age category from the provided list.
    2. If **{age}** does not fit into any of these age categories, output `["others"]`.

    ### Output format:
    Always respond in this format:  
    `["age"]`

    For example:  
    If **{age}** is "12 years old", output `["[10 years old, 15 years old)"]`.  
    If **{age}** is not in the list, output `["others"]`.
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
                    print(f"[{age}] -> {categories}")
                    return age, categories
                else:
                    print(f"No JSON found for {age} (attempt {attempt+1}).")
            else:
                print(f"Request to {ip_port} failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error contacting {ip_port}: {e}")
    # If all attempts fail, classify as others
    print(f"Defaulting to 'others' for {age}")
    return age, ['others']


def save_results(results, batch_num, output_dir):
    """
    Save a batch of results to an Excel file in the output directory.
    """
    df = pd.DataFrame(results, columns=['age', 'categories'])
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"results_batch_{batch_num}.xlsx")
    df.to_excel(filename, index=False)
    print(f"Batch {batch_num} saved to {filename}")
    return batch_num + 1


def load_processed_age(output_dir):
    processed = set()
    if not os.path.isdir(output_dir):
        return processed
    for fname in os.listdir(output_dir):
        if fname.startswith('results_batch_') and fname.endswith('.xlsx'):
            path = os.path.join(output_dir, fname)
            try:
                df = pd.read_excel(path)
                processed.update(df['age'].astype(str).tolist())
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

    input_csv = f"data\donor-meta\age_yearold\age_{round_number}.csv"
    output_dir = f"data\donor-meta\age_yearold\age_{round_number}"

    if not os.path.isfile(input_csv):
        print(f"Input file {input_csv} not found.")
        return

    df = pd.read_csv(input_csv, encoding='latin1')
    if 'age' not in df.columns:
        print("CSV must have a 'age' column.")
        return

    processed = load_processed_age(output_dir)
    all_age = df['age'].astype(str).tolist()
    to_process = [s for s in all_age if s not in processed]
    print(f"Total: {len(all_age)}, Remaining: {len(to_process)}")
    if not to_process:
        print("No new age to process.")
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