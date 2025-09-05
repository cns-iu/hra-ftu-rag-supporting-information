import requests
import pandas as pd
import openpyxl  

def get_related_terms(uberon_id, api_key):
    base_url = "https://data.bioontology.org/search"
    params = {
        'q': uberon_id,
        'apikey': api_key,
        'include': 'prefLabel,synonym,definition',
        'display_context': 'false'
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} for {uberon_id}")
        return None


input_csv = 'data/input-data/organ-ftu-uberon.csv'
api_key   = "your_api_key"  

labels_to_remove = {
    "Uberon",
    "UBERON Terminology",
    "UBERON: anatomical entity",
    "anatomical entity (from UBERON)"
}


df_csv = pd.read_csv(input_csv)


all_data = []

for _, row in df_csv.iterrows():
    uberon_id = row['uberon_id']
    print("Querying", uberon_id)
    related = get_related_terms(uberon_id, api_key)
    if not related:
        continue

    for item in related.get('collection', []):
        pref = item.get('prefLabel', 'N/A')
        if pref in labels_to_remove:
            continue
        syn  = ", ".join(item.get('synonym', []))
        defi = item.get('definition', ['N/A'])[0]
        src  = item.get('links', {}).get('ontology', 'N/A')

        all_data.append({
            'Uberon ID':       uberon_id,
            'Preferred Label': pref,
            'Synonyms':        syn,
            'Definition':      defi,
            'Source Ontology': src
        })
        print("  →", pref)


df_out = pd.DataFrame(all_data).drop_duplicates(
    subset=['Uberon ID', 'Preferred Label', 'Synonyms', 'Definition', 'Source Ontology']
)

output_file = 'data/input-data/ftu-description-from-bioportal.csv'
df_out.to_csv(output_file, index=False)
print(f"All results have been saved to {output_file} ({len(df_out)} records in total)")
