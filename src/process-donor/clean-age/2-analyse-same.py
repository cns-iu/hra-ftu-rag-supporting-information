import pandas as pd
import ast 

def get_round_number():
    round_file = r'data\donor-meta\age\round.csv'
    try:
        df_round = pd.read_csv(round_file, header=None)
        round_number = int(df_round.iloc[0, 0])
        return round_number, round_file
    except Exception as e:
        print(f"Error reading round.csv: {e}")
        return None, None

def update_round_number(round_file, new_round):
    try:
        pd.DataFrame([[new_round]]).to_csv(round_file, index=False, header=False)
    except Exception as e:
        print(f"Error updating round.csv: {e}")

def main():
    round_number, round_file = get_round_number()
    if round_number is None:
        print("No round.csv")
        return

    current_file = f'data\donor-meta\age\merged_age_{round_number}.xlsx'
    previous_file = f'data\donor-meta\age\merged_age_{round_number - 1}.xlsx'


    df1 = pd.read_excel(current_file)
    df2 = pd.read_excel(previous_file)


    df1['json_rs'] = df1['json_rs'].apply(ast.literal_eval)
    df2['json_rs'] = df2['json_rs'].apply(ast.literal_eval)


    merged = pd.merge(df1, df2, on='age', suffixes=('_r1', '_r2'))


    same_rows = []
    same_others_rows = []
    different_rows = []

    for _, row in merged.iterrows():
        age = row['age']
        json_rs_r1 = row['json_rs_r1']
        json_rs_r2 = row['json_rs_r2']
        
        if json_rs_r1 == json_rs_r2:
            if json_rs_r1 == ['others']:
                same_others_rows.append({'age': age, 'json_rs': json_rs_r1})
            elif len(json_rs_r1) == 1:
                same_rows.append({'age': age, 'json_rs': json_rs_r1})
            else:
                different_rows.append({'age': age, 'json_rs_r1': json_rs_r1, 'json_rs_r2': json_rs_r2})
        else:
            different_rows.append({'age': age, 'json_rs_r1': json_rs_r1, 'json_rs_r2': json_rs_r2})

    output_same = f'data\donor-meta\age\same_{round_number}.xlsx'
    output_same_others = f'data\donor-meta\age\same-others_{round_number}.xlsx'
    output_different = f'data\donor-meta\age\age_{round_number + 1}.xlsx'
    output_different_csv = f'data\donor-meta\age\age_{round_number + 1}.csv'

    pd.DataFrame(same_rows).to_excel(output_same, index=False)
    pd.DataFrame(same_others_rows).to_excel(output_same_others, index=False)
    df_different = pd.DataFrame(different_rows)
    df_different.to_excel(output_different, index=False)  


    df_different.to_csv(output_different_csv, index=False)


    update_round_number(round_file, round_number + 1)

if __name__ == '__main__':
    main()
