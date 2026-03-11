# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
import re
import pandas as pd
import pagexml
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
TEXTREGION_THRESHOLD_MIN_WIDTH = 1000
TEXTREGION_THRESHOLD_MIN_HEIGHT = 1000
HEADERREGION_THRESHOLD_MIN_X_COORD = 500
HEADERREGION_THRESHOLD_MAX_X_COORD = 2000
HEADERREGION_THRESHOLD_MAX_H_COORD = 500
NUMBERREGION_THRESHOLD_MAX_X_COORD = 750
NUMBERREGION_THRESHOLD_MAX_W_COORD = 500
NUMBERREGION_THRESHOLD_MIN_X_COORD = 2250
REGEST_THRESHOLD_MIN_X_COORD_LEFT = 650
PLACE_THRESHOLD_MIN_X_COORD_LEFT =  450
REGEST_THRESHOLD_MIN_X_COORD_RIGHT = 400
PLACE_THRESHOLD_MIN_X_COORD_RIGHT =  250
NEW_POPE_THRESHOLD_Y_COOD = 300

current_month = ''
current_day = ''

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
def new_dictionaries() ->  tuple[dict, dict, dict]:
    '''
        Helper function to easily create new empty dictionaries of the necessary format.

        :return: textRegion_dict, unknown_region_dict, final_regest_dict
    '''

    textRegion_dict = {
        'x': [],
        'y': [],
        'w': [],
        'h': [],
        'type': [],
        'text': []
    }
    unknown_region_dict = {
        'x': [],
        'y': [],
        'h': [],
        'w': []
    }
    final_regest_dict = {
        'pope': [],
        'date': [],
        'place': [],
        'number': [],
        'text': [],
    }

    return textRegion_dict, unknown_region_dict, final_regest_dict  

def detect_page_from_filename(filename: str) -> str:
    '''
        Classifies the given file as left or right page by its name since even page numbers are always left page. Presumes that xml files must be named after its page number.
        :param: filename: The name of the file to classify
        :return: 'l' or 'r' for left or right page. In case of classification failure defaults to left page
    '''
    match = re.search(r'page_(\d+)\.png', filename)
    if match:
        page_nr = int(match.group(1))
        if page_nr % 2 == 0:
            return 'l'
        else:
            return 'r'
    print(f'{filename}: Could not detect page side. Classifying with left page thresholds as default.')
    return 'l'

def add_coords_to_dict(dict: dict, coords: dict) -> dict:
        '''
            Adds the given coords to the respective list of the given dictionary. Coords and dict does have specific conditions.

            :param dict: The dictionary to which the coords get added to. A dictionary with a list each at keys 'x', 'y', 'w', 'h'.
            :param coords: The coords that get added. A dictionary with one value each at keys 'x', 'y', 'w', 'h'.
            :return: The dictionary containing the added coords.
        '''

        dict['x'].append(coords['x'])
        dict['y'].append(coords['y'])
        dict['w'].append(coords['w'])
        dict['h'].append(coords['h'])

        return dict

def classify_left_page_columns(scan, textRegion_dict: dict, unknown_region_dict: dict, final_regest_dict: dict) ->  tuple[dict, dict, dict]:
    '''
        Iterates through each region of the passed scan and tries to classify it based on the globally defined thresholds for left page. Page Number region doesnt get recognised because its not relevant.
        Also makes basic classification of all lines from the table region filling the textRegion_dict with the coordinates of each line, its text and a basic classification of either on of the three columns ('date', 'place', 'regest_text')

        :param scan: A PageXMLScan object from the physical_document_model containing all relevant pagexml informations.
        :param textRegion_dict: A dictionary containing informations of the lines of the table region. Must contain lists on keys 'x', 'y', 'w', 'h', 'type', 'text'.
        :param unknown_region_dict: The dictioniary regions get added to if they dont fit in the conditions of all other regions Must contain lists on keys 'x', 'y', 'w', 'h'.
        :return: textRegion_dict, unknown_region_dict
    '''

    for region in scan.text_regions:
        if len(region.lines) > 0: # If region doesnt have lines its not relevant
            # Iterate through each text region and try to classify it based on coordinates and the global defined thresholds
            region_coords = region.coords.box

            if region_coords['w'] > TEXTREGION_THRESHOLD_MIN_WIDTH and region_coords['h'] > TEXTREGION_THRESHOLD_MIN_HEIGHT:
                # Table region
                for line in region.lines:
                    # Iterate through each line of the table region and try to classify it based coordinates and the global defined thresholds         
                    line_coords = line.coords.box
                    add_coords_to_dict(textRegion_dict, line_coords)

                    if line_coords['x'] > REGEST_THRESHOLD_MIN_X_COORD_LEFT:  
                        # Regest text column
                        textRegion_dict['type'].append('regest_text')
                    elif line_coords['x'] < REGEST_THRESHOLD_MIN_X_COORD_LEFT and line_coords['x'] > PLACE_THRESHOLD_MIN_X_COORD_LEFT:
                        # Regest place column
                        textRegion_dict['type'].append('place')
                    else:
                        # Regest date column
                        textRegion_dict['type'].append('date')

                    textRegion_dict['text'].append(line.text)                 

            elif region_coords['x'] > HEADERREGION_THRESHOLD_MIN_X_COORD and region_coords['x'] < HEADERREGION_THRESHOLD_MAX_X_COORD and region_coords['h'] < HEADERREGION_THRESHOLD_MAX_H_COORD:
                # Header region
                pope = ''
                header_text = region.lines[0].text
                if header_text:
                    for char in header_text:
                        pope += char
                        if char == '.':
                            break
                final_regest_dict['pope'].append(pope)
            else:
                # Unknown region
                add_coords_to_dict(unknown_region_dict, region_coords)

    return textRegion_dict, unknown_region_dict, final_regest_dict

