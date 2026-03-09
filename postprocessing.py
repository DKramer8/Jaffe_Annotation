# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
import pandas as pd
import os
import re
import math
from rapidfuzz import process, fuzz

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# GLOBALS
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
DIR_PATH = os.getcwd()
DICTIONARY_FILE = f'{DIR_PATH}/data/static/jaffe_dicts.xlsx'
INPUT_PATH = f'{DIR_PATH}/data/output/'
OUTPUT_FILE = f'{DIR_PATH}/data/postprocessed/postprocessed_'

POSTPROCESSING_COLUMNS = ['date', 'pope', 'place', 'number'] # The Columns to be postprocessed

# The minimum Levenshtein distance for each category, which must be met for a replacement to occur
MIN_LEVDIS_SCORE_NUMBER = 85
MIN_LEVDIS_SCORE_YEAR = 70
MIN_LEVDIS_SCORE_MONTH = 66
MIN_LEVDIS_SCORE_DAY = 70
MIN_LEVDIS_SCORE = 70

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
def replace_by_dict(text: str, dictionary: list, lev_distance: int, row_nmb: int) -> str:
    '''
    Replaces a given text with the closest match from a provided dictionary if the Levenshtein distance score is above a certain threshold.
    
    :param text: The text to be replaced
    :type text: str
    :param dictionary: A list of valid entries to compare against
    :type dictionary: list
    :param lev_distance: The minimum Levenshtein distance score required for a replacement to occur
    :type lev_distance: int
    :param row_nmb: The row number in the original DataFrame, used for logging purposes
    :type row_nmb: int
    :return: The original text if no close match is found, or the closest match from the dictionary if the score is above the threshold
    :rtype: str
    '''

    match, score, _ = process.extractOne(
        text,
        dictionary,
        scorer=fuzz.ratio
    )

    if score >= lev_distance and score != 100:
        print(f"Ersetze '{text}' durch '{match}' (Score: {score}) at row {row_nmb+2}")
        return match
    else:
        return text
    
def split_date(full_date: str) -> tuple:
    '''
    Splits a full date string into its components: year, month, and day. The function uses regular expressions to identify and extract these components, handling various formats and potential noise in the input string.
    
    :param full_date: The full date string to be split, which may contain the year, month, and day in various formats and with potential noise (e.g., extra characters, inconsistent spacing).
    :type full_date: str
    :return: A tuple containing the year, month, and day components
    :rtype: tuple
    '''

    if not full_date or full_date.strip() == '':
        return ' ', ' ', ' '

    full_date = full_date.strip()

    year_match = re.match(r'^\(?\d{4}(?:\s*[—-]\s*\d{4})?\)?', full_date) # Regex by ChatGPT

    if year_match:
        year = year_match.group().strip()
        rest = full_date[year_match.end():].strip()
    else:
        year = ' '
        rest = full_date

    month = re.sub(r"[^a-zA-Z()]", "", rest)
    if not month:
        month = ' '

    day = re.sub(r"[^0-9]", "", rest)
    if not day:
        day = ' '

    return year, month, day

def clean_number(s) -> str:
    '''
    Cleans a string by removing all characters except digits, parentheses, and spaces. This function is specifically designed to handle the 'number' column, which may contain various formats and noise. If the input is None or NaN, it returns an empty string.
    
    :param s: The string to be cleaned
    :type s: str or float
    :return: The cleaned string with only digits, parentheses, and spaces
    :rtype: str
    '''

    if s is None or (isinstance(s, float) and math.isnan(s)):
        return ''
    return re.sub(r'[^0-9() ]', '', str(s))

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
if __name__ == '__main__':
    print('Please enter file name (must end in .xlsx)')
    user_input = input()
    input_file = INPUT_PATH + user_input
    output_file = OUTPUT_FILE + user_input

    df_dict = pd.read_excel(DICTIONARY_FILE) # Load the dictionary file as a DataFrame for comparison
    df_input = pd.read_excel(input_file)
    output_df = df_input

    for column in POSTPROCESSING_COLUMNS:        
        if column == 'date': # Postprocessing of date
            # Prepare dictionaries for year, montah and day
            year_dict = df_dict['year'].dropna().astype(str).tolist()
            month_dict = df_dict['month'].dropna().astype(str).tolist()
            month_dict = [x.replace('.', '') for x in month_dict] # To avoid complicating the string comparison with the dict, the dots are removed from the dict and added manually later
            day_dict = df_dict['day'].dropna().astype(int).astype(str).tolist()

            # Split dates into year, month and day components
            years_raw = [split_date(t)[0] for t in df_input['date'].astype(str)]
            months_raw = [split_date(t)[1] for t in df_input['date'].astype(str)]
            days_raw = [split_date(t)[2] for t in df_input['date'].astype(str)]

            # Replace year, month and day components by closest match from the respective dictionaries
            years = [replace_by_dict(y, year_dict, MIN_LEVDIS_SCORE_YEAR, idx) for idx, y in enumerate(years_raw)]
            months = [replace_by_dict(m, month_dict, MIN_LEVDIS_SCORE_MONTH, idx) for idx, m in enumerate(months_raw)]
            months = [x + '.' if x != ' ' else x for x in months]
            days = [replace_by_dict(d, day_dict, MIN_LEVDIS_SCORE_DAY, idx) for idx, d in enumerate(days_raw)]
            days = [x + '.' if x != ' ' else x for x in days]

            # Recombine the cleaned year, month and day components into a full date string and store it in the output DataFrame
            i = 0
            while i < len(years):
                output_df.loc[i, 'date'] = f'{years[i].strip()} {months[i].strip()} {days[i].strip()}'
                i += 1

        elif column == 'number': # Postprocessing of Jaffe numbers
            numbers_raw = df_input['number'].tolist()
            output_df['number'] = [clean_number(s) for s in numbers_raw]

        else: # Postprocessing of pope and place
            dictionary = df_dict[column].dropna().astype(str).tolist()
            text = df_input[column].astype(str).tolist()
            output_df[column] = [replace_by_dict(t, dictionary, MIN_LEVDIS_SCORE, idx) for idx, t in enumerate(text)]

    output_df.to_excel(output_file, index=False)
