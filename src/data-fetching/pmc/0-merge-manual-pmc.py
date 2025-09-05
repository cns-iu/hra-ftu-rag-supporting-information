import os
import csv


folder_path = r'data\input-data\ftu-pmc-manual'  
output_file = r'data\input-data\0-0-ftu-pmc-total.csv'  

with open(output_file, mode='w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['ftu', 'pmcid']) 

    for filename in os.listdir(folder_path):
        if filename.startswith("pmc_result_") and filename.endswith(".txt"):
            file_base_name = filename.replace("pmc_result_", "").replace(".txt", "")
            
            with open(os.path.join(folder_path, filename), 'r') as f:
                for line in f:
                    pmcid = line.strip()  
                    writer.writerow([file_base_name, pmcid])

print("CSV file created successfully.")
