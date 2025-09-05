import os
import tarfile
import pandas as pd
import zlib
from multiprocessing import Pool

# Input and output directories
input_dir = r"data\input-data\ftu-pub-pmc" 
error_log_file = "data\input-data\error_files-new.csv" 

# List to store error file details
error_files = []

# Function to extract .tar.gz files
def extract_tar_gz(file_path_target):
    """
    Extract a .tar.gz file to the specified target directory.
    Handles empty files, corrupted files, and other extraction errors.
    """
    file_path, target_dir = file_path_target

    if not file_path.endswith('.tar.gz'):
        return
    
    # Skip empty files
    if os.path.getsize(file_path) == 0:
        print(f"[Empty File] {file_path} - Skipped extraction.")
        error_files.append({'File': file_path, 'Error': 'Empty file'})
        os.remove(file_path)  # Remove empty file
        print(f"{file_path} has been deleted.")
        return

    print(f"Extracting {file_path}...")
    try:
        # Open tar.gz file and extract members one by one
        with tarfile.open(file_path, 'r:gz') as tar:
            for member in tar.getmembers():
                try:
                    tar.extract(member, path=target_dir)
                except IOError as e:
                    print(f"Failed to extract {member.name}: {e}")
                    error_files.append({'File': file_path, 'Error': f"Failed to extract {member.name}: {e}"})
        print(f"{file_path} extraction complete.")

        # Delete the .tar.gz file after successful extraction
        os.remove(file_path)
        print(f"{file_path} has been deleted.")

    except tarfile.ReadError as e:
        print(f"[Error] Failed to extract {file_path}: {e}")
        error_files.append({'File': file_path, 'Error': str(e)})
    except EOFError as e:
        print(f"[EOF Error] {file_path} is incomplete: {e}")
        error_files.append({'File': file_path, 'Error': 'EOFError - File ended prematurely'})
    except zlib.error as e:
        print(f"[Compression Error] Failed to extract {file_path}: {e}")
        error_files.append({'File': file_path, 'Error': 'zlib error - Invalid compressed file'})
    except Exception as e:
        print(f"[Unknown Error] Failed to extract {file_path}: {e}")
        error_files.append({'File': file_path, 'Error': str(e)})

# Function to traverse directories and process .tar.gz files
def traverse_and_extract(root_dir):
    """
    Traverse the root directory and its subdirectories to process .tar.gz files.
    """
    tasks = []
    for root, _, files in os.walk(root_dir):  
        for file_name in files:
            full_file_path = os.path.join(root, file_name)
            if file_name.endswith('.tar.gz'):
                tasks.append((full_file_path, root))  

    return tasks

if __name__ == "__main__":
    print("Starting extraction of all .tar.gz files...")
    
    # Gather tasks
    tasks = traverse_and_extract(input_dir)

    # Use multiprocessing to process tasks
    with Pool(processes=os.cpu_count()) as pool:
        pool.map(extract_tar_gz, tasks)

    print("Extraction process complete.")

    # Save error details to a CSV file
    if error_files:
        error_df = pd.DataFrame(error_files)
        error_df.to_csv(error_log_file, index=False)
        print(f"Error files have been saved to {error_log_file}.")
    else:
        print("No errors encountered during extraction.")

