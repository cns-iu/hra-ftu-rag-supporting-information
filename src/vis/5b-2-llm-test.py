import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

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

df = pd.read_csv(r'data\vis-source-data\5b-2-llm-test.csv') 

color_a = '#8dd2c5'
color_b = '#bfbcda'

def clean_axes(ax):
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)


fig, ax = plt.subplots(figsize=(2.5, 2))
ax.bar(df['LLM'], df['Accuracy'], color=color_a, width=0.6)
# ax.set_title('a', loc='left', fontweight='bold')
ax.set_ylabel('Accuracy')
ax.set_xlabel('LLM')
ax.set_ylim(0, 1.0)
ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_xticks(range(len(df['LLM'])))
ax.set_xticklabels(df['LLM'], rotation=45, ha='right')
ax.grid(False)
clean_axes(ax)
plt.tight_layout()
# plt.savefig(r"vis\figures\3b-lvm-accu.png", dpi=600, bbox_inches='tight')
plt.savefig(r"vis\5b-2-llm-accu.svg", bbox_inches='tight')
plt.close()


# 图 b: Avg Response Time
fig, ax = plt.subplots(figsize=(2.5, 2))
ax.bar(df['LLM'], df['Avg Response Time (s)'], color=color_b, width=0.6)
# ax.set_title('b', loc='left', fontweight='bold')
ax.set_ylabel('Avg Response Time (s)')
ax.set_xlabel('LLM')
ax.set_ylim(0, 50)
ax.set_yticks([0, 10, 20, 30, 40, 50])
ax.set_xticks(range(len(df['LLM'])))
ax.set_xticklabels(df['LLM'], rotation=45, ha='right')
ax.grid(False)
clean_axes(ax)
plt.tight_layout()
# plt.savefig(r"vis\4b-2-lvm-time.png", dpi=600, bbox_inches='tight')
plt.savefig(r"vis\4b-2-llm-time.svg", bbox_inches='tight')
plt.close()
