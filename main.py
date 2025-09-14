# Main entry point for the investment analysis system

import os
# Local imports
from portfolio.portfolio_management import PortfolioManager 
from interface.interface import analyze_single_stock
from user_profiling.profile_analyzer import ProfileAnalyzer

def main():
    """Main application entry point"""
    portfolio_manager = PortfolioManager()
    profile_analyzer = ProfileAnalyzer()
    user_profile = None
    
    while True:
        print("\n=== Investment Analysis System ===")
        print("1. Analyze Individual Stock")
        print("2. Create/Update Investment Profile")
        print("3. Optimize Portfolio")
        print("4. View Current Portfolio")
        print("5. View Investment Profile")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ")
        
        if choice == '1':
            analyze_single_stock()
            
        elif choice == '2':
            recommendations = profile_analyzer.analyze_profile()
            user_profile = profile_analyzer.risk_profiler.get_profile()
            
            print("\n=== Investment Recommendations ===")
            print(f"Portfolio Type: {recommendations['portfolio_type']}")
            print("\nRecommended Asset Allocation:")
            for asset, pct in recommendations['asset_allocation'].items():
                print(f"{asset.title()}: {pct}%")
            print("\nInvestment Strategy:")
            for strategy in recommendations['investment_strategy']:
                print(f"• {strategy}")
            print(f"\nRebalancing Frequency: {recommendations['rebalancing_frequency']}")
            
        elif choice == '3':
            if user_profile:
                print("\nOptimizing portfolio based on your risk profile...")
                portfolio_manager.optimize_portfolio(profile_constraints=user_profile['constraints'])
            else:
                print("\nNo risk profile found. Creating portfolio with default settings...")
                portfolio_manager.optimize_portfolio()
                
        elif choice == '4':
            if portfolio_manager.current_portfolio:
                portfolio_manager._display_optimization_results(
                    portfolio_manager.current_portfolio
                )
            else:
                print("\nNo portfolio currently loaded.")
                
        elif choice == '5':
            if user_profile:
                print("\n=== Current Investment Profile ===")
                print(user_profile['summary'])
                print("\nInvestment Constraints:")
                print(f"Minimum Target Return: {user_profile['constraints']['min_return']}%")
                print(f"Maximum Risk Level: {user_profile['constraints']['max_risk']}%")
                print(f"Investment Horizon: {user_profile['constraints']['investment_horizon']} years")
                
                if user_profile['constraints']['preferred_sectors']:
                    print("Preferred Sectors:", ", ".join(user_profile['constraints']['preferred_sectors']))
                    
                if user_profile['constraints']['excluded_sectors']:
                    print("Excluded Sectors:", ", ".join(user_profile['constraints']['excluded_sectors']))
            else:
                print("\nNo investment profile created yet.")
                
        elif choice == '6':
            print("Exiting program. Thank you for using the Investment Analysis System.")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()