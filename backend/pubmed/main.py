"""
PubMed Data Processing and Transformation Tool

This script downloads, processes, and transforms PubMed XML data into structured JSON format.
It handles various data types including articles, authors, affiliations, and keywords.

Features:
- Downloads compressed XML files from PubMed FTP server
- Extracts and parses XML data to JSON
- Processes dates, authors, affiliations, and keywords
- Groups and aggregates data based on specified columns
- Outputs both raw CSV and processed JSON formats

Required Packages:
- wget: For downloading files from FTP server
- gzip: For handling compressed files
- xmltodict: For XML to dictionary conversion
- pandas: For data processing and transformation
- pathlib: For cross-platform path handling

Usage:
    python main.py

The script will:
1. Download the specified PubMed XML file
2. Extract and parse the XML data
3. Transform the data with proper grouping
4. Save results in both CSV and JSON formats
"""

import wget
import gzip
import xmltodict
import json
import pandas as pd
from pathlib import Path


# Configuration constants
url='https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed25n1274.xml.gz'
output_directory = Path(__file__).parent / 'data'  # Creates 'data' directory in same folder as script
output_directory.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist

# Column configurations
required_columns=['MedlineCitation.PMID.#text','MedlineCitation.DateRevised.Year','MedlineCitation.DateRevised.Month','MedlineCitation.DateRevised.Day','MedlineCitation.Article.Journal.ISSN.#text','MedlineCitation.Article.Journal.JournalIssue.Volume','MedlineCitation.Article.Journal.JournalIssue.Issue','MedlineCitation.Article.Journal.Title','MedlineCitation.Article.Journal.ISOAbbreviation','MedlineCitation.Article.ArticleTitle','MedlineCitation.Article.Pagination.MedlinePgn','MedlineCitation.Article.Abstract.AbstractText.i','MedlineCitation.Article.Abstract.AbstractText.#text','MedlineCitation.Article.AuthorList.Author','MedlineCitation.Article.Language','MedlineCitation.Article.PublicationTypeList.PublicationType.@UI','MedlineCitation.Article.PublicationTypeList.PublicationType.#text','MedlineCitation.Article.ArticleDate.Year','MedlineCitation.Article.ArticleDate.Month','MedlineCitation.Article.ArticleDate.Day','MedlineCitation.MedlineJournalInfo.Country','MedlineCitation.MedlineJournalInfo.MedlineTA','MedlineCitation.MedlineJournalInfo.NlmUniqueID','MedlineCitation.MedlineJournalInfo.ISSNLinking','MedlineCitation.KeywordList.Keyword','MedlineCitation.CoiStatement']
groupby_columns=['MedlineCitation.PMID.text','MedlineCitation.Article.Journal.ISSN.text','MedlineCitation.Article.Journal.JournalIssue.Volume','MedlineCitation.Article.Journal.JournalIssue.Issue','MedlineCitation.Article.Journal.Title','MedlineCitation.Article.Journal.ISOAbbreviation','MedlineCitation.Article.ArticleTitle','MedlineCitation.Article.Pagination.MedlinePgn','MedlineCitation.Article.Abstract.AbstractText.i','MedlineCitation.Article.Abstract.AbstractText.text','MedlineCitation.Article.Language','MedlineCitation.Article.PublicationTypeList.PublicationType.UI','MedlineCitation.Article.PublicationTypeList.PublicationType.text','MedlineCitation.MedlineJournalInfo.Country','MedlineCitation.MedlineJournalInfo.MedlineTA','MedlineCitation.MedlineJournalInfo.NlmUniqueID','MedlineCitation.MedlineJournalInfo.ISSNLinking','MedlineCitation.CoiStatement', 'DateRevised', 'ArticleDate', 'ValidYN','LastName', 'ForeName', 'Initials', 'IdentifierSource','Identifiertext', 'EqualContrib', 'AffiliationInfoIdentifierSource','AffiliationInfoIdentifiertext', 'CollectiveName', 'Suffix','IdentifierAffln_Source', 'IdentifierAffln_text','MajorTopicYN']
agg_columns=['Affiliations', 'text']  # Columns to aggregate during grouping
raw_data='pubmed_raw.csv'  # Filename for raw data output
final_data='pubmed_final.csv'  # Filename for processed data output

