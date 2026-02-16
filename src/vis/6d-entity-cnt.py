import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl


file_path = r'data\vis-source-data\6d-entity-cnt.csv'  
df = pd.read_csv(file_path)

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


df['#entities'] = pd.to_numeric(df['#entities'], errors='coerce')


plt.figure(figsize=(5, 10))
plt.barh(df['ftu'], df['#entities'], color='#a58db3')
plt.xlabel('#entities')
plt.ylabel('ftu')
plt.gca().invert_yaxis()
plt.tight_layout()
# plt.savefig(r"vis\5d-entity-cnt.png", dpi=600, bbox_inches='tight')
plt.savefig(r"vis\6d-entity-cnt.svg", bbox_inches='tight')
plt.close()
