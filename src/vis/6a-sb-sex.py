# import pandas as pd
# import seaborn as sns
# import matplotlib.pyplot as plt
# import matplotlib as mpl
# import textwrap

# # ✅ 全局字体和图形样式设定
# mpl.rcParams.update({
#     'font.family': 'sans-serif',
#     'font.sans-serif': ['Arial'],  
#     'font.size': 10,
#     'axes.labelsize': 10,
#     'axes.titlesize': 10,
#     'xtick.labelsize': 9,
#     'ytick.labelsize': 9,
#     'legend.fontsize': 9,
#     'axes.linewidth': 0.5,
#     'xtick.major.width': 0.5,
#     'ytick.major.width': 0.5,
#     'xtick.major.size': 2,
#     'ytick.major.size': 2
# })

# # ✅ seaborn 使用统一样式 + 继承 matplotlib rcParams
# sns.set_theme(style="whitegrid", rc=mpl.rcParams)

# # ✅ 读取数据
# df = pd.read_csv(r'data\vis-source-data\6a-sb-sex.csv')
# df['value'] = pd.to_numeric(df['value'], errors='coerce')
# df = df.groupby(['ftu', 'sex_tag']).filter(lambda x: x['value'].nunique() > 1)
# df = df[~((df['ftu'] == 'prostate glandular acinus') & (df['sex_tag'] == 'female'))]
# df = df[(df['value'] >= 0) & (df['value'] <= 10000)]

# # ✅ 读取 organ-ftu 映射表，并合并 organ 信息
# organ_map = pd.read_csv(r'data\input-data\organ-ftu-uberon.csv')
# df = df.merge(organ_map[['organ', 'ftu']], on='ftu', how='left')

# # ✅ organ name 换行（避免过长）
# df['organ_wrapped'] = df['organ'].apply(lambda x: "\n".join(textwrap.wrap(x, width=15)))

# # ✅ 获取有序的 ftu 列表：按 organ 分组，组内按 ftu 升序
# ftu_order_df = (
#     df[['organ', 'ftu', 'organ_wrapped']]
#     .drop_duplicates()
#     .sort_values(by=['organ', 'ftu'])
#     .reset_index(drop=True)
# )
# ftu_order = ftu_order_df['ftu'].tolist()

# male_color   = (142/255, 160/255, 204/255)
# female_color = (214/255, 195/255, 223/255)

# # ✅ 设置颜色
# # palette = {'male': '#56B4E9', 'female': '#A569BD'}
# palette = {'male': male_color, 'female': female_color}

# # ✅ 绘图
# plt.figure(figsize=(16, 6))
# ax = sns.violinplot(
#     data=df,
#     x='ftu',
#     y='value',
#     hue='sex_tag',
#     order=ftu_order,
#     hue_order=['male', 'female'],
#     split=False,
#     inner='box',
#     cut=0,
#     scale='width',
#     palette=palette
# )
# ax.legend_.remove()

# # ✅ 坐标轴和标题
# plt.xticks(rotation=45, ha='right')
# plt.xlabel('FTU')
# plt.ylabel('Value (um)')
# plt.ylim(0, 1000)
# # plt.title('Violin Plot Grouped by Organ and FTU')

# # ✅ 添加 organ 分隔虚线 和 顶部 organ 标签
# positions = ftu_order_df.reset_index().groupby('organ_wrapped')['index'].agg(['min', 'max'])
# n = len(ftu_order)

# for organ, row in positions.iterrows():
#     s, e = row['min'], row['max']
#     if e < n - 1:
#         ax.axvline(e + 0.5, color='gray', linestyle='--', linewidth=1)
#     mid = (s + e) / 2
#     ax.text(
#         mid, 1.02, organ,
#         transform=ax.get_xaxis_transform(),
#         ha='center', va='bottom',
#         fontsize=10  # 和你设置的 font.size 一致
#     )

# plt.tight_layout()
# plt.show()


import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import textwrap

