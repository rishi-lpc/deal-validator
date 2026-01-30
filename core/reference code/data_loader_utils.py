from simple_salesforce import Salesforce
import requests
import secrets
import base64
import hashlib
import pandas as pd
import numpy as np


# Function to remove keys with None values from a dictionary
def remove_none_fields(input_dict):
    for record in input_dict:
        # Create a list of keys to avoid modifying the dictionary while iterating
        keys_to_remove = [key for key in record.keys() if record[key] is None]
        for key in keys_to_remove:
            del record[key]


def normalize_records(records):
    normalized_data = []
    for record in records:
        del record['attributes']  # Remove Salesforce record attributes
        normalized_data.append(record)
    return normalized_data


def recolumn_df(table_name, df, mapping):
    """
    Filters and renames columns in a DataFrame based on a mapping DataFrame for a specific table.

    Parameters:
    - table_name (str): The name of the table to filter the mapping.
    - df (pd.DataFrame): The DataFrame to be processed.
    - mapping (pd.DataFrame): A mapping DataFrame with columns 'table', 'business_name', and 'object_col'.

    Returns:
    - pd.DataFrame: A DataFrame with columns filtered and renamed.
    """
    # Filter mapping for the specific table
    filtered_mapping = mapping[mapping['table'] == table_name]
    
    # Create a dictionary for renaming
    rename_dict = dict(zip(filtered_mapping['business_name'], filtered_mapping['object_col']))
    
    # Retain only columns in df that are in the mapping, explicitly create a copy
    df = df[[col for col in df.columns if col in rename_dict]].copy()
    
    # Rename the columns in df, avoid inplace modification
    df = df.rename(columns=rename_dict)
    
    return df



def convert_timestamps_to_strings(df: pd.DataFrame) -> None:
    """
    Converts all columns with datetime data type in the given DataFrame
    to strings in-place. If a value is NaT, it is converted to None.
    The time portion is excluded, keeping only the date.

    Args:
        df (pd.DataFrame): The input pandas DataFrame.
    """
    # Identify columns with datetime data type
    timestamp_columns = df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']).columns

    # Convert these columns to string with date only, handling NaT
    for col in timestamp_columns:
        df[col] = df[col].apply(lambda x: None if pd.isna(x) else x.date().isoformat())


def connect(creds):

    client_id = creds['client_id']
    client_secret = creds['client_secret']
    client_url = creds['client_url']

    authorization = base64.b64encode(bytes(f"{client_id}:{client_secret}", "ISO-8859-1")).decode("ascii")
    headers = {
            "Authorization": f"Basic {authorization}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    body = {
            "grant_type": "client_credentials"
        }
    
    response = requests.post(client_url, data=body, headers=headers)
    print(response.json())
    sf = Salesforce(instance_url=response.json()["instance_url"], session_id=response.json()["access_token"])
    return sf 


#from sf_eda.py file
def get_all_fields(sf, object_name):
    try:
        object_descriptor = getattr(sf, object_name)  # Dynamic object access
        describe_result = object_descriptor.describe()
        field_names = [field['name'] for field in describe_result['fields']]
        return field_names
    except Exception as e:
        print(f"Error retrieving fields for {object_name}: {e}")
        return None

def get_sf_data(sf, object_name, field_names=None):
    if field_names is None:
        field_names = get_all_fields(sf, object_name)

    fields_str = ', '.join(field_names)
    query = f"SELECT {fields_str} FROM {object_name}"

    data = sf.query_all(query)
    data_normed = normalize_records(data['records'])

    if(len(data_normed) > 0):
        df = pd.DataFrame(data_normed)
    else:
        df = pd.DataFrame(columns=field_names)

    df.columns = df.columns.str.upper()
    return df

def standardize_date_string(X, col_name):
      X[col_name] = X[col_name].apply(
    lambda x: pd.to_datetime(x, errors='coerce').strftime('%Y-%m-%d') if pd.notna(x) else None
)  


if __name__ == '__main__':
    pass
