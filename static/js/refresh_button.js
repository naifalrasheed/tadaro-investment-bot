/**
 * Add refresh button to the analysis page
 */
function addRefreshButton() {
    // Find the company overview card header
    const cardHeaders = document.querySelectorAll('.card-header');
    
    for (const header of cardHeaders) {
        if (header.textContent.includes('Company Overview')) {
            // Make the header a flex container
            header.classList.add('d-flex', 'justify-content-between', 'align-items-center');
            
            // Get the current symbol from the page
            const symbolElement = document.querySelector('.card-body p:first-child');
            const symbolText = symbolElement ? symbolElement.textContent : '';
            let symbol = '';
            
            // Try to extract the symbol from text like "Symbol: AAPL" or just get from URL
            if (symbolText.includes(':')) {
                symbol = symbolText.split(':')[1].trim();
            } else {
                // Extract from URL
                const pathParts = window.location.pathname.split('/');
                symbol = pathParts[pathParts.length - 1];
            }
            
            if (!symbol) {
                // If still no symbol, try to find it in the page title
                const titleText = document.querySelector('h2').textContent;
                if (titleText.includes('for')) {
                    symbol = titleText.split('for')[1].trim();
                }
            }
            
            // Create the refresh button
            const refreshButton = document.createElement('a');
            refreshButton.href = `/clear-cache?symbol=${symbol}`;
            refreshButton.className = 'btn btn-sm btn-outline-secondary';
            refreshButton.innerHTML = '<i class="fa fa-refresh"></i> Refresh Data';
            
            // Add the button to the header
            header.appendChild(refreshButton);
            break;
        }
    }
    
    // Add data source to the first card body
    const firstCardBody = document.querySelector('.card-body');
    if (firstCardBody) {
        const dataSource = document.createElement('p');
        dataSource.className = 'text-muted small';
        dataSource.textContent = 'Click Refresh Data to get the latest market data';
        firstCardBody.appendChild(dataSource);
    }
}

// Run the function when the page is fully loaded
document.addEventListener('DOMContentLoaded', addRefreshButton);