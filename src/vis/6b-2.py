import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# ---------------------------
# Input data
# ---------------------------
data = [
    ("Kidney","cortical collecting duct",2785.432432,669.0697674,75,15,24,1),
    ("Kidney","descending limb of loop of Henle",1333.212766,1443.867476,2465.454545,18,58,9),
    ("Kidney","inner medullary collecting duct",88.23529412,239.4206897,np.nan,6,12,np.nan),
    ("Kidney","loop of Henle ascending limb thin segment",17500,2849.090909,2500,1,7,1),
    ("Kidney","nephron",565.7530364,144.9237473,44.05263158,51,116,9),
    ("Kidney","outer medullary collecting duct",7229.285714,54,np.nan,4,5,np.nan),
    ("Kidney","renal corpuscle",100,23.26071429,np.nan,2,6,np.nan),
    ("Kidney","thick ascending limb of loop of Henle",1824.366667,1097.59875,8608.571429,13,33,3),
    ("Large Intestine","crypt of Lieberkuhn of large intestine",1694.890411,671.6331624,2232,24,80,8),
    ("Liver","liver lobule",83.17073171,1271.919355,2302.857143,10,29,3),
    ("Lung","alveolus of lung",262.125,467.3058824,161.4375,6,14,1),
    ("Lung","bronchus submucosal gland",1130,108.1527778,661.2222222,2,4,4),
    ("Pancreas","intercalated duct of pancreas",113.3333333,29.82,np.nan,2,4,np.nan),
    ("Pancreas","islet of Langerhans",136.2204724,100.1345,267.5,26,44,4),
    ("Pancreas","pancreatic acinus",148.5643564,257.7069767,112.5,22,52,5),
    ("Prostate Gland","prostate glandular acinus",52.98387097,154.6775,128.3333333,12,33,4),
    ("Skin","epidermal ridge of digit",158.7058824,364.9478114,72.76271186,23,71,10),
    ("Skin","papillary layer of dermis",402.8768657,940.3984099,2235.102273,29,126,25),
    ("Small Intestine","intestinal villus",368.1420233,145.7857143,24.88888889,58,53,5),
    ("Spleen","red pulp of spleen",307.5704225,141.594697,130.0980392,24,68,9),
    ("Spleen","white pulp of spleen",402.0673077,330.2258065,165,16,56,6),
    ("Thymus","thymus lobule",190.5882353,np.nan,35,4,np.nan,1),
]

df = pd.DataFrame(
    data,
    columns=["Organ","FTU","young","medium","old","#young-pmcid","#medium-pmcid","#old-pmcid"]
)

age_cols = ["young", "medium", "old"]
pmcid_cols = ["#young-pmcid", "#medium-pmcid", "#old-pmcid"]
age_to_pmcid = dict(zip(age_cols, pmcid_cols))

# ---------------------------
# Long format for plotting
# ---------------------------
long = df.melt(
    id_vars=["Organ","FTU"],
    value_vars=age_cols,
    var_name="Age",
    value_name="Value"
)

pmcid_map = df.set_index(["Organ","FTU"])[pmcid_cols]
long["PMCID"] = long.apply(
    lambda r: pmcid_map.loc[(r["Organ"], r["FTU"]), age_to_pmcid[r["Age"]]],
    axis=1
)

plot_data = long.dropna(subset=["Value"]).copy()

# ---------------------------
# LOG scaling
#   - Color: log scale on Value
#   - Size: diameter ∝ log(1 + PMCID)
# ---------------------------
vmin = plot_data["Value"].min()
vmax = plot_data["Value"].max()
color_norm = LogNorm(vmin=vmin, vmax=vmax)

max_p = np.nanmax(df[pmcid_cols].values.astype(float))
dmax = 26.0  # max diameter in points (tune if needed)
k = dmax / np.log1p(max_p)

plot_data["diam"] = k * np.log1p(plot_data["PMCID"].astype(float))
plot_data["s"] = plot_data["diam"]**2  # scatter uses area

# ---------------------------
# Positions (increase y spacing by 1.2x)
# ---------------------------
y_spacing = 1.2

df["Label"] = df["Organ"] + " — " + df["FTU"]
labels = df["Label"].tolist()
y_map = {lab: i * y_spacing for i, lab in enumerate(labels)}

plot_data["y"] = (plot_data["Organ"] + " — " + plot_data["FTU"]).map(y_map)
x_map = {"young": 0, "medium": 1, "old": 2}
plot_data["x"] = plot_data["Age"].map(x_map)

# ---------------------------
# Plot
# ---------------------------
n_rows = len(df)
fig_h = max(7, 0.42 * n_rows * y_spacing)  # scale height too
fig_w = 9.5
fig, ax = plt.subplots(figsize=(fig_w, fig_h))

sc = ax.scatter(
    plot_data["x"], plot_data["y"],
    s=plot_data["s"],
    c=plot_data["Value"],
    cmap="Blues",
    norm=color_norm,
    edgecolors="black",
    linewidths=0.4
)

ax.set_xticks([0, 1, 2])
ax.set_xticklabels(["young", "medium", "old"])

ax.set_yticks([i * y_spacing for i in range(n_rows)])
ax.set_yticklabels(labels, fontsize=8)

ax.invert_yaxis()
ax.set_xlim(-0.5, 2.5)
ax.grid(axis="x", linestyle=":", linewidth=0.6)
ax.set_xlabel("Age group")
ax.set_ylabel("")
ax.set_title("Dot-heatmap (log-scaled): color = mean scale bar; circle diameter = #pmcid")

# Colorbar (log scale)
cbar = fig.colorbar(sc, ax=ax, pad=0.02)
cbar.set_label("Mean scale bar (μm, log scale)")

# Size legend
legend_counts = [1, 10, 50, 100, 126]
legend_counts = [c for c in legend_counts if c <= max_p]

handles = []
for c in legend_counts:
    diam = k * np.log1p(c)
    handles.append(ax.scatter([], [], s=diam**2, facecolors="none", edgecolors="black"))

ax.legend(
    handles, [str(int(c)) for c in legend_counts],
    title="# pmcid\n(diameter ∝ log(1+count))",
    loc="upper center",
    bbox_to_anchor=(0.5, -0.06),
    ncol=len(legend_counts),
    frameon=True
)

fig.tight_layout()
plt.savefig("fig7b_dot_heatmap_logscaled_yspacing1p2.png", dpi=300, bbox_inches="tight")
plt.show()
