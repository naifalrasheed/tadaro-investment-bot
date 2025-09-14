#!/usr/bin/env python
# Fix for preferences route issue in base.html template

import os

def fix_route():
    """
    Fix the route in base.html from 'preferences' to 'user_preferences'
    """
    base_html_path = os.path.join(os.path.dirname(__file__), 'templates', 'base.html')
    
    if not os.path.exists(base_html_path):
        print(f"Error: Cannot find file {base_html_path}")
        return False
    
    with open(base_html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for the preferences URL pattern
    if 'url_for(\'preferences\')' in content:
        # Replace with the correct route
        updated_content = content.replace('url_for(\'preferences\')', 'url_for(\'user_preferences\')')
        
        with open(base_html_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Successfully updated route in {base_html_path}")
        return True
    else:
        print("Could not find 'preferences' route in the file")
        return False

if __name__ == "__main__":
    if fix_route():
        print("Fix applied successfully. You can now run the app.")
    else:
        print("Fix could not be applied. Please check the file manually.")