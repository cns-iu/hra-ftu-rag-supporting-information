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


df = pd.read_csv(r'data\vis-source-data\5d-1-sb-test.csv') 


color_a = '#879db6'
color_b = '#bfbcda'

def clean_axes(ax):
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

fig, ax = plt.subplots(figsize=(2.5, 2))
ax.bar(df['LLM'], df['Similarity'], color=color_a, width=0.6)
ax.set_ylabel('Similarity')
ax.set_xlabel('LLM')
ax.set_ylim(0.55, 0.60)
ax.set_yticks([0.55, 0.56, 0.57, 0.58, 0.59, 0.60])
ax.set_xticks(range(len(df['LLM'])))
ax.set_xticklabels(df['LLM'], rotation=45, ha='right')
ax.grid(False)
clean_axes(ax)
plt.tight_layout()
# plt.savefig(r"vis\4d-1-sb-accu.png", dpi=600, bbox_inches='tight')
plt.savefig(r"vis\5d-1-sb-accu.svg", bbox_inches='tight')
plt.close()



fig, ax = plt.subplots(figsize=(2.5, 2))
ax.bar(df['LLM'], df['Avg Response Time (s)'], color=color_b, width=0.6)
ax.set_ylabel('Avg Response Time (s)')
ax.set_xlabel('LLM')
ax.set_ylim(0, 30)
ax.set_yticks([0, 10, 20, 30])
ax.set_xticks(range(len(df['LLM'])))
ax.set_xticklabels(df['LLM'], rotation=45, ha='right')
ax.grid(False)
clean_axes(ax)
plt.tight_layout()
# plt.savefig(r"vis\4d-1-sb-time.png", dpi=600, bbox_inches='tight')
plt.savefig(r"vis\5d-1-sb-time.svg", bbox_inches='tight')
plt.close()
