import pandas as pd

# 读取 CSV 文件
df = pd.read_csv(r"data\donor-meta\ftu-donor-cnt.csv", encoding='gbk')  # 按需更改编码

# 筛选出 Homo sapiens
df = df[df['species_tag'] == 'Homo sapiens']

# ✅ 标准化 sex_tag
def normalize_sex_tag(x):
    if pd.isna(x):
        return x
    elif x.lower() in ['male', 'female']:
        return x.lower()
    else:
        return 'others'

df['sex_tag'] = df['sex_tag'].apply(normalize_sex_tag)

# ✅ 分组统计 donor_record_count 的总和
grouped = (
    df.groupby(
        ['ftu', 'species_tag', 'age_tag', 'sex_tag', 'bmi_tag', 'age_yearold_tag'],
        dropna=False
    )
    .agg(total_donor_record_count=('donor_record_count', 'sum'))
    .reset_index()
)

# ✅ 保存为 CSV
grouped.to_csv(r"data\donor-meta\homo_sapiens_summary_cnt.csv", index=False)
