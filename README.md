# Jaffe_Annotation_Basic
Repository for automatic annotation and postprocessing of PageXML transcriptions of Philipp Jaffés *Regesta pontificum romanorum : ab condita ecclesia ad annum post Christum natum MCXCVIII.*. 
Transcription has been done with eScriptorium. You can find the finetuned segmentation and transcription models in the *models* folder.


### Annotation
Main file is for annotation handling. It classifies pope, date, place, jaffé number, regest text, and incipit for each regest. 
Input files must be either single PageXML files or zip archives of PageXML files. Input files must be located in *data/input* folder and should contain the jaffe page number in its names (which is standard for eScriptorium PageXML export).
Possible output formats are tsv, csv, excel, xml (either as one file or one file for each regest).

### Postprocessing
Postprocessing file provides an automatic dictionary based correction of the annotated transcription text. The dictionary file in the *data/static* folder got build with the help of manual corrected transcriptions.
Input files must be excel files and be located in *data/output* folder.
Output file will be a corrected excel file.  

### XML Conversion
*ExcelToXML* folder provides scripts to convert the manual corrected excel files into valid xml files.
