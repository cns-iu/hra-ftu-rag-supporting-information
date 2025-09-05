import pandas as pd
import os
import json
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

# 定义要读取的文件夹路径
folder_path = r'data\input-data\ols'
output_folder = r'data\input-data\ols2excel'  # 定义保存CSV的文件夹路径

# 创建输出文件夹，如果不存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 需要处理的列
definition_columns = [
    'definition.type', 'definition.datatype', 'definition.value', 
    'definition.lang', 'definitionProperty.type', 'definitionProperty.value',
    'definition', 'definitionProperty', 'definition.value.type', 
    'definition.value.value', 'definition.axioms'
]

# 文件处理函数
def process_file(file_name):
    if file_name.endswith('.xlsx') or file_name.endswith('.xls'):  # 检查是否是Excel文件
        output_file = os.path.join(output_folder, f"{os.path.splitext(file_name)[0]}.xlsx")
        
        # 如果输出文件已经存在，跳过处理
        if os.path.exists(output_file):
            print(f"{output_file} already exists, skipping.")
            return
        
        file_path = os.path.join(folder_path, file_name)
        # 读取Excel文件
        try:
            data = pd.read_excel(file_path)
            
            # 只保留必要的列
            columns_to_keep = ['curie.value', 'http://www.w3.org/2000/01/rdf-schema#label.value', 'label.value']
            columns_to_keep += [col for col in definition_columns if col in data.columns]  # 如果definition相关的列存在，添加进去
            
            # 过滤出存在的列
            data = data[[col for col in columns_to_keep if col in data.columns]]
            
            # Step 1: 如果 `label.value` 和 `http://www.w3.org/2000/01/rdf-schema#label.value` 相同，则将 `label.value` 设置为空
            if 'label.value' in data.columns and 'http://www.w3.org/2000/01/rdf-schema#label.value' in data.columns:
                data['label.value'] = data.apply(
                    lambda row: None if row['label.value'] == row['http://www.w3.org/2000/01/rdf-schema#label.value'] else row['label.value'], axis=1
                )
            
            # Step 2: 如果整个 `label.value` 列都是空的，则删除该列
            if 'label.value' in data.columns and data['label.value'].isna().all():
                data.drop(columns=['label.value'], inplace=True)
            
            # Step 3: 将与 definition 相关的列合并为一个字典，并去除空属性
            def create_definition(row):
                definition = {col: row[col] for col in definition_columns if col in row and pd.notna(row[col])}
                return definition if definition else None
            
            if any(col in data.columns for col in definition_columns):
                data['definition'] = data.apply(create_definition, axis=1)
            
            data = data.dropna(axis=1, how='all')

            # 保存为Excel文件
            data.to_excel(output_file, index=False)
            print(f"Processed {file_name} and saved as {output_file}")
        
        except Exception as e:
            print(f"Error processing {file_name}: {e}")

# 多线程处理所有文件
def process_files_concurrently(start_ontology, end_ontology):
    files = os.listdir(folder_path)
    
    # 筛选符合start_ontology和end_ontology范围内的文件
    selected_files = [
        file for file in files 
        if file.startswith('classes_output_ontology_') 
        and file.endswith('.xlsx')
    ]
    
    # 获取文件中的ontology和part信息，过滤出符合start和end范围的文件
    filtered_files = []
    for file in selected_files:
        try:
            ontology_num = int(file.split('_')[3])
            part_num = int(file.split('_')[5].split('.')[0])
            if start_ontology <= ontology_num <= end_ontology:
                filtered_files.append(file)
        except ValueError:
            continue

    # 使用系统的最大线程数
    max_threads = multiprocessing.cpu_count()

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        executor.map(process_file, filtered_files)

if __name__ == "__main__":
    # 可以在这里调整start和end的ontology number
    start_ontology = 70
    end_ontology = 90
    process_files_concurrently(start_ontology, end_ontology)

