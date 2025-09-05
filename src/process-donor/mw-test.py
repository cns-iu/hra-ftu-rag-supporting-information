import pandas as pd
from scipy.stats import mannwhitneyu

# 读取数据
df = pd.read_csv(r"data\vis-source-data\6a-sb-sex.csv")  # 替换为你的路径

# 确保 value 是数值型
df['value'] = pd.to_numeric(df['value'], errors='coerce')

# 结果列表
results = []

# 按 ftu 分组
for ftu, group in df.groupby('ftu'):
    male_vals = group[group['sex_tag'] == 'male']['value'].dropna()
    female_vals = group[group['sex_tag'] == 'female']['value'].dropna()

    # 如果两组都有数据才进行统计
    if len(male_vals) > 0 and len(female_vals) > 0:
        # 计算中位数
        male_median = male_vals.median()
        female_median = female_vals.median()
        # 样本量
        n_male = len(male_vals)
        n_female = len(female_vals)

        # Mann–Whitney U 检验
        try:
            stat, p = mannwhitneyu(male_vals, female_vals, alternative='two-sided')
        except ValueError:
            p = float('nan')  # 完全相同时可能出错

        # male 中位数是否大于 female
        male_gt_female = 1 if male_median > female_median else 0

        results.append({
            'ftu': ftu,
            'male_median': male_median,
            'female_median': female_median,
            'n_male': n_male,
            'n_female': n_female,
            'p_value': p,
            'male_gt_female': male_gt_female
        })

# 转换成 DataFrame 并输出
results_df = pd.DataFrame(results)
results_df.to_csv(r"data\donor-meta\ftu_sex_comparison_mwu.csv", index=False)
