import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl


file_path = r"data\vis-source-data\6b-itype-ratio.csv" 
df = pd.read_csv(file_path)

mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial'],  
    'font.size': 12,
    'axes.labelsize': 12,
    'axes.titlesize': 10,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'axes.linewidth': 0.5,
    'xtick.major.width': 0.5,
    'ytick.major.width': 0.5,
    'xtick.major.size': 2,
    'ytick.major.size': 2
})


count_columns = [
    "micro_yes_count", "schema_yes_count", "statis_yes_count",
    "d3_yes_count", "chem_yes_count", "math_yes_count"
]


df_filtered = df[["ftu"] + count_columns].copy()
df_filtered["total"] = df_filtered[count_columns].sum(axis=1)


for col in count_columns:
    df_filtered[col] = df_filtered[col] / df_filtered["total"]


df_filtered_sorted = df_filtered
ftu_labels = df_filtered_sorted["ftu"]


colors = {
    "micro_yes_count": "#ace0cf",
    "schema_yes_count": "#8ebcdb",
    "statis_yes_count": "#a79fce",
    "d3_yes_count": "#3d9f3c",
    "chem_yes_count": "#dc7c6e",
    "math_yes_count": "#8a3122"
}

plt.figure(figsize=(10, 10))
bottom = [0] * len(df_filtered_sorted)

for col in count_columns:
    plt.barh(ftu_labels, df_filtered_sorted[col], left=bottom, label=col, color=colors[col])
    bottom = [i + j for i, j in zip(bottom, df_filtered_sorted[col])]

plt.xlabel("Proportion")
plt.ylabel("FTU")
plt.gca().invert_yaxis()
plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x * 100)}%"))
plt.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
plt.tight_layout(rect=[0, 0, 0.85, 1])

# plt.savefig(r"vis\5b-itype-ratio.png", dpi=300, bbox_inches='tight')
plt.savefig(r"vis\6b-itype-ratio.svg", bbox_inches='tight')
