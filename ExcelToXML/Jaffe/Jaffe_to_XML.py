# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
from lxml import etree
import pandas as pd
import re
import calendar
from datetime import datetime

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Globals
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
INPUT_PATH = "ExcelToXML/Jaffe/input/Jaffe_Korrekturdatei_I_komplett.xlsx"
OUTPUT_FOLDER = "output"

# A dictionary mapping excel columns and its corresponding xml elements
COLUMNS_XML_MAP = { # "excel_column": "xml" 
    "pope": "legal_actor_issuer_inner",
    # year, month, date sind Sonderfälle
    "place": "place_name",
    "JL": "bibl_jaffe",
    "J": "bibl_jaffe_alt",
    "incipit": "incipit_diploPart",
    "abstract": "abstract_p",
    "commentary": "commentary_p",
    "editions": "editions_list_bibl",
    "decretals": "decretals_list_bibl",
}
# A dictionary mapping xml elements and its default content
XML_DEFAULT_CONTENT_MAP = { # "xml": "content"
    "title": "[Die Nummer des Regests im Projekt]",
    "resp1": "Ursprünglicher Bearbeiter/Bearbeiter Datenquelle",
    "pers_name1": "[Vorname und Nachname der Bearbeiter*in]",
    "resp2": "Encoding:",
    "pers_name2": "[Vorname und Nachname der Überarbeiter*in/Auszeichnung]",
    "publisher": "Die Formierung Europas",
    "idno": "",
    "licence": "Lizenz",
    "bibl_jaffe": "[JL-Nummer]",
    "bibl_jaffe_alt": "[Jaffe-Nummer 1. Auflage]",
    "place_name": "[Ausstellungsort]",
    "date": "[Ausstellungsdatum]",
    "date_notBefore": "1000-01-01",
    "date_notAfter": "1000-01-01",
    "legal_actor_issuer_inner": "[Issuer]",
    "legal_actor_recipient_inner": "[Recipient 1]",
    "object_type_inner": "[Typisierung 1]",
    "abstract_p": "[Regestentext kann diploParts mit Sprachangabe enthalten.]",
    "authen_p": "[*+?-]",
    "incipit_diploPart": "[Lorem ipsum dolor sit amet]",
    "datatio_diploPart": "-",
    "ms_list_bibl": "[Handschrift oder Alter Druck]",
    "decretals_list_bibl": "[Dekretale 1]",
    "historiography_list_bibl": "[i.d.R. nach Edition, also Literaturtitel zitiert]",
    "editions_list_bibl": "[Edition 1]",
    "regesta_list_bibl": "[Regest 1]",
    "commentary_p": "[Inhalt des Sachkommentars. Bibliographische Referenzen werden als <bibl>Bibliographische Angabe</bibl> getagged.]",
    "archival_history_bibl": "[Weitere Referenzen als listBibl]",
    "notes_p": "[Anmerkungen, Notizen und Fragen der Bearbeiter*in.]",
}

MONTH_DICT = {
    'januar': '01', 'janr': '01', 'ianuar': '01', 'ianr': '01',
    'februar': '02',
    'märz': '03', 'mart': '03', 'maerz': '03',
    'april': '04',
    'may': '05', 'mai': '05',
    'iuni': '06', 'juni': '06',
    'iuli': '07', 'juli': '07',
    'august': '08',
    'september': '09',
    'october': '10', 'oktober': '10',
    'november': '11',
    'december': '12', 'dezember': '12'
}

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
def get_month_digits(month_str: str) -> str:
    """
    Converts a month name or abbreviation to its corresponding digits.
    Args:
        month_str (str): The name or abbreviation of the month (e.g., "January", "Jan", "Feb").
    Returns:
        int: The digits corresponding to the month (01 for January, 02 for February, etc.),
        None if the input does not match any month in the MONTH_DICT.
    """
    
    for key, value in MONTH_DICT.items():
        if re.search(month_str.lower(), key):
            return value
    return "" 

