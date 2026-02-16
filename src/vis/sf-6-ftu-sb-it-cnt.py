import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial'],
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'axes.linewidth': 0.8,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
    'xtick.major.size': 3,
    'ytick.major.size': 3
})

file_path = r"data\vis-source-data\sf-6-ftu-sb-it-cnt.csv"
df = pd.read_csv(file_path)

df["micro_scaled"] = df["micro_yes_count"] / 1000
df["schema_scaled"] = df["schema_yes_count"] / 1000


fig, ax = plt.subplots(figsize=(7, 7)) 

y_positions = range(len(df))

ax.barh(
    y_positions,
    df["micro_scaled"],
    color="#156082",
    label="#microscopy images"
)

ax.barh(
    y_positions,
    df["schema_scaled"],
    left=df["micro_scaled"],
    color="#e97132",
    label="#schematic images"
)

ax.set_yticks(y_positions)
ax.set_yticklabels(df["ftu"])
ax.invert_yaxis() 

max_total = (df["micro_scaled"] + df["schema_scaled"]).max()
ax.set_xlim(0, max_total * 1.05)

ax.set_xlabel("The number of images (thousand)")
ax.set_ylabel("FTU")

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

ax.legend(frameon=False)

plt.tight_layout()

plt.savefig(r"vis\sf-6-ftu-sb-it.svg", bbox_inches='tight')

plt.close()