def download_unzip_file(url: str, output_directory: str) -> tuple:
    """
    Downloads a file from PubMed FTP server to specified directory.
    
    Args:
        url (str): URL of the file to download
        output_directory (str): Directory to save the downloaded file
        
    Returns:
        tuple: (filename, path) of the downloaded file
        
    Raises:
        wget.Error: If download fails
    """
    output_directory = Path(output_directory)  # Convert to Path object
    wget.download(url, out=str(output_directory))
    file_name = url.rsplit('/', 1)
    print(f"\n{file_name[1]} is downloaded successfully from url - {file_name[0]} to local directory {output_directory}")
    return file_name


def unzip_files(gz_file: str, xml_file: str) -> str:
    """
    Extracts a gzipped XML file.
    
    Args:
        gz_file (str): Path to the gzipped file
        xml_file (str): Path where the extracted XML should be saved
        
    Returns:
        str: Path to the extracted XML file
    """
    with gzip.open(gz_file, 'rb') as gz:
        with open(xml_file, 'wb') as xml:
            xml.write(gz.read())
    print(f"Unzipped {gz_file} to {xml_file}.")
    return xml_file

def parse_xml_to_json(xml_file: str, json_file: str) -> None:
    """
    Converts XML file to JSON format.
    
    Args:
        xml_file (str): Path to input XML file
        json_file (str): Path where JSON should be saved
        
    Raises:
        xmltodict.ParsingError: If XML parsing fails
    """
    with open(xml_file, encoding="utf8") as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
        json_data = json.dumps(data_dict)

    with open(json_file, "w") as json_file:
        json_file.write(json_data)

def date_conversion(df: pd.DataFrame, column_names: list) -> pd.DataFrame:
    """
    Combines separate year, month, day columns into a single datetime column.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        column_names (list): List of date column prefixes to process
        
    Returns:
        pd.DataFrame: DataFrame with processed date columns
    """
    for date in column_names:
        columnName = date.split('.')[1] if '.' in date else date
        df[columnName] = pd.to_datetime(
            df[f'MedlineCitation.{date}.Month'] + '/' + 
            df[f"MedlineCitation.{date}.Day"] + '/' + 
            df[f"MedlineCitation.{date}.Year"]
        )
        df.drop(
            [f'MedlineCitation.{date}.Month',
             f"MedlineCitation.{date}.Day",
             f"MedlineCitation.{date}.Year"],
            axis='columns', 
            inplace=True
        )
    return df

def list_to_df(df: pd.DataFrame, column_name: str, sep: str = None) -> pd.DataFrame:
    """
    Expands a column containing lists or nested data into separate columns.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        column_name (str): Name of column to expand
        sep (str, optional): Separator for new column names
        
    Returns:
        pd.DataFrame: DataFrame with expanded columns
    """
    df = df.explode(column_name)
    df = df.reset_index(drop=True)
    df = pd.concat([df, pd.json_normalize(df[column_name], sep=sep)], axis=1)
    return df

