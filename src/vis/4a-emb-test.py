import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np


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


df = pd.read_csv(r'data\vis-source-data\4a-emb-test.csv')  


color_a = '#ddaeab'
color_b = '#bfbcda'

def clean_axes(ax):
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

fig, ax = plt.subplots(figsize=(2.5, 2.9))
ax.bar(df['Embedding_model'], df['Embedding_score'], color=color_a, width=0.6)
ax.set_ylabel('Embedding_score')
ax.set_xlabel('Embedding_model')
ax.set_ylim(0.0, 1.0)
ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_xticks(range(len(df['Embedding_model'])))
ax.set_xticklabels(df['Embedding_model'], rotation=45, ha='right')
ax.grid(False)
clean_axes(ax)
plt.tight_layout()
# plt.savefig(r"vis\4a-emb.png", dpi=600, bbox_inches='tight')
plt.savefig(r"vis\4a-emb.svg", bbox_inches='tight')
plt.close()