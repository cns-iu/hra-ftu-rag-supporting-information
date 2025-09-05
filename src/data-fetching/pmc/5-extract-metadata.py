import json
import os
import re

import pandas as pd
from multiprocessing import Pool

from bs4 import BeautifulSoup
from clickhouse_driver import Client

ch_host = 'your_ch_host'
database = 'hra_rag_ftu'
# Initialize the global client
client = Client(
    host=ch_host,
    port=9000,
    user='your_username',
    password='your_password',
    database=database
)


def insert_ftu_pub_pmc(batch_data):
    # Format the data into a list of tuples
    records = [
        (row['pmcid'], row['figid'], row['label'], row['graphic'], row['caption'], row['file_path'])
        for _, row in batch_data.iterrows()
    ]

    insert_query = """
        INSERT INTO ftu_pub_pmc (pmcid, figid, label, graphic, caption, file_path) 
        VALUES
    """

    client.execute(insert_query, records)
    print(f"Finished inserting {len(records)} records.")


def create_tables():
    create_table_query = """
        CREATE TABLE IF NOT EXISTS ftu_pub_pmc (
            pmcid String,
            figid String,
            label String,
            graphic String,
            caption String,
            ref_text String,
            file_path String
        ) ENGINE = MergeTree()
        ORDER BY pmcid;
    """
    client.execute(create_table_query)

    create_table_query = """
        CREATE TABLE IF NOT EXISTS publication_summary (
            pmcid String,
            article_title String,
            pmid String,
            doi String,
            abstract String,
            pub_year String,
            journal_title String,
            file_path String
        ) ENGINE = MergeTree()
        ORDER BY pmcid;
    """
    client.execute(create_table_query)

    create_table_query = """
            CREATE TABLE IF NOT EXISTS publication_subject (
                pmcid String,
                subject String,
                group_type String,

                file_path String
            ) ENGINE = MergeTree()
            ORDER BY pmcid;
        """
    client.execute(create_table_query)

    create_table_query = """
            CREATE TABLE IF NOT EXISTS publication_authors (
                pmcid String,
                surname String,
                given_names String,
                email String,
                file_path String
            ) ENGINE = MergeTree()
            ORDER BY pmcid;
        """
    client.execute(create_table_query)

    create_table_query = """
            CREATE TABLE IF NOT EXISTS image_refs (
                pmcid String,
                rid String,
                ref_type String,
                ref_xml String,
                ref_text String,
                file_path String
            ) ENGINE = MergeTree()
            ORDER BY pmcid;
        """
    client.execute(create_table_query)

    create_table_query = """
CREATE TABLE IF NOT EXISTS img_fulltext
(
    pmcid String,
    pid String,
    ref_xml String,
    ref_text String,
    version DateTime DEFAULT now(), 
    PRIMARY KEY (pmcid, pid)
) 
ENGINE = ReplacingMergeTree(version)
ORDER BY (pmcid, pid);

        """
    client.execute(create_table_query)

    print("Tables created successfully.")


def get_publication_summary(file_path):
    pmcid = os.path.basename(os.path.dirname(file_path))
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_content = file.read()

    soup = BeautifulSoup(xml_content, features="lxml-xml")


    article_title = soup.find('title-group').find("article-title").text if soup.find('title-group') and soup.find(
        'title-group').find("article-title") else ""
    pmid = soup.find("article-id", {"pub-id-type": "pmid"}).text if soup.find("article-id",
                                                                              {"pub-id-type": "pmid"}) else ""
    doi = soup.find("article-id", {"pub-id-type": "doi"}).text if soup.find("article-id",
                                                                            {"pub-id-type": "doi"}) else ""
    # abstract = soup.find("abstract", {"abstract-type": "toc"}).text.strip() if soup.find("abstract", {"abstract-type": "toc"}) else ""
    abstract = str(soup.find("abstract")) if soup.find("abstract") else ""


    pub_types = ["ppub", "epub", "pmc-release"]
    pub_year = ""

    for pub_type in pub_types:
        pub_date = soup.find("pub-date", {"pub-type": pub_type})
        if pub_date and pub_date.find("year"):
            pub_year = pub_date.find("year").text
            break

    journal_title = soup.find("journal-title").text if soup.find("journal-title") else ""

    extracted_data = {
        "pmcid": pmcid,
        "article_title": article_title,
        "pmid": pmid,
        "doi": doi,
        "abstract": abstract,
        "pub_year": pub_year,
        "journal_title": journal_title,
        "file_path": file_path,
    }
    # print(extracted_data)
    return [extracted_data]


def get_xref_info(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_content = file.read()
    pmcid = os.path.basename(os.path.dirname(file_path))
    xref_list = []

    try:
        soup = BeautifulSoup(xml_content, features="lxml-xml")
        p_results = soup.find_all('p')
        for p in p_results:
            xref_rs = p.find_all('xref')
            if xref_rs:
                for xref in xref_rs:
                    ref_type = xref.get('ref-type','')  
                    rid = xref.get('rid','')  

                    xref_list.append(
                        {
                            'rid': rid,
                            'ref_type': ref_type,
                            'ref_xml': str(p),
                            'ref_text': p.text,
                            'pmcid': pmcid,
                            'file_path': file_path
                        }
                    )

        if xref_list:
            insert_image_refs(xref_list)
        # return f"Success: {file_path}"
    except Exception as e:
        print( f"Error processing {file_path}: {e}")

def insert_image_refs(records):
    try:
        client = Client(
            host=ch_host,
            port=9000,
            user='default',
            password='kyx321',
            database=database
        )
        
        insert_query = """
                INSERT INTO image_refs (pmcid, rid, ref_type, ref_xml, ref_text, file_path) 
                VALUES
            """
        
        record_values = [
            (record['pmcid'], record['rid'], record['ref_type'], record['ref_xml'], record['ref_text'],
             record['file_path'])
            for record in records
        ]
        
        client.execute(insert_query, record_values)
    except Exception as e:
        print(f"Database insert failed: {e}")


def process_image_refs(file_paths):
    with Pool(50) as pool:
        results = pool.map(get_xref_info, file_paths)

    print("Publication summary processing completed.")


def get_publication_authors(file_path):
    pmcid = os.path.basename(os.path.dirname(file_path))
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_content = file.read()

    soup = BeautifulSoup(xml_content, features="lxml-xml")

    
    authors = []
    contribs = soup.find_all('contrib')

    for contrib in contribs:
        
        name_tag = contrib.find('name')
        if name_tag:
            surname = name_tag.find('surname').text if name_tag.find('surname') else ''
            given_names = name_tag.find('given-names').text if name_tag.find('given-names') else ''
        else:
            surname = ''
            given_names = ''

        
        email = contrib.find('email').text if contrib.find('email') else ''

        
        author_info = {
            'surname': surname,
            'given_names': given_names,
            'email': email,
            'pmcid': pmcid,
            'file_path': file_path,
        }

        authors.append(author_info)
    return authors


def insert_publication_authors(batch_data):
    records = [
        (
            row['pmcid'], row['surname'], row['given_names'], row['email'], row['file_path']
        )
        for _, row in batch_data.iterrows()
    ]

    insert_query = """
        INSERT INTO publication_authors (pmcid, surname, given_names,email, file_path) 
        VALUES
    """

    client.execute(insert_query, records)
    print(f"Finished inserting {len(records)} records.")


def get_publication_subject(file_path):
    pmcid = os.path.basename(os.path.dirname(file_path))
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_content = file.read()

    soup = BeautifulSoup(xml_content, features="lxml-xml")
    # Adjusted function to ensure correct handling of XML structure
    def extract_subjects_fixed(subj_group, subj_type):
        """Recursive extraction of subject content with corrected structure."""
        results = []
        # Direct subjects within the current subj-group
        direct_subjects = subj_group.find_all("subject", recursive=False)
        for subject in direct_subjects:
            results.append((subj_type, subject.get_text(strip=True)))

        # Child subj-groups within the current subj-group
        child_groups = subj_group.find_all("subj-group", recursive=False)
        for child_group in child_groups:
            results.extend(extract_subjects_fixed(child_group, subj_type))

        return results

    results = []
    subjects = []
    for top_subj_group in soup.find_all("subj-group", attrs={"subj-group-type": True}, recursive=True):
        subj_type = top_subj_group["subj-group-type"]
        results.extend(extract_subjects_fixed(top_subj_group, subj_type))

    
    unique_results = list(set(results))

    for subj_type, subject in unique_results:
        subjects.append({
            "group_type": subj_type,
            "subject": subject,
            'pmcid': pmcid,
            'file_path': file_path,
        })
    return subjects


def insert_publication_subject(batch_data):
    records = [
        (
            row['pmcid'], row['group_type'], row['subject'], row['file_path']
        )
        for _, row in batch_data.iterrows()
    ]

    insert_query = """
        INSERT INTO publication_subject (pmcid, group_type, subject, file_path) 
        VALUES
    """

    client.execute(insert_query, records)
    print(f"Finished inserting {len(records)} records.")


def insert_publication_summary(batch_data):
    records = [
        (
            row['pmcid'], row['article_title'], row['pmid'], row['doi'], row['abstract'], row['pub_year'],
            row['journal_title'], row['file_path']
        )
        for _, row in batch_data.iterrows()
    ]

    insert_query = """
        INSERT INTO publication_summary (pmcid, article_title, pmid, doi, abstract, pub_year, journal_title,file_path) 
        VALUES
    """

    client.execute(insert_query, records)
    print(f"Finished inserting {len(records)} records.")


def get_fig_info(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_content = file.read()

    soup = BeautifulSoup(xml_content, features="lxml-xml")

    fig_results = soup.find_all("fig")
    data = []

    if fig_results:
        for fig in fig_results:
            pmcid = os.path.basename(os.path.dirname(file_path))
            figid = fig.get("id", "")
            label = fig.find("label").get_text(strip=True) if fig.find("label") else ""
            graphic_elem = fig.find("graphic")
            graphic = graphic_elem["xlink:href"] if graphic_elem and "xlink:href" in graphic_elem.attrs else ""

            caption_elem = fig.find("caption")
            caption = caption_elem.get_text(separator=" ", strip=True) if caption_elem else ""

            data.append({
                "pmcid": pmcid,
                "figid": figid,
                "label": label,
                "graphic": graphic,
                "caption": caption,
                "file_path":file_path
            })

    else:
        data.append({
            "pmcid": '',
            "file_path": file_path,
            "figid": '',
            "label": '',
            "graphic": '',
            "caption": '',
        })
    return data


def process_nxml_files_in_directory(root_dir):
    output_file = "nxml_total.csv"

    if os.path.exists(output_file):
        print(f"{output_file} already exists. Skipping directory processing.")
        return pd.read_csv(output_file)['file_path'].tolist()

    file_paths = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith(".nxml"):
                file_paths.append(os.path.join(dirpath, file))

    total_files = len(file_paths)
    print(f"Total files to process: {total_files}")

    # Save file paths to a CSV
    pd.DataFrame({'file_path': file_paths}).to_csv(output_file, index=False)
    print(f"File paths saved to {output_file}.")

    return file_paths


def process_ftu(file_paths):
    with Pool(200) as pool:
        results = pool.map(get_fig_info, file_paths)

    all_data = [item for sublist in results for item in sublist]
    df = pd.DataFrame(all_data)

    batch_size = 1000
    for start in range(0, len(df), batch_size):
        batch_data = df.iloc[start:start + batch_size]
        insert_ftu_pub_pmc(batch_data)
    print("FTU processing completed.")


def process_publication_summary(file_paths):
    with Pool(500) as pool:
        results = pool.map(get_publication_summary, file_paths)

    all_data = [item for sublist in results for item in sublist]
    df = pd.DataFrame(all_data)

    batch_size = 1000
    for start in range(0, len(df), batch_size):
        batch_data = df.iloc[start:start + batch_size]
        insert_publication_summary(batch_data)
    print("Publication summary processing completed.")


def process_publication_subject(file_paths):
    with Pool(500) as pool:
        results = pool.map(get_publication_subject, file_paths)

    all_data = [item for sublist in results for item in sublist]
    df = pd.DataFrame(all_data)

    batch_size = 1000
    for start in range(0, len(df), batch_size):
        batch_data = df.iloc[start:start + batch_size]
        insert_publication_subject(batch_data)
    print("Publication summary processing completed.")


def process_publication_authors(file_paths):
    with Pool(500) as pool:
        results = pool.map(get_publication_authors, file_paths)

    all_data = [item for sublist in results for item in sublist]
    df = pd.DataFrame(all_data)

    batch_size = 1000
    for start in range(0, len(df), batch_size):
        batch_data = df.iloc[start:start + batch_size]
        insert_publication_authors(batch_data)
    print("Publication summary processing completed.")


def process_img_fulltext(file_paths):
    with Pool(500) as pool:
        results = pool.map(get_img_fulltext, file_paths)

    all_data = [item for sublist in results for item in sublist]
    df = pd.DataFrame(all_data)

    batch_size = 1000
    for start in range(0, len(df), batch_size):
        batch_data = df.iloc[start:start + batch_size]
        insert_img_fulltext(batch_data)
    print("Publication summary processing completed.")


def get_img_fulltext(file_path):
    pmcid = os.path.basename(os.path.dirname(file_path))
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_content = file.read()
    results = []

    soup = BeautifulSoup(xml_content, features="lxml-xml")


    body_tag = soup.find("body")
    if  body_tag==None:
        results.append({
            "pid": '',
            "pmcid": pmcid,
            "ref_xml": '',
            "ref_text": ''
        })
        return results


    p_tags = body_tag.find_all("p")



    for p in p_tags:
        pid = p.get("id")
        if pid and pid.startswith("Par"):
            ref_xml = str(p)  
            ref_text = p.get_text(strip=True)  
            results.append({
                "pid": pid,
                "pmcid": pmcid,
                "ref_xml": ref_xml,
                "ref_text": ref_text
            })
    return results


def insert_img_fulltext(batch_data):
    records = [
        (
            row['pmcid'], row['pid'], row['ref_xml'], row['ref_text']
        )
        for _, row in batch_data.iterrows()
    ]

    insert_query = """
        INSERT INTO img_fulltext (pmcid, pid, ref_xml,ref_text) 
        VALUES
    """

    client.execute(insert_query, records)
    print(f"Finished inserting {len(records)} records.")


if __name__ == "__main__":
    # get_publication_subject(r'C:\Users\Administrator\Downloads\pone.0282775.nxml')
    root_directory = r"data\input-data\ftu-pub-pmc"
    create_tables()
    file_paths = process_nxml_files_in_directory(root_directory)

    process_img_fulltext(file_paths)
    process_ftu(file_paths)
    process_publication_summary(file_paths)
    process_image_refs(file_paths)
    process_publication_authors(file_paths)
    process_publication_subject(file_paths)
    process_publication_summary(file_paths)
