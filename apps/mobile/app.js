// SASTI DAWAI - PWA Application Logic
const API_BASE = 'http://localhost:8000/api/v1';

// SVG Icons
const icons = {
    check: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    x: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    warning: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    pill: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.5 20.5 3.5 13.5a4.95 4.95 0 1 1 7-7l7 7a4.95 4.95 0 1 1-7 7Z"/><path d="m8.5 8.5 7 7"/></svg>',
    camera: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
    search: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    upload: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    file: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    flask: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6"/><path d="M10 3v5.5L4.5 18a2 2 0 0 0 1.8 3h11.4a2 2 0 0 0 1.8-3L14 8.5V3"/><line x1="7" y1="15" x2="17" y2="15"/></svg>',
    users: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
};

// Screen navigation
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');

    if (screenId === 'scan-screen') {
        startCamera();
    } else {
        stopCamera();
    }
}

// Camera handling
let stream = null;

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } }
        });
        const video = document.getElementById('camera-video');
        video.srcObject = stream;
    } catch (err) {
        console.error('Camera error:', err);
        alert('Camera access denied. Please use upload option.');
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
}

// Capture image
function captureImage() {
    const video = document.getElementById('camera-video');
    if (!video || !stream) {
        alert('Camera not ready. Please wait or use upload.');
        return;
    }

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    canvas.toBlob(processImage, 'image/jpeg', 0.85);
}

// Handle file upload
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        if (file.size > 10 * 1024 * 1024) {
            alert('File too large. Maximum 10MB allowed.');
            return;
        }
        processImage(file);
    }
}

// Process image - send to OCR API
async function processImage(imageBlob) {
    showScreen('analyzing-screen');
    simulateAnalysis();

    try {
        const formData = new FormData();
        formData.append('file', imageBlob, 'medicine.jpg');

        const response = await fetch(`${API_BASE}/scan`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error('OCR failed');
        }

        const result = await response.json();
        displayResult(result);
    } catch (err) {
        console.error('OCR error:', err);
        showManualEntry();
    }
}

// Simulate analysis steps
function simulateAnalysis() {
    const steps = ['step-text', 'step-medicine', 'step-composition', 'step-matching'];
    let i = 0;
    const interval = setInterval(() => {
        if (i > 0) {
            document.getElementById(steps[i-1]).classList.remove('active');
            document.getElementById(steps[i-1]).classList.add('completed');
        }
        if (i < steps.length) {
            document.getElementById(steps[i]).classList.add('active');
            i++;
        } else {
            clearInterval(interval);
        }
    }, 800);
}

// Display result
function displayResult(result) {
    const content = document.getElementById('result-content');

    if (!result.exact_match) {
        content.innerHTML = `
            <div class="result-card">
                <div class="medicine-name">${result.brand_name || 'Unknown Medicine'}</div>
                <div class="medicine-composition">${result.ingredients?.map(i => i.name).join(' + ') || 'Composition unknown'}</div>
                <div class="medicine-details">${result.dosage_form || ''} ${result.strength || ''}</div>
            </div>
            <div class="match-status no-match">
                ${icons.x}
                <span>No exact equivalent found</span>
            </div>
            <div class="safety-notice">
                <span class="safety-icon">${icons.warning}</span>
                <span class="safety-text">Unable to confidently verify an exact equivalent. Please check the medicine details with your pharmacist or doctor.</span>
            </div>
        `;
    } else {
        const savings = result.savings;
        content.innerHTML = `
            <div class="result-card">
                <div class="medicine-name">${result.brand_name || 'Medicine'}</div>
                <div class="medicine-composition">${result.ingredients?.map(i => `${i.name} ${i.strength}${i.unit}`).join(' + ') || ''}</div>
                <div class="medicine-details">${result.dosage_form || ''}</div>
            </div>
            <div class="match-status exact">
                ${icons.check}
                <span>EXACT EQUIVALENT FOUND</span>
            </div>
            ${savings ? `
            <div class="savings-card">
                <div class="savings-label">Potential Saving</div>
                <div class="savings-amount">₹${savings.absolute_saving}</div>
                <div class="savings-percent">${savings.percentage_saving}% cheaper</div>
                <div class="savings-details">
                    <div class="savings-item">
                        <div class="savings-item-value">₹${savings.current_price}</div>
                        <div class="savings-item-label">Your Medicine</div>
                    </div>
                    <div class="savings-item">
                        <div class="savings-item-value">₹${savings.equivalent_price}</div>
                        <div class="savings-item-label">Jan Aushadhi</div>
                    </div>
                </div>
            </div>
            ` : ''}
            <div class="why-match">
                <h3>WHY THIS MATCHES</h3>
                <ul>
                    <li>Same active ingredient</li>
                    <li>Same strength</li>
                    <li>Same dosage form</li>
                </ul>
            </div>
            <div class="safety-notice">
                <span class="safety-icon">${icons.warning}</span>
                <span class="safety-text">Confirm with your doctor or pharmacist before switching.</span>
            </div>
        `;
    }

    showScreen('result-screen');
}

// Manual entry fallback
function showManualEntry() {
    const content = document.getElementById('result-content');
    content.innerHTML = `
        <div class="result-card">
            <h3>Manual Entry</h3>
            <p style="color: var(--text-muted); margin-bottom: 16px; font-size: 14px;">OCR couldn't read the image. Please enter medicine details manually.</p>
            <input type="text" id="manual-name" placeholder="Medicine name" class="manual-input">
            <input type="text" id="manual-salt" placeholder="Salt/Composition" class="manual-input">
            <input type="text" id="manual-strength" placeholder="Strength (e.g., 500mg)" class="manual-input">
            <select id="manual-form" class="manual-input">
                <option value="tablet">Tablet</option>
                <option value="capsule">Capsule</option>
                <option value="syrup">Syrup</option>
                <option value="injection">Injection</option>
                <option value="drops">Drops</option>
                <option value="cream">Cream</option>
                <option value="ointment">Ointment</option>
            </select>
            <button class="btn-primary" onclick="submitManualEntry()" style="margin-top: 16px;">
                <span>Find Equivalent</span>
            </button>
        </div>
    `;
    showScreen('result-screen');
}

async function submitManualEntry() {
    const name = document.getElementById('manual-name').value;
    const salt = document.getElementById('manual-salt').value;
    const strength = document.getElementById('manual-strength').value;
    const form = document.getElementById('manual-form').value;

    if (!salt || !strength || !form) {
        alert('Please fill all fields');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/match`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                brand_name: name,
                ingredients: [{ name: salt, strength: parseFloat(strength), unit: 'mg' }],
                dosage_form: form,
            }),
        });

        const result = await response.json();
        displayResult(result);
    } catch (err) {
        alert('Failed to find equivalent. Please try again.');
    }
}

// Search medicines
async function searchMedicines(query) {
    if (query.length < 2) {
        document.getElementById('search-results').innerHTML = '';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/medicines/search?q=${encodeURIComponent(query)}`);
        const results = await response.json();

        const container = document.getElementById('search-results');
        if (results.length === 0) {
            container.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:20px;font-size:14px;">No medicines found</p>';
            return;
        }

        container.innerHTML = results.map(med => `
            <div class="search-result-item" onclick="showMedicineDetail(${med.id})">
                <div class="search-result-name">${med.name}</div>
                <div class="search-result-meta">${med.manufacturer || ''} • ${med.dosage_form || ''}</div>
                <div class="search-result-price">${med.price ? '₹' + med.price : 'Price unavailable'}</div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Search error:', err);
    }
}

// Search by category
async function searchCategory(category) {
    showScreen('search-screen');
    document.getElementById('search-input').value = category;
    searchMedicines(category);
}

// Show medicine detail
async function showMedicineDetail(id) {
    try {
        const response = await fetch(`${API_BASE}/medicines/${id}`);
        const med = await response.json();

        const content = document.getElementById('detail-content');
        content.innerHTML = `
            <div class="detail-card">
                <div class="detail-name">${med.name}</div>
                <div class="detail-row">
                    <span class="detail-label">Manufacturer</span>
                    <span class="detail-value">${med.manufacturer || 'Unknown'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Price</span>
                    <span class="detail-value">${med.price ? '₹' + med.price : 'Unavailable'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Form</span>
                    <span class="detail-value">${med.dosage_form || 'Unknown'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Pack Size</span>
                    <span class="detail-value">${med.pack_size_label || 'Unknown'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Composition</span>
                    <span class="detail-value">${med.ingredients?.map(i => i.name).join(' + ') || 'Unknown'}</span>
                </div>
            </div>
            <button class="btn-primary" onclick="findAlternatives(${med.id})">
                <span>Find Exact Equivalents</span>
            </button>
        `;

        showScreen('detail-screen');
    } catch (err) {
        alert('Failed to load medicine details');
    }
}

// Find alternatives
async function findAlternatives(id) {
    try {
        const response = await fetch(`${API_BASE}/medicines/${id}/alternatives`);
        const data = await response.json();

        const content = document.getElementById('detail-content');
        if (data.exact_matches === 0) {
            content.innerHTML = `
                <div class="match-status no-match">
                    ${icons.x}
                    <span>No exact equivalent found</span>
                </div>
                <div class="safety-notice">
                    <span class="safety-icon">${icons.warning}</span>
                    <span class="safety-text">No exact equivalent found in our current database.</span>
                </div>
            `;
        } else {
            content.innerHTML = `
                <div class="match-status exact">
                    ${icons.check}
                    <span>${data.exact_matches} EXACT EQUIVALENT(S) FOUND</span>
                </div>
                ${data.matches.map(m => `
                    <div class="detail-card">
                        <div class="detail-name">${m.name}</div>
                        <div class="detail-row">
                            <span class="detail-label">Price</span>
                            <span class="detail-value">${m.mrp ? '₹' + m.mrp : 'Unavailable'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Confidence</span>
                            <span class="detail-value">${(m.confidence * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                `).join('')}
                <div class="safety-notice">
                    <span class="safety-icon">${icons.warning}</span>
                    <span class="safety-text">Confirm with your doctor or pharmacist before switching.</span>
                </div>
            `;
        }
    } catch (err) {
        alert('Failed to find alternatives');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Check for camera support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn('Camera not supported');
    }

    // Register service worker for PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js').catch(console.error);
    }

    // Hide splash screen after animation
    setTimeout(() => {
        const splash = document.getElementById('splash-screen');
        if (splash) {
            splash.style.display = 'none';
        }
    }, 3000);
});
