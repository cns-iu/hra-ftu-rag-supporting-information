# import pandas as pd
# import numpy as np
# import re

# # 1. 读取两个 CSV
# df1 = pd.read_csv(r"data\donor-meta\ftu-donor-yearold.csv")
# df2 = pd.read_csv(r"data\input-data\organ-ftu-uberon.csv")

# # 2. 丢弃 unit 为空或全空白的行
# df1 = df1[df1['unit'].notna() & (df1['unit'].str.strip() != "")].copy()

# # 3. 统一单位到 µm
# df1['unit'] = df1['unit'].str.lower()
# df1['value_um'] = np.where(
#     df1['unit'] == 'mm',
#     df1['value'] * 1000,
#     df1['value']
# )

# # 4. 从 age_yearold_tag 提取下限数值
# def parse_lower(tag):
#     tag = tag.strip()
#     if tag.startswith('<'):
#         return 0.0
#     m = re.match(r'\[(\d+)', tag)
#     return float(m.group(1)) if m else np.nan

# df1['age_lower'] = df1['age_yearold_tag'].apply(parse_lower)

# # 5. 根据下限分组到 young/medium/old
# def map_age_group(lb):
#     if lb < 15:
#         return 'young'
#     elif lb < 70:
#         return 'medium'
#     else:
#         return 'old'

# df1['age_group'] = df1['age_lower'].apply(map_age_group)

# # 6. 按 ftu 做内连接
# df = df2.merge(df1, on='ftu', how='inner')

# # 7. 按 organ, ftu, age_group 分组，计算中位数
# summary = (
#     df
#     .groupby(['organ', 'ftu', 'age_group'], as_index=False)
#     .agg(median_value=('value_um', 'median'))
# )

# # 8. 将 age_group 展开成列：young, medium, old
# pivoted = (
#     summary
#     .pivot(index=['organ', 'ftu'], columns='age_group', values='median_value')
#     .reset_index()
# )

# # 9. 确保列顺序 organ, ftu, young, medium, old
# pivoted = pivoted[['organ', 'ftu', 'young', 'medium', 'old']]

# # 10. 保存到 CSV
# pivoted.to_csv(r"data\vis-source-data\6b-sb-yearold.csv", index=False)

# print("✅ 已将结果保存到 data\\donor-meta\\donor_yearold_summary_cnt.csv")


import pandas as pd
import numpy as np
import re

# 1. 读取两个 CSV
df1 = pd.read_csv(r"data\donor-meta\ftu-donor-yearold.csv")
df2 = pd.read_csv(r"data\input-data\organ-ftu-uberon.csv")

# 2. 丢弃 unit 为空或全空白的行
df1 = df1[df1['unit'].notna() & (df1['unit'].str.strip() != "")].copy()

# 3. 统一单位到 µm
df1['unit'] = df1['unit'].str.lower()
df1['value_um'] = np.where(
    df1['unit'] == 'mm',
    df1['value'] * 1000,
    df1['value']
)

# 4. 从 age_yearold_tag 提取下限数值
def parse_lower(tag):
    tag = str(tag).strip()
    if tag.startswith('<'):
        return 0.0
    m = re.match(r'\[(\d+)', tag)
    return float(m.group(1)) if m else np.nan

df1['age_lower'] = df1['age_yearold_tag'].apply(parse_lower)

# 5. 根据下限分组到 young/medium/old
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

# 6. 按 ftu 做内连接
df = df2.merge(df1, on='ftu', how='inner')

# 7. 按 organ, ftu, age_group 分组，计算中位数 & 不重复 pmcid 数量
summary = (
    df
    .groupby(['organ', 'ftu', 'age_group'], as_index=False)
    .agg(
        median_value=('value_um', 'mean'),
        pmcid_count=('pmcid', 'nunique')
    )
)

# 8. 分别 pivot median 和 pmcid_count
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

# 9. 改列名避免冲突
pivot_pmcid = pivot_pmcid.rename(
    columns={'young': 'young-pmcid', 'medium': 'medium-pmcid', 'old': 'old-pmcid'}
)

# 10. 合并两个 pivot
final = pivot_median.merge(pivot_pmcid, on=['organ', 'ftu'], how='left')

# 11. 确保列顺序 organ, ftu, young, medium, old, young-pmcid, medium-pmcid, old-pmcid
final = final[['organ', 'ftu', 'young', 'medium', 'old', 
               'young-pmcid', 'medium-pmcid', 'old-pmcid']]

# 12. 保存到 CSV
final.to_csv(r"data\vis-source-data\6b-sb-yearold.csv", index=False)

print("✅ 已将结果保存到 data\\vis-source-data\\6b-sb-yearold.csv")
