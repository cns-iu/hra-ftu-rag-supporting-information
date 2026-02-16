import pandas as pd
import plotly.graph_objects as go


df = pd.read_csv(r'data\vis-source-data\6e-donor-cnt.csv')


merge_species = ['Callithrix jacchus', 'Macaca mulatta', 'Pan troglodytes']
df['species_tag'] = df['species_tag'].replace(
    merge_species,
    'Callithrix jacchus/Macaca mulatta/Pan troglodytes'
)


df['species_tag'] =  df['species_tag'].astype(str)
df['sex_tag'] =  df['sex_tag'].astype(str)
df['age_tag'] =  df['age_tag'].astype(str)
df['age_yearold_tag'] =  df['age_yearold_tag'].astype(str)
df['bmi_tag'] =  df['bmi_tag'].astype(str)

columns = ['species_tag', 'sex_tag', 'age_yearold_tag', 'bmi_tag']


stage_colors = {
    ('species_tag', 'sex_tag'): 'rgba(213, 232, 241, 0.6)',
    ('sex_tag', 'age_yearold_tag'): 'rgba(202, 235, 231, 0.6)',
    ('age_yearold_tag', 'bmi_tag'): 'rgba(157, 153, 199, 0.6)',
}

label_pairs = []
sources, targets, values, link_colors = [], [], [], []


for i in range(len(columns) - 1):
    col_from = columns[i]
    col_to = columns[i + 1]
    grouped = df.groupby([col_from, col_to])['count'].sum().reset_index()
    
    for _, row in grouped.iterrows():
        source = row[col_from]
        target = row[col_to]
        if 'others' in source.lower() or 'others' in target.lower() or \
           'unknown' in source.lower() or 'unknown' in target.lower():
            continue
        label_pairs.append((source, target, row['count'], stage_colors[(col_from, col_to)]))


used_labels = pd.unique([p[0] for p in label_pairs] + [p[1] for p in label_pairs])
label_to_index = {label: i for i, label in enumerate(used_labels)}


for source, target, count, color in label_pairs:
    sources.append(label_to_index[source])
    targets.append(label_to_index[target])
    values.append(count)
    link_colors.append(color)


fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=10,
        thickness=12,
        line=dict(color="black", width=0.3),
        label=list(used_labels)
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
        color=link_colors
    )
)])

fig.update_layout(
    font=dict(family="Arial", size=20),
    margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor='white',
    plot_bgcolor='white'
)

fig.show()
