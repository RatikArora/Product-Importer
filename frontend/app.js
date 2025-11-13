/**
 * Product Importer Frontend Application
 * Handles CSV upload, product management, and webhook configuration
 */

// Configuration
const API_BASE_URL = window.location.origin;
const API_V1 = `${API_BASE_URL}/api/v1`;

// Global state
let currentUploadJobId = null;
let progressEventSource = null;
let currentProductsPage = 0;
let productsPerPage = 20;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupFileUpload();
    setupTabHandlers();
    loadInitialData();
    
    // Set up search input handlers with debounce
    setupSearch();
}

function setupFileUpload() {
    const dropZone = document.getElementById('dropZone');
    const csvFile = document.getElementById('csvFile');

    // Click to select file
    dropZone.addEventListener('click', function() {
        csvFile.click();
    });

    // File input change
    csvFile.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Drag and drop
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });
}

function setupTabHandlers() {
    document.getElementById('products-tab').addEventListener('shown.bs.tab', function() {
        loadProducts();
    });
    
    document.getElementById('webhooks-tab').addEventListener('shown.bs.tab', function() {
        loadWebhooks();
    });
    
    document.getElementById('health-tab').addEventListener('shown.bs.tab', function() {
        checkHealth();
    });
}

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const skuFilter = document.getElementById('skuFilter');
    const activeFilter = document.getElementById('activeFilter');
    
    let searchTimeout;
    
    const debouncedSearch = function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(loadProducts, 500);
    };
    
    searchInput?.addEventListener('input', debouncedSearch);
    skuFilter?.addEventListener('input', debouncedSearch);
    activeFilter?.addEventListener('change', debouncedSearch);
}

function loadInitialData() {
    loadRecentImports();
}

// File Upload Functions
async function handleFileUpload(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showAlert('danger', 'Only CSV files are allowed');
        return;
    }

    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
        showAlert('danger', 'File too large. Maximum size is 100MB');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        showProgress(true);
        updateProgress(0, 'Uploading file...', 0, 0, 0);

        const response = await fetch(`${API_V1}/upload/`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Upload failed');
        }

        const result = await response.json();
        currentUploadJobId = result.job_id;
        
        showAlert('success', result.message);
        
        // Start progress monitoring
        startProgressMonitoring(result.job_id);
        
        // Refresh recent imports
        loadRecentImports();

    } catch (error) {
        showAlert('danger', `Upload failed: ${error.message}`);
        showProgress(false);
    }
}

function startProgressMonitoring(jobId) {
    // Close existing event source
    if (progressEventSource) {
        progressEventSource.close();
    }

    // Start Server-Sent Events for real-time progress
    progressEventSource = new EventSource(`${API_V1}/upload/progress/${jobId}/stream`);
    
    progressEventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        updateProgress(
            data.progress_percentage,
            getStatusMessage(data.status),
            data.processed_records,
            data.total_records,
            data.failed_records
        );

        if (data.status === 'completed' || data.status === 'failed') {
            progressEventSource.close();
            progressEventSource = null;
            
            if (data.status === 'completed') {
                showAlert('success', 'Import completed successfully!');
                // Refresh products if on products tab
                if (document.getElementById('products-tab').classList.contains('active')) {
                    loadProducts();
                }
            } else {
                showAlert('danger', `Import failed: ${data.error_message}`);
            }
            
            loadRecentImports();
        }
    };

    progressEventSource.onerror = function() {
        progressEventSource.close();
        progressEventSource = null;
        // Fallback to polling
        pollProgress(jobId);
    };
}

async function pollProgress(jobId) {
    let attempts = 0;
    const maxAttempts = 60; // 2 minutes max polling
    
    const poll = async () => {
        try {
            const response = await fetch(`${API_V1}/upload/progress/${jobId}`);
            const data = await response.json();
            
            updateProgress(
                data.progress_percentage,
                getStatusMessage(data.status),
                data.processed_records,
                data.total_records,
                data.failed_records
            );

            if (data.status === 'completed' || data.status === 'failed') {
                if (data.status === 'completed') {
                    showAlert('success', 'Import completed successfully!');
                } else {
                    showAlert('danger', `Import failed: ${data.error_message}`);
                }
                loadRecentImports();
                return;
            }

            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(poll, 2000);
            }
        } catch (error) {
            console.error('Progress polling error:', error);
        }
    };

    poll();
}

function updateProgress(percentage, message, processed, total, failed) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressLabel = document.getElementById('progressLabel');
    const progressPercent = document.getElementById('progressPercent');
    const processedCount = document.getElementById('processedCount');
    const totalCount = document.getElementById('totalCount');
    const failedCount = document.getElementById('failedCount');

    const roundedPercentage = Math.round(percentage);
    
    progressBar.style.width = `${percentage}%`;
    progressText.textContent = `${roundedPercentage}%`;
    progressLabel.textContent = message;
    progressPercent.textContent = `${roundedPercentage}%`;
    processedCount.textContent = processed.toLocaleString();
    totalCount.textContent = total.toLocaleString();
    failedCount.textContent = failed.toLocaleString();
}

function showProgress(show) {
    const progressContainer = document.getElementById('progressContainer');
    progressContainer.style.display = show ? 'block' : 'none';
    
    if (!show) {
        updateProgress(0, 'Ready', 0, 0, 0);
    }
}

function getStatusMessage(status) {
    const messages = {
        'pending': 'Waiting to start...',
        'processing': 'Processing records...',
        'completed': 'Import completed!',
        'failed': 'Import failed'
    };
    return messages[status] || 'Processing...';
}

// Recent Imports Functions
async function loadRecentImports() {
    try {
        const response = await fetch(`${API_V1}/upload/jobs?limit=5`);
        const jobs = await response.json();
        
        const container = document.getElementById('recentImports');
        
        if (jobs.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No recent imports</p>';
            return;
        }

        const html = jobs.map(job => `
            <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                <div>
                    <strong>${job.filename}</strong>
                    <br>
                    <small class="text-muted">${new Date(job.created_at).toLocaleString()}</small>
                </div>
                <div class="text-end">
                    <span class="status-badge status-${job.status}">${job.status}</span>
                    <br>
                    <small class="text-muted">${job.processed_records}/${job.total_records} records</small>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
        
    } catch (error) {
        console.error('Failed to load recent imports:', error);
        document.getElementById('recentImports').innerHTML = '<p class="text-danger">Failed to load recent imports</p>';
    }
}

// Product Management Functions
async function loadProducts(page = 0) {
    const tableContainer = document.getElementById('productsTable');
    tableContainer.innerHTML = '<div class="loading-spinner"><div class="spinner-border-custom"></div><p class="mt-2">Loading products...</p></div>';

    try {
        const searchInput = document.getElementById('searchInput');
        const skuFilter = document.getElementById('skuFilter');
        const activeFilter = document.getElementById('activeFilter');
        
        const params = new URLSearchParams({
            limit: productsPerPage,
            offset: page * productsPerPage
        });

        if (searchInput?.value) params.append('search', searchInput.value);
        if (skuFilter?.value) params.append('sku', skuFilter.value);
        if (activeFilter?.value) params.append('active', activeFilter.value);

        const response = await fetch(`${API_V1}/products/?${params}`);
        const data = await response.json();
        
        renderProductsTable(data.items);
        renderPagination(data, 'productsPagination', loadProducts);
        currentProductsPage = page;

    } catch (error) {
        console.error('Failed to load products:', error);
        tableContainer.innerHTML = '<div class="alert alert-danger">Failed to load products</div>';
    }
}

function renderProductsTable(products) {
    const tableContainer = document.getElementById('productsTable');
    
    if (products.length === 0) {
        tableContainer.innerHTML = '<div class="alert alert-info text-center">No products found</div>';
        return;
    }

    const html = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>SKU</th>
                        <th>Description</th>
                        <th>Price</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${products.map(product => `
                        <tr>
                            <td><strong>${escapeHtml(product.name)}</strong></td>
                            <td><code>${escapeHtml(product.sku)}</code></td>
                            <td>${product.description ? escapeHtml(product.description.substring(0, 100) + (product.description.length > 100 ? '...' : '')) : '-'}</td>
                            <td>$${Number(product.price || 0).toFixed(2)}</td>
                            <td>
                                <span class="status-badge ${product.active ? 'status-active' : 'status-inactive'}">
                                    ${product.active ? 'Active' : 'Inactive'}
                                </span>
                            </td>
                            <td>${new Date(product.created_at).toLocaleDateString()}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-info me-1" onclick="editProduct(${product.id})">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteProduct(${product.id}, '${product.name.replace(/'/g, "\\'")}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;

    tableContainer.innerHTML = html;
}

function renderPagination(data, containerId, loadFunction) {
    const container = document.getElementById(containerId);
    const totalPages = Math.ceil(data.total / data.limit);
    const currentPage = Math.floor(data.offset / data.limit);
    
    if (totalPages <= 1) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    const pagination = container.querySelector('.pagination');
    
    let html = '';
    
    // Previous button
    html += `
        <li class="page-item ${!data.has_prev ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="event.preventDefault(); ${data.has_prev ? `${loadFunction.name}(${currentPage - 1})` : ''}">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Page numbers
    const startPage = Math.max(0, currentPage - 2);
    const endPage = Math.min(totalPages - 1, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="event.preventDefault(); ${loadFunction.name}(${i})">
                    ${i + 1}
                </a>
            </li>
        `;
    }
    
    // Next button
    html += `
        <li class="page-item ${!data.has_next ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="event.preventDefault(); ${data.has_next ? `${loadFunction.name}(${currentPage + 1})` : ''}">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

function showCreateProductModal() {
    clearProductForm();
    document.getElementById('productModalTitle').textContent = 'Add Product';
    const modal = new bootstrap.Modal(document.getElementById('productModal'));
    modal.show();
}

async function editProduct(productId) {
    try {
        const response = await fetch(`${API_V1}/products/${productId}`);
        const product = await response.json();
        
        document.getElementById('productId').value = product.id;
        document.getElementById('productName').value = product.name;
        document.getElementById('productSku').value = product.sku;
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productPrice').value = product.price || 0;
        document.getElementById('productActive').checked = product.active;
        
        document.getElementById('productModalTitle').textContent = 'Edit Product';
        const modal = new bootstrap.Modal(document.getElementById('productModal'));
        modal.show();
        
    } catch (error) {
        showAlert('danger', 'Failed to load product details');
    }
}

async function saveProduct() {
    const productId = document.getElementById('productId').value;
    const isEdit = !!productId;
    
    const productData = {
        name: document.getElementById('productName').value,
        sku: document.getElementById('productSku').value,
        description: document.getElementById('productDescription').value || null,
        price: parseFloat(document.getElementById('productPrice').value) || 0,
        active: document.getElementById('productActive').checked
    };

    try {
        const url = isEdit ? `${API_V1}/products/${productId}` : `${API_V1}/products/`;
        const method = isEdit ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Save failed');
        }

        showAlert('success', `Product ${isEdit ? 'updated' : 'created'} successfully`);
        bootstrap.Modal.getInstance(document.getElementById('productModal')).hide();
        loadProducts(currentProductsPage);
        
    } catch (error) {
        showAlert('danger', `Failed to save product: ${error.message}`);
    }
}

function deleteProduct(productId, productName) {
    if (!productName) {
        productName = 'this product';
    }
    
    showConfirmModal(
        'Delete Product',
        `Are you sure you want to delete "${productName}"? This action cannot be undone.`,
        async () => {
            try {
                const response = await fetch(`${API_V1}/products/${productId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Delete failed');
                }

                showAlert('success', 'Product deleted successfully');
                loadProducts(currentProductsPage);
                
            } catch (error) {
                console.error('Error deleting product:', error);
                showAlert('danger', error.message || 'Failed to delete product');
            }
        }
    );
}

function confirmBulkDelete() {
    showConfirmModal(
        'Delete All Products',
        'Are you sure you want to delete ALL products? This action cannot be undone and will remove all product data from the system.',
        async () => {
            try {
                const response = await fetch(`${API_V1}/products/`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    throw new Error('Bulk delete failed');
                }

                const result = await response.json();
                showAlert('success', result.message);
                loadProducts(0);
                
            } catch (error) {
                showAlert('danger', 'Failed to delete products');
            }
        }
    );
}

function clearProductForm() {
    document.getElementById('productForm').reset();
    document.getElementById('productId').value = '';
    document.getElementById('productActive').checked = true;
}

// Webhook Management Functions
async function loadWebhooks() {
    const tableContainer = document.getElementById('webhooksTable');
    tableContainer.innerHTML = '<div class="loading-spinner"><div class="spinner-border-custom"></div><p class="mt-2">Loading webhooks...</p></div>';

    try {
        const response = await fetch(`${API_V1}/webhooks/`);
        const webhooks = await response.json();
        
        renderWebhooksTable(webhooks);

    } catch (error) {
        console.error('Failed to load webhooks:', error);
        tableContainer.innerHTML = '<div class="alert alert-danger">Failed to load webhooks</div>';
    }
}

function renderWebhooksTable(webhooks) {
    const tableContainer = document.getElementById('webhooksTable');
    
    if (webhooks.length === 0) {
        tableContainer.innerHTML = '<div class="alert alert-info text-center">No webhooks configured</div>';
        return;
    }

    const html = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>URL</th>
                        <th>Events</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${webhooks.map(webhook => `
                        <tr>
                            <td><strong>${escapeHtml(webhook.name)}</strong></td>
                            <td>
                                <code>${escapeHtml(webhook.url.length > 50 ? webhook.url.substring(0, 50) + '...' : webhook.url)}</code>
                            </td>
                            <td>
                                <small>
                                    ${webhook.event_types.map(event => `<span class="badge bg-secondary me-1">${event}</span>`).join('')}
                                </small>
                            </td>
                            <td>
                                <span class="status-badge ${webhook.active ? 'status-active' : 'status-inactive'}">
                                    ${webhook.active ? 'Active' : 'Inactive'}
                                </span>
                            </td>
                            <td>${new Date(webhook.created_at).toLocaleDateString()}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-success me-1" onclick="testWebhook(${webhook.id})">
                                    <i class="fas fa-play"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-info me-1" onclick="editWebhook(${webhook.id})">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteWebhook(${webhook.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;

    tableContainer.innerHTML = html;
}

function showCreateWebhookModal() {
    clearWebhookForm();
    document.getElementById('webhookModalTitle').textContent = 'Add Webhook';
    const modal = new bootstrap.Modal(document.getElementById('webhookModal'));
    modal.show();
}

async function editWebhook(webhookId) {
    try {
        const response = await fetch(`${API_V1}/webhooks/${webhookId}`);
        const webhook = await response.json();
        
        document.getElementById('webhookId').value = webhook.id;
        document.getElementById('webhookName').value = webhook.name;
        document.getElementById('webhookUrl').value = webhook.url;
        document.getElementById('webhookSecret').value = webhook.secret || '';
        document.getElementById('webhookActive').checked = webhook.active;
        
        // Set event checkboxes
        const eventCheckboxes = document.querySelectorAll('#webhookModal input[type="checkbox"][value]');
        eventCheckboxes.forEach(cb => {
            cb.checked = webhook.event_types.includes(cb.value);
        });
        
        document.getElementById('webhookModalTitle').textContent = 'Edit Webhook';
        const modal = new bootstrap.Modal(document.getElementById('webhookModal'));
        modal.show();
        
    } catch (error) {
        showAlert('danger', 'Failed to load webhook details');
    }
}

async function saveWebhook() {
    const webhookId = document.getElementById('webhookId').value;
    const isEdit = !!webhookId;
    
    const eventTypes = Array.from(document.querySelectorAll('#webhookModal input[type="checkbox"][value]:checked'))
        .map(cb => cb.value);
    
    if (eventTypes.length === 0) {
        showAlert('warning', 'Please select at least one event type');
        return;
    }
    
    const webhookData = {
        name: document.getElementById('webhookName').value,
        url: document.getElementById('webhookUrl').value,
        event_types: eventTypes,
        secret: document.getElementById('webhookSecret').value || null,
        active: document.getElementById('webhookActive').checked
    };

    try {
        const url = isEdit ? `${API_V1}/webhooks/${webhookId}` : `${API_V1}/webhooks/`;
        const method = isEdit ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(webhookData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Save failed');
        }

        showAlert('success', `Webhook ${isEdit ? 'updated' : 'created'} successfully`);
        bootstrap.Modal.getInstance(document.getElementById('webhookModal')).hide();
        loadWebhooks();
        
    } catch (error) {
        showAlert('danger', `Failed to save webhook: ${error.message}`);
    }
}

async function testWebhook(webhookId) {
    try {
        const response = await fetch(`${API_V1}/webhooks/${webhookId}/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();
        
        if (result.success) {
            showAlert('success', `Webhook test successful! Response: ${result.status_code} (${result.response_time_ms}ms)`);
        } else {
            showAlert('warning', `Webhook test failed: ${result.error}`);
        }
        
    } catch (error) {
        showAlert('danger', 'Failed to test webhook');
    }
}

function deleteWebhook(webhookId) {
    showConfirmModal(
        'Delete Webhook',
        'Are you sure you want to delete this webhook? This action cannot be undone.',
        async () => {
            try {
                const response = await fetch(`${API_V1}/webhooks/${webhookId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    throw new Error('Delete failed');
                }

                showAlert('success', 'Webhook deleted successfully');
                loadWebhooks();
                
            } catch (error) {
                showAlert('danger', 'Failed to delete webhook');
            }
        }
    );
}

function clearWebhookForm() {
    document.getElementById('webhookForm').reset();
    document.getElementById('webhookId').value = '';
    document.getElementById('webhookActive').checked = true;
    
    // Clear event checkboxes
    const eventCheckboxes = document.querySelectorAll('#webhookModal input[type="checkbox"][value]');
    eventCheckboxes.forEach(cb => {
        cb.checked = false;
    });
}

// Health Check Functions
async function checkHealth() {
    const container = document.getElementById('healthStatus');
    container.innerHTML = '<div class="loading-spinner"><div class="spinner-border-custom"></div><p class="mt-2">Checking system health...</p></div>';

    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const health = await response.json();
        
        renderHealthStatus(health);

    } catch (error) {
        console.error('Failed to check health:', error);
        container.innerHTML = '<div class="alert alert-danger">Failed to check system health</div>';
    }
}

function renderHealthStatus(health) {
    const container = document.getElementById('healthStatus');
    
    const getStatusClass = (status) => {
        if (status === 'healthy') return 'success';
        if (status === 'degraded') return 'warning';
        return 'danger';
    };
    
    const getStatusIcon = (status) => {
        if (status === 'healthy') return 'fas fa-check-circle';
        if (status === 'degraded') return 'fas fa-exclamation-triangle';
        return 'fas fa-times-circle';
    };

    const html = `
        <div class="row">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="${getStatusIcon(health.status)} fa-2x text-${getStatusClass(health.status)}"></i>
                        <h5 class="card-title mt-2">Overall</h5>
                        <span class="badge bg-${getStatusClass(health.status)}">${health.status}</span>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="${getStatusIcon(health.database.includes('healthy') ? 'healthy' : 'unhealthy')} fa-2x text-${getStatusClass(health.database.includes('healthy') ? 'healthy' : 'unhealthy')}"></i>
                        <h5 class="card-title mt-2">Database</h5>
                        <span class="badge bg-${getStatusClass(health.database.includes('healthy') ? 'healthy' : 'unhealthy')}">${health.database}</span>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="${getStatusIcon(health.redis.includes('healthy') ? 'healthy' : 'unhealthy')} fa-2x text-${getStatusClass(health.redis.includes('healthy') ? 'healthy' : 'unhealthy')}"></i>
                        <h5 class="card-title mt-2">Redis</h5>
                        <span class="badge bg-${getStatusClass(health.redis.includes('healthy') ? 'healthy' : 'unhealthy')}">${health.redis}</span>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="${getStatusIcon(health.celery.includes('healthy') ? 'healthy' : 'degraded')} fa-2x text-${getStatusClass(health.celery.includes('healthy') ? 'healthy' : 'degraded')}"></i>
                        <h5 class="card-title mt-2">Celery</h5>
                        <span class="badge bg-${getStatusClass(health.celery.includes('healthy') ? 'healthy' : 'degraded')}">${health.celery}</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="mt-4">
            <div class="card">
                <div class="card-body">
                    <h6 class="card-title">System Information</h6>
                    <ul class="list-unstyled">
                        <li><strong>Last Check:</strong> ${new Date(health.timestamp).toLocaleString()}</li>
                        <li><strong>API Status:</strong> <span class="text-success">Operational</span></li>
                    </ul>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// Utility Functions
function showAlert(type, message) {
    const alertContainer = document.getElementById('alertContainer');
    const alertId = 'alert-' + Date.now();
    
    const alert = document.createElement('div');
    alert.id = alertId;
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            const bsAlert = bootstrap.Alert.getInstance(alertElement);
            if (bsAlert) {
                bsAlert.close();
            } else {
                alertElement.remove();
            }
        }
    }, 5000);
}

function showConfirmModal(title, message, onConfirm) {
    document.querySelector('#confirmModal .modal-title').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    
    const confirmButton = document.getElementById('confirmButton');
    
    // Remove existing click handlers
    const newButton = confirmButton.cloneNode(true);
    confirmButton.parentNode.replaceChild(newButton, confirmButton);
    
    // Add new click handler
    newButton.addEventListener('click', function() {
        bootstrap.Modal.getInstance(document.getElementById('confirmModal')).hide();
        onConfirm();
    });
    
    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    modal.show();
}

// Product Management Functions
function showCreateProductModal() {
    document.getElementById('productModalTitle').textContent = 'Add New Product';
    document.getElementById('saveButtonText').textContent = 'Save Product';
    document.getElementById('productForm').reset();
    document.getElementById('productId').value = '';
    document.getElementById('productActive').checked = true;
    
    const modal = new bootstrap.Modal(document.getElementById('productModal'));
    modal.show();
}

function editProduct(productId) {
    // Fetch product details and populate modal
    fetch(`${API_V1}/products/${productId}`)
        .then(response => response.json())
        .then(product => {
            document.getElementById('productModalTitle').textContent = 'Edit Product';
            document.getElementById('saveButtonText').textContent = 'Update Product';
            document.getElementById('productId').value = product.id;
            document.getElementById('productSku').value = product.sku;
            document.getElementById('productName').value = product.name;
            document.getElementById('productDescription').value = product.description || '';
            document.getElementById('productPrice').value = product.price || '';
            document.getElementById('productActive').checked = product.active;
            
            const modal = new bootstrap.Modal(document.getElementById('productModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error fetching product:', error);
            showAlert('Error loading product details', 'danger');
        });
}

function saveProduct() {
    const form = document.getElementById('productForm');
    const productId = document.getElementById('productId').value;
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const productData = {
        sku: document.getElementById('productSku').value.trim(),
        name: document.getElementById('productName').value.trim(),
        description: document.getElementById('productDescription').value.trim() || null,
        price: parseFloat(document.getElementById('productPrice').value) || 0,
        active: document.getElementById('productActive').checked
    };
    
    const url = productId ? `${API_V1}/products/${productId}` : `${API_V1}/products/`;
    const method = productId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(productData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(result => {
        bootstrap.Modal.getInstance(document.getElementById('productModal')).hide();
        loadProducts(); // Refresh the products list
        showAlert(`Product ${productId ? 'updated' : 'created'} successfully!`, 'success');
    })
    .catch(error => {
        console.error('Error saving product:', error);
        showAlert(error.detail || 'Error saving product', 'danger');
    });
}

// Global functions for window

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Export functions for global access
window.showCreateProductModal = showCreateProductModal;
window.editProduct = editProduct;
window.saveProduct = saveProduct;
window.deleteProduct = deleteProduct;
window.confirmBulkDelete = confirmBulkDelete;
window.showCreateWebhookModal = showCreateWebhookModal;
window.editWebhook = editWebhook;
window.saveWebhook = saveWebhook;
window.testWebhook = testWebhook;
window.deleteWebhook = deleteWebhook;
window.loadProducts = loadProducts;