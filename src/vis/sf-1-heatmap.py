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
    'axes.linewidth': 0.8,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
    'xtick.major.size': 3,
    'ytick.major.size': 3
})

# visualization: age
df = pd.read_csv(r"data\vis-source-data\sf-1a-age.csv")
df = df.set_index("FTU").fillna(0)

plt.figure(figsize=(7, 7))
im = plt.imshow(df.values, cmap="YlGnBu", vmin=0)
plt.imshow(df.values, cmap="YlGnBu", vmin=0)
plt.yticks(range(len(df.index)), df.index)
plt.xticks(range(len(df.columns)), df.columns, rotation=90)
cbar = plt.colorbar(im, label="#Records", shrink=0.6)  
plt.xlabel("Age group")
plt.ylabel("FTU")

plt.tight_layout()
plt.savefig(r"vis\sf-1a-age.svg", bbox_inches='tight')
plt.close()


# visualization: sex
df = pd.read_csv(r"data\vis-source-data\sf-1b-sex.csv")
df = df.set_index("FTU").fillna(0)

plt.figure(figsize=(4.2, 4.2))
im = plt.imshow(df.values, cmap="YlGnBu", vmin=0)
plt.imshow(df.values, cmap="YlGnBu", vmin=0)
plt.yticks(range(len(df.index)), df.index)
plt.xticks(range(len(df.columns)), df.columns, rotation=90)
cbar = plt.colorbar(im, label="#Records", shrink=0.6)  
plt.xlabel("Sex")
plt.ylabel("FTU")

plt.tight_layout()
plt.savefig(r"vis\sf-1b-sex.svg", bbox_inches='tight')
plt.close()

# visualization: BMI
df = pd.read_csv(r"data\vis-source-data\sf-1c-bmi.csv")
df = df.set_index("FTU").fillna(0)

plt.figure(figsize=(4.6, 4.6))
im = plt.imshow(df.values, cmap="YlGnBu", vmin=0)
plt.yticks(range(len(df.index)), df.index)
plt.xticks(range(len(df.columns)), df.columns, rotation=90)
cbar = plt.colorbar(im, label="#Records", shrink=0.6)  
plt.xlabel("BMI")
plt.ylabel("FTU")

plt.tight_layout()
plt.savefig(r"vis\sf-1c-bmi.svg", bbox_inches='tight')
plt.close()