# ✅ 全局字体和图形样式设定
mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial'],  
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'axes.linewidth': 0.5,
    'xtick.major.width': 0.5,
    'ytick.major.width': 0.5,
    'xtick.major.size': 2,
    'ytick.major.size': 2
})

# ✅ seaborn 使用统一样式 + 继承 matplotlib rcParams
sns.set_theme(style="whitegrid", rc=mpl.rcParams)

# ✅ 读取数据
df = pd.read_csv(r'data\vis-source-data\6a-sb-sex.csv')
df['value'] = pd.to_numeric(df['value'], errors='coerce')
df = df.groupby(['ftu', 'sex_tag']).filter(lambda x: x['value'].nunique() > 1)
df = df[~((df['ftu'] == 'prostate glandular acinus') & (df['sex_tag'] == 'female'))]
df = df[(df['value'] >= 0) & (df['value'] <= 10000)]

# ✅ 读取 organ-ftu 映射表，并合并 organ 信息
organ_map = pd.read_csv(r'data\input-data\organ-ftu-uberon.csv')
df = df.merge(organ_map[['organ', 'ftu']], on='ftu', how='left')

# ✅ organ name 换行（避免过长）
df['organ_wrapped'] = df['organ'].apply(lambda x: "\n".join(textwrap.wrap(x, width=15)))

# ✅ 获取有序的 ftu 列表：按 organ 分组，组内按 ftu 升序
ftu_order_df = (
    df[['organ', 'ftu', 'organ_wrapped']]
    .drop_duplicates()
    .sort_values(by=['organ', 'ftu'])
    .reset_index(drop=True)
)
ftu_order = ftu_order_df['ftu'].tolist()

male_color   = (142/255, 160/255, 204/255)
female_color = (214/255, 195/255, 223/255)

# ✅ 设置颜色
palette = {'male': male_color, 'female': female_color}

# ✅ 绘图
plt.figure(figsize=(16, 6))
ax = sns.violinplot(
    data=df,
    x='ftu',
    y='value',
    hue='sex_tag',
    order=ftu_order,
    hue_order=['male', 'female'],
    split=False,
    inner='box',
    cut=0,
    scale='width',
    palette=palette
)
ax.legend_.remove()

# ✅ 坐标轴和标题
plt.xticks(rotation=45, ha='right')
plt.xlabel('FTU')
plt.ylabel('Value (µm)')
plt.ylim(0, 1000)

# ✅ 添加 organ 分隔虚线 和 顶部 organ 标签
positions = ftu_order_df.reset_index().groupby('organ_wrapped')['index'].agg(['min', 'max'])
n = len(ftu_order)

for organ, row in positions.iterrows():
    s, e = row['min'], row['max']
    if e < n - 1:
        ax.axvline(e + 0.5, color='gray', linestyle='--', linewidth=1)
    mid = (s + e) / 2
    ax.text(
        mid, 1.02, organ,
        transform=ax.get_xaxis_transform(),
        ha='center', va='bottom',
        fontsize=10
    )

# reference_color = 	(255/255, 140/255, 0/255)
reference_color = (255/255,0/255,0/255)

# ✅ 添加每个 FTU 的 reference-size 圆点
mean_df = pd.read_csv(r'data\vis-source-data\6a-sb-sex-mean.csv')
ref_map = mean_df.set_index('ftu')['reference-size'].to_dict()

for i, ftu in enumerate(ftu_order):
    if ftu in ref_map and pd.notna(ref_map[ftu]):
        ax.plot(i, ref_map[ftu], marker='o', color=reference_color, markersize=4, zorder=5)

for i in range(len(ftu_order)):
    ax.plot([i, i], [0, -10], color='black', linewidth=0.7, clip_on=False)
for spine in ['left', 'bottom', 'top', 'right']:
    ax.spines[spine].set_color('black')
    ax.spines[spine].set_linewidth(0.5)

ax.grid(False)
ax.set_xlim(-0.5, len(ftu_order) - 0.5)
plt.tight_layout()
# plt.show()
plt.savefig(r"vis\6a-sb-sex.svg", bbox_inches='tight')
plt.close()