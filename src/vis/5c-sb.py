import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import matplotlib as mpl


# df = pd.read_csv(r'data\scale-bar\sb-cleaned2.csv')
df = pd.read_csv(r'data\scale-bar\sb-cleaned2.csv\sb-cleaned2.csv')

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

conversion_factors = {
    "m": 1e6,
    "cm": 1e4,
    "mm": 1e3,
    "um": 1,
    "nm": 1e-3,
    "pm": 1e-6,
    "angstrom": 1e-4
}

def is_numeric(s):
    try:
        if ',' in str(s):
            return False
        float(s)
        return True
    except:
        return False


df_numeric = df[df['value_new'].apply(is_numeric) & df['standard_unit'].isin(conversion_factors.keys())].copy()
df_numeric['numeric_value'] = df_numeric['value_new'].astype(float)
df_numeric['length_um'] = df_numeric.apply(lambda row: row['numeric_value'] * conversion_factors[row['standard_unit']], axis=1)
df_numeric = df_numeric[df_numeric['length_um'] > 0]

df_numeric['order'] = df_numeric['length_um'].apply(lambda x: math.floor(math.log10(x)))
df_numeric['rep_length_um'] = df_numeric['order'].apply(lambda o: 10**(o + 0.5))
df_numeric['pmcid_graphic'] = df_numeric.apply(lambda row: (row['pmcid'], row['graphic']), axis=1)

grouped = df_numeric.groupby(['ftu', 'order']).agg({
    'rep_length_um': 'first',
    'pmcid_graphic': pd.Series.nunique
}).reset_index()
grouped.rename(columns={'pmcid_graphic': 'count'}, inplace=True)
grouped = grouped[(grouped['rep_length_um'] >= 1e-4) & (grouped['rep_length_um'] <= 1e7)]

grouped['standard_unit'] = "all"
grouped['value_new'] = grouped['rep_length_um']
output_table = grouped[['ftu', 'standard_unit', 'value_new', 'count']].copy()
output_table.to_csv('output_aggregated.csv', index=False)


ref_order_df = pd.read_csv(r'data\vis-source-data\5a-ftu-pub-img-cnt.csv')
ftu_categories = ref_order_df['ftu'].drop_duplicates().tolist()
ftu_to_num = {ftu: i for i, ftu in enumerate(ftu_categories)}
grouped['ftu_num'] = grouped['ftu'].map(ftu_to_num)

def calculate_size(count, scale=5, exponent=2.46):
    diameter = scale * (np.log(count + 1))**exponent / 50
    return diameter**2

grouped['size'] = grouped['count'].apply(lambda c: calculate_size(c))

pivot_table = grouped.pivot_table(index='rep_length_um', columns='ftu', 
                                   values=['count', 'size'], aggfunc='first')

def format_cell(count, size):
    if pd.isna(count) or pd.isna(size):
        return ""
    return f"{int(count)} ({size:.1f})"

formatted_table = pd.DataFrame(index=pivot_table.index)
for ftu in ftu_categories:
    count_col = pivot_table['count'].get(ftu)
    size_col = pivot_table['size'].get(ftu)
    formatted_table[ftu] = [format_cell(c, s) for c, s in zip(count_col, size_col)]

formatted_table.to_csv(r'data\vis-source-data\5c-output-sb-size-cnt.csv')

min_count = grouped['count'].min()

def size_with_conditional_floor(c, min_size=2):
    return max(calculate_size(c), min_size) if c == min_count else calculate_size(c)

grouped['size'] = grouped['count'].apply(lambda c: size_with_conditional_floor(c, min_size=2))
grouped['log10_length'] = np.log10(grouped['rep_length_um'])

ref_df = pd.read_csv(r'data\vis-source-data\5c-ftu-sb-ref.csv')
ref_df = ref_df[ref_df['size'].apply(is_numeric)]
ref_df['numeric_value'] = ref_df['size'].astype(float)
ref_df['log10_length'] = np.log10(ref_df['numeric_value'])
ref_df['ftu_num'] = ref_df['ftu'].map(ftu_to_num)

ref_df['count'] = 1
ref_df['size_val'] = 100  
pivot_ref = ref_df.pivot_table(index='numeric_value', columns='ftu', values=['count', 'size_val'], aggfunc='sum')

formatted_ref = pd.DataFrame(index=pivot_ref.index)
for ftu in ftu_categories:
    count_col = pivot_ref['count'].get(ftu)
    size_col = pivot_ref['size_val'].get(ftu)
    formatted_ref[ftu] = [format_cell(c, s) for c, s in zip(count_col, size_col)]

formatted_ref.to_csv(r'data\vis-source-data\5c-output-sb-ref-size-cnt.csv')


plt.figure(figsize=(8, 11))
plt.scatter(
    ref_df['log10_length'],
    ref_df['ftu_num'],
    s=100,
    color="#9D3029",
    alpha=0.8,
    edgecolor='none',
    zorder=1
)
plt.scatter(
    grouped['log10_length'],
    grouped['ftu_num'],
    s=grouped['size'],
    alpha=0.4,
    color='blue',
    edgecolor='none',
    zorder=2
)

min_order = int(np.floor(grouped['log10_length'].min()))
max_order = int(np.ceil(grouped['log10_length'].max()))
xticks = list(range(min_order, max_order + 1))
plt.xticks(xticks)
plt.xlabel('log10(Length in um)')
plt.yticks(list(ftu_to_num.values()), list(ftu_to_num.keys()))
plt.ylabel('ftu')
plt.subplots_adjust(left=0.2, right=0.8)

median_count = int(np.median(grouped['count']))
max_count = grouped['count'].max()
rep_counts = [min_count, median_count, max_count]
legend_sizes = [
    max(calculate_size(c), 2) if c == min_count else calculate_size(c)
    for c in rep_counts
]
handles = [plt.scatter([], [], s=size, color='blue', alpha=0.4, edgecolor='none') for size in legend_sizes]
labels = [str(c) for c in rep_counts]

handles.append(plt.Line2D(
    [], [], marker='o',
    linestyle='',
    label='Reference',
    markerfacecolor="#9D3029",
    markeredgecolor='none',
    markersize=8
))
labels.append("Reference")

plt.gca().invert_yaxis()
plt.legend(
    handles,
    labels,
    title="Count",
    scatterpoints=1,
    bbox_to_anchor=(1.05, 1),
    loc='upper left',
    borderaxespad=0.,
    labelspacing=1.3,
    borderpad=0.8
)

plt.subplots_adjust(left=0.3)
# plt.savefig(r"vis\5c-ftu-sb.png", dpi=300, bbox_inches='tight')
plt.savefig(r"vis\5c-ftu-sb.svg", bbox_inches='tight')
# plt.show()