def check_for_timespan(date_value: str, year: str) -> tuple[str, str]:  
    '''
        Checks the passed date_value string for a possible timespan returns either both timespan components or just the passed date_value.

        :param: date_value: The string which gets checked
        :return: First and last date of timespan or date_value if no timespan got detected
    '''
    date_value = str(date_value)
    if year == "": 
        # No entry
        first, last = "", ""

    elif any(c in date_value for c in ["-", "—","–", "/"]): 
        # Timespan detected because of '-' similar char
        parts = re.split(r"[-—–/]", date_value, maxsplit=1)
        first, last = parts[0], parts[1]

    elif re.search(r"(?<=\d)\s(?=\d)|(?<!\d)\s(?!\d)|(?<=\d\.)\s(?=\d)|(?<=\D\.)\s(?=\D)", date_value): 
        # Timespan detecteed because of whitespace
        parts = re.split(r"\s", date_value, maxsplit=1)
        first, last = parts[0], parts[1]

    else: 
        # No timespan
        first, last = date_value, date_value
    
    return first, last

def build_date(year: str, month: str, day: str, xml_content_map_instance: dict, id: str):
    '''
        Inlucdes correct date content into xml_content_map_instance including correct notBefore/notAfters attributes

        :param: year: Year or year range string string
        :param: month: Month or month range string
        :param: day: Day or day range string
        :param: xml_content_map_instance: The instance of the xml_content_map dict in which the dates get inserted
        :param: id: The lfdnr of the current row for debugging purposes
    '''
    year = "" if pd.isna(year) else str(year)
    month = "" if pd.isna(month) else str(month)
    day = "" if pd.isna(day) else str(day)

    # Build date element content
    xml_content_map_instance["date"] = f"{day.replace('[', '(').replace(']', ')')} {month} {year}"

    # Detect timespan for year, month and date to prepare notBefore/notAfter attributes
    firstYear, lastYear = check_for_timespan(year, year)
    if firstYear == "" or lastYear == "":
        firstYear, lastYear = "1159", "1181"
    else:
        firstYear, lastYear = re.sub(r"\D", "", firstYear), re.sub(r"\D", "", lastYear) # Remove non-digit characters

    firstMonth, lastMonth = check_for_timespan(month, year)
    firstMonth, lastMonth = re.sub(r"[^a-zA-ZäöüÄÖÜß]", "", firstMonth), re.sub(r"[^a-zA-ZäöüÄÖÜß]", "", lastMonth) # Remove non-alphabetic characters
    if firstMonth != "" or lastMonth != "":
        firstMonth, lastMonth = get_month_digits(firstMonth), get_month_digits(lastMonth)
    else:
        firstMonth, lastMonth = "01", "12" # If month is not found -> get full year timespan

    firstDay, lastDay = check_for_timespan(day, year)
    firstDay, lastDay = re.sub(r'\D', '', firstDay), re.sub(r'\D', '', lastDay) # Remove non-digit characters
    firstDay, lastDay = firstDay.zfill(2), lastDay.zfill(2) # Ensure two digits for day
    if firstDay == '00': # Happens if day is not found
        firstDay = '01'  # Day is not found -> get full month timespan  
        try:
            _, last_day_of_month = calendar.monthrange(int(lastYear), int(lastMonth))
            lastDay = str(last_day_of_month).zfill(2)    
        except ValueError as e:
            print(f'{id}, {year}.{month}.{day}: Cant get first and last day of month: {e}')    

    # Build date notBefore/notAfter attributes if possible
    try:
        notBefore = f"{firstYear}-{firstMonth}-{firstDay}"
        datetime.strptime(notBefore, "%Y-%m-%d")
        notAfter = f"{lastYear}-{lastMonth}-{lastDay}"
        datetime.strptime(notAfter, "%Y-%m-%d")
    except ValueError as e:
        print(f'{id}, {year}.{month}.{day}: Cant build full date: {e}')
        notBefore, notAfter = None, None
        return

    # Insert otBefore/notAfter values into xml_content_map instance
    xml_content_map_instance["date_notBefore"] = notBefore 
    xml_content_map_instance["date_notAfter"] = notAfter

