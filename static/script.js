// Global variables
let currentSearchId = null;
let searchInterval = null;

// DOM elements
const partNumberInput = document.getElementById('partNumber');
const searchBtn = document.getElementById('searchBtn');
const clearBtn = document.getElementById('clearBtn');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsContainer = document.getElementById('resultsContainer');

// Website checkboxes
const systemGeneralCb = document.getElementById('systemgeneral');
const dataioCb = document.getElementById('dataio');
const bpmicroCb = document.getElementById('bpmicro');

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    searchBtn.addEventListener('click', startSearch);
    clearBtn.addEventListener('click', clearResults);
    
    // Enter key support for part number input
    partNumberInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            startSearch();
        }
    });
    
    // Input validation
    partNumberInput.addEventListener('input', function() {
        const value = this.value;
        if (value.length > 255) {
            this.value = value.substring(0, 255);
        }
    });
});

function startSearch() {
    const partNumber = partNumberInput.value.trim();
    
    // Validation
    if (!partNumber) {
        showError('Please enter a part number');
        return;
    }
    
    const selectedWebsites = getSelectedWebsites();
    if (selectedWebsites.length === 0) {
        showError('Please select at least one website');
        return;
    }
    
    // Disable search button and show progress
    searchBtn.disabled = true;
    searchBtn.textContent = 'Searching...';
    showProgress();
    clearResults();
    
    // Start search
    fetch('/api/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            part_number: partNumber,
            websites: selectedWebsites
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        currentSearchId = data.search_id;
        startStatusPolling();
    })
    .catch(error => {
        showError('Failed to start search: ' + error.message);
        resetSearchButton();
        hideProgress();
    });
}

function getSelectedWebsites() {
    const websites = [];
    if (systemGeneralCb.checked) websites.push('systemgeneral');
    if (dataioCb.checked) websites.push('dataio');
    if (bpmicroCb.checked) websites.push('bpmicro');
    return websites;
}

function startStatusPolling() {
    if (searchInterval) {
        clearInterval(searchInterval);
    }
    
    searchInterval = setInterval(() => {
        if (currentSearchId) {
            checkSearchStatus();
        }
    }, 1000); // Poll every second
    
    // Initial check
    checkSearchStatus();
}

function checkSearchStatus() {
    if (!currentSearchId) return;
    
    fetch(`/api/search/${currentSearchId}/status`)
    .then(response => response.json())
    .then(data => {
        updateProgress(data.progress || 0, data.current_search || 'Searching...');
        
        if (data.status === 'completed') {
            clearInterval(searchInterval);
            searchInterval = null;
            displayResults(data);
            resetSearchButton();
            hideProgress();
        } else if (data.status === 'error') {
            clearInterval(searchInterval);
            searchInterval = null;
            showError('Search failed: ' + (data.error || 'Unknown error'));
            resetSearchButton();
            hideProgress();
        }
    })
    .catch(error => {
        console.error('Error checking search status:', error);
        clearInterval(searchInterval);
        searchInterval = null;
        showError('Failed to check search status');
        resetSearchButton();
        hideProgress();
    });
}

function updateProgress(percentage, message) {
    progressFill.style.width = percentage + '%';
    progressText.textContent = message;
}

function showProgress() {
    progressContainer.style.display = 'block';
    updateProgress(0, 'Initializing search...');
}

function hideProgress() {
    progressContainer.style.display = 'none';
}

function resetSearchButton() {
    searchBtn.disabled = false;
    searchBtn.textContent = 'Search';
}

function displayResults(data) {
    const results = data.results || [];
    const summary = data.summary || {};
    
    let html = '';
    
    // Add summary
    if (results.length > 0) {
        html += `
            <div class="search-summary">
                <h3>🎯 Search Complete!</h3>
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-number">${summary.total_searched || 0}</span>
                        <span class="stat-label">Websites Searched</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${summary.found_count || 0}</span>
                        <span class="stat-label">Results Found</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add individual results
    results.forEach(result => {
        const statusClass = result.status;
        const statusText = getStatusText(result.status);
        const statusIcon = getStatusIcon(result.status);
        
        html += `
            <div class="result-item ${statusClass}">
                <div class="result-header">
                    <div class="website-name">${statusIcon} ${result.website}</div>
                    <div class="status-badge ${statusClass}">${statusText}</div>
                </div>
                <div class="result-details">
                    ${getResultDetails(result)}
                </div>
            </div>
        `;
    });
    
    // Show final message if no results
    if (results.length === 0) {
        html = '<div class="no-results">No search was performed.</div>';
    } else if (summary.found_count === 0) {
        html += `
            <div class="result-item not-found">
                <div class="result-header">
                    <div class="website-name">😞 Final Result</div>
                    <div class="status-badge not-found">No Results</div>
                </div>
                <div class="result-details">
                    No results found on any selected website. Try modifying the part number or selecting different websites.
                </div>
            </div>
        `;
    }
    
    resultsContainer.innerHTML = html;
}

function getStatusText(status) {
    switch (status) {
        case 'found': return 'Found';
        case 'not_found': return 'Not Found';
        case 'error': return 'Error';
        default: return 'Unknown';
    }
}

function getStatusIcon(status) {
    switch (status) {
        case 'found': return '✅';
        case 'not_found': return '❌';
        case 'error': return '⚠️';
        default: return '❓';
    }
}

function getResultDetails(result) {
    let details = `<strong>Part Number Used:</strong> ${result.part_used}<br>`;
    
    if (result.status === 'found') {
        details += `<strong>Socket/Adapter Info:</strong> ${result.socket_info}<br>`;
        
        if (result.modified) {
            details += `<span class="warning-text">⚠️ Original part number modified (removed ${result.chars_removed} characters)</span>`;
        }
    } else if (result.status === 'error') {
        details += `<span class="error-text">Error: ${result.error || 'Unknown error occurred'}</span>`;
    } else {
        details += '<span class="error-text">No matching device found</span>';
    }
    
    return details;
}

function clearResults() {
    resultsContainer.innerHTML = '<div class="no-results">Enter a part number and select websites to begin searching.</div>';
}

function showError(message) {
    resultsContainer.innerHTML = `
        <div class="result-item error">
            <div class="result-header">
                <div class="website-name">⚠️ Error</div>
                <div class="status-badge error">Error</div>
            </div>
            <div class="result-details">
                <span class="error-text">${message}</span>
            </div>
        </div>
    `;
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (searchInterval) {
        clearInterval(searchInterval);
    }
});
