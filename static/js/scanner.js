// Dark Web Scanner JS
// Handles search form submission and result processing

document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    const step3 = document.getElementById('step3');
    const step1Indicator = document.getElementById('step1-indicator');
    const step2Indicator = document.getElementById('step2-indicator');
    const step3Indicator = document.getElementById('step3-indicator');
    const progressBar = document.getElementById('progress-bar');
    const currentStatus = document.getElementById('current-status');
    const loadingMessage = document.getElementById('loading-message');
    const resultsContainer = document.getElementById('results');
    const scanStats = document.getElementById('scan-stats');
    const scanStatus = document.getElementById('scan-status');
    const searchError = document.getElementById('search-error');
    
    // Try to get scan info elements, but don't require them
    const scanTarget = document.getElementById('scan-target');
    const scanType = document.getElementById('scan-type');
    const startTime = document.getElementById('start-time');

    // Progress simulation values
    let progress = 0;
    let progressInterval;
    let currentQuery = '';
    let currentType = '';
    let resultsPollingInterval;
    const engineProgressContainer = document.getElementById('engine-progress-container');

    // Handle form submission
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get search query and type
        const searchType = document.getElementById('searchType').value;
        const searchQuery = document.getElementById('searchQuery').value;
        
        // Store current search parameters
        currentQuery = searchQuery;
        currentType = searchType;
        
        if (!searchQuery || searchQuery.trim() === '') {
            showError('Please enter a valid search query.');
            return;
        }
        
        // Validate input based on search type
        if (searchType === 'email' && !validateEmail(searchQuery)) {
            showError('Please enter a valid email address.');
            return;
        } else if (searchType === 'phone' && !validatePhone(searchQuery)) {
            showError('Please enter a valid phone number.');
            return;
        } else if (searchType === 'domain' && !validateDomain(searchQuery)) {
            showError('Please enter a valid domain name.');
            return;
        }
        
        // Start the search process
        startSearch(searchQuery, searchType);
    });
    
    // Validation functions
    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
    
    function validatePhone(phone) {
        return /^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/.test(phone.replace(/\s/g, ''));
    }
    
    function validateDomain(domain) {
        return /^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$/.test(domain);
    }
    
    // Start the search process
    function startSearch(query, type) {
        // Clear any existing errors
        searchError.textContent = '';
        searchError.style.display = 'none';
        
        // Prepare form data
        const formData = new FormData();
        formData.append('searchQuery', query);
        formData.append('searchType', type);
        
        // Update UI for search in progress
        step1.classList.remove('active');
        step2.classList.add('active');
        step1Indicator.classList.remove('active');
        step1Indicator.classList.add('completed');
        step2Indicator.classList.add('active');
        
        // Update scan information
        if (scanTarget) {
            scanTarget.textContent = query;
        }
        if (scanType) {
            scanType.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        }
        if (startTime) {
            startTime.textContent = new Date().toLocaleTimeString();
        }
        
        // Start progress indicator
        progressInterval = setInterval(updateProgress, 100);
        
        // Send the search request
        fetch('/search', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'error') {
                clearInterval(progressInterval);
                showError(data.message);
                return;
            }
            
            // Begin polling for results
            setTimeout(pollResults, 1000);
        })
        .catch(error => {
            clearInterval(progressInterval);
            showError('An error occurred while submitting the search. Please try again.');
            console.error('Search error:', error);
        });
    }

    // Update progress bar for visual feedback
    function updateProgress() {
        if (progress < 90) {
            progress += Math.random() * 5;
            progressBar.style.width = `${progress}%`;
            
            // Update status messages for user feedback
            if (progress > 10 && progress < 30) {
                currentStatus.textContent = 'Querying dark web search engines...';
            } else if (progress > 30 && progress < 50) {
                currentStatus.textContent = 'Analyzing breach databases...';
            } else if (progress > 50 && progress < 70) {
                currentStatus.textContent = 'Scanning paste sites...';
            } else if (progress > 70) {
                currentStatus.textContent = 'Processing results...';
            }
        }
    }

    // Poll for search results
    function pollResults() {
        fetch(`/results?searchQuery=${encodeURIComponent(currentQuery)}&searchType=${encodeURIComponent(currentType)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Poll results:', data);
            
            // Update main progress
            if (data.progress) {
                progress = data.progress;
                progressBar.style.width = `${progress}%`;
            }
            
            // Update current status message
            if (data.message) {
                currentStatus.textContent = data.message;
            }

            // Update engine-specific progress bars
            if (data.engines_progress) {
                updateEngineProgress(data.engines_progress);
            }
            
            if (data.status === 'completed' || data.status === 'error') {
                // Stop progress simulation and polling
                clearInterval(progressInterval);
                clearInterval(resultsPollingInterval);
                
                // Complete progress bar
                progress = 100;
                progressBar.style.width = '100%';
                
                // Show results
                setTimeout(showResults, 500, data);
            } else {
                // Continue polling
                if (!resultsPollingInterval) {
                    resultsPollingInterval = setInterval(pollResults, 2000);
                }
            }
        })
        .catch(error => {
            console.error('Error polling results:', error);
        });
    }

    // Update engine-specific progress bars
    function updateEngineProgress(enginesProgress) {
        // Clear the container first if needed
        if (engineProgressContainer.children.length === 0) {
            engineProgressContainer.innerHTML = '<h4>Search Engines Progress</h4>';
        }
        
        // Process each engine category
        Object.keys(enginesProgress).forEach(category => {
            const categoryData = enginesProgress[category];
            
            // Look for existing category element or create a new one
            let categoryElement = document.getElementById(`engine-category-${category}`);
            
            if (!categoryElement) {
                categoryElement = document.createElement('div');
                categoryElement.id = `engine-category-${category}`;
                categoryElement.className = 'engine-progress-item';
                categoryElement.innerHTML = `
                    <div class="engine-progress-header">
                        <div class="engine-name">${formatCategoryName(category)}</div>
                        <div class="engine-stats">
                            <span id="${category}-completed">0</span>/<span id="${category}-total">0</span> sites,
                            <span id="${category}-results">0</span> results
                        </div>
                    </div>
                    <div class="engine-progress-bar">
                        <div class="engine-progress-fill" id="${category}-progress-fill"></div>
                    </div>
                `;
                engineProgressContainer.appendChild(categoryElement);
            }
            
            // Update the stats
            document.getElementById(`${category}-completed`).textContent = categoryData.completed || 0;
            document.getElementById(`${category}-total`).textContent = categoryData.total || 0;
            document.getElementById(`${category}-results`).textContent = categoryData.found_results || 0;
            
            // Update progress bar
            const progressPercent = categoryData.total ? Math.round((categoryData.completed / categoryData.total) * 100) : 0;
            document.getElementById(`${category}-progress-fill`).style.width = `${progressPercent}%`;
        });
    }
    
    // Format category name for display
    function formatCategoryName(category) {
        return category
            .replace(/_/g, ' ')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    // Show search results
    function showResults(data) {
        // Transition to results screen
        step2.classList.remove('active');
        step3.classList.add('active');
        step2Indicator.classList.remove('active');
        step2Indicator.classList.add('completed');
        step3Indicator.classList.add('active');
        
        // Update status
        scanStatus.textContent = data.status === 'completed' ? 'Completed' : 'Error';
        
        // Clear previous results
        resultsContainer.innerHTML = '';
        scanStats.innerHTML = '';
        
        if (data.status === 'error') {
            resultsContainer.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${data.message || 'An error occurred during the search. Please try again.'}</p>
                </div>
            `;
            return;
        }
        
        // No results
        if (!data.results || Object.keys(data.results).length === 0) {
            resultsContainer.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-check-circle"></i>
                    <p>No mentions of this ${currentType} were found on the dark web. This is good news!</p>
                </div>
            `;
            scanStats.innerHTML = `
                <div class="stat">
                    <div class="stat-value">0</div>
                    <div class="stat-label">Mentions Found</div>
                </div>
                <div class="stat">
                    <div class="stat-value">${data.sites_searched || 'N/A'}</div>
                    <div class="stat-label">Sites Searched</div>
                </div>
            `;
            return;
        }
        
        // Display stats
        const totalMentions = Object.values(data.results).reduce((sum, site) => sum + site.mentions.length, 0);
        scanStats.innerHTML = `
            <div class="stat">
                <div class="stat-value">${totalMentions}</div>
                <div class="stat-label">Mentions Found</div>
            </div>
            <div class="stat">
                <div class="stat-value">${data.sites_searched || 'N/A'}</div>
                <div class="stat-label">Sites Searched</div>
            </div>
            <div class="stat">
                <div class="stat-value">${Object.keys(data.results).length}</div>
                <div class="stat-label">Sites with Hits</div>
            </div>
        `;
        
        // Display results
        const resultsByRisk = {
            'critical': [],
            'high': [],
            'medium-high': [],
            'medium': [],
            'low': []
        };
        
        // Sort results by risk level
        Object.entries(data.results).forEach(([siteName, siteData]) => {
            const riskLevel = siteData.risk_level || 'medium';
            if (!resultsByRisk[riskLevel]) {
                resultsByRisk[riskLevel] = [];
            }
            resultsByRisk[riskLevel].push([siteName, siteData]);
        });
        
        // Risk level labels and colors
        const riskLevelInfo = {
            'critical': { label: 'Critical Risk', color: '#e74c3c' },
            'high': { label: 'High Risk', color: '#e67e22' },
            'medium-high': { label: 'Medium-High Risk', color: '#f39c12' },
            'medium': { label: 'Medium Risk', color: '#3498db' },
            'low': { label: 'Low Risk', color: '#2ecc71' }
        };
        
        // Add a section for each risk level that has results
        Object.keys(resultsByRisk).forEach(risk => {
            if (resultsByRisk[risk].length === 0) return;
            
            // Add risk level section header
            const riskSection = document.createElement('div');
            riskSection.className = 'risk-section';
            riskSection.innerHTML = `
                <h3 style="margin: 25px 0 15px; padding-bottom: 10px; border-bottom: 2px solid ${riskLevelInfo[risk].color};">
                    <i class="fas fa-shield-alt" style="color: ${riskLevelInfo[risk].color};"></i> 
                    ${riskLevelInfo[risk].label} Findings (${resultsByRisk[risk].length})
                </h3>
            `;
            resultsContainer.appendChild(riskSection);
            
            // Add each result in this risk level
            resultsByRisk[risk].forEach(([siteName, siteData]) => {
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                resultItem.style.borderLeftColor = riskLevelInfo[risk].color;
                
                let mentionsHtml = '';
                siteData.mentions.forEach(mention => {
                    // Format the mention context
                    let mentionContext = mention.context || 'Context not available';
                    
                    // Check if the mention starts with "Found on onion site:" and format it specially
                    if (mentionContext.startsWith("Found on onion site:")) {
                        // Extract the URL and the context
                        const lines = mentionContext.split("\n");
                        const siteInfo = lines[0];
                        const contextText = lines.slice(1).join("\n");
                        
                        // Format with the URL as a clickable link (if TOR browser is installed)
                        mentionsHtml += `
                            <div class="mention">
                                <div class="mention-header">
                                    <strong>${siteInfo}</strong>
                                </div>
                                <div class="mention-context">${contextText}</div>
                                <div class="mention-date">${mention.date || 'Date unknown'}</div>
                            </div>
                        `;
                    } else {
                        // Standard format for other mentions
                        mentionsHtml += `
                            <div class="mention">
                                <div class="mention-context">${mentionContext}</div>
                                <div class="mention-date">${mention.date || 'Date unknown'}</div>
                            </div>
                        `;
                    }
                });
                
                resultItem.innerHTML = `
                    <div class="result-header">
                        <h3 style="margin: 0; font-size: 18px;">${siteName}</h3>
                        <span class="badge ${siteData.risk_level || 'medium'}"
                              style="background-color: ${riskLevelInfo[siteData.risk_level || 'medium'].color}; color: white; padding: 5px 10px; border-radius: 4px;">
                            ${riskLevelInfo[siteData.risk_level || 'medium'].label}
                        </span>
                    </div>
                    <div class="result-body">
                        <p style="margin-bottom: 15px;">${siteData.description || 'No additional information available.'}</p>
                        <div class="mentions">
                            <h4 style="margin-top: 0; margin-bottom: 15px; font-size: 16px;">Mentions (${siteData.mentions.length})</h4>
                            ${mentionsHtml}
                        </div>
                    </div>
                `;
                
                resultsContainer.appendChild(resultItem);
            });
        });
        
        // Add a back to top button
        const backToTop = document.createElement('div');
        backToTop.className = 'back-to-top';
        backToTop.innerHTML = '<i class="fas fa-arrow-up"></i>';
        backToTop.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        document.body.appendChild(backToTop);
        
        // Show back to top button on scroll
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });
    }

    // Show error message
    function showError(message) {
        clearInterval(progressInterval);
        clearInterval(resultsPollingInterval);
        
        step2.classList.remove('active');
        step3.classList.add('active');
        step2Indicator.classList.remove('active');
        step3Indicator.classList.add('active');
        
        scanStatus.textContent = 'Error';
        resultsContainer.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
            </div>
        `;
    }
});