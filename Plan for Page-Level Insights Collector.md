Plan: Facebook Marketing API Insights Collector
1. Project Objective
To create a Python script that automatically fetches daily ad performance data from the Facebook Marketing API for a specified Ad Account. The script will process this data, including specified breakdowns, and append it to a dedicated Google Sheet.

2. Core Requirements
Authentication: Utilize an access token that has been granted the ads_read permission.

Configuration: The script must be configurable for the Ad Account ID, access token, desired metrics (fields), and desired dimensions (breakdowns).

Data Scope:

Collect time-series data at the campaign or ad level.

Aggregate key performance indicators (KPIs) like spend, impressions, clicks, and cost-per-click.

Data Storage: Append the collected data to a new, dedicated worksheet in Google Sheets, ensuring no duplicate entries. A unique record will be defined by its date, campaign ID, and any applied breakdowns.

3. Technical Plan
Step 1: Configuration
The script will start with a dedicated configuration block for the Marketing API.

MARKETING_CONFIG:

MARKETING_CONFIG = {
    'ad_account_id': 'act_xxxxxxxxxxxxxxx', # IMPORTANT: Ad Account ID, prefixed with 'act_'
    'access_token': 'YOUR_ADS_READ_ACCESS_TOKEN',
    'api_version': 'v23.0'
}

GOOGLE_SHEETS_CONFIG: Update to point to a new worksheet.

GOOGLE_SHEETS_CONFIG = {
    'credentials_path': '/path/to/your/credentials.json',
    'spreadsheet_name': 'Faceboook Insights Metrics_Data Warehouse',
    'worksheet_name': 'raw_marketing_data' # New worksheet
}

INSIGHTS_CONFIG: A new dictionary to define the query parameters.

INSIGHTS_CONFIG = {
    'level': 'campaign', # ad, adset, or campaign
    'fields': [
        'campaign_name',
        'spend',
        'impressions',
        'clicks',
        'cpc',
        'ctr',
        'reach'
    ],
    'breakdowns': [
        'publisher_platform',
        'device_platform'
    ] # e.g., ['country'], or empty list [] for no breakdowns
}

Step 2: Core Functions
fetch_marketing_insights(config, insights_config, since, until)

Purpose: Fetch ad performance data.

Endpoint: /{ad_account_id}/insights

Logic:

Construct the API request parameters:

level: From insights_config.

fields: Comma-separated string from insights_config.

breakdowns: Comma-separated string from insights_config.

time_range: A JSON string like {'since': 'YYYY-MM-DD', 'until': 'YYYY-MM-DD'}.

time_increment: Hardcode to 1 to get daily data.

The API returns a list of objects, with each object representing a single day for a specific breakdown combination.

Handle pagination using the paging.next URL provided in the API response until all data is fetched.

Return: A list of flat dictionaries, where each dictionary is a single row of data (e.g., { 'date_start': '...', 'campaign_name': '...', 'spend': 10.50, 'publisher_platform': 'facebook', ... }).

process_marketing_data(insights_data, ad_account_id)

Purpose: Convert the raw list of dictionaries into a clean Pandas DataFrame.

Logic:

Directly convert the list from the fetch function into a DataFrame: pd.DataFrame(insights_data).

Add supplementary columns like fetch_date and ad_account_id.

Rename columns for clarity (e.g., date_start to date).

Ensure data types are correct (e.g., numeric fields are floats/integers).

Return: A clean Pandas DataFrame.

write_data_to_google_sheets(...): This function will be adapted from the existing notebook.

De-duplication Logic: The unique key for a row will be a combination of date, campaign_id, and all breakdown columns (e.g., publisher_platform, device_platform).

Step 3: Main Execution Flow
A main() function will orchestrate the process:

Initialization: Set the date range (e.g., last 30 days).

Connections: Set up and test connections to the Facebook API and Google Sheets.

Fetch: Call fetch_marketing_insights() to retrieve the data.

Process: Call process_marketing_data() to create the DataFrame.

Write: Call write_data_to_google_sheets() to append the new, unique data to the marketing worksheet.

Logging: Provide clear status updates throughout the execution.