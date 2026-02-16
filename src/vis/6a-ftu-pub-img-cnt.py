import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
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


df = pd.read_csv(r"data\vis-source-data\6a-ftu-pub-img-cnt.csv")

df = df[::-1].reset_index(drop=True)

ftus = df['ftu']
pmcid_counts = df['pmcid']
image_counts = df['image']
y = np.arange(len(ftus))
height = 0.4


pmcid_ticks = [i * 1e4 for i in range(7)]   
image_ticks = [i * 1e5 for i in range(8)]   


fig, ax1 = plt.subplots(figsize=(5, 10))

# left x：PMCID
bars1 = ax1.barh(y - height/2, pmcid_counts, height, label='PMCID', color="#8ea0cc")
ax1.set_xlabel(r'Number of publications ($\times 10^4$)', color="#000000")
ax1.tick_params(axis='x', labelcolor="#000000", labelsize=10)
ax1.set_yticks(y)
ax1.set_yticklabels(ftus, ha='right')
ax1.set_xticks(pmcid_ticks)
ax1.set_xticklabels([str(int(i / 1e4)) for i in pmcid_ticks])
ax1.set_xlim(0, 6 * 1e4)
ax1.grid(False)
ax1.spines['bottom'].set_visible(True)

# right x ：Image
ax2 = ax1.twiny()
bars2 = ax2.barh(y + height/2, image_counts, height, label='Image', color="#ccb4d7", alpha=0.8)
ax2.set_xlabel(r'Number of images ($\times 10^5$)', color="#000000", labelpad=20)
ax2.tick_params(axis='x', labelcolor="#000000", labelsize=10)
ax2.set_xticks(image_ticks)
ax2.set_xticklabels([str(int(i / 1e5)) for i in image_ticks])
ax2.set_xlim(0, 7 * 1e5)
ax2.grid(False)
ax2.spines['top'].set_visible(True)

plt.legend([bars1[0], bars2[0]], ['#Publications', '#Images'],
           loc='center left', bbox_to_anchor=(1.02, 0.5), frameon=False)


ax1.invert_yaxis()
ax2.invert_yaxis()

plt.subplots_adjust(left=0.4, right=0.75)
# plt.savefig(r"vis\5a-ftu-pub-img-cnt.png", dpi=300, bbox_inches='tight')
plt.savefig(r"vis\6a-ftu-pub-img-cnt.svg", bbox_inches='tight')
