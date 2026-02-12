import pandas as pd
import numpy as np
import re


df1 = pd.read_csv(r"data\donor-meta\ftu-donor-yearold.csv")
df2 = pd.read_csv(r"data\input-data\organ-ftu-uberon.csv")


df1 = df1[df1['unit'].notna() & (df1['unit'].str.strip() != "")].copy()


df1['unit'] = df1['unit'].str.lower()
df1['value_um'] = np.where(
    df1['unit'] == 'mm',
    df1['value'] * 1000,
    df1['value']
)

def parse_lower(tag):
    tag = str(tag).strip()
    if tag.startswith('<'):
        return 0.0
    m = re.match(r'\[(\d+)', tag)
    return float(m.group(1)) if m else np.nan

df1['age_lower'] = df1['age_yearold_tag'].apply(parse_lower)

def map_age_group(lb):
    if pd.isna(lb):
        return np.nan
    if lb < 15:
        return 'young'
    elif lb < 70:
        return 'medium'
    else:
        return 'old'

df1['age_group'] = df1['age_lower'].apply(map_age_group)


df = df2.merge(df1, on='ftu', how='inner')

summary = (
    df
    .groupby(['organ', 'ftu', 'age_group'], as_index=False)
    .agg(
        median_value=('value_um', 'mean'),
        pmcid_count=('pmcid', 'nunique')
    )
)

pivot_median = (
    summary
    .pivot(index=['organ', 'ftu'], columns='age_group', values='median_value')
    .reset_index()
)

pivot_pmcid = (
    summary
    .pivot(index=['organ', 'ftu'], columns='age_group', values='pmcid_count')
    .reset_index()
)

pivot_pmcid = pivot_pmcid.rename(
    columns={'young': 'young-pmcid', 'medium': 'medium-pmcid', 'old': 'old-pmcid'}
)

final = pivot_median.merge(pivot_pmcid, on=['organ', 'ftu'], how='left')

final = final[['organ', 'ftu', 'young', 'medium', 'old', 
               'young-pmcid', 'medium-pmcid', 'old-pmcid']]

final.to_csv(r"data\vis-source-data\6b-sb-yearold.csv", index=False)

print("saved: data\\vis-source-data\\6b-sb-yearold.csv")


#Count for health sample
health_file = r'data\scale-bar\sb-health.csv'
age_file = r'data\donor-meta\ftu-donor-yearold.csv'

df_health = pd.read_csv(health_file, encoding='utf-8-sig')
df_age = pd.read_csv(age_file, encoding='utf-8-sig')

df_health.columns = df_health.columns.str.strip()
df_age.columns = df_age.columns.str.strip()

df1 = df_age.merge(
    df_health[['pmcid', 'graphic']].drop_duplicates(),
    on=['pmcid', 'graphic'],
    how='inner'
)

df2 = pd.read_csv(r"data\input-data\organ-ftu-uberon.csv")


df1 = df1[df1['unit'].notna() & (df1['unit'].str.strip() != "")].copy()


df1['unit'] = df1['unit'].str.lower()
df1['value_um'] = np.where(
    df1['unit'] == 'mm',
    df1['value'] * 1000,
    df1['value']
)

def parse_lower(tag):
    tag = str(tag).strip()
    if tag.startswith('<'):
        return 0.0
    m = re.match(r'\[(\d+)', tag)
    return float(m.group(1)) if m else np.nan

df1['age_lower'] = df1['age_yearold_tag'].apply(parse_lower)

def map_age_group(lb):
    if pd.isna(lb):
        return np.nan
    if lb < 15:
        return 'young'
    elif lb < 70:
        return 'medium'
    else:
        return 'old'

df1['age_group'] = df1['age_lower'].apply(map_age_group)


df = df2.merge(df1, on='ftu', how='inner')

summary = (
    df
    .groupby(['organ', 'ftu', 'age_group'], as_index=False)
    .agg(
        median_value=('value_um', 'mean'),
        pmcid_count=('pmcid', 'nunique')
    )
)

pivot_median = (
    summary
    .pivot(index=['organ', 'ftu'], columns='age_group', values='median_value')
    .reset_index()
)

pivot_pmcid = (
    summary
    .pivot(index=['organ', 'ftu'], columns='age_group', values='pmcid_count')
    .reset_index()
)

pivot_pmcid = pivot_pmcid.rename(
    columns={'young': 'young-pmcid', 'medium': 'medium-pmcid', 'old': 'old-pmcid'}
)

final = pivot_median.merge(pivot_pmcid, on=['organ', 'ftu'], how='left')

final = final[['organ', 'ftu', 'young', 'medium', 'old', 
               'young-pmcid', 'medium-pmcid', 'old-pmcid']]

final.to_csv(r"data\vis-source-data\sf-6a-sb-yearold-health.csv", index=False)



# Count for disease

health_file = r'data\scale-bar\sb-disease.csv'
age_file = r'data\donor-meta\ftu-donor-yearold.csv'

df_health = pd.read_csv(health_file, encoding='utf-8-sig')
df_age = pd.read_csv(age_file, encoding='utf-8-sig')

df_health.columns = df_health.columns.str.strip()
df_age.columns = df_age.columns.str.strip()

df1 = df_age.merge(
    df_health[['pmcid', 'graphic']].drop_duplicates(),
    on=['pmcid', 'graphic'],
    how='inner'
)

df2 = pd.read_csv(r"data\input-data\organ-ftu-uberon.csv")


df1 = df1[df1['unit'].notna() & (df1['unit'].str.strip() != "")].copy()


df1['unit'] = df1['unit'].str.lower()
df1['value_um'] = np.where(
    df1['unit'] == 'mm',
    df1['value'] * 1000,
    df1['value']
)

def parse_lower(tag):
    tag = str(tag).strip()
    if tag.startswith('<'):
        return 0.0
    m = re.match(r'\[(\d+)', tag)
    return float(m.group(1)) if m else np.nan

df1['age_lower'] = df1['age_yearold_tag'].apply(parse_lower)

def map_age_group(lb):
    if pd.isna(lb):
        return np.nan
    if lb < 15:
        return 'young'
    elif lb < 70:
        return 'medium'
    else:
        return 'old'

df1['age_group'] = df1['age_lower'].apply(map_age_group)


df = df2.merge(df1, on='ftu', how='inner')

summary = (
    df
    .groupby(['organ', 'ftu', 'age_group'], as_index=False)
    .agg(
        median_value=('value_um', 'mean'),
        pmcid_count=('pmcid', 'nunique')
    )
)

pivot_median = (
    summary
    .pivot(index=['organ', 'ftu'], columns='age_group', values='median_value')
    .reset_index()
)

pivot_pmcid = (
    summary
    .pivot(index=['organ', 'ftu'], columns='age_group', values='pmcid_count')
    .reset_index()
)

pivot_pmcid = pivot_pmcid.rename(
    columns={'young': 'young-pmcid', 'medium': 'medium-pmcid', 'old': 'old-pmcid'}
)

final = pivot_median.merge(pivot_pmcid, on=['organ', 'ftu'], how='left')

final = final[['organ', 'ftu', 'young', 'medium', 'old', 
               'young-pmcid', 'medium-pmcid', 'old-pmcid']]

final.to_csv(r"data\vis-source-data\sf-6b-sb-yearold-disease.csv", index=False)