def create_tei_xml(output_file: str, lfdN: str):
    '''
        Builds the final xml output file based on the xml_content_map_instance content

        :param: output_file: The output filename
        :param: lfdN: The id
    '''
    # Define namespaces
    namespaces = {
        None: "http://www.tei-c.org/ns/1.0",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    }

    # Root element
    tei = etree.Element("TEI", nsmap=namespaces, source="formierung-europas_jaffe")

    # teiHeader
    tei_header = etree.SubElement(tei, "teiHeader")
    file_desc = etree.SubElement(tei_header, "fileDesc")
    title_stmt = etree.SubElement(file_desc, "titleStmt")
    title = etree.SubElement(title_stmt, "title")
    title.text = str(xml_content_map_instance["title"])

    resp_stmt1 = etree.SubElement(title_stmt, "respStmt")
    resp1 = etree.SubElement(resp_stmt1, "resp")
    resp1.text = str(xml_content_map_instance["resp1"])
    pers_name1 = etree.SubElement(resp_stmt1, "persName")
    pers_name1.text = str(xml_content_map_instance["pers_name1"])

    resp_stmt2 = etree.SubElement(title_stmt, "respStmt")
    resp2 = etree.SubElement(resp_stmt2, "resp", attrib={"when": "2024"})
    resp2.text = str(xml_content_map_instance["resp2"])
    pers_name2 = etree.SubElement(resp_stmt2, "persName")
    pers_name2.text = str(xml_content_map_instance["pers_name2"])

    publication_stmt = etree.SubElement(file_desc, "publicationStmt")
    publisher = etree.SubElement(publication_stmt, "publisher")
    publisher.text = str(xml_content_map_instance["publisher"])
    idno = etree.SubElement(publication_stmt, "idno")
    if str(xml_content_map_instance["bibl_jaffe"]) != str(XML_DEFAULT_CONTENT_MAP["bibl_jaffe"]):
        if str(xml_content_map_instance["bibl_jaffe_alt"]) != str(XML_DEFAULT_CONTENT_MAP["bibl_jaffe_alt"]):
            idno_text = f'{str(xml_content_map_instance["bibl_jaffe"])}_{lfdN}_{str(xml_content_map_instance["bibl_jaffe_alt"])}'
        else:
            idno_text = f'{str(xml_content_map_instance["bibl_jaffe"])}_{lfdN}'
    else:
        idno_text = ""
    idno.text = idno_text
    availability = etree.SubElement(publication_stmt, "availability")
    licence = etree.SubElement(availability, "licence")
    licence.text = str(xml_content_map_instance["licence"])

    source_desc = etree.SubElement(file_desc, "sourceDesc")
    bibl_jaffe = etree.SubElement(source_desc, "bibl", attrib={"type": "jaffe"})
    bibl_jaffe.text = str(xml_content_map_instance["bibl_jaffe"])
    bibl_jaffe_alt = etree.SubElement(source_desc, "bibl", attrib={"type": "jaffe_alt"})
    bibl_jaffe_alt.text = str(xml_content_map_instance["bibl_jaffe_alt"])    

    diplo_desc = etree.SubElement(source_desc, "diploDesc")
    issued = etree.SubElement(diplo_desc, "p")
    issued_inner = etree.SubElement(issued, "issued")
    place_name = etree.SubElement(issued_inner, "placeName")
    place_name.text = str(xml_content_map_instance["place_name"])
    date = etree.SubElement(issued_inner, "date", attrib={
        "type": "issued",
        "notBefore": str(xml_content_map_instance["date_notBefore"]),
        "notAfter": str(xml_content_map_instance["date_notAfter"])
    })
    date.text = str(xml_content_map_instance["date"])

    legal_actor_issuer = etree.SubElement(diplo_desc, "p")
    legal_actor_issuer_inner = etree.SubElement(legal_actor_issuer, "legalActor", attrib={"type": "issuer"})
    legal_actor_issuer_inner.text = str(xml_content_map_instance["legal_actor_issuer_inner"])

    legal_actor_recipient = etree.SubElement(diplo_desc, "p")
    legal_actor_recipient_inner = etree.SubElement(legal_actor_recipient, "legalActor", attrib={"type": "recipient"})
    legal_actor_recipient_inner.text = str(xml_content_map_instance["legal_actor_recipient_inner"])     

    object_type = etree.SubElement(diplo_desc, "p")
    object_type_inner = etree.SubElement(object_type, "objectType")
    object_type_inner.text = str(xml_content_map_instance["object_type_inner"])

    # profileDesc
    profile_desc = etree.SubElement(tei_header, "profileDesc")
    lang_usage = etree.SubElement(profile_desc, "langUsage")
    etree.SubElement(lang_usage, "language", attrib={"ident": "ger"}).text = "German"
    etree.SubElement(lang_usage, "language", attrib={"ident": "lat"}).text = "Latin"
    etree.SubElement(lang_usage, "language", attrib={"ident": "en-GB"}).text = "English"

    # xenoData
    xeno_data = etree.SubElement(tei_header, "xenoData")
    rdf = etree.SubElement(xeno_data, "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF", nsmap={
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "as": "http://www.w3.org/ns/activitystreams#",
        "cwrc": "http://sparql.cwrc.ca/ontologies/cwrc#",
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcterms": "http://purl.org/dc/terms/",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "geo": "http://www.geonames.org/ontology#",
        "oa": "http://www.w3.org/ns/oa#",
        "schema": "http://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "fabio": "https://purl.org/spar/fabio#",
        "bf": "http://www.openlinksw.com/schemas/bif#",
        "cito": "https://sparontologies.github.io/cito/current/cito.html#",
        "org": "http://www.w3.org/ns/org#"
    })

    # text
    text = etree.SubElement(tei, "text")
    body = etree.SubElement(text, "body")

    # Abstract
    abstract_div = etree.SubElement(body, "div", attrib={"type": "abstract"})
    etree.SubElement(abstract_div, "head").text = "Abstract:"
    etree.SubElement(abstract_div, "p").text = str(xml_content_map_instance["abstract_p"])

    # Echtheitskriterien
    authen_div = etree.SubElement(body, "div", attrib={"type": "other"})
    etree.SubElement(authen_div, "head").text = "Echtheitskriterien:"
    authen = etree.SubElement(authen_div, "authen", attrib={"type": "formula"})
    etree.SubElement(authen, "p").text = str(xml_content_map_instance["authen_p"])

    # Incipit
    incipit_div = etree.SubElement(body, "div")
    etree.SubElement(incipit_div, "head").text = "Incipit:"
    etree.SubElement(incipit_div, "diploPart", attrib={"type": "incipit", "{http://www.w3.org/XML/1998/namespace}lang": "lat"}).text = str(xml_content_map_instance["incipit_diploPart"])

    # Datatio
    datatio_div = etree.SubElement(body, "div")
    etree.SubElement(datatio_div, "head").text = "Datatio:"
    etree.SubElement(datatio_div, "diploPart", attrib={"type": "datatio"}).text = str(xml_content_map_instance["datatio_diploPart"])

    # Handschriftliche Überlieferung
    ms_sources_div = etree.SubElement(body, "div", attrib={"type": "msSources"})
    etree.SubElement(ms_sources_div, "head").text = "Handschriftliche Überlieferung und alte Drucke"
    ms_list_bibl = etree.SubElement(ms_sources_div, "listBibl")
    etree.SubElement(ms_list_bibl, "bibl").text = str(xml_content_map_instance["ms_list_bibl"])

    # Dekretalen
    decretals_div = etree.SubElement(body, "div", attrib={"type": "decretals"})
    etree.SubElement(decretals_div, "head").text = "Dekretalen"
    decretals_list_bibl = etree.SubElement(decretals_div, "listBibl")
    etree.SubElement(decretals_list_bibl, "bibl").text = str(xml_content_map_instance["decretals_list_bibl"])

    # Historiography
    historiography_div = etree.SubElement(body, "div", attrib={"type": "historiography"})
    etree.SubElement(historiography_div, "head").text = "Erwähnungen in der Historiographie"
    historiography_list_bibl = etree.SubElement(historiography_div, "listBibl")
    etree.SubElement(historiography_list_bibl, "bibl").text = str(xml_content_map_instance["historiography_list_bibl"])

    # Editions
    editions_div = etree.SubElement(body, "div", attrib={"type": "editions"})
    etree.SubElement(editions_div, "head").text = "Editionen"
    editions_list_bibl = etree.SubElement(editions_div, "listBibl")
    etree.SubElement(editions_list_bibl, "bibl").text = str(xml_content_map_instance["editions_list_bibl"])

    # Regesta
    regesta_div = etree.SubElement(body, "div", attrib={"type": "regesta"})
    etree.SubElement(regesta_div, "head").text = "Regesten"
    regesta_list_bibl = etree.SubElement(regesta_div, "listBibl")
    etree.SubElement(regesta_list_bibl, "bibl").text = str(xml_content_map_instance["regesta_list_bibl"])

    # Commentary
    commentary_div = etree.SubElement(body, "div", attrib={"type": "commentary"})
    etree.SubElement(commentary_div, "head").text = "Sachkommentar"
    etree.SubElement(commentary_div, "p").text = str(xml_content_map_instance["commentary_p"])

    # Bibliography
    archival_history_div = etree.SubElement(body, "div", attrib={"type": "bibliography"})
    etree.SubElement(archival_history_div, "head").text = "Bibliographie"
    archival_history_bibl = etree.SubElement(archival_history_div, "listBibl")
    etree.SubElement(archival_history_bibl, "bibl").text = str(xml_content_map_instance["archival_history_bibl"]) 

    # Notes
    notes_div = etree.SubElement(body, "div", attrib={"type": "note"})
    etree.SubElement(notes_div, "head").text = "Fußnoten"
    etree.SubElement(notes_div, "p").text = str(xml_content_map_instance["notes_p"])

    # Write to file with processing instructions
    with open(output_file, "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(b'<?xml-model href="https://raw.githubusercontent.com/cceh/FormierungEuropas/refs/heads/main/CEI_TEI_Schema/tei_cei_formierung_edited.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n')
        f.write(b'<?xml-stylesheet type="text/css" href="https://raw.githubusercontent.com/hannahbusch/Formierung_Europas_wip/master/style.css"?>\n')
        f.write(etree.tostring(tei, pretty_print=True, xml_declaration=False, encoding="UTF-8"))
    print(f"XML-Datei wurde erstellt: {output_file}")

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
if __name__ == '__main__':
    df = pd.read_excel(INPUT_PATH, header=0, dtype=str)

    # Create seperate xml file for each regest
    for _, row in df.iterrows():
        id = row["LfdNrFinal"]
        xml_content_map_instance = XML_DEFAULT_CONTENT_MAP.copy() # Create an instance of xml_content_map to replace its values with the excel content

        for col, value in row.items():

            if col in COLUMNS_XML_MAP and str(value) != "nan" and value is not None and not pd.isna(value):
                # If the excel column is in the columns_xml_map replace this rows value in the xml_content_map instance
                try:
                    xml_content_map_instance[COLUMNS_XML_MAP[col]] = value
                except:
                    print(f"{id}: Spalte '{col}' nicht in xml_content_map_instance gefunden.")

        # Build date element content and attributes since it is slightly more comlicated than other elements
        build_date(row["year"], row["month"], row["day"], xml_content_map_instance, id)

        # Create actual xml output file from the xml_content_map instance
        output_file = f"{OUTPUT_FOLDER}/Jaffe_{id}.xml"
        create_tei_xml(output_file, id)