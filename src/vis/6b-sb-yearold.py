# # import pandas as pd
# # import numpy as np
# # import matplotlib.pyplot as plt
# # import matplotlib as mpl

# # mpl.rcParams.update({
# #     'font.family': 'sans-serif',
# #     'font.sans-serif': ['Arial'],  
# #     'font.size': 10,
# #     'axes.labelsize': 10,
# #     'axes.titlesize': 10,
# #     'xtick.labelsize': 9,
# #     'ytick.labelsize': 9,
# #     'legend.fontsize': 9,
# #     'axes.linewidth': 0.5,
# #     'xtick.major.width': 0.5,
# #     'ytick.major.width': 0.5,
# #     'xtick.major.size': 2,
# #     'ytick.major.size': 2
# # })

# # df = pd.read_csv(r'data\vis-source-data\6b-sb-yearold.csv')

# # def pick_linestyle(org):
# #     if org == 'Kidney':
# #         return '--'
# #     elif org in ('Pancreas', 'Skin'):
# #         return ':'
# #     else:
# #         return '-'

# # df['linestyle'] = df['organ'].apply(pick_linestyle)

# # color_mapping = {}
# # for ls, sub in df.groupby('linestyle'):
# #     ftus = sub['ftu'].unique()
# #     palette = plt.cm.tab10(np.linspace(0, 1, len(ftus)))
# #     color_mapping[ls] = dict(zip(ftus, palette))

# # fig, ax = plt.subplots(figsize=(10, 6))
# # fig.subplots_adjust(right=0.75)
# # x = ['young', 'medium', 'old']

# # for _, row in df.iterrows():
# #     ls = row['linestyle']
# #     ftu = row['ftu']
# #     color = color_mapping[ls][ftu]

# #     # y 值（数值）
# #     # y = [row['young'], row['medium'], row['old']]
# #     # ax.plot(x, y, linestyle=ls, color=color, linewidth=2, label=ftu)
# #     y = [row['young'], row['medium'], row['old']]
# #     mask = np.isfinite(y)  # 只保留不是 NaN 的位置
# #     ax.plot(np.array(x)[mask], np.array(y)[mask],
# #         linestyle=ls, color=color, linewidth=2, label=ftu)

# #     # 对应 pmcid 数量
# #     pmcids = [row['young-pmcid'], row['medium-pmcid'], row['old-pmcid']]

# #     # 画散点，大小与 pmcid 成正比
# #     ax.scatter(x, y, s=np.array(pmcids) * 2,  # 这里调整比例因子 20 可调
# #                facecolors='none', edgecolors=color, linewidths=1.5, zorder=3)

# # ax.set_yscale('log')
# # ax.set_xlabel('Age group')
# # ax.set_ylabel('Mean scale bar (µm)')
# # ax.set_ylim(1, 100000)

# # ftu_order = list(dict.fromkeys(df['ftu']))  
# # handles, labels = ax.get_legend_handles_labels()
# # ordered = [(handles[labels.index(ftu)], ftu) for ftu in ftu_order if ftu in labels]
# # if ordered:
# #     ordered_handles, ordered_labels = zip(*ordered)
# #     ax.legend(ordered_handles, ordered_labels,
# #               loc='center left', bbox_to_anchor=(1.02, 0.5),
# #               title='FTU', fontsize='small', ncol=1)
# # else:
# #     ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5),
# #               title='FTU', fontsize='small', ncol=1)

# # plt.tight_layout()
# # plt.show()
# # # plt.savefig(r"vis\6b-sb-yearold-v2.svg", bbox_inches='tight')
# # # plt.close()


# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib as mpl
# from matplotlib.lines import Line2D

# mpl.rcParams.update({
#     'font.family': 'sans-serif',
#     'font.sans-serif': ['Arial'],  
#     'font.size': 10,
#     'axes.labelsize': 10,
#     'axes.titlesize': 10,
#     'xtick.labelsize': 9,
#     'ytick.labelsize': 9,
#     'legend.fontsize': 9,
#     'axes.linewidth': 0.5,
#     'xtick.major.width': 0.5,
#     'ytick.major.width': 0.5,
#     'xtick.major.size': 2,
#     'ytick.major.size': 2
# })

# df = pd.read_csv(r'data\vis-source-data\6b-sb-yearold.csv')

# def pick_linestyle(org):
#     if org == 'Kidney':
#         return '--'
#     elif org in ('Pancreas', 'Skin'):
#         return ':'
#     else:
#         return '-'

# df['linestyle'] = df['organ'].apply(pick_linestyle)

# color_mapping = {}
# for ls, sub in df.groupby('linestyle'):
#     ftus = sub['ftu'].unique()
#     palette = plt.cm.tab10(np.linspace(0, 1, len(ftus)))
#     color_mapping[ls] = dict(zip(ftus, palette))

# fig, ax = plt.subplots(figsize=(10, 6))
# fig.subplots_adjust(right=0.75)
# x = ['young', 'medium', 'old']

# scale_factor = 2  # 控制圆的缩放比例

# for _, row in df.iterrows():
#     ls = row['linestyle']
#     ftu = row['ftu']
#     color = color_mapping[ls][ftu]

#     # y 值（数值），自动跳过 NaN
#     y = [row['young'], row['medium'], row['old']]
#     mask = np.isfinite(y)
#     ax.plot(np.array(x)[mask], np.array(y)[mask],
#             linestyle=ls, color=color, linewidth=2, label=ftu)

#     # 对应 pmcid 数量
#     pmcids = [row['young-pmcid'], row['medium-pmcid'], row['old-pmcid']]

#     # 画散点，大小与 pmcid 成正比
#     ax.scatter(x, y, s=np.array(pmcids) * scale_factor,
#                facecolors='none', edgecolors=color, linewidths=1.5, zorder=3)

# ax.set_yscale('log')
# ax.set_xlabel('Age group')
# ax.set_ylabel('Mean scale bar (µm)')
# ax.set_ylim(1, 100000)

# # ------- FTU legend -------
# ftu_order = list(dict.fromkeys(df['ftu']))  
# handles, labels = ax.get_legend_handles_labels()
# ordered = [(handles[labels.index(ftu)], ftu) for ftu in ftu_order if ftu in labels]
# if ordered:
#     ordered_handles, ordered_labels = zip(*ordered)
#     ftu_legend = ax.legend(ordered_handles, ordered_labels,
#                            loc='center left', bbox_to_anchor=(1.02, 0.5),
#                            title='FTU', fontsize='small', ncol=1)
#     ax.add_artist(ftu_legend)

# # ------- Circle legend (PMCID count) -------
# all_pmcids = pd.concat([df['young-pmcid'], df['medium-pmcid'], df['old-pmcid']]).dropna()
# sizes = [all_pmcids.min(), all_pmcids.median(), all_pmcids.max()]

# circle_handles = [
#     plt.scatter([], [], s=s*scale_factor, facecolors='none', edgecolors='black', linewidths=1.5)
#     for s in sizes
# ]

# ax.legend(circle_handles, 
#           [f"{int(s)} pmcid" for s in sizes],
#           title="PMCID count",
#           loc='center left', bbox_to_anchor=(1.22, 0.5),
#           labelspacing=1.2, borderpad=1, frameon=True)

# plt.tight_layout()
# plt.show()
# # plt.savefig(r"vis\6b-sb-yearold-v2.svg", bbox_inches='tight')
# # plt.close()


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D

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

df = pd.read_csv(r'data\vis-source-data\6b-sb-yearold.csv')

def pick_linestyle(org):
    if org == 'Kidney':
        return '--'
    elif org in ('Pancreas', 'Skin'):
        return ':'
    else:
        return '-'

df['linestyle'] = df['organ'].apply(pick_linestyle)

# 颜色映射
color_mapping = {}
for ls, sub in df.groupby('linestyle'):
    ftus = sub['ftu'].unique()
    palette = plt.cm.tab10(np.linspace(0, 1, len(ftus)))
    color_mapping[ls] = dict(zip(ftus, palette))

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(right=0.75)
x = ['young', 'medium', 'old']

scale_factor = 2  # 控制圆的缩放比例

for _, row in df.iterrows():
    ls = row['linestyle']
    ftu = row['ftu']
    color = color_mapping[ls][ftu]

    # y 值（自动跳过 NaN）
    y = [row['young'], row['medium'], row['old']]
    mask = np.isfinite(y)
    ax.plot(np.array(x)[mask], np.array(y)[mask],
            linestyle=ls, color=color, linewidth=2, label=ftu)

    # 对应 pmcid 数量
    pmcids = [row['young-pmcid'], row['medium-pmcid'], row['old-pmcid']]

    # 画散点
    ax.scatter(x, y, s=np.array(pmcids) * scale_factor,
               facecolors='none', edgecolors=color, linewidths=1.5, zorder=3)

ax.set_yscale('log')
ax.set_xlabel('Age group')
ax.set_ylabel('Mean scale bar (µm)')
ax.set_ylim(10, 100000)
ax.set_box_aspect(1)

# ================= Legends =================
# FTU legend 顺序
ftu_order = list(dict.fromkeys(df['ftu']))  
handles, labels = ax.get_legend_handles_labels()
ordered = [(handles[labels.index(ftu)], ftu) for ftu in ftu_order if ftu in labels]

# Legend 位置参数
ftu_legend_y = 0.75
circle_legend_y = 0.2

if ordered:
    ordered_handles, ordered_labels = zip(*ordered)
    ftu_legend = ax.legend(ordered_handles, ordered_labels,
                           loc='center left', bbox_to_anchor=(1.02, ftu_legend_y),
                           title='FTU', fontsize='small', ncol=1)
    ax.add_artist(ftu_legend)

# Circle legend (PMCID count)
all_pmcids = pd.concat([df['young-pmcid'], df['medium-pmcid'], df['old-pmcid']]).dropna()
sizes = [all_pmcids.min(), all_pmcids.median(), all_pmcids.max()]

circle_handles = [
    plt.scatter([], [], s=s*scale_factor, facecolors='none', edgecolors='black', linewidths=1.5)
    for s in sizes
]

ax.legend(circle_handles, 
          [f"{int(s)} pmcid" for s in sizes],
          title="PMCID count",
          loc='center left', bbox_to_anchor=(1.02, circle_legend_y),
          labelspacing=1.2, borderpad=1, frameon=True)

plt.tight_layout()
# plt.show()
plt.savefig(r"vis\6b-sb-yearold.svg", bbox_inches='tight')
plt.close()
