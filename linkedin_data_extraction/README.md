# LinkedIn Data Extraction

This project contains code for extracting and analyzing data from LinkedIn using the unofficial LinkedIn API. It allows searching and retrieving information about LinkedIn users based on various criteria like keywords, location, and job titles.

[View LinkedIn Data Extraction Code](./linkedin_data_extraction)

## Features

- Search for LinkedIn users based on:
  - Keywords (e.g., skills, job titles)
  - Geographic regions
  - Current/past companies
  - Industries
  - Schools
  - And more search parameters

- Extract user profile information including:
  - Name
  - Current job title
  - Location
  - Network distance
  - Unique identifier (URN)

## Usage

The main functionality is implemented in a Jupyter notebook (`linkedin_data_extraction.ipynb`) which demonstrates:

1. Authentication with LinkedIn credentials
2. Performing searches with specific criteria
3. Processing and analyzing the returned user data

## Requirements

- Python 3.x
- pandas
- numpy
- linkedin_api

## Note

This project uses the unofficial LinkedIn API. Please ensure you comply with LinkedIn's terms of service and rate limits when using this code.

## Disclaimer

This code is for educational purposes only. Users are responsible for ensuring their use of the LinkedIn API complies with LinkedIn's terms of service and applicable laws.
