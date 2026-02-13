import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.gridspec import GridSpec
import matplotlib as mpl

# ---------------------------
# Input data
# ---------------------------


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

df = pd.read_csv(r"data\vis-source-data\6b-sb-yearold.csv")

age_cols = ["young", "medium", "old"]
pmcid_cols = ["young-pmcid", "medium-pmcid", "old-pmcid"]
age_to_pmcid = dict(zip(age_cols, pmcid_cols))

# ---------------------------
# Long format
# ---------------------------
long = df.melt(
    id_vars=["organ", "ftu"],
    value_vars=age_cols,
    var_name="Age",
    value_name="Value"
)

pmcid_map = df.set_index(["organ", "ftu"])[pmcid_cols]
long["pmcid"] = long.apply(
    lambda r: pmcid_map.loc[(r["organ"], r["ftu"]), age_to_pmcid[r["Age"]]],
    axis=1
)

plot_data = long.dropna(subset=["Value"]).copy()

# ---------------------------
# LOG scaling
# ---------------------------
vmin = plot_data["Value"].min()
vmax = plot_data["Value"].max()
color_norm = LogNorm(vmin=vmin, vmax=vmax)

max_p = np.nanmax(df[pmcid_cols].values.astype(float))
dmax = 26.0
k = dmax / np.log1p(max_p)

plot_data["diam"] = k * np.log1p(plot_data["pmcid"].astype(float))
plot_data["s"] = plot_data["diam"] ** 2

# ---------------------------
# Positions (FTU on X axis)
# ---------------------------
x_spacing = 1.2

df["Label"] = df["ftu"]
labels = df["Label"].tolist()
x_map = {lab: i * x_spacing for i, lab in enumerate(labels)}

plot_data["x"] = plot_data["ftu"].map(x_map)
y_map = {"young": 0, "medium": 1, "old": 2}
plot_data["y"] = plot_data["Age"].map(y_map)

# ---------------------------
# Figure layout (2:1 ratio)
# ---------------------------
fig_w = max(12, 0.4 * len(df))
fig_h = 5

fig = plt.figure(figsize=(fig_w, fig_h))
gs = GridSpec(2, 1, height_ratios=[2, 1], hspace=0.05)

ax = fig.add_subplot(gs[0])          # Main plot (top)
legend_ax = fig.add_subplot(gs[1])   # Legend area (bottom)
legend_ax.axis("off")

# ---------------------------
# Main scatter plot
# ---------------------------
sc = ax.scatter(
    plot_data["x"], plot_data["y"],
    s=plot_data["s"],
    c=plot_data["Value"],
    cmap="Blues",
    norm=color_norm,
    edgecolors="black",
    linewidths=0.4
)

# Axis formatting
ax.set_yticks([0, 1, 2])
ax.set_yticklabels(["young", "medium", "old"])

ax.set_xticks([i * x_spacing for i in range(len(labels))])
ax.set_xticklabels(labels, rotation=45, ha="right")

ax.set_ylim(-0.5, 2.5)
ax.grid(axis="y", linestyle=":", linewidth=0.6)
ax.set_ylabel("Age group")
ax.set_xlabel("")

# ---------------------------
# Bottom section layout
# ---------------------------

# Create two sub-areas inside bottom panel
gs_bottom = GridSpec(
    1, 2,
    width_ratios=[1, 1],
    left=0.08,
    right=0.95,
    bottom=0.05,
    top=0.30,
    wspace=0.25
)

# ---- Colorbar (left) ----
cax_parent = fig.add_subplot(gs_bottom[0])
cax_parent.axis("off")
cax = cax_parent.inset_axes([0.275, 0.45, 0.6, 0.06])
# cax = fig.add_subplot(gs_bottom[0])
cbar = fig.colorbar(
    sc,
    cax=cax,
    orientation="horizontal"
)
cbar.set_label("Mean scale bar (μm, log scale)")

# ---- Size legend (right) ----
legend_ax2 = fig.add_subplot(gs_bottom[1])
legend_ax2.axis("off")

legend_counts = [1, 50, 126]
legend_counts = [c for c in legend_counts if c <= max_p]

handles = []
for c in legend_counts:
    diam = k * np.log1p(c)
    handles.append(
        legend_ax2.scatter([], [], s=diam**2,
                           facecolors="none",
                           edgecolors="black")
    )

legend_ax2.legend(
    handles,
    [str(int(c)) for c in legend_counts],
    # title="# PMCID (log scale)",
    loc="center",
    ncol=len(legend_counts),
    frameon=True,
    borderpad=1.2,
    columnspacing=1.5,
    handletextpad=1.0
)

pos=ax.get_position()
new_h=pos.height *0.5
ax.set_position([pos.x0, pos.y1 - new_h, pos.width, new_h])

plt.savefig(
    r"vis\6b-sb-yearold.svg",
    dpi=300,
    bbox_inches="tight"
)

plt.close()