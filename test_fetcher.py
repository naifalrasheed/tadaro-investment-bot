from data.data_fetcher import DataFetcher

def display_menu():
    print("\nStock Market Analysis Menu:")
    print("1. Analyze single sector")
    print("2. Compare multiple sectors")
    print("3. Find highest dividend stocks")
    print("4. Analyze stocks by ROTC and Growth")
    print("5. Exit")
    return input("\nChoose an option (1-5): ")

def analyze_single_sector(fetcher, sectors_list):
    print("\nAvailable sectors:")
    for i, sector in enumerate(sectors_list, 1):
        print(f"{i}. {sector}")
    
    try:
        choice = int(input("\nEnter sector number: "))
        if 1 <= choice <= len(sectors_list):
            chosen_sector = sectors_list[choice-1]
            print(f"\nAnalyzing {chosen_sector} sector...")
            
            sector_stocks = fetcher.get_sector_stocks(chosen_sector)
            
            if sector_stocks:
                print(f"\nFound {len(sector_stocks)} stocks in {chosen_sector} sector")
                sort_by = input("\nSort by (1. Market Cap, 2. Dividend Yield, 3. P/E Ratio): ")
                
                if sort_by == '1':
                    sector_stocks.sort(key=lambda x: x['market_cap'] or 0, reverse=True)
                    metric = 'Market Cap'
                elif sort_by == '2':
                    sector_stocks.sort(key=lambda x: x['dividend_yield'] or 0, reverse=True)
                    metric = 'Dividend Yield'
                else:
                    sector_stocks.sort(key=lambda x: x['pe_ratio'] or float('inf'))
                    metric = 'P/E Ratio'
                
                print(f"\nTop 10 stocks by {metric}:")
                for stock in sector_stocks[:10]:
                    print(f"\nSymbol: {stock['symbol']}")
                    print(f"Name: {stock['name']}")
                    print(f"Market Cap: ${stock['market_cap']:,}" if stock['market_cap'] else "Market Cap: N/A")
                    print(f"Price: ${stock['price']:,.2f}" if stock['price'] else "Price: N/A")
                    print(f"P/E Ratio: {stock['pe_ratio']:.2f}" if stock['pe_ratio'] else "P/E Ratio: N/A")
                    print(f"Dividend Yield: {stock['dividend_yield']*100:.2f}%" if stock['dividend_yield'] else "Dividend Yield: N/A")
                    print("-" * 60)
    except ValueError:
        print("Please enter a valid number.")

def compare_sectors(fetcher, sectors_list):
    print("\nAvailable sectors:")
    for i, sector in enumerate(sectors_list, 1):
        print(f"{i}. {sector}")
    
    try:
        sectors_to_compare = input("\nEnter sector numbers separated by commas (e.g., 1,2,3): ").split(',')
        sectors_to_analyze = []
        
        for sector_num in sectors_to_compare:
            idx = int(sector_num.strip()) - 1
            if 0 <= idx < len(sectors_list):
                sectors_to_analyze.append(sectors_list[idx])
        
        print("\nSector Comparison:")
        print("-" * 80)
        print(f"{'Sector':<30} {'Avg Market Cap':>15} {'Avg P/E':>10} {'Avg Div Yield':>12}")
        print("-" * 80)
        
        for sector in sectors_to_analyze:
            stocks = fetcher.get_sector_stocks(sector)
            if stocks:
                avg_market_cap = sum(s['market_cap'] or 0 for s in stocks) / len(stocks)
                avg_pe = sum(s['pe_ratio'] or 0 for s in stocks if s['pe_ratio']) / len(stocks) if any(s['pe_ratio'] for s in stocks) else 0
                avg_div = sum(s['dividend_yield'] or 0 for s in stocks) / len(stocks)
                
                print(f"{sector:<30} ${avg_market_cap:>14,.0f} {avg_pe:>10.2f} {avg_div*100:>11.2f}%")
        
        print("-" * 80)
    except ValueError:
        print("Please enter valid sector numbers.")

def analyze_stocks_by_rotc(fetcher, sectors_list):
    """
    Analyze stocks using ROTC and growth criteria
    """
    print("\nAnalyzing stocks with ROTC and growth criteria...")
    
    try:
        min_rotc = float(input("Enter minimum ROTC % (e.g., 15): ") or 15)
        print("\nAnalyzing stocks...")
        
        all_results = []
        growth_results = []
        
        for sector in sectors_list:
            print(f"Analyzing {sector}...")
            stocks = fetcher.get_sector_stocks(sector)  # Fetch list of stock dictionaries
            
            for stock in stocks:
                # Ensure each stock is a dictionary with a 'symbol' key
                if 'symbol' in stock:
                    rotc_data = fetcher.calculate_rotc(stock['symbol'])
                    growth_data = fetcher.get_growth_metrics(stock['symbol'])
                    
                    if rotc_data['rotc'] is not None:
                        stock_data = {
                            'symbol': stock['symbol'],
                            'name': stock.get('name', 'N/A'),
                            'sector': sector,
                            'rotc': rotc_data['rotc'],
                            'revenue_growth': growth_data.get('revenue_growth'),
                            'cash_flow': growth_data.get('operating_cash_flow')
                        }
                        
                        # Apply ROTC and growth filtering criteria
                        if rotc_data['rotc'] >= min_rotc:
                            all_results.append(stock_data)
                        elif (growth_data.get('revenue_growth') is not None and
                              growth_data['revenue_growth'] > 20 and
                              growth_data['operating_cash_flow'] > 0):
                            growth_results.append(stock_data)
        
        # Display results for ROTC criteria
        print("\n=== Stocks Meeting ROTC Criteria ===")
        all_results.sort(key=lambda x: x['rotc'], reverse=True)
        for stock in all_results[:10]:
            print(f"\nSymbol: {stock['symbol']}")
            print(f"Name: {stock['name']}")
            print(f"Sector: {stock['sector']}")
            print(f"ROTC: {stock['rotc']:.2f}%")
            if stock['revenue_growth'] is not None:
                print(f"Revenue Growth: {stock['revenue_growth']:.2f}%")
            if stock['cash_flow'] is not None:
                print(f"Operating Cash Flow: ${stock['cash_flow']:,.2f}")
            print("-" * 60)
        
        # Display results for growth stocks
        print("\n=== High Growth Stocks (Lower ROTC) ===")
        growth_results.sort(key=lambda x: x['revenue_growth'], reverse=True)
        for stock in growth_results[:10]:
            print(f"\nSymbol: {stock['symbol']}")
            print(f"Name: {stock['name']}")
            print(f"Sector: {stock['sector']}")
            print(f"Revenue Growth: {stock['revenue_growth']:.2f}%")
            print(f"Operating Cash Flow: ${stock['cash_flow']:,.2f}")
            print("-" * 60)
            
    except ValueError:
        print("Please enter valid numbers for criteria.")

def find_highest_dividend_stocks(fetcher, sectors_list):
    all_stocks = []
    print("Analyzing all sectors for highest dividend yields...")
    
    for sector in sectors_list:
        stocks = fetcher.get_sector_stocks(sector)
        all_stocks.extend(stocks)
    
    # Sort by dividend yield
    dividend_stocks = [s for s in all_stocks if s['dividend_yield']]
    dividend_stocks.sort(key=lambda x: x['dividend_yield'], reverse=True)
    
    print("\nTop 10 Dividend Stocks across all sectors:")
    for stock in dividend_stocks[:10]:
        print(f"\nSymbol: {stock['symbol']}")
        print(f"Name: {stock['name']}")
        print(f"Sector: {stock['sector']}")
        print(f"Dividend Yield: {stock['dividend_yield']*100:.2f}%")
        print(f"Price: ${stock['price']:,.2f}" if stock['price'] else "Price: N/A")
        print("-" * 60)

def main():
    fetcher = DataFetcher()
    sectors_dict = fetcher.get_sp500_sector_stocks()
    sectors_list = sorted(list(sectors_dict.keys()))
    
    while True:
        choice = display_menu()
        
        if choice == '1':
            analyze_single_sector(fetcher, sectors_list)
        elif choice == '2':
            compare_sectors(fetcher, sectors_list)
        elif choice == '3':
            find_highest_dividend_stocks(fetcher, sectors_list)
        elif choice == '4':
            analyze_stocks_by_rotc(fetcher, sectors_list)
        elif choice == '5':
            print("\nThank you for using the Stock Market Analysis tool!")
            break
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()