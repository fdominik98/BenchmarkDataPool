import glob2
import pandas
import numpy
import sys
import os.path
import itertools

# CSV schema data
doc_numbers = range(1, 7)
doc_number_combinations = itertools.product(doc_numbers, doc_numbers)
doc_combinations = [f'Pride{c[0]}_Sense{c[1]}' for c in doc_number_combinations]

csv_header = ['type', 'name', 'input_id', 'time', 'team', 'meas_id']
column_types = {
    'type': str,
    'name': str,
    'input_id': str,
    'time': numpy.float64,
    'team': str,
    'meas_id': str
}
unique_columns = ['team', 'meas_id', 'name', 'input_id', 'type']
type_col_values = ['QUEUE', 'START', 'STOP']
name_col_values = [f'Tokenize{num}' for num in range(1, 3)] + [f'Collect{num}' for num in range(1, 3)] + \
                  [f'ComputeScalar{num}' for num in range(1, 4)] + ['ComputeCosine']
input_id_col_values = [f'Pride{num}' for num in doc_numbers] + [f'Sense{num}' for num in doc_numbers] + doc_combinations
meas_id_col_values = doc_combinations

# Util functions


def validate_column_range(data_frame, col, valid_values):
    invalid_row_indicators = ~data_frame[col].isin(valid_values)
    if invalid_row_indicators.any():
        print(f'ERROR: Invalid "{col}" column values for the following rows')
        print(data_frame[invalid_row_indicators])
        print(f'Valid values are: {valid_values}')
        return False
    return True


def check_for_duplicates(data_frame):
    duplicate_df = data_frame[data_frame.duplicated()]
    num_of_duplicates = len(duplicate_df)
    if num_of_duplicates > 0:
        print(f'ERROR: Contains the following {num_of_duplicates} duplicated rows')
        print(duplicate_df)
        return False
    return True


def check_for_missing_values(data_frame, col):
    missing_value_indicators = data_frame[col].isna()
    if missing_value_indicators.any():
        print(f'ERROR: Missing values for "{col}" column in the following rows')
        print(data_frame[missing_value_indicators])
        return False
    return True


dir_to_validate = sys.argv[1] if len(sys.argv) == 2 else './csvs'
path_pattern = os.path.join(dir_to_validate, '*.csv')
merged_csv_path = os.path.join('./', 'MERGED.csv')
valid_data_frames = []

for file_path in glob2.glob(path_pattern):
    print('Processing file: %s' % file_path)
    df = pandas.read_csv(file_path, header=0, names=csv_header, low_memory=False, dtype=column_types)
    valid = True

    valid &= validate_column_range(df, 'type', type_col_values)
    valid &= validate_column_range(df, 'name', name_col_values)
    valid &= validate_column_range(df, 'input_id', input_id_col_values)
    valid &= validate_column_range(df, 'meas_id', meas_id_col_values)
    valid &= check_for_missing_values(df[(df['type'] == 'START') | (df['type'] == 'STOP')], 'time')
    valid &= check_for_duplicates(df[unique_columns])

    if not valid:
        print('ERROR: Invalid CSV: ' + file_path)
        exit(1)

    valid_data_frames.append(df)

if len(valid_data_frames) == 0:
    print('ERROR: No valid CSVs found in directory ' + dir_to_validate)
    exit(1)

print('Merging CSVs...')
merged_df = pandas.concat(valid_data_frames)

if not check_for_duplicates(merged_df[unique_columns]):
    exit(1)

print(merged_df.pivot_table(index=['team', 'meas_id', 'name', 'input_id'], columns='type', values='time').reset_index())

merged_df.to_csv(merged_csv_path, index=False)
print('Valid CSVs saved: ' + merged_csv_path)
exit(0)
