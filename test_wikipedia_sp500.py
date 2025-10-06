#!/usr/bin/env python3
"""
Test script to debug S&P 500 Wikipedia scraping issue
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)

def test_wikipedia_scraping():
    """Test what tables are available on the Wikipedia S&P 500 page"""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        print(f"Fetching: {url}")

        response = requests.get(url)
        print(f"Response status: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all tables
        all_tables = soup.find_all('table')
        print(f"Found {len(all_tables)} tables on the page")

        # Check for wikitable class
        wikitable = soup.find('table', {'class': 'wikitable'})
        print(f"Table with 'wikitable' class: {'Found' if wikitable else 'NOT FOUND'}")

        # Check for other table classes
        for i, table in enumerate(all_tables[:5]):  # Check first 5 tables
            classes = table.get('class', [])
            print(f"Table {i+1} classes: {classes}")

            # Check if this might be the S&P 500 table
            rows = table.find_all('tr')
            if len(rows) > 10:  # S&P 500 should have many rows
                print(f"  Table {i+1} has {len(rows)} rows")

                # Check first few rows for S&P 500 data
                for j, row in enumerate(rows[:3]):
                    columns = row.find_all(['td', 'th'])
                    if columns:
                        text_columns = [col.text.strip()[:20] for col in columns[:5]]
                        print(f"  Row {j+1}: {text_columns}")

        # Try to find the table by looking for specific content
        for i, table in enumerate(all_tables):
            rows = table.find_all('tr')
            if len(rows) > 100:  # S&P 500 should have ~500 rows
                print(f"\n*** Table {i+1} might be the S&P 500 table (has {len(rows)} rows) ***")
                classes = table.get('class', [])
                print(f"Classes: {classes}")

                # Check first data row
                if len(rows) > 1:
                    columns = rows[1].find_all('td')
                    if len(columns) >= 4:
                        symbol = columns[0].text.strip()
                        company = columns[1].text.strip()
                        sector = columns[3].text.strip()
                        print(f"Sample data - Symbol: {symbol}, Company: {company}, Sector: {sector}")
                break

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_wikipedia_scraping()