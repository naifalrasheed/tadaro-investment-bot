#!/usr/bin/env python
# Add Naif Al-Rasheed model to navigation

import os
import re

def add_naif_model_to_nav():
    """Add Naif Al-Rasheed model to the navigation bar in base.html"""
    base_html_path = os.path.join(os.path.dirname(__file__), 'templates', 'base.html')
    
    if not os.path.exists(base_html_path):
        print(f"Error: Cannot find file {base_html_path}")
        return False
    
    with open(base_html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for the recommendations menu item
    recommendations_pattern = r'<li class="nav-item">\s*<a class="nav-link" href="\{\{ url_for\(\'recommendations\'\) \}\}">\s*<i class="fas fa-star"></i> Recommendations\s*</a>\s*</li>\s*\{% endif %\}'
    
    # Check if the Naif model is already in the navigation
    if 'Naif Al-Rasheed Model' in content:
        print("Naif Al-Rasheed Model already exists in navigation")
        return True
    
    # Create the replacement pattern
    naif_model_nav = '''<li class="nav-item">
                        <a class="nav-link" href="{{ url_for('recommendations') }}">
                            <i class="fas fa-star"></i> Recommendations
                        </a>
                    </li>
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="naifModelDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                            <i class="fas fa-chart-pie"></i> Naif Al-Rasheed Model
                        </a>
                        <ul class="dropdown-menu" aria-labelledby="naifModelDropdown">
                            <li>
                                <a class="dropdown-item" href="{{ url_for('naif_model_screen') }}">
                                    <i class="fas fa-filter"></i> Stock Screening
                                </a>
                            </li>
                            <li>
                                <a class="dropdown-item" href="{{ url_for('naif_sector_analysis') }}">
                                    <i class="fas fa-building"></i> Sector Analysis
                                </a>
                            </li>
                        </ul>
                    </li>
                    {% endif %}'''
    
    # Try an alternative approach using search for key marker in the navigation
    nav_marker = '<a class="nav-link" href="{{ url_for(\'recommendations\') }}">'
    if nav_marker in content:
        nav_end_marker = '{% endif %}'
        
        # Find the insert position
        start_pos = content.find(nav_marker)
        if start_pos != -1:
            # Find the end of the recommendations nav item
            item_end = content.find('</li>', start_pos)
            # Find the next {% endif %} after the item end
            endif_pos = content.find(nav_end_marker, item_end)
            
            if item_end != -1 and endif_pos != -1:
                # Create insert position (include </li> and keep the {% endif %})
                insert_pos = endif_pos
                
                # Construct new content
                new_content = content[:insert_pos] + '''
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="naifModelDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                            <i class="fas fa-chart-pie"></i> Naif Al-Rasheed Model
                        </a>
                        <ul class="dropdown-menu" aria-labelledby="naifModelDropdown">
                            <li>
                                <a class="dropdown-item" href="{{ url_for('naif_model_screen') }}">
                                    <i class="fas fa-filter"></i> Stock Screening
                                </a>
                            </li>
                            <li>
                                <a class="dropdown-item" href="{{ url_for('naif_sector_analysis') }}">
                                    <i class="fas fa-building"></i> Sector Analysis
                                </a>
                            </li>
                        </ul>
                    </li>
                    ''' + content[insert_pos:]
                
                with open(base_html_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"Successfully added Naif Al-Rasheed Model to navigation in {base_html_path}")
                return True
    
    print("Could not find the proper insertion point in the navigation.")
    return False

if __name__ == "__main__":
    if add_naif_model_to_nav():
        print("Successfully added Naif Al-Rasheed Model to the navigation menu.")
    else:
        print("Failed to add Naif Al-Rasheed Model to the navigation menu. Please check the file manually.")