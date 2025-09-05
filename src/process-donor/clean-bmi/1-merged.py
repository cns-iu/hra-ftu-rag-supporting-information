import pandas as pd
import os
import glob

def get_round_number():
    round_file = 'data\donor-meta\bmi\round.csv'
    try:
        df_round = pd.read_csv(round_file, header=None)
        round_number = int(df_round.iloc[0, 0])
        return round_number
    except Exception as e:
        print(f"Error reading round.csv: {e}")
        return None

def main():
    round_number = get_round_number()
    if round_number is None:
        print("Round number not found. Exiting.")
        return

    folder_path = f'data\donor-meta\bmi\bmi_{round_number}'  
    output_file = f'data\donor-meta\bmi\merged_bmi_{round_number}.xlsx'  

    xlsx_files = glob.glob(os.path.join(folder_path, '*.xlsx'))

    if not xlsx_files:
        return

    df_list = []
    for file in xlsx_files:
        df = pd.read_excel(file)
        df_list.append(df)

    merged_df = pd.concat(df_list, ignore_index=True)

    merged_df.to_excel(output_file, index=False)


if __name__ == '__main__':
    main()

