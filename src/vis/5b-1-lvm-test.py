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


df = pd.read_csv(r'data\vis-source-data\5b-1-lvm-test.csv')  


color_a = '#8dd2c5'
color_b = '#bfbcda'

def clean_axes(ax):
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)


fig, ax = plt.subplots(figsize=(2.5, 2))
ax.bar(df['LVM'], df['Accuracy'], color=color_a, width=0.6)
# ax.set_title('a', loc='left', fontweight='bold')
ax.set_ylabel('Accuracy')
ax.set_xlabel('LVM')
ax.set_ylim(0.7, 1.0)
ax.set_yticks([0.7, 0.8, 0.9, 1.0])
ax.set_xticks(range(len(df['LVM'])))
ax.set_xticklabels(df['LVM'], rotation=45, ha='right')
ax.grid(False)
clean_axes(ax)
plt.tight_layout()
# plt.savefig(r"vis\4b-1-lvm-accu.png", dpi=600, bbox_inches='tight')
plt.savefig(r"vis\5b-1-lvm-accu.svg", bbox_inches='tight')
plt.close()



fig, ax = plt.subplots(figsize=(2.5, 2))
ax.bar(df['LVM'], df['Avg Response Time (s)'], color=color_b, width=0.6)
ax.set_ylabel('Avg Response Time (s)')
ax.set_xlabel('LVM')
ax.set_ylim(0, 10)
ax.set_yticks([0, 5, 10])
ax.set_xticks(range(len(df['LVM'])))
ax.set_xticklabels(df['LVM'], rotation=45, ha='right')
ax.grid(False)
clean_axes(ax)
plt.tight_layout()
# plt.savefig(r"vis\4b-1-lvm-accu.png", dpi=600, bbox_inches='tight')
plt.savefig(r"vis\5b-1-lvm-time.svg", bbox_inches='tight')
plt.close()