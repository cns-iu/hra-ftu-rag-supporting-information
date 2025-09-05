import os
import csv

root_dir = r"data\input-data\ftu-pub-pmc" 
output_csv = "data\input-data\image_paths.csv"
preferred_order = ["jpg", "png", "jpeg", "bmp", "gif"]  

image_dict = {} 

for root, dirs, files in os.walk(root_dir):
    for file in files:
        file_name, file_ext = os.path.splitext(file)
        file_ext = file_ext.lower().lstrip('.') 

        if file_ext in preferred_order:
            full_path = os.path.join(root, file)

            if file_name not in image_dict:
                image_dict[file_name] = {}
            image_dict[file_name][file_ext] = full_path


final_paths = []
for name, formats in image_dict.items():

    for ext in preferred_order:
        if ext in formats:
            final_paths.append(formats[ext])
            break


with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["image_path"])  
    for path in final_paths:
        writer.writerow([path])

print(f"results {len(final_paths)} in {output_csv}")