def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans up column names by removing special characters.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with cleaned column names
    """
    df.columns = df.columns.str.replace('@', '')
    df.columns = df.columns.str.replace('#', '')
    return df

def data_transformation(json_file: str) -> None:
    """
    Main data transformation function that processes PubMed data.
    
    This function:
    1. Loads JSON data into a DataFrame
    2. Processes dates, authors, affiliations, and keywords
    3. Groups and aggregates data
    4. Saves results in both CSV and JSON formats
    
    Args:
        json_file (str): Path to input JSON file
        
    Raises:
        Exception: If any transformation step fails
    """
    # Load and initialize data
    with open(json_file) as f:
        data = json.load(f)
    
    df = pd.json_normalize(data['PubmedArticleSet']['PubmedArticle'])
    raw_output = output_directory / raw_data
    df.to_csv(raw_output)
    print("Shape of Dataframe initially", df.shape)
    
    # Select and process columns
    existing_cols = [col for col in required_columns if col in df.columns]
    df = df[existing_cols]
    
    # Process dates
    df = date_conversion(df, ['DateRevised', 'Article.ArticleDate'])
    
    # Process authors and affiliations
    df = list_to_df(df, 'MedlineCitation.Article.AuthorList.Author', '')
    print("Shape of Dataframe after exploding Author List", df.shape)
    
    # Process affiliations if present
    if 'AffiliationInfo' in df.columns:
        df = list_to_df(df, 'AffiliationInfo', 'Affln_')
        df['Affiliations'] = df['AffiliationInfoAffiliation'].fillna('') + df['Affiliation'].fillna('')
    print("Shape of Dataframe after exploding Affiliation", df.shape)
    
    # Process keywords if present
    if 'MedlineCitation.KeywordList.Keyword' in df.columns:
        df = list_to_df(df, 'MedlineCitation.KeywordList.Keyword', 'Keyword_')
    print("Shape of Dataframe after exploding Keywords", df.shape)
    
    # Clean up processed columns
    columns_to_drop = ['MedlineCitation.KeywordList.Keyword', 'AffiliationInfo', 
                      'AffiliationInfoAffiliation', 'Affiliation', 
                      'MedlineCitation.Article.AuthorList.Author']
    existing_cols_to_drop = [col for col in columns_to_drop if col in df.columns]
    df.drop(existing_cols_to_drop, axis='columns', inplace=True)
    
    # Clean up data
    df = rename_columns(df)
    df = df.fillna('')
    
    # Convert datetime columns to string format
    datetime_cols = df.select_dtypes(include=['datetime64']).columns
    for col in datetime_cols:
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    
    # Save intermediate state
    temp_file = output_directory / 'temp_file.csv'
    df.to_csv(temp_file, index=False)
    
    try:
        # Prepare for grouping
        clean_groupby_cols = [col.replace('#', '').replace('@', '') for col in groupby_columns]
        valid_group_cols = [col for col in clean_groupby_cols if col in df.columns]
        valid_agg_cols = [col for col in agg_columns if col in df.columns]
        
        print(f"Grouping by {len(valid_group_cols)} columns")
        print(f"Aggregating {len(valid_agg_cols)} columns")
        
        # Perform grouping and aggregation
        if not valid_group_cols or not valid_agg_cols:
            print("Warning: Missing required columns for grouping")
            output_data = df
        else:
            # Convert grouping columns to string
            for col in valid_group_cols:
                df[col] = df[col].astype(str)
            
            # Group and aggregate data
            grouped = df.groupby(valid_group_cols, dropna=False)
            output_data = grouped[valid_agg_cols].agg(list).reset_index()
            
            # Clean up aggregated lists
            for col in valid_agg_cols:
                output_data[col] = output_data[col].apply(
                    lambda x: list(set(i for i in x if i and str(i).strip()))
                )
        
        # Save final output as JSON
        final_output = output_directory / 'pubmed_final.json'
        result = output_data.to_dict(orient='records')
        
        with open(final_output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved JSON with {len(result)} records")
        print(f"Output file: {final_output}")
        
    except Exception as e:
        print(f"Error during transformation: {str(e)}")
        error_file = output_directory / 'error_state.csv'
        df.to_csv(error_file, index=False)
        print(f"Error state saved to: {error_file}")
        raise
    
    print("Data transformation complete")


if __name__ == "__main__":
    # Execute main workflow
    file_name = download_unzip_file(url, str(output_directory))

    name = file_name[1].rsplit('.',1)[0]
    download_zip_file = output_directory / file_name[1]
    download_unzip_file = output_directory / name
    xml_file = unzip_files(str(download_zip_file), str(download_unzip_file))

    json_file = str(Path(xml_file).with_suffix('.json'))
    parse_xml_to_json(xml_file, json_file)
    print(f"{xml_file} is parsed and saved to json file - {json_file}")
    data_transformation(json_file)
