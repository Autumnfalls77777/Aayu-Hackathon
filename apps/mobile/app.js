// SASTI DAWAI - PWA Application Logic
const API_BASE = 'http://localhost:8000/api/v1';

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
        // Fallback: show manual entry
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
                <span>❌</span>
                <span>No exact equivalent found</span>
            </div>
            <div class="safety-notice">
                <span class="safety-icon">⚠️</span>
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
                <span>✓</span>
                <span>EXACT EQUIVALENT FOUND</span>
            </div>
            ${savings ? `
            <div class="savings-card">
                <div class="savings-label">Potential Saving</div>
                <div class="savings-amount">₹${savings.absolute_saving}</div>
                <div class="savings-label">${savings.percentage_saving}% cheaper</div>
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
                <span class="safety-icon">⚠️</span>
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
            <p style="color: var(--text-light); margin-bottom: 16px;">OCR couldn't read the image. Please enter medicine details manually.</p>
            <input type="text" id="manual-name" placeholder="Medicine name" style="width:100%;padding:12px;margin-bottom:12px;border:2px solid var(--border);border-radius:8px;">
            <input type="text" id="manual-salt" placeholder="Salt/Composition" style="width:100%;padding:12px;margin-bottom:12px;border:2px solid var(--border);border-radius:8px;">
            <input type="text" id="manual-strength" placeholder="Strength (e.g., 500mg)" style="width:100%;padding:12px;margin-bottom:12px;border:2px solid var(--border);border-radius:8px;">
            <select id="manual-form" style="width:100%;padding:12px;margin-bottom:16px;border:2px solid var(--border);border-radius:8px;">
                <tablet>Tablet</tablet>
                <capsule>Capsule</capsule>
                <syrup>Syrup</syrup>
                <injection>Injection</injection>
                <drops>Drops</drops>
                <cream>Cream</cream>
                <ointment>Ointment</ointment>
            </select>
            <button class="btn btn-primary" onclick="submitManualEntry()">Find Equivalent</button>
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
            container.innerHTML = '<p style="text-align:center;color:var(--text-light);padding:20px;">No medicines found</p>';
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
            <button class="btn btn-primary" onclick="findAlternatives(${med.id})">Find Exact Equivalents</button>
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
                    <span>❌</span>
                    <span>No exact equivalent found</span>
                </div>
                <div class="safety-notice">
                    <span class="safety-icon">⚠️</span>
                    <span class="safety-text">No exact equivalent found in our current database.</span>
                </div>
            `;
        } else {
            content.innerHTML = `
                <div class="match-status exact">
                    <span>✓</span>
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
                    <span class="safety-icon">⚠️</span>
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
});
