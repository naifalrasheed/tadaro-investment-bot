import os
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
import re
from datetime import datetime
import tempfile
import yfinance as yf
from data.data_fetcher import DataFetcher
import tabula

class FileImportException(Exception):
    """Custom exception for file import errors with specific error details"""
    def __init__(self, message: str, validation_errors: Dict = None):
        self.message = message
        self.validation_errors = validation_errors or {}
        super().__init__(self.message)

class PortfolioFileImporter:
    """
    Portfolio file importer that supports Excel, CSV, and PDF formats
    with validation and error handling.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_fetcher = DataFetcher()
        self.required_columns = ['symbol', 'quantity', 'purchase_price', 'purchase_date']
        self.optional_columns = ['sector', 'asset_class', 'current_price']
        
        # Column name mappings (common variations)
        self.column_mappings = {
            'symbol': ['symbol', 'ticker', 'stock', 'security', 'security_id', 'stocksymbol'],
            'quantity': ['quantity', 'qty', 'shares', 'no_of_shares', 'amount', 'units', 'volume'],
            'purchase_price': ['purchase_price', 'price', 'cost', 'entry_price', 'buy_price', 'unit_price', 'cost_per_share'],
            'purchase_date': ['purchase_date', 'date', 'entry_date', 'buy_date', 'transaction_date', 'acquired_date'],
            'sector': ['sector', 'industry_sector', 'market_sector'],
            'asset_class': ['asset_class', 'security_type', 'asset_type', 'instrument_type', 'type'],
            'current_price': ['current_price', 'market_price', 'last_price', 'close_price', 'now_price']
        }
        
    def import_file(self, file_path: str) -> Dict:
        """
        Import portfolio data from file with validation
        
        Args:
            file_path: Path to the portfolio file
            
        Returns:
            Dict containing portfolio data and validation results
            
        Raises:
            FileImportException: If file cannot be imported or has validation errors
        """
        self.logger.info(f"Importing portfolio from {file_path}")
        
        if not os.path.exists(file_path):
            raise FileImportException(f"File not found: {file_path}")
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.xlsx':
                df = self._import_excel(file_path)
            elif file_ext == '.csv':
                df = self._import_csv(file_path)
            elif file_ext == '.pdf':
                df = self._import_pdf(file_path)
            else:
                raise FileImportException(f"Unsupported file format: {file_ext}. Please use .xlsx, .csv, or .pdf")
                
            # Clean and normalize the dataframe
            df = self._clean_dataframe(df)
            
            # Validate the data
            validation_errors = self._validate_data(df)
            
            if validation_errors:
                raise FileImportException(
                    "Portfolio import has validation errors. Please fix them and try again.",
                    validation_errors
                )
                
            # Process and enrich the data
            result = self._process_portfolio_data(df)
            return result
            
        except pd.errors.EmptyDataError:
            raise FileImportException("The file does not contain any data")
        except pd.errors.ParserError:
            raise FileImportException("Unable to parse the file. Please check the file format")
        except Exception as e:
            if isinstance(e, FileImportException):
                raise
            else:
                self.logger.error(f"Error importing file: {str(e)}", exc_info=True)
                raise FileImportException(f"Error importing file: {str(e)}")
    
    def _import_excel(self, file_path: str) -> pd.DataFrame:
        """Import data from Excel file, prioritizing common sheet names"""
        try:
            # First try common sheet names
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            # Priority sheets to check
            priority_sheets = ['Portfolio', 'Holdings', 'Positions', 'Stocks', 'Investments']
            
            # Try priority sheets first
            for sheet in priority_sheets:
                if sheet in sheet_names:
                    self.logger.info(f"Using sheet: {sheet}")
                    return pd.read_excel(file_path, sheet_name=sheet)
            
            # If no priority sheet found, use the first sheet
            self.logger.info(f"Using first sheet: {sheet_names[0]}")
            return pd.read_excel(file_path, sheet_name=0)
            
        except Exception as e:
            self.logger.error(f"Error importing Excel file: {str(e)}")
            raise FileImportException(f"Error importing Excel file: {str(e)}")
    
    def _import_csv(self, file_path: str) -> pd.DataFrame:
        """Import data from CSV file, handling different delimiters"""
        try:
            # Try comma delimiter first
            df = pd.read_csv(file_path, delimiter=',')
            
            # If only one column, try semicolon
            if len(df.columns) == 1:
                df = pd.read_csv(file_path, delimiter=';')
                
            # If still only one column, try tab
            if len(df.columns) == 1:
                df = pd.read_csv(file_path, delimiter='\t')
                
            return df
            
        except Exception as e:
            self.logger.error(f"Error importing CSV file: {str(e)}")
            raise FileImportException(f"Error importing CSV file: {str(e)}")
    
    def _import_pdf(self, file_path: str) -> pd.DataFrame:
        """Import data from PDF file using OCR capabilities for tables"""
        try:
            # Try to extract tables using tabula
            tables = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
            
            if not tables:
                raise FileImportException("No tables found in the PDF file")
                
            # Combine all tables into one dataframe
            df = pd.concat(tables, ignore_index=True)
            
            # If the dataframe is empty, raise an exception
            if df.empty:
                raise FileImportException("Failed to extract data from PDF file")
                
            return df
            
        except Exception as e:
            self.logger.error(f"Error importing PDF file: {str(e)}")
            raise FileImportException(f"Error importing PDF file. Make sure it contains tabular data: {str(e)}")
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize the dataframe columns and values"""
        # Convert all column names to lowercase
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Replace whitespace and special characters in column names
        df.columns = [re.sub(r'[^a-z0-9]', '_', col) for col in df.columns]
        
        # Find the best matching column for each required field
        mapped_columns = {}
        
        for target_col, possible_names in self.column_mappings.items():
            # Check if any of the possible column names exist in our dataframe
            for col_name in df.columns:
                if col_name in possible_names or any(name in col_name for name in possible_names):
                    mapped_columns[target_col] = col_name
                    break
        
        # Create a new dataframe with standardized columns
        result_df = pd.DataFrame()
        
        # Map each found column to our standardized names
        for target_col, source_col in mapped_columns.items():
            result_df[target_col] = df[source_col]
        
        # Handle symbols - convert to uppercase
        if 'symbol' in result_df.columns:
            result_df['symbol'] = result_df['symbol'].str.upper()
        
        return result_df
    
    def _validate_data(self, df: pd.DataFrame) -> Dict:
        """
        Validate the portfolio data
        
        Returns:
            Dict with validation errors by column and row index
        """
        validation_errors = {}
        
        # Check for required columns
        missing_columns = []
        for col in self.required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            validation_errors['missing_columns'] = missing_columns
        
        # If missing required columns, return errors without further validation
        if validation_errors:
            return validation_errors
        
        # Validate rows
        symbol_errors = []
        quantity_errors = []
        price_errors = []
        date_errors = []
        
        for idx, row in df.iterrows():
            # Symbol validation
            symbol = row['symbol']
            if pd.isna(symbol) or not isinstance(symbol, str) or len(symbol.strip()) == 0:
                symbol_errors.append({
                    'row': idx + 2,  # +2 for header row and 0-indexing
                    'value': symbol,
                    'error': 'Symbol is required'
                })
            else:
                # Validate symbol exists in the market
                try:
                    # Simple validation check - will be enhanced with actual API validation
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    if not info or 'symbol' not in info:
                        symbol_errors.append({
                            'row': idx + 2,
                            'value': symbol,
                            'error': 'Symbol not found in market'
                        })
                except Exception as e:
                    symbol_errors.append({
                        'row': idx + 2,
                        'value': symbol,
                        'error': f'Error validating symbol: {str(e)}'
                    })
            
            # Quantity validation
            quantity = row['quantity']
            if pd.isna(quantity):
                quantity_errors.append({
                    'row': idx + 2,
                    'value': quantity,
                    'error': 'Quantity is required'
                })
            else:
                try:
                    qty = float(quantity)
                    if qty <= 0:
                        quantity_errors.append({
                            'row': idx + 2,
                            'value': quantity,
                            'error': 'Quantity must be positive'
                        })
                except (ValueError, TypeError):
                    quantity_errors.append({
                        'row': idx + 2,
                        'value': quantity,
                        'error': 'Quantity must be a number'
                    })
            
            # Purchase price validation
            price = row['purchase_price']
            if pd.isna(price):
                price_errors.append({
                    'row': idx + 2,
                    'value': price,
                    'error': 'Purchase price is required'
                })
            else:
                try:
                    p = float(price)
                    if p <= 0:
                        price_errors.append({
                            'row': idx + 2,
                            'value': price,
                            'error': 'Purchase price must be positive'
                        })
                except (ValueError, TypeError):
                    price_errors.append({
                        'row': idx + 2,
                        'value': price,
                        'error': 'Purchase price must be a number'
                    })
            
            # Date validation
            date = row['purchase_date']
            if pd.isna(date):
                date_errors.append({
                    'row': idx + 2,
                    'value': date,
                    'error': 'Purchase date is required'
                })
            else:
                # Try to parse the date
                try:
                    if isinstance(date, str):
                        # Try multiple date formats
                        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
                        parsed_date = None
                        
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(date, fmt)
                                break
                            except ValueError:
                                continue
                                
                        if parsed_date is None:
                            date_errors.append({
                                'row': idx + 2,
                                'value': date,
                                'error': 'Invalid date format. Use YYYY-MM-DD or MM/DD/YYYY'
                            })
                        elif parsed_date > datetime.now():
                            date_errors.append({
                                'row': idx + 2,
                                'value': date,
                                'error': 'Purchase date cannot be in the future'
                            })
                    elif isinstance(date, (pd.Timestamp, datetime)):
                        if date > datetime.now():
                            date_errors.append({
                                'row': idx + 2,
                                'value': date,
                                'error': 'Purchase date cannot be in the future'
                            })
                except Exception as e:
                    date_errors.append({
                        'row': idx + 2,
                        'value': date,
                        'error': f'Invalid date: {str(e)}'
                    })
        
        # Add errors to the validation results
        if symbol_errors:
            validation_errors['symbol'] = symbol_errors
        if quantity_errors:
            validation_errors['quantity'] = quantity_errors
        if price_errors:
            validation_errors['purchase_price'] = price_errors
        if date_errors:
            validation_errors['purchase_date'] = date_errors
            
        return validation_errors
    
    def _process_portfolio_data(self, df: pd.DataFrame) -> Dict:
        """
        Process validated portfolio data and fill in missing values
        
        Returns:
            Dict with processed portfolio data
        """
        # Create a copy to avoid modifying the original
        processed_df = df.copy()
        
        # Convert and standardize data types
        processed_df['symbol'] = processed_df['symbol'].astype(str).str.upper()
        processed_df['quantity'] = processed_df['quantity'].astype(float)
        processed_df['purchase_price'] = processed_df['purchase_price'].astype(float)
        
        # Standardize date format
        processed_df['purchase_date'] = pd.to_datetime(processed_df['purchase_date'], errors='coerce')
        
        # Fetch missing data from market API
        for idx, row in processed_df.iterrows():
            symbol = row['symbol']
            
            # Fetch current price if missing
            if 'current_price' not in processed_df.columns or pd.isna(row.get('current_price')):
                try:
                    stock_info = self.data_fetcher.get_stock_info(symbol)
                    if stock_info:
                        # Add current price
                        if 'current_price' not in processed_df.columns:
                            processed_df['current_price'] = np.nan
                        processed_df.at[idx, 'current_price'] = stock_info.get('price', 0)
                        
                        # Add sector if missing
                        if 'sector' not in processed_df.columns or pd.isna(row.get('sector')):
                            if 'sector' not in processed_df.columns:
                                processed_df['sector'] = np.nan
                            processed_df.at[idx, 'sector'] = stock_info.get('sector', '')
                except Exception as e:
                    self.logger.warning(f"Error fetching market data for {symbol}: {str(e)}")
            
            # Determine asset class from symbol if missing
            if 'asset_class' not in processed_df.columns or pd.isna(row.get('asset_class')):
                if 'asset_class' not in processed_df.columns:
                    processed_df['asset_class'] = np.nan
                
                # Simple logic to determine asset class from symbol
                if symbol.endswith('-USD') or symbol in ['BTC', 'ETH', 'XRP']:
                    processed_df.at[idx, 'asset_class'] = 'Cryptocurrency'
                elif any(x in symbol for x in ['-', '/']):
                    processed_df.at[idx, 'asset_class'] = 'Forex'
                elif symbol.startswith('^'):
                    processed_df.at[idx, 'asset_class'] = 'Index'
                elif symbol.endswith('.B'):
                    processed_df.at[idx, 'asset_class'] = 'Bond'
                elif symbol.endswith(('F', 'Z', 'H', 'M', 'U', 'X')):
                    processed_df.at[idx, 'asset_class'] = 'Futures'
                else:
                    processed_df.at[idx, 'asset_class'] = 'Equity'
        
        # Calculate basic portfolio metrics
        total_value = (processed_df['quantity'] * processed_df['current_price']).sum()
        
        # Calculate position weights
        processed_df['position_value'] = processed_df['quantity'] * processed_df['current_price']
        processed_df['weight'] = processed_df['position_value'] / total_value
        
        # Calculate profit/loss
        processed_df['cost_basis'] = processed_df['quantity'] * processed_df['purchase_price']
        processed_df['gain_loss'] = processed_df['position_value'] - processed_df['cost_basis']
        processed_df['gain_loss_pct'] = processed_df['gain_loss'] / processed_df['cost_basis']
        
        # Create portfolio summary
        summary = {
            'total_value': total_value,
            'total_cost': processed_df['cost_basis'].sum(),
            'total_gain_loss': processed_df['gain_loss'].sum(),
            'total_gain_loss_pct': processed_df['gain_loss'].sum() / processed_df['cost_basis'].sum(),
            'positions_count': len(processed_df),
            'holdings': processed_df.to_dict(orient='records'),
            'asset_allocation': processed_df.groupby('asset_class')['weight'].sum().to_dict(),
            'sector_allocation': processed_df.groupby('sector')['weight'].sum().to_dict()
        }
        
        return summary