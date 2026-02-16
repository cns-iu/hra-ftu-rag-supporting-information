import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import textwrap

sex_file = r'data\vis-source-data\6a-sb-sex.csv'
health_file = r'data\scale-bar\sb-health.csv'
output_file = r'data\vis-source-data\sf-5a-sb-sex-health.csv'

df_sex = pd.read_csv(sex_file, encoding='utf-8-sig')
df_health = pd.read_csv(health_file, encoding='utf-8-sig')

df_sex.columns = df_sex.columns.str.strip()
df_health.columns = df_health.columns.str.strip()

health_keys = set(zip(df_health['pmcid'], df_health['graphic']))

df_filtered = df_sex[
    df_sex.apply(lambda row: (row['pmcid'], row['graphic']) in health_keys, axis=1)
]

df_filtered.to_csv(output_file, index=False)



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

sns.set_theme(style="whitegrid", rc=mpl.rcParams)

df = pd.read_csv(r'data\vis-source-data\sf-7a-sb-sex-health.csv')
df['value'] = pd.to_numeric(df['value'], errors='coerce')
df = df.groupby(['ftu', 'sex_tag']).filter(lambda x: x['value'].nunique() > 1)
df = df[~((df['ftu'] == 'prostate glandular acinus') & (df['sex_tag'] == 'female'))]
df = df[(df['value'] >= 0) & (df['value'] <= 10000)]

organ_map = pd.read_csv(r'data\input-data\organ-ftu-uberon.csv')
df = df.merge(organ_map[['organ', 'ftu']], on='ftu', how='left')

df['organ_wrapped'] = df['organ'].apply(lambda x: "\n".join(textwrap.wrap(x, width=15)))

ftu_order_df = (
    df[['organ', 'ftu', 'organ_wrapped']]
    .drop_duplicates()
    .sort_values(by=['organ', 'ftu'])
    .reset_index(drop=True)
)
ftu_order = ftu_order_df['ftu'].tolist()

male_color   = (142/255, 160/255, 204/255)
female_color = (214/255, 195/255, 223/255)

palette = {'male': male_color, 'female': female_color}

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

plt.xticks(rotation=45, ha='right')
plt.xlabel('FTU')
plt.ylabel('Scale bar (µm)')
plt.ylim(0, 1000)

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
plt.savefig(r"vis\sf-7a-sb-sex-health.svg", bbox_inches='tight')
plt.close()