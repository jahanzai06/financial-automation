// App State
let currentTab = 'dashboard';
let accountChartInstance = null;
let trendChartInstance = null;
let parsedTransactions = []; // Holds items parsed from receipt before saving

// On Document Load
document.addEventListener("DOMContentLoaded", () => {
    // Initial fetch of data
    refreshData();
    
    // Set up file drop zone
    setupDragAndDrop();
    
    // Set default dates for report generator
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('report-date').value = today;
    
    const curMonth = today.substring(0, 7); // YYYY-MM
    document.getElementById('report-month').value = curMonth;
    
    document.getElementById('report-start-date').value = today;
    document.getElementById('report-end-date').value = today;
});

// Toast notification helper
function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-message');
    toastMsg.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

// Show/Hide Loader
function showLoader(show, text = "Analyzing with Gemini...") {
    const loader = document.getElementById('loader');
    const loaderText = document.getElementById('loader-text');
    loaderText.textContent = text;
    loader.style.display = show ? 'flex' : 'none';
}

// Refresh all dashboard and transaction views
function refreshData() {
    fetchStats();
    fetchTransactions();
}

// Switch between SPA tabs
function switchTab(tabId) {
    // Remove active class from all tabs
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    
    // Add active class to target tab
    document.getElementById(`tab-${tabId}`).classList.add('active');
    
    // Find nav button matching tab
    const navItems = Array.from(document.querySelectorAll('.nav-item'));
    const targetNav = navItems.find(item => item.getAttribute('onclick').includes(tabId));
    if (targetNav) targetNav.classList.add('active');
    
    // Set headers
    const titleEl = document.getElementById('page-title');
    const subtitleEl = document.getElementById('page-subtitle');
    
    if (tabId === 'dashboard') {
        titleEl.textContent = 'Financial Dashboard';
        subtitleEl.textContent = 'Real-time ledger overview & analytics';
    } else if (tabId === 'transactions') {
        titleEl.textContent = 'Transaction Ledger';
        subtitleEl.textContent = 'Search, filter, and edit transactions';
    } else if (tabId === 'scanner') {
        titleEl.textContent = 'Gemini AI Receipt Parser';
        subtitleEl.textContent = 'Extract transaction structures from screenshots or text';
    } else if (tabId === 'reports') {
        titleEl.textContent = 'Outbound Statements';
        subtitleEl.textContent = 'Generate formatted text statements for communication channels';
    }
    
    currentTab = tabId;
    refreshData();
}

// Fetch stats for charts and KPI cards
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // 1. Update KPI Values
        document.getElementById('kpi-total-volume').textContent = `${data.total_volume.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2})} PKR`;
        
        // Find transaction count (sum counts of accounts)
        let totalCount = 0;
        data.account_stats.forEach(item => totalCount += item.count);
        document.getElementById('kpi-transaction-count').textContent = totalCount;
        
        // 2. Render account donut chart
        renderAccountChart(data.account_stats);
        
        // 3. Render monthly trend chart
        renderTrendChart(data.monthly_trend);
        
    } catch (e) {
        console.error("Error loading stats:", e);
        showToast("Error loading financial stats");
    }
}

// Render Donut Chart for Account Volumes
function renderAccountChart(stats) {
    const ctx = document.getElementById('accountChart').getContext('2d');
    
    // Destroy previous instance
    if (accountChartInstance) {
        accountChartInstance.destroy();
    }
    
    if (!stats || stats.length === 0) {
        // Draw empty text or placeholder if no data
        return;
    }
    
    const labels = stats.map(item => item.account);
    const totals = stats.map(item => item.total);
    
    // Account specific styling colors
    const colors = labels.map(label => {
        if (label.includes("Muhammad Jahanzaib")) return '#00E5FF'; // HBL Jahanzaib
        if (label.includes("Sana Kanwal")) return '#7F00FF'; // HBL Sana
        if (label === 'EasyPaisa') return '#00F5A0'; // EasyPaisa
        if (label === 'JazzCash') return '#FF8F00'; // JazzCash
        return '#9CA3AF'; // Cash / Other
    });
    
    accountChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: totals,
                backgroundColor: colors,
                borderColor: 'rgba(18, 24, 38, 0.85)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#9CA3AF',
                        font: { family: 'Outfit', size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${context.raw.toLocaleString('en-US')} PKR`;
                        }
                    }
                }
            }
        }
    });
}

// Render Monthly Trend Chart
function renderTrendChart(trend) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    if (trendChartInstance) {
        trendChartInstance.destroy();
    }
    
    if (!trend || trend.length === 0) return;
    
    const labels = trend.map(item => item.month);
    const totals = trend.map(item => item.total);
    
    trendChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Monthly Volume (PKR)',
                data: totals,
                backgroundColor: 'rgba(0, 229, 255, 0.15)',
                borderColor: '#00E5FF',
                borderWidth: 2,
                borderRadius: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` Total: ${context.raw.toLocaleString('en-US')} PKR`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#9CA3AF', font: { family: 'Outfit' } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#9CA3AF', font: { family: 'Outfit' } }
                }
            }
        }
    });
}

// Helper to assign account labels
function getAccountBadgeClass(account) {
    if (account.includes("Muhammad Jahanzaib")) return 'badge-hbl';
    if (account.includes("Sana Kanwal")) return 'badge-hbl-sana';
    if (account === 'EasyPaisa') return 'badge-easypaisa';
    if (account === 'JazzCash') return 'badge-jazzcash';
    return 'badge-cash';
}

// Fetch all transactions with filters
async function fetchTransactions() {
    const search = document.getElementById('search-tx').value;
    const account = document.getElementById('filter-account').value;
    const startDate = document.getElementById('filter-start-date').value;
    const endDate = document.getElementById('filter-end-date').value;
    
    let url = `/api/transactions?`;
    if (search) url += `search=${encodeURIComponent(search)}&`;
    if (account) url += `account=${encodeURIComponent(account)}&`;
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}&`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        // 1. Populate All Transactions View
        const tbody = document.getElementById('all-transactions-tbody');
        tbody.innerHTML = '';
        
        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-secondary);">No transactions found matching filters.</td></tr>`;
        } else {
            data.forEach(tx => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${tx.date}</td>
                    <td><span class="badge ${getAccountBadgeClass(tx.source_account)}">${tx.source_account}</span></td>
                    <td>${tx.recipient_or_use || 'N/A'}</td>
                    <td><strong>${tx.amount.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2})}</strong></td>
                    <td><span class="text-secondary">${tx.comment || ''}</span></td>
                    <td>
                        <div class="btn-action-group">
                            <button class="btn-action" onclick="openEditTransactionModal(${JSON.stringify(tx).replace(/"/g, '&quot;')})">
                                <i data-lucide="edit-2"></i>
                            </button>
                            <button class="btn-action delete" onclick="deleteTransaction(${tx.id})">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        // 2. Populate Recent Transactions Dashboard Table (Max 5 items)
        const recentTbody = document.getElementById('recent-transactions-tbody');
        recentTbody.innerHTML = '';
        
        const recents = data.slice(0, 5);
        if (recents.length === 0) {
            recentTbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-secondary);">No transactions logged yet.</td></tr>`;
        } else {
            recents.forEach(tx => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${tx.date}</td>
                    <td><span class="badge ${getAccountBadgeClass(tx.source_account)}">${tx.source_account}</span></td>
                    <td>${tx.recipient_or_use || 'N/A'}</td>
                    <td><strong>${tx.amount.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2})}</strong></td>
                    <td><span class="text-secondary">${tx.comment || ''}</span></td>
                `;
                recentTbody.appendChild(tr);
            });
        }
        
        lucide.createIcons();
    } catch (e) {
        console.error("Error loading transactions:", e);
        showToast("Error loading transactions");
    }
}

// Reset filter bar fields
function resetFilters() {
    document.getElementById('search-tx').value = '';
    document.getElementById('filter-account').value = '';
    document.getElementById('filter-start-date').value = '';
    document.getElementById('filter-end-date').value = '';
    fetchTransactions();
}

// Delete transaction helper
async function deleteTransaction(id) {
    if (!confirm("Are you sure you want to delete this transaction record?")) return;
    
    try {
        const response = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
        const res = await response.json();
        if (res.success) {
            showToast("Transaction deleted successfully");
            refreshData();
        } else {
            showToast(res.message || "Failed to delete transaction");
        }
    } catch (e) {
        console.error("Error deleting transaction:", e);
        showToast("Server error during deletion");
    }
}

// Modals Handling
function openAddTransactionModal() {
    document.getElementById('modal-title').textContent = "Add Transaction";
    document.getElementById('tx-id-input').value = "";
    document.getElementById('tx-form').reset();
    
    // Set default date as today
    document.getElementById('tx-date').value = new Date().toISOString().split('T')[0];
    
    document.getElementById('tx-modal').style.display = 'flex';
    lucide.createIcons();
}

function openEditTransactionModal(tx) {
    document.getElementById('modal-title').textContent = "Edit Transaction";
    document.getElementById('tx-id-input').value = tx.id;
    document.getElementById('tx-date').value = tx.date;
    document.getElementById('tx-amount').value = tx.amount;
    document.getElementById('tx-account').value = tx.source_account;
    document.getElementById('tx-recipient').value = tx.recipient_or_use || '';
    document.getElementById('tx-comment').value = tx.comment || '';
    
    document.getElementById('tx-modal').style.display = 'flex';
    lucide.createIcons();
}

function closeTxModal() {
    document.getElementById('tx-modal').style.display = 'none';
}

// Save (Add or Update) Transaction
async function saveTransaction(event) {
    event.preventDefault();
    
    const id = document.getElementById('tx-id-input').value;
    const txData = {
        date: document.getElementById('tx-date').value,
        amount: parseFloat(document.getElementById('tx-amount').value),
        source_account: document.getElementById('tx-account').value,
        recipient_or_use: document.getElementById('tx-recipient').value,
        comment: document.getElementById('tx-comment').value
    };
    
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/transactions/${id}` : '/api/transactions';
    
    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(txData)
        });
        const res = await response.json();
        
        if (res.success) {
            showToast(id ? "Transaction updated successfully" : "Transaction created successfully");
            closeTxModal();
            refreshData();
        } else {
            showToast(res.message || "Failed to save transaction");
        }
    } catch (e) {
        console.error("Error saving transaction:", e);
        showToast("Server error occurred while saving");
    }
}

// Receipt/Statement Parser (Gemini) Actions
async function triggerClipboardParse() {
    showLoader(true, "Scanning clipboard data and parsing with Gemini...");
    
    try {
        const response = await fetch('/api/parse-clipboard', { method: 'POST' });
        const res = await response.json();
        
        showLoader(false);
        
        if (res.success) {
            showToast("Gemini parsed transactions successfully!");
            renderParsedPreview(res.data);
            // Switch to scanner tab if not already there, to view preview
            switchTab('scanner');
        } else {
            showToast(res.message || "No parseable financial content found on clipboard.");
        }
    } catch (e) {
        showLoader(false);
        console.error("Error parsing clipboard:", e);
        showToast("Gemini parsing failed or server is offline");
    }
}

async function triggerTextParse() {
    const text = document.getElementById('paste-text-input').value;
    if (!text || !text.trim()) {
        showToast("Please paste some transaction description text first");
        return;
    }
    
    showLoader(true, "Parsing statement text with Gemini 2.5 Flash...");
    
    const formData = new FormData();
    formData.append("text", text.trim());
    
    try {
        const response = await fetch('/api/upload-receipt', {
            method: 'POST',
            body: formData
        });
        const res = await response.json();
        
        showLoader(false);
        if (res.success) {
            showToast("Gemini parsed transactions successfully!");
            renderParsedPreview(res.data);
        } else {
            showToast(res.message || "Gemini could not identify any transaction structures in this text.");
        }
    } catch (e) {
        showLoader(false);
        console.error("Error parsing text:", e);
        showToast("Gemini parsing failed");
    }
}

// Upload local file helper
async function uploadReceiptFile(file) {
    showLoader(true, "Uploading image and executing Gemini multimodal inference...");
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const response = await fetch('/api/upload-receipt', {
            method: 'POST',
            body: formData
        });
        const res = await response.json();
        
        showLoader(false);
        if (res.success) {
            showToast("Gemini analyzed receipt image successfully!");
            renderParsedPreview(res.data);
        } else {
            showToast(res.message || "Failed to extract transaction data from image.");
        }
    } catch (e) {
        showLoader(false);
        console.error("Error uploading receipt:", e);
        showToast("Error communicating with parsing server");
    }
}

// Render the parsed data into editable preview rows
function renderParsedPreview(txList) {
    parsedTransactions = txList;
    
    const container = document.getElementById('parsed-preview-card');
    const tbody = document.getElementById('parsed-preview-tbody');
    tbody.innerHTML = '';
    
    if (!txList || txList.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    txList.forEach((tx, idx) => {
        const tr = document.createElement('tr');
        tr.id = `parsed-row-${idx}`;
        tr.innerHTML = `
            <td>
                <input type="date" class="input-table-edit" id="parsed-date-${idx}" value="${tx.date}">
            </td>
            <td>
                <select class="input-table-edit" id="parsed-account-${idx}">
                    <option value="HBL (Muhammad Jahanzaib)" ${tx.source_account.includes("Jahanzaib") ? 'selected' : ''}>HBL (Muhammad Jahanzaib)</option>
                    <option value="HBL (Sana Kanwal)" ${tx.source_account.includes("Sana") ? 'selected' : ''}>HBL (Sana Kanwal)</option>
                    <option value="EasyPaisa" ${tx.source_account === "EasyPaisa" ? 'selected' : ''}>EasyPaisa</option>
                    <option value="JazzCash" ${tx.source_account === "JazzCash" ? 'selected' : ''}>JazzCash</option>
                    <option value="Cash" ${tx.source_account === "Cash" ? 'selected' : ''}>Cash</option>
                </select>
            </td>
            <td>
                <input type="text" class="input-table-edit" id="parsed-recipient-${idx}" value="${tx.recipient_or_use || ''}">
            </td>
            <td>
                <input type="number" step="0.01" class="input-table-edit" id="parsed-amount-${idx}" value="${tx.amount}">
            </td>
            <td>
                <input type="text" class="input-table-edit" id="parsed-comment-${idx}" value="${tx.comment || ''}">
            </td>
            <td>
                <button class="btn-action delete" onclick="deleteParsedPreviewRow(${idx})" title="Remove">
                    <i data-lucide="minus-circle"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    container.style.display = 'block';
    // Scroll down to preview card
    container.scrollIntoView({ behavior: 'smooth' });
    lucide.createIcons();
}

function deleteParsedPreviewRow(idx) {
    const row = document.getElementById(`parsed-row-${idx}`);
    if (row) {
        row.remove();
    }
}

function cancelParsedPreview() {
    parsedTransactions = [];
    document.getElementById('parsed-preview-card').style.display = 'none';
    document.getElementById('paste-text-input').value = '';
}

// Commit the reviewed & edited transactions to the DB
async function commitParsedTransactions() {
    const listToCommit = [];
    const tbody = document.getElementById('parsed-preview-tbody');
    const rows = tbody.querySelectorAll('tr');
    
    if (rows.length === 0) {
        showToast("No transactions left to save.");
        return;
    }
    
    for (let r of rows) {
        const idx = r.id.split('-').pop();
        const dateVal = document.getElementById(`parsed-date-${idx}`).value;
        const amountVal = parseFloat(document.getElementById(`parsed-amount-${idx}`).value);
        const accountVal = document.getElementById(`parsed-account-${idx}`).value;
        const recipientVal = document.getElementById(`parsed-recipient-${idx}`).value;
        const commentVal = document.getElementById(`parsed-comment-${idx}`).value;
        
        if (!dateVal || isNaN(amountVal)) {
            showToast("Please ensure Date and Amount are filled in all rows.");
            return;
        }
        
        listToCommit.push({
            date: dateVal,
            amount: amountVal,
            source_account: accountVal,
            recipient_or_use: recipientVal,
            comment: commentVal
        });
    }
    
    showLoader(true, "Writing transactions to SQLite storage...");
    
    try {
        const response = await fetch('/api/commit-parsed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(listToCommit)
        });
        const res = await response.json();
        
        showLoader(false);
        if (res.success) {
            showToast(res.message);
            cancelParsedPreview();
            refreshData();
            // Go to dashboard to show committed items
            switchTab('dashboard');
        } else {
            showToast("Failed to write transactions to ledger.");
        }
    } catch (e) {
        showLoader(false);
        console.error("Error committing:", e);
        showToast("Error writing to local database");
    }
}

// Statement Generator Actions
function toggleReportIntervalInputs() {
    const interval = document.getElementById('report-interval').value;
    
    document.getElementById('report-date-container').style.display = interval === 'daily' ? 'block' : 'none';
    document.getElementById('report-month-container').style.display = interval === 'monthly' ? 'block' : 'none';
    document.getElementById('report-range-container').style.display = interval === 'custom' ? 'block' : 'none';
}

async function generateReport() {
    const interval = document.getElementById('report-interval').value;
    let start = '';
    let end = '';
    
    if (interval === 'daily') {
        const dateVal = document.getElementById('report-date').value;
        start = dateVal;
        end = dateVal;
    } else if (interval === 'monthly') {
        const monthVal = document.getElementById('report-month').value; // YYYY-MM
        start = `${monthVal}-01`;
        end = `${monthVal}-31`;
    } else {
        start = document.getElementById('report-start-date').value;
        end = document.getElementById('report-end-date').value;
    }
    
    if (!start || !end) {
        showToast("Please enter valid date criteria.");
        return;
    }
    
    try {
        const response = await fetch(`/api/report?start_date=${start}&end_date=${end}&report_type=${interval}`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('report-result-card').style.display = 'block';
            document.getElementById('report-output-text').textContent = data.report;
            showToast("Report generated successfully!");
        } else {
            showToast("Failed to compile statement report.");
        }
    } catch (e) {
        console.error("Error generating report:", e);
        showToast("Server error during statement compilation");
    }
}

function copyReportToClipboard() {
    const text = document.getElementById('report-output-text').textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast("Statement copied to clipboard!");
    }).catch(e => {
        showToast("Could not copy automatically. Please select and copy manually.");
    });
}

// Drag and drop event listeners
function setupDragAndDrop() {
    const zone = document.getElementById('drop-zone');
    const input = document.getElementById('file-input');
    
    zone.addEventListener('click', () => input.click());
    
    input.addEventListener('change', (e) => {
        if (input.files.length > 0) {
            uploadReceiptFile(input.files[0]);
        }
    });
    
    window.addEventListener('dragover', (e) => {
        e.preventDefault();
    }, false);
    
    window.addEventListener('drop', (e) => {
        e.preventDefault();
    }, false);
    
    zone.addEventListener('dragenter', (e) => {
        e.preventDefault();
        zone.style.borderColor = '#00E5FF';
        zone.style.background = 'rgba(0, 229, 255, 0.05)';
    });
    
    zone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        zone.style.borderColor = 'rgba(255, 255, 255, 0.15)';
        zone.style.background = 'transparent';
    });
    
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.style.borderColor = 'rgba(255, 255, 255, 0.15)';
        zone.style.background = 'transparent';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadReceiptFile(files[0]);
        }
    });
}