def classify_right_page_columns(scan, textRegion_dict: dict, unknown_region_dict: dict, final_regest_dict: dict) -> tuple[dict, dict, dict]:
    '''
        Iterates through each region of the passed scan and tries to classify it based on the globally defined thresholds for right page. Page Number region doesnt get recognised because its only relevant.
        Also makes basic classification of all lines from the table region filling the textRegion_dict with the coordinates of each line, its text and a basic classification of either on of the three columns ('date', 'place', 'regest_text')

        :param scan: A PageXMLScan object from the physical_document_model containing all relevant pagexml informations.
        :param textRegion_dict: A dictionary containing informations of the lines of the table region. Must contain lists on keys 'x', 'y', 'w', 'h', 'type', 'text'.
        :param unknown_region_dict: The dictioniary regions get added to if they dont fit in the conditions of all other regions Must contain lists on keys 'x', 'y', 'w', 'h'.
        :return: textRegion_dict, unknown_region_dict
    '''

    for region in scan.text_regions:
        if len(region.lines) > 0 : # If region doesnt have lines its not relevant
            # Iterate through each text region and try to classify it based on coordinates and the global defined thresholds
            region_coords = region.coords.box

            if region_coords['w'] > TEXTREGION_THRESHOLD_MIN_WIDTH and region_coords['h'] > TEXTREGION_THRESHOLD_MIN_HEIGHT:
                # Table region
                for line in region.lines:
                    # Iterate through each line of the table region and try to classify it based coordinates and the global defined thresholds         
                    line_coords = line.coords.box
                    add_coords_to_dict(textRegion_dict, line_coords)

                    if line_coords['x'] > REGEST_THRESHOLD_MIN_X_COORD_RIGHT:  
                        # Regest text column
                        textRegion_dict['type'].append('regest_text')
                    elif line_coords['x'] < REGEST_THRESHOLD_MIN_X_COORD_RIGHT and line_coords['x'] > PLACE_THRESHOLD_MIN_X_COORD_RIGHT:
                        # Regest place column
                        textRegion_dict['type'].append('place')  
                    else:
                        # Regest date column
                        textRegion_dict['type'].append('date')

                    textRegion_dict['text'].append(line.text)                 

            elif region_coords['x'] > HEADERREGION_THRESHOLD_MIN_X_COORD and region_coords['x'] < HEADERREGION_THRESHOLD_MAX_X_COORD and region_coords['h'] < HEADERREGION_THRESHOLD_MAX_H_COORD:
                # Header region
                pope = ''
                header_text = region.lines[0].text
                if header_text:
                    for char in header_text:
                        pope += char
                        if char == '.':
                            break
                final_regest_dict['pope'].append(pope)
            else:
                # Unknown region
                add_coords_to_dict(unknown_region_dict, region_coords)

    return textRegion_dict, unknown_region_dict, final_regest_dict

def detect_new_pope(df: pd.DataFrame) -> pd.DataFrame:
    '''
        Iterates through all lines of given DataFrame and detects those that belong to pope overview. Removes those detected lines and returns the cleaned DataFrame.

        :param: df: A Pandas DataFrame created from the textRegion_dict structure containing all lines of the table region.
        :return: The DataFrame without pope stuff
    '''
    drop_idxs = [] # Index of lines that get classified as belonging to pope overview get stored here
    pope_overview = False
    is_next_date = False
    df_text = df[(df['type'] == 'regest_text')]
    x_min = df_text['x'].min()
    x_avg = df_text['x'].mean()    
    regestDate_threshold_max_x_Coord = x_min + x_avg*0.015    

    # Iterate through all lines and check whether they belong to pope overview
    for idx, row in df.iterrows(): 
        is_next_date = False
        if idx > 0 and idx < len(df.index)-1: # The used classification method needs to check lines before and after the current line. So we cant classify those lines here. For first line there is the method detect_first_line_pope_overview function

            # Check whether next line is a date line
            if df.iloc[idx+1]['x'] < regestDate_threshold_max_x_Coord:
                is_next_date = True
            
            # Check if we currently are in a pope overviwew
            if pope_overview == False:
                y_distance = row['y'] - df.iloc[idx-1]['y']
                if y_distance >= NEW_POPE_THRESHOLD_Y_COOD and is_next_date == False: 
                    # Current Row is a pope header and the next row isnt a date -> Begin of pope overview
                    drop_idxs.append(idx)
                    pope_overview = True
                elif y_distance >= NEW_POPE_THRESHOLD_Y_COOD and is_next_date == True: 
                    # Pope overview, but next row is date: standard regests begin again
                    drop_idxs.append(idx)   

            else:
                # Append current line to the list of lines that will get removed and check whether the pope overview section ends after this line (next line would be date line)
                if is_next_date == True:
                    pope_overview = False
                drop_idxs.append(idx)

        elif idx == len(df.index)-1 and pope_overview == True:
            # There is no next line, but we are still in pope overview -> add line to remove list
            drop_idxs.append(idx)   

    # Remove those lines which got classified as belonging to pope overview
    df = df.drop(index=drop_idxs)
    df = df.reset_index(drop=True)

    return df

def detect_first_line_pope_overview(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Detects whether the page started with a pope overview start that needs to get dropped and didnt get recognised in detect_new_pope()

    :param: df: The dataframe to check
    :return: The Pandas DataFrame without pope overview
    '''
    drop_idx = []
    new_pope_overview = False
    df_text = df[(df['type'] == 'regest_text')]
    x_min = df_text['x'].min()
    x_avg = df_text['x'].mean()    
    regestDate_threshold_max_x_Coord = x_min + x_avg*0.015
    for idx, row in df.iterrows():
        if idx == 0:
            if row['type'] == 'regest_text': # Normal regest pages always start with a date. Otherwise ist part of pope overview that startet on previous page, so it didnt get recognised in detect_new_pope()
                new_pope_overview = True
        if df.iloc[idx]['x'] >= regestDate_threshold_max_x_Coord and new_pope_overview == True:
            drop_idx.append(idx)
        elif df.iloc[idx]['x'] < regestDate_threshold_max_x_Coord and new_pope_overview == True:
            new_pope_overview = False
    df = df.drop(index=drop_idx)
    df = df.reset_index(drop=True)
    
    return df

def drop_unnecessary(df):
    '''
        Detects lines that are unnecessary for regest classification and dont contain necessary information.

        :param: df: The Pandas DataFrame to drop the unnecessary lines from
        :return: The passed DataFrame without unnecessary lines
    '''
    drop_idx = []
    for idx, row in df.iterrows():
        if row['type'] == 'date' and row['h'] < 130 and row['w'] > 500: # Sometimes there is a text at the bottom of date column which doesnt contain relevant information.
            drop_idx.append(idx)
        if row['type'] == 'regest_text' and row['x'] > 2300 and row['y'] > 3450 and row['w'] < 100: # Sometimes there are numbers at the bottom right corner that are not needed.
            drop_idx.append(idx)
    df = df.drop(index=drop_idx)
    df = df.reset_index(drop=True)

    return df

def classify_regest_start(df):
    '''
        Classifies all indented lines (regest_start) of the third column (regest_text) based on the lines on the far left and the mean starting coordinate of all lines.

        :param: df: A Pandas DataFrame created from the textRegion_dict structure containing all lines of the table region.
        :return: df
    '''

    regest_df = df[(df['type'] == 'regest_text')] # Only get lines of third column
    x_min = regest_df['x'].min()
    x_avg = regest_df['x'].mean()
    x_max = regest_df['x'].max()
    regestStart_threshold_max_x_Coord = x_min + x_avg*0.07 # The rows on the far left, including some space if the rows as a whole are moved slightly to the right over time
    for idx, row in df.iterrows():
        if row['type'] == 'regest_text' and row['x'] < regestStart_threshold_max_x_Coord and row['x'] != x_max:            
            df.at[idx, 'type'] = 'regest_start'

    return df

def classify_textregion_date(df):
    '''
        Classifies all years headers that are part of the third columns of the indented lines (regest_start) based on the lines on the far left and the mean starting coordinate of all indented lines since they are even more far left than the regest start lines.

        :param: df: A Pandas DataFrame created from the textRegion_dict structure containing all lines of the table region.
        :return: df
    '''

    regest_df = df[(df['type'] == 'regest_start')] # Only get rows tha are indented
    x_min = regest_df['x'].min()
    x_avg = regest_df['x'].mean()
    w_avg = regest_df['w'].mean()
    h_max = regest_df['h'].max()
    h_avg = regest_df['h'].mean()
    regestDate_threshold_max_x_Coord = x_min + x_avg*0.015
    regestDate_threshold_max_w_Coord = x_avg + w_avg - w_avg*0.025
    regestDate_threshold_min_h_Coord = h_max - h_avg*0.075
    for idx, row in df.iterrows():
        if row['type'] == 'regest_start' and row['x'] < regestDate_threshold_max_x_Coord and row['text'][0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] : # The rows on the far left, including some space if the rows as a whole are moved slightly to the right over time
            if row['w'] < regestDate_threshold_max_w_Coord or row['h'] > regestDate_threshold_min_h_Coord: # The rows dont spread over the whole distance and are a little bit higher than other indented lines
                df.at[idx, 'type'] = 'regest_date'

    return df  

def get_closest_regest(df, df_regest_start, type):
    '''
    Creates a list containing the idx of each row in df and idx of the closest regest starting line  to that row (of df). If two rows have the same closest starting regest, pop the last one as it is most propablly something unnecessary in that case.

    :param: df: The Pandas DataFrame containing the rows to which we want to find the closest regests.
    :param: df_regest_start: A Pandas DataFrame containing only thr rows that are the start of a new regest.
    :param: type:
    :return: An list of indices containing tuples of row idx, closest regest idx and the distance
    '''

    closest_regest = []
    for idx, line in df.iterrows():
        min_distance = 9999999
        min_regest_idx = 0
        for regest_idx, regest_line in df_regest_start.iterrows():
            if abs(regest_line['y'] - line['y']) < min_distance:
                min_distance = abs(regest_line['y'] - line['y'])
                min_regest_idx = regest_idx
        if len(closest_regest) > 0:
            if closest_regest[-1][1] == min_regest_idx and type == 'date': # Many pages have an unnecessary text at the bottom left that gets classified as date. So if the last two date have the same closest neighbour, remove the last one as it is most propably the unnecassary text              
                if closest_regest[-1][2] >= min_distance:
                    closest_regest.pop()
                    closest_regest.append([idx, min_regest_idx, min_distance])
            else:
                closest_regest.append([idx, min_regest_idx, min_distance])
        else:
            closest_regest.append([idx, min_regest_idx, min_distance])
    return closest_regest

def merge_to_string(l):
    '''
        Merges all strings of passed list and returns them
    '''
    text = []
    for i, line in enumerate(l):
        if line is not None:
            if line.endswith('-'): # in case that line ends with unfinished word
                if i + 1 < len(l):
                    l[i + 1] = line[:-1] + l[i + 1]
            else:
                text.append(line)
    result = ' '.join(text)
    return result

def get_full_date(dates, closest_regests, current_year, idx):
    '''
        Detects closest date for regest and appends it to the passed dict.
    '''
    full_date = current_year
    global current_month
    global current_day
    for i in closest_regests:
        if i[1] == idx:
            if dates.loc[i[0]]['text'] is not None:
                month_day = dates.loc[i[0]]['text']
                try:
                    month, day = month_day.split(' ', 1)
                except:
                    month = ' '
                    day = ' '
                if '(„)' in month or '(„' in month or '„)' in month:
                    month = '(' + current_month + ')'
                    full_date += ' ' + month
                elif '„' in month:
                    full_date += ' ' + current_month
                else:
                    current_month = month
                    full_date += ' ' + month

                if '(„)' in day or '(„' in day or '„)' in day:
                    day = '(' + current_day + ')'
                    full_date += ' ' + day
                elif '„' in day:
                    full_date += ' ' + current_day
                else:
                    current_day = day
                    full_date += ' ' + day                        
            else:
                full_date += ' '

    return full_date

def append_place(dict, places, closest_regests, current_place, idx):
    '''
        Detects closest place for regest and appends it to the passed dict.
    '''

    place = ' '
    for i in closest_regests:
        if i[1] == idx:
            if places.loc[i[0]]['text'] is not None:
                place = places.loc[i[0]]['text']
    if not any(char.isalpha() for char in place):
        if current_place != '':
            if '(„)' in place or '(„' in place or '„)' in place:
                place = '(' + current_place + ')'
                dict['place'].append(place)
            elif '„' in place:
                dict['place'].append(current_place)
            else:
                dict['place'].append(' ')
        else:
            if '(„)' in place or '(„' in place or '„)' in place:
                place = '(' + current_place + ')'
                dict['place'].append('(prev_regest)')
            elif '„' in place:
                dict['place'].append('prev_regest')
            else:
                dict['place'].append(' ')
    else:
        dict['place'].append(place)
        current_place = place  

def get_regest_number(txt: str):
    '''
    Slices the given string so that the regest number at the start of the string gets seperated.

    :param: txt: The string to extract the regest number from
    :type:
    :return: The seperated regest number or False if no number has been found and the remaining text
    '''

    nr_chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '(', ' ']
    slice_idx = 0
    if txt is not None:
        for idx, char in enumerate(txt):
            if char in nr_chars:
                pass
            else:
                if idx == 0:
                    if len(txt) > 1:
                        if txt[idx+1] not in nr_chars:
                            slice_idx = idx
                            break
                else:
                    if txt[idx-1] == ' ':
                        slice_idx = idx
                    elif txt[idx-1] == '(':
                        slice_idx = idx-1
                    else:
                        slice_idx = idx+1
                    break
        regest_nr = txt[:slice_idx]
        txt = txt[slice_idx:]
        if len(txt) > 0:
            if txt[0] == ' ':
                txt = txt[1:]
        
        if len(regest_nr) > 1:
            if regest_nr[-1] == ' ':
                regest_nr = regest_nr[:-1]
        elif len(regest_nr) == 0:
            regest_nr = False

    else:
        regest_nr = False

    return regest_nr, txt

def get_year(txt: str) -> str:
    '''
    Slices the given string so that the year at the start of the string gets seperated.

    :param: txt: The string to extract the year from
    :type txt: str
    :return: The seperated year
    '''

    year_chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '?', '—', '-', ' ']
    slice_idx = len(txt)
    for idx, char in enumerate(txt):
        if char in year_chars:
            pass
        else:
            slice_idx = idx
            break
    txt = txt[:slice_idx]

    return txt

def classify_lines_as_regest(df: pd.DataFrame, final_regest_dict: dict) -> tuple[pd.DataFrame, dict]:
    '''
        Gets a Pandas DataFrame whichs lines already got classified and tries to detect which lines make one regest.

        :param: df: The pandas DataFrame containing the lines to classify
        :type: df: pd.DataFrame
        :param: final_regest_dict: A dictionary conatining lists on keys date, place, number and text to which the final classified regests get added
        :type: final_regest_dict: dict
        :return: The passed DataFrame and the passed dictionary filled with all regests
        :rtype: tuple[pd.DataFrame, dict]
    '''

    current_year = ''
    current_place = ''
    regest_full_text = []
    first_regest = True
    df_regest_start = df[(df['type'] == 'regest_start')]
    df_date = df[(df['type'] == 'date')]
    df_place = df[(df['type'] == 'place')]
    date_closest_regest = get_closest_regest(df_date, df_regest_start, 'date')
    place_closest_regest = get_closest_regest(df_place, df_regest_start, 'place')

    for idx, row in df.iterrows(): # Iterate through all lines
        if row['type'] == 'regest_date': 
            # Get the current year as it is'nt a part of the date column due to Jaffé Layout
            current_year = get_year(row['text'])
        elif row['type'] == 'regest_start':
            # Line is start of a new regest
            if first_regest == False:
                # Finish prior regest by appending its full text to final_regest_dict                
                final_regest_dict['text'].append(merge_to_string(regest_full_text))
                # Start new regest by splitting first line into regest number and text
                regest_nr, txt = get_regest_number(row['text'])
            elif first_regest == True and len(regest_full_text) > 0: 
                # Regest started on previous page
                # Finsish prior regest by appending its full text to final_regest_dict and filling date, place and number with placeholder 'prev_page'
                final_regest_dict['date'] = ['prev_page']
                final_regest_dict['place'] = ['prev_page']
                final_regest_dict['number'] = ['prev_page']
                final_regest_dict['text'].append(merge_to_string(regest_full_text))
                # Start new regest
                txt = row['text']
                regest_nr == False # No regest number, because it is on prev page               
                first_regest = False
            else:
                regest_nr, txt = get_regest_number(row['text'])
                first_regest = False

            # Start new regest by cleaning up the full text list and appending first text line
            regest_full_text = []
            if txt is not None:
                regest_full_text.append(txt)

            # Append regest number to final_regest_dict
            if regest_nr != False:
                final_regest_dict['number'].append(regest_nr)
            else: 
                final_regest_dict['number'].append('')
            
            # Append date of regest to final_regest_dict
            full_date = get_full_date(df_date, date_closest_regest, current_year, idx)
            final_regest_dict['date'].append(full_date)

            # Append place of regest to final_regest_dict
            append_place(final_regest_dict, df_place, place_closest_regest, current_place, idx)

        elif row['type'] == 'regest_text' and first_regest == False:
            # Line is simple text, so just append the lines text to the regests full text list and proceed with next line
            if row['text'] is not None:
                regest_full_text.append(row['text'])
        elif row['type'] == 'regest_text' and first_regest == True:
            # Line ist simple text but start of its regest is on previous page, so fill the regests full text list 
            # but also insert placeholder 'prev_page' into final_regest_dict date, place and number
            final_regest_dict['date'] = ['prev_page']
            final_regest_dict['place'] = ['prev_page']
            final_regest_dict['number'] = ['prev_page']
            if row['text'] is not None:
                regest_full_text.append(row['text'])
            first_regest = False

    if len(regest_full_text) > 0:
        final_regest_dict['text'].append(merge_to_string(regest_full_text)) # don't forget last regest

    return df, final_regest_dict

def classify(scan) -> tuple[pd.DataFrame, pd.DataFrame]:
    '''
        Main classification function. Iterates through each region of the passed scan and manages classification of table region 

        :param: scan: The PageXML scan to classify the regests from
        :type: pagexml.PageXMLScan
        :return: A Pandas DataFrame containing positional data for plotting and Pandas Dataframe containing all regests
        :rtype: tuple[pd.DataFrame, pd.DataFrame]
    '''

    # Get new dictionaries
    textRegion_dict, unknown_region_dict, final_regest_dict = new_dictionaries()

    # Classify basic regions header, date, place, text
    page = detect_page_from_filename(scan.id)
    if page == 'l':
        textRegion_dict, unknown_region_dict, final_regest_dict = classify_left_page_columns(scan, textRegion_dict, unknown_region_dict, final_regest_dict)
    elif page == 'r':
        textRegion_dict, unknown_region_dict, final_regest_dict = classify_right_page_columns(scan, textRegion_dict, unknown_region_dict, final_regest_dict)

    # Data cleansing and preparation for more detailed classification
    df = pd.DataFrame(textRegion_dict)
    df = df.sort_values('y')
    df = df.reset_index(drop=True)
    df['text'] = df['text'].fillna(' ')
    df = detect_new_pope(df)
    df = detect_first_line_pope_overview(df)
    df = drop_unnecessary(df)

    # Detailed classification of the text region lines
    df = classify_regest_start(df)  
    df = classify_textregion_date(df)
    
    # Combine lines into whole regests
    df, final_regest_dict = classify_lines_as_regest(df, final_regest_dict)

    i = 0
    while i < len(final_regest_dict['date']):
        if i >= len(final_regest_dict['pope']):
            if len(final_regest_dict['pope']) == 0:
                final_regest_dict['pope'].append('')
            else:
                final_regest_dict['pope'].append(final_regest_dict['pope'][0])
        i += 1

    # In case of classification problems atleast append an empty string and get all lists to the same length to prevent export problems
    max_len = max(len(lst) for lst in final_regest_dict.values())
    for key, lst in final_regest_dict.items():
        while len(lst) < max_len:
            if key == 'pope':
                lst.append(lst[0] if lst else '')
            else:
                lst.append('')

    final_df = pd.DataFrame(final_regest_dict)

    return df, final_df