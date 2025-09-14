// Investment Bot - Enhanced UI JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add hover effects to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 20px rgba(0,0,0,0.1)';
            this.style.transition = 'all 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.08)';
            this.style.transition = 'all 0.3s ease';
        });
    });

    // Format currency values
    const currencyElements = document.querySelectorAll('.currency');
    currencyElements.forEach(element => {
        const value = parseFloat(element.textContent);
        if (!isNaN(value)) {
            const marketType = element.getAttribute('data-market') || 'US';
            const symbol = marketType === 'Saudi' ? 'SAR ' : '$';
            element.textContent = symbol + value.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    });

    // Format percentage values
    const percentElements = document.querySelectorAll('.percent');
    percentElements.forEach(element => {
        const value = parseFloat(element.textContent);
        if (!isNaN(value)) {
            // Add appropriate classes for positive/negative values
            if (value > 0) {
                element.classList.add('text-success');
                element.innerHTML = '<i class="fas fa-caret-up me-1"></i>' + value.toFixed(2) + '%';
            } else if (value < 0) {
                element.classList.add('text-danger');
                element.innerHTML = '<i class="fas fa-caret-down me-1"></i>' + Math.abs(value).toFixed(2) + '%';
            } else {
                element.innerHTML = value.toFixed(2) + '%';
            }
        }
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            document.querySelector(targetId).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Initialize date pickers if available
    if (typeof flatpickr !== 'undefined') {
        flatpickr(".datepicker", {
            dateFormat: "Y-m-d",
            allowInput: true
        });
    }
});