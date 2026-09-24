# Code for ETL operations on Country-GDP data

# Importing the required libraries
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from datetime import datetime
import requests
from lxml import etree, html
import sqlite3


table_attribs = ["Name", "MC_USD_Billion"]
output_path = "./Largest_banks_data.csv"
csv_path = "./exchange_rate.csv"
db_name = "Banks.db"
table_name = "Largest_banks"
log_file = "code_log.txt"
url = "https://web.archive.org/web/20260113075706/https://en.wikipedia.org/wiki/List_of_largest_banks"

def log_progress(message):
    ''' This function logs the mentioned message of a given stage of the
    code execution to a log file. Function returns nothing'''

    timpestamp_format = "%Y-%m-%d-%H:%M:%S"
    now = datetime.now()
    timpestamp = now.strftime(timpestamp_format)
    with open(log_file, "a") as f:
        f.write(timpestamp + ":" + message +"\n" )


def extract(url, table_attribs):
    ''' This function aims to extract the required
    information from the website and save it to a data frame. The
    function returns the data frame for further processing. '''
    page  = requests.get(url).text
    data = BeautifulSoup(page, "html.parser")
    df = pd.DataFrame(columns=table_attribs)
    tables = data.find_all("tbody")
    rows = tables[2].find_all("tr")
    for row in rows :
        col = row.find_all("td")
        if len(col) !=0 :
            data_dict = {
                "Name" : col[0].text.strip(),
                "MC_USD_Billion" : col[2].text.strip() #market_cap = float(col[2].contents[0][:-1])
            }
            df1 = pd.DataFrame(data_dict, index=[0])
            df = pd.concat([df, df1], ignore_index=True)
            df['MC_USD_Billion'] = df['MC_USD_Billion'].replace('', np.nan).astype(float)
            df = df.dropna(subset=['MC_USD_Billion'])
    return df

def transform(df, csv_path):
    ''' This function accesses the CSV file for exchange rate
	information, and adds three columns to the data frame, each
	containing the transformed version of Market Cap column to
	respective currencies'''

    df_exchange_rates = pd.read_csv(csv_path)
    exchange_dict = df_exchange_rates.set_index("Currency").to_dict()["Rate"]
    # Ensure exchange_rate['GBP'] is always a float
    gbp_rate = float(exchange_dict['GBP'])
    df['MC_GBP_Billion'] = [np.round(x * gbp_rate, 2) for x in df['MC_USD_Billion']]
    gbp_rate = float(exchange_dict["EUR"])
    df["MC_EUR_Billion"] = [np.round(x * gbp_rate, 2) for x in df["MC_USD_Billion"]]
    gbp_rate = float(exchange_dict["INR"])
    df["MC_INR_Billion"] = [np.round(x * gbp_rate, 2) for x in df["MC_USD_Billion"]]

    return df

def load_to_csv(df, output_path):
    ''' This function saves the final data frame as a CSV file in
	the provided path. Function returns nothing.'''
    df.to_csv(output_path, index=False)

def load_to_db(df, sql_connection, table_name):
    ''' This function saves the final data frame to a database
	table with the provided name. Function returns nothing.'''
    sql_connection = sqlite3.connect(db_name)
    df.to_sql(table_name, sql_connection, if_exists="replace", index=False)

def run_query(query_statement, sql_connection):
    ''' This function runs the query on the database table and
    prints the output on the terminal. Function returns nothing. '''

    
    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)


''' Here, you define the required entities and call the relevant
functions in the correct order to complete the project. Note that this
portion is not inside any function.'''

log_progress('Preliminaries complete. Initiating ETL process')

df = extract(url, table_attribs)

log_progress('Data extraction complete. Initiating Transformation process')

df = transform(df, csv_path)

log_progress('Data transformation complete. Initiating loading process')

load_to_csv(df, output_path)

log_progress('Data saved to CSV file')

sql_connection = sqlite3.connect(db_name)

log_progress('SQL Connection initiated.')

load_to_db(df, sql_connection, table_name)

log_progress('Data loaded to Database as table. Executing queries')

#QUERY 1
query_statement = f"SELECT * FROM Largest_banks"
run_query(query_statement,sql_connection)
#QUERY 2
query_statement = f"SELECT AVG(MC_GBP_Billion) FROM Largest_banks"
run_query(query_statement,sql_connection)
#QUERY 3
query_statement = f"SELECT Name from Largest_banks LIMIT 5"
run_query(query_statement,sql_connection)

log_progress('Process Complete.')

sql_connection.close()

log_progress("Server Connection closed")

