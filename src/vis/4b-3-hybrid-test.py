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


df = pd.read_csv(r'data\vis-source-data\4b-3-hybrid-test.csv')  


color_a = '#8dd2c5'
color_b = '#bfbcda'

def clean_axes(ax):
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)


fig, ax = plt.subplots(figsize=(2.5, 2.3))
ax.bar(df['Model'], df['Accuracy'], color=color_a, width=0.6)
ax.set_ylabel('Accuracy')
ax.set_xlabel('Model')
ax.set_ylim(0.88, 0.92)
ax.set_yticks([0.88, 0.89, 0.90, 0.91, 0.92])
ax.set_xticks(range(len(df['Model'])))
ax.set_xticklabels(df['Model'], rotation=45, ha='right')
ax.grid(False)
clean_axes(ax)
plt.tight_layout()
# plt.savefig(r"vis\4b-3-hybrid-accu.png", dpi=600, bbox_inches='tight')
plt.savefig(r"vis\4b-3-hybrid-accu.svg", bbox_inches='tight')
plt.close()




fig, ax = plt.subplots(figsize=(2.5, 2.3))
ax.bar(df['Model'], df['Avg Response Time (s)'], color=color_b, width=0.6)
ax.set_ylabel('Avg Response Time (s)')
ax.set_xlabel('Model')
ax.set_ylim(0, 250)
ax.set_yticks([0, 50, 100, 150, 200, 250])
ax.set_xticks(range(len(df['Model'])))
ax.set_xticklabels(df['Model'], rotation=45, ha='right')
ax.grid(False)
clean_axes(ax)
plt.tight_layout()
# plt.savefig(r"vis\4b-3-hybrid-time.png", dpi=600, bbox_inches='tight')
plt.savefig(r"vis\4b-3-hybrid-time.svg", bbox_inches='tight')
plt.close()
