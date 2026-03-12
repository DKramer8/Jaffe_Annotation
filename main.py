# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import io
from pagexml.helper.file_helper import  read_page_archive_files
from pagexml import parser as pxml_parser
from zipfile import ZipFile
from classification import classify

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
DIR_PATH = os.getcwd()
INPUT_PATH = DIR_PATH + f'\\data\\input'
OUTPUT_PATH = DIR_PATH + f'\\data\\output'

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
def console_welcome() -> str:
    '''
        Prints out the welcome text and asks for input format

        :return: The entered input in lower format
        :rtype: str
    '''

    print('----------------------------------------------------------------------------------------------------------------------')
    print('Welcome to the classification script for Jaffé OCR')
    print('----------------------------------------------------------------------------------------------------------------------')
    print('Do you want to classify a specific PageXML file or a whole Zip Archive of PageXML? (single/zip)')
    i = input()
    print('----------------------------------------------------------------------------------------------------------------------')

    return i.lower()

def ask_for_plot() -> bool:
    '''
        Asks the user if they want to plot the line regions of a specific file

        :return: True if the user wants to plot, False otherwise
        :rtype: bool
    '''

    print('Do you want to plot the line regions of a specific file? (y/n)')
    yes = ['y', 'Y', 'yes', 'Yes']
    no = ['n', 'N', 'no', 'No']
    i = input()
    if i in yes:
        print('----------------------------------------------------------------------------------------------------------------------')
        return True
    elif i in no:
        print('----------------------------------------------------------------------------------------------------------------------')
        return False
    else:
        print('Invalid input. Continuing without plotting...')
        return False

def plot_text_regions(df: pd.DataFrame):
    '''
        Creates a window using matplotlib that plots the regions of all rows.

        :param: df: The pandas DataFrame to plot the image from
        :type: df: pd.DataFrame
    '''
    fig, ax = plt.subplots(figsize=(10, 8))
    for idx, row in df.iterrows():
        if row['type'] == 'date':
            color = 'g'         
        elif row['type'] == 'place':
            color = 'b'
        elif row['type'] == 'regest_text':
            color = 'y'
        elif row['type'] == 'regest_start':
            color = 'r'        
        elif row['type'] == 'regest_date':
            color = 'c'          
        elif row['type'] == 'new_pope':
            color = 'm'             
        else:
            color = 'k'
        rect = patches.Rectangle((row['x'], row['y']), row['w'], row['h'], linewidth=1, edgecolor=color, facecolor='none')
        ax.add_patch(rect)
        #ax.text(row['x'], row['y'], row['text'], fontsize=8, verticalalignment='top')
    ax.set_xlim(0, df['x'].max() + df['w'].max())
    ax.set_ylim(df['y'].max() + df['h'].max(), 0)
    plt.axis('off')
    plt.show()          

def find_incipit(df: pd.DataFrame) -> pd.DataFrame:
    '''
        Slices the regest text at the position of '-' char and puts all text behind that as incipit into the df

        :param: df: The comlpete DataFrame to search for incipits
        :return: The DateFrame including the detected incipits
    '''

    incipits = []
    texts = []
    slice_idx = False
    for idx, regest in df.iterrows():
        txt = regest['text']

        # Juste get the last 75 chars of regest text since the '-' char could appear before
        if len(txt) > 75:
            max_chars = len(txt) - 75
        else:
            max_chars = len(txt)

        # Find '-' char position to slice of incipit afterwards
        for idx, char in enumerate(txt):
            if idx > max_chars:
                if char == '—':
                    slice_idx = idx

        # Slice incpit if '-' char has been found
        if slice_idx != False:
            incipit = txt[slice_idx+2:]
            only_txt = txt[:slice_idx-1:]
            incipits.append(incipit)
            texts.append(only_txt)
        else:
            incipits.append('')
            texts.append(txt)

    df['incipit'] = incipits
    df['text'] = texts

    return df

def combine_regests(df: pd.DataFrame) -> pd.DataFrame:
    '''
        Deletes all lines categorised as belonging to the previous page and adds their text to previous line text. Also detects all regest thats places are categorised to be the same as previous places regest
    
        :param: df: The Pandas DataFrame whichs regests get merged
        :type: df: pd.DataFrame
        :return: The Pandas DataFrame without rows that belong to previous regest
        :rtype: pd.DataFrame
    '''



    # Merge text of regests that span over two pages
    drop_idx = []
    for idx, row in df.iterrows():
        if row['date'] == 'prev_page' and row['place'] == 'prev_page' and row['number'] == 'prev_page':
            if idx != 0:
                if df.iloc[idx-1]['text'].endswith('-'):
                    txt = df.iloc[idx-1]['text'][:-1] + row['text']
                else:
                    txt = ' '.join([df.iloc[idx-1]['text'], row['text']])
                df.loc[idx-1, 'text'] = txt
                drop_idx.append(idx)
            else:
                drop_idx.append(idx)
    df = df.drop(index=drop_idx)
    df = df.reset_index(drop=True)    

    # Detect places that are classified as being the same as previous place
    for idx, row in df.iterrows():
        if row['place'] == 'prev_regest':
            i = idx-1
            while i > 0:
                if any(char.isalpha() for char in df.loc[i, 'place']):
                    weg = ['(', ')']
                    place = ''.join([p for p in df.loc[i, 'place'] if p not in weg])
                    df.loc[idx, 'place'] = place
                    i = 0
                i = i-1
        elif row['place'] == '(prev_regest)':
            i = idx-1
            while i > 0:
                if any(char.isalpha() for char in df.loc[i, 'place']):
                    df.loc[idx, 'place'] = '(' + df.loc[i, 'place'] + ')'
                    i = 0
                i = i-1                

    df = find_incipit(df)

    return df

def output(df: pd.DataFrame, format: str, file_name: str):
    '''
        Exports the given pandas DataFrame into csv, xml or tsv file depending on passed format string.

        :param: df: The Pandas DataFrame to export
        :param: format: Either 'csv' or 'tsv' depending on favored output format.
        :param: file_name: The name of the file to export to
        :type: df: pd.DataFrame
        :type: format: str
        :type: file_name: str
    '''

    file_name = file_name[:-4]
    if format.lower() == 'csv':
        df.to_csv(OUTPUT_PATH + '\\' + file_name + 'CSV.csv', index=True)
    elif format.lower() == 'tsv':
        df.to_csv(OUTPUT_PATH + '\\' + file_name + 'TSV.tsv', index=True, sep='\t')
    elif format.lower() == 'single_xml':
        df.to_xml(OUTPUT_PATH + '\\' + file_name + 'XML.xml')
    elif format.lower() == 'multi_xml':
        zip = OUTPUT_PATH + '\\' + file_name + '.zip'
        with ZipFile(zip, 'w') as zipFile:
            for i in range(len(df)):
                single_regest = df.iloc[[i]]
                with io.BytesIO() as puffer:
                    single_regest.to_xml(puffer, index=False, encoding='utf-8')
                    puffer.seek(0)
                    zipFile.writestr(f"{i}_{single_regest['number'].values[0]}.xml", puffer.read())
    elif format.lower() == 'excel':
        df.to_excel(OUTPUT_PATH + '\\' + file_name + '.xlsx', index=False)
    else:
        print('Invalid output format. Could not create output file.')

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
input_type = console_welcome()

if input_type == 'single': # Single page classification
    # Enter file name
    print('Please enter file name (Must be in PageXML folder and end in .xml)')
    file_name = input()
    single_file = INPUT_PATH + '\\' + file_name
    if os.path.exists(single_file) != True:
        print('Path doesnt exist. Stopping process...')
        quit()
    print('----------------------------------------------------------------------------------------------------------------------')

    scan = pxml_parser.parse_pagexml_file(single_file)
    df, final_df = classify(scan)

    # Plot the regions if wanted
    if ask_for_plot() == True:
        plot_text_regions(df)

    # Ask for output format
    print('----------------------------------------------------------------------------------------------------------------------')
    print('Please enter output format (csv/tsv//single_xml/multi_xml/excel)')
    output_format = input()

    output(final_df, output_format, file_name)

elif input_type == 'zip': # Zip archive classification
    # Enter file name
    ('Please enter zip archive name (Must end in .zip)')
    file_name = input()
    zip_file = INPUT_PATH + '\\' + file_name
    if os.path.exists(zip_file) != True:
        print('Path doesnt exist. Stopping process...')
        quit()
    print('----------------------------------------------------------------------------------------------------------------------')

    # Ask if a specific page should get plotted
    plot_file = ''
    if ask_for_plot() == True:
        print('Please enter file name of the page you want to plot (Must be inpage the zip archive and end in .xml)')
        plot_file = input()

    # Ask for output format
    print('----------------------------------------------------------------------------------------------------------------------')
    print('Please enter output format (csv/tsv//single_xml/multi_xml/excel)')
    output_format = input()

    print('Processing...')
    zip_df = []
    for info, data in read_page_archive_files(zip_file):
        if info['archived_filename'] != 'METS.xml':
            print(info['archived_filename'])
            scan = pxml_parser.parse_pagexml_file(pagexml_file=info['archived_filename'], pagexml_data=data)
            df, final_df = classify(scan) #info['archived_filename']
            zip_df.append(final_df)

            # Plot specific page if wanted
            if plot_file != '' and plot_file == info['archived_filename']:
                plot_text_regions(df)

    # Merge all dataframe together
    zip_df = pd.concat(zip_df, ignore_index=True)
    zip_df = combine_regests(zip_df)

    output(zip_df, output_format, file_name)
    print('Finished :)')

else:
    print('Invalid input. Stopping process...')