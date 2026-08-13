// Global Chart Instances
let spendingChart = null;
let profitSensitivityChart = null;
let radarSuitabilityChart = null;
let yieldBenchmarkChart = null;

let currentPredictionData = null;
let savedScenarios = [];

document.addEventListener('DOMContentLoaded', () => {
    initRangeSliders();
    initCropDefaultListener();
    initFormSubmit();
    initCharts();
    
    // Auto-run initial prediction on page load & load DB scenarios
    triggerPrediction();
    loadDatabaseScenarios();
});

// Sync range sliders with value display
function initRangeSliders() {
    const sliders = [
        { id: 'temp', displayId: 'temp_val', unit: ' °C' },
        { id: 'rainfall', displayId: 'rainfall_val', unit: ' mm' },
        { id: 'pesticides', displayId: 'pesticides_val', unit: ' Tonnes' },
        { id: 'farm_area', displayId: 'farm_area_val', unit: ' Ha' }
    ];

    sliders.forEach(s => {
        const input = document.getElementById(s.id);
        const display = document.getElementById(s.displayId);
        if (input && display) {
            input.addEventListener('input', (e) => {
                display.innerText = e.target.value + s.unit;
            });
        }
    });
}

// Fetch default market price when crop changes
function initCropDefaultListener() {
    const cropSelect = document.getElementById('crop');
    if (cropSelect) {
        cropSelect.addEventListener('change', async (e) => {
            const cropName = e.target.value;
            try {
                const res = await fetch(`/api/crop_defaults/${encodeURIComponent(cropName)}`);
                const json = await res.json();
                if (json.status === 'success') {
                    const priceInput = document.getElementById('market_price');
                    if (priceInput && !priceInput.dataset.userModified) {
                        priceInput.placeholder = `Default: $${json.default_market_price}`;
                        priceInput.value = json.default_market_price;
                    }
                }
            } catch (err) {
                console.error("Error fetching crop defaults:", err);
            }
        });
    }
}

// Handle Form Submission
function initFormSubmit() {
    const form = document.getElementById('predictionForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            triggerPrediction();
        });
    }
}

async function triggerPrediction() {
    const form = document.getElementById('predictionForm');
    if (!form) return;

    const formData = new FormData(form);
    const payload = {};
    formData.forEach((val, key) => payload[key] = val);

    try {
        const btn = document.getElementById('btnSubmit');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculating AI Predictions...';
            btn.disabled = true;
        }

        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const resJson = await response.json();
        if (resJson.status === 'success') {
            currentPredictionData = resJson.data;
            updateDashboardUI(currentPredictionData);
        } else {
            alert('Prediction error: ' + resJson.message);
        }
    } catch (err) {
        console.error("Prediction failed:", err);
    } finally {
        const btn = document.getElementById('btnSubmit');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-brain"></i> Predict Yield & Calculate Profit';
            btn.disabled = false;
        }
    }
}

// Update KPI Stats and Charts
function updateDashboardUI(data) {
    // 1. Yield Cards
    const yieldEl = document.getElementById('kpiYield');
    if (yieldEl) yieldEl.innerText = data.total_yield_tonnes.toLocaleString() + ' Tonnes';
    const yieldHaEl = document.getElementById('kpiYieldPerHa');
    if (yieldHaEl) yieldHaEl.innerText = `${data.yield_per_ha_tonnes} Tonnes / Ha`;
    
    // 2. Spending Card
    const spendEl = document.getElementById('kpiSpending');
    if (spendEl) spendEl.innerText = '$' + data.total_spending.toLocaleString();
    const spendHaEl = document.getElementById('kpiSpendingPerHa');
    if (spendHaEl) spendHaEl.innerText = `$${data.spending_per_ha} / Ha`;

    // 3. Revenue Card
    const revEl = document.getElementById('kpiRevenue');
    if (revEl) revEl.innerText = '$' + data.gross_revenue.toLocaleString();
    const mktPriceEl = document.getElementById('kpiMarketPrice');
    if (mktPriceEl) mktPriceEl.innerText = `@ $${data.market_price_per_tonne} / Tonne`;

    // 4. Net Profit Card
    const profitEl = document.getElementById('kpiProfit');
    if (profitEl) profitEl.innerText = '$' + data.net_profit.toLocaleString();
    const profitBadge = document.getElementById('kpiMargin');
    if (profitBadge) {
        if (data.net_profit >= 0) {
            if (profitEl) profitEl.className = 'kpi-value text-green';
            profitBadge.className = 'kpi-subtext text-green';
            profitBadge.innerText = `+${data.profit_margin_percent}% Margin`;
        } else {
            if (profitEl) profitEl.className = 'kpi-value text-red';
            profitBadge.className = 'kpi-subtext text-red';
            profitBadge.innerText = `${data.profit_margin_percent}% Margin`;
        }
    }

    // 5. ROI & Breakeven
    const roiEl = document.getElementById('kpiRoi');
    if (roiEl) roiEl.innerText = `${data.roi_percent}%`;
    const breakEl = document.getElementById('kpiBreakeven');
    if (breakEl) breakEl.innerText = `Break-even: $${data.breakeven_price} / Tonne`;

    // 6. Agronomic Score
    const scoreEl = document.getElementById('kpiAgronomicScore');
    if (scoreEl) scoreEl.innerText = `${data.agronomic_score}%`;

    // Render Charts
    renderSpendingChart(data.spending_breakdown_total);
    renderProfitSensitivityChart(data);
    renderSuitabilityRadarChart(data.factors);
    renderYieldBenchmarkChart(data);
}

// Initialize Chart.js Instances
function initCharts() {
    // 1. Spending Donut
    const ctx1 = document.getElementById('costBreakdownCanvas');
    if (ctx1) {
        spendingChart = new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: ['Seeds', 'Pesticides', 'Water & Irrigation', 'Fertilizer & Soil', 'Labor & Machinery'],
                datasets: [{
                    data: [1, 1, 1, 1, 1],
                    backgroundColor: ['#10B981', '#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899'],
                    borderWidth: 2,
                    borderColor: '#0B0F19'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: '#9CA3AF', font: { family: 'Inter', size: 11 } } },
                    tooltip: { callbacks: { label: (ctx) => ` $${ctx.raw.toLocaleString()}` } }
                },
                cutout: '70%'
            }
        });
    }

    // 2. Profit Sensitivity Line Chart
    const ctx2 = document.getElementById('profitSensitivityCanvas');
    if (ctx2) {
        profitSensitivityChart = new Chart(ctx2, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Projected Net Profit ($)',
                    data: [],
                    borderColor: '#10B981',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    fill: true,
                    tension: 0.35,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // 3. Agronomic Radar Chart
    const ctx3 = document.getElementById('agronomicRadarCanvas');
    if (ctx3) {
        radarSuitabilityChart = new Chart(ctx3, {
            type: 'radar',
            data: {
                labels: ['Soil Compatibility', 'Water Availability', 'Water Quality', 'Season Match', 'Climate Optimal'],
                datasets: [{
                    label: 'Agronomic Factor Score',
                    data: [1, 1, 1, 1, 1],
                    backgroundColor: 'rgba(245, 158, 11, 0.25)',
                    borderColor: '#F59E0B',
                    pointBackgroundColor: '#F59E0B'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255,255,255,0.1)' },
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        pointLabels: { color: '#9CA3AF', font: { size: 10 } },
                        ticks: { display: false, min: 0, max: 1.5 }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // 4. Yield Benchmark Bar Chart
    const ctx4 = document.getElementById('yieldBenchmarkCanvas');
    if (ctx4) {
        yieldBenchmarkChart = new Chart(ctx4, {
            type: 'bar',
            data: {
                labels: ['ML Raw Base Yield', 'Agronomically Adjusted Yield'],
                datasets: [{
                    label: 'Yield (Tonnes / Ha)',
                    data: [0, 0],
                    backgroundColor: ['#3B82F6', '#10B981'],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#9CA3AF' }, grid: { display: false } },
                    y: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
}

function renderSpendingChart(spendingMap) {
    if (!spendingChart) return;
    spendingChart.data.labels = Object.keys(spendingMap);
    spendingChart.data.datasets[0].data = Object.values(spendingMap);
    spendingChart.update();
}

function renderProfitSensitivityChart(data) {
    if (!profitSensitivityChart) return;
    const basePrice = data.market_price_per_tonne;
    const yieldTonnes = data.total_yield_tonnes;
    const spending = data.total_spending;

    const prices = [
        Math.round(basePrice * 0.6),
        Math.round(basePrice * 0.8),
        Math.round(basePrice * 1.0),
        Math.round(basePrice * 1.2),
        Math.round(basePrice * 1.4)
    ];

    const profits = prices.map(p => Math.round(yieldTonnes * p - spending));

    profitSensitivityChart.data.labels = prices.map(p => `$${p}/Tonne`);
    profitSensitivityChart.data.datasets[0].data = profits;
    profitSensitivityChart.update();
}

function renderSuitabilityRadarChart(factors) {
    if (!radarSuitabilityChart) return;
    radarSuitabilityChart.data.datasets[0].data = [
        factors.soil_factor,
        factors.water_avail_factor,
        factors.water_qual_factor,
        factors.season_factor,
        factors.climate_factor
    ];
    radarSuitabilityChart.update();
}

function renderYieldBenchmarkChart(data) {
    if (!yieldBenchmarkChart) return;
    const rawBaseHa = data.raw_ml_base_yield_hg_ha / 10000.0;
    const netHa = data.yield_per_ha_tonnes;

    yieldBenchmarkChart.data.datasets[0].data = [
        roundNum(rawBaseHa, 2),
        roundNum(netHa, 2)
    ];
    yieldBenchmarkChart.update();
}

function roundNum(num, dec) {
    return Number(Math.round(num + 'e' + dec) + 'e-' + dec);
}

// Preset Loader
function loadPreset(type) {
    const presets = {
        wheat_optimal: {
            area: 'India', crop: 'Wheat', year: 2024, farm_area: 15, rainfall: 1200, temp: 24, pesticides: 180,
            soil_type: 'Loamy', water_availability: 'High (Canal / Drip Irrigation)',
            water_quality: 'Optimal Freshwater (pH 6.5 - 7.5)', season: 'Rabi (Winter)', market_price: 340
        },
        rice_paddy: {
            area: 'India', crop: 'Rice, paddy', year: 2024, farm_area: 12, rainfall: 1800, temp: 28, pesticides: 220,
            soil_type: 'Clay', water_availability: 'High (Canal / Drip Irrigation)',
            water_quality: 'Optimal Freshwater (pH 6.5 - 7.5)', season: 'Kharif (Monsoon)', market_price: 390
        },
        potato_sandy: {
            area: 'Germany', crop: 'Potatoes', year: 2024, farm_area: 10, rainfall: 950, temp: 20, pesticides: 140,
            soil_type: 'Sandy', water_availability: 'Moderate (Seasonal Irrigation)',
            water_quality: 'Optimal Freshwater (pH 6.5 - 7.5)', season: 'Rabi (Winter)', market_price: 460
        },
        sorghum_drought: {
            area: 'Australia', crop: 'Sorghum', year: 2024, farm_area: 25, rainfall: 450, temp: 31, pesticides: 80,
            soil_type: 'Black', water_availability: 'Low (Rainfed)',
            water_quality: 'Slight Salinity / Mineralized', season: 'Zaid (Summer)', market_price: 250
        }
    };

    const p = presets[type];
    if (!p) return;

    for (let key in p) {
        const el = document.getElementById(key);
        if (el) {
            el.value = p[key];
            el.dispatchEvent(new Event('change'));
            el.dispatchEvent(new Event('input'));
        }
    }

    triggerPrediction();
}

// Scenario Storage & Database Persistence
async function saveCurrentScenario() {
    if (!currentPredictionData) return;
    const name = prompt("Enter a name for this farm scenario to save in Database:", `${currentPredictionData.crop} - ${currentPredictionData.area} (${currentPredictionData.year})`);
    if (!name) return;

    const payload = {
        scenario_name: name,
        area: currentPredictionData.area,
        crop: currentPredictionData.crop,
        farm_area: currentPredictionData.farm_area_ha,
        year: currentPredictionData.year,
        rainfall: document.getElementById('rainfall') ? document.getElementById('rainfall').value : 1000,
        pesticides: document.getElementById('pesticides') ? document.getElementById('pesticides').value : 150,
        temp: document.getElementById('temp') ? document.getElementById('temp').value : 25,
        soil_type: document.getElementById('soil_type') ? document.getElementById('soil_type').value : 'Loamy',
        water_availability: document.getElementById('water_availability') ? document.getElementById('water_availability').value : 'Moderate (Seasonal Irrigation)',
        water_quality: document.getElementById('water_quality') ? document.getElementById('water_quality').value : 'Optimal Freshwater (pH 6.5 - 7.5)',
        season: document.getElementById('season') ? document.getElementById('season').value : 'Kharif (Monsoon)',
        market_price: currentPredictionData.market_price_per_tonne,
        total_yield_tonnes: currentPredictionData.total_yield_tonnes,
        yield_per_ha_tonnes: currentPredictionData.yield_per_ha_tonnes,
        total_spending: currentPredictionData.total_spending,
        net_profit: currentPredictionData.net_profit,
        roi_percent: currentPredictionData.roi_percent,
        agronomic_score: currentPredictionData.agronomic_score
    };

    try {
        const response = await fetch('/api/scenarios/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const resJson = await response.json();
        if (resJson.status === 'success') {
            alert('Scenario saved successfully to Database!');
            loadDatabaseScenarios();
        } else {
            alert('Failed to save scenario: ' + resJson.message);
        }
    } catch (err) {
        console.error("Save scenario error:", err);
        alert("Error saving scenario to Database.");
    }
}

async function loadDatabaseScenarios() {
    const tbody = document.getElementById('scenariosTableBody');
    if (!tbody) return;

    try {
        const response = await fetch('/api/scenarios');
        const resJson = await response.json();

        if (resJson.status === 'success') {
            savedScenarios = resJson.scenarios;
            renderScenariosTable();
        }
    } catch (err) {
        console.error("Error loading scenarios:", err);
    }
}

function renderScenariosTable() {
    const tbody = document.getElementById('scenariosTableBody');
    if (!tbody) return;

    if (!savedScenarios || savedScenarios.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-table"><i class="fas fa-folder-open"></i> No saved scenarios in database yet. Click "Save Scenario to Database" above to save farm runs.</td></tr>';
        return;
    }

    tbody.innerHTML = savedScenarios.map(s => `
        <tr>
            <td><strong>${escapeHtml(s.scenario_name)}</strong></td>
            <td>${escapeHtml(s.area)}</td>
            <td>${escapeHtml(s.crop)}</td>
            <td><strong>${s.predicted_yield.toLocaleString()} T</strong></td>
            <td>$${s.total_spending.toLocaleString()}</td>
            <td class="${s.net_profit >= 0 ? 'text-green' : 'text-red'}"><strong>$${s.net_profit.toLocaleString()}</strong></td>
            <td><span class="kpi-badge ${s.roi_percent >= 0 ? 'badge-success' : 'badge-danger'}">${s.roi_percent}%</span></td>
            <td>
                <button class="table-action-btn" onclick="applyScenarioToForm(${s.id})"><i class="fas fa-arrow-right"></i> Load</button>
                <button class="table-action-btn btn-delete" onclick="deleteScenarioFromDB(${s.id})"><i class="fas fa-trash-alt"></i></button>
            </td>
        </tr>
    `).join('');
}

function applyScenarioToForm(scenarioId) {
    const s = savedScenarios.find(item => item.id === scenarioId);
    if (!s) return;

    setValueIfExist('area', s.area);
    setValueIfExist('crop', s.crop);
    setValueIfExist('farm_area', s.farm_area);
    setValueIfExist('year', s.year);
    setValueIfExist('rainfall', s.rainfall);
    setValueIfExist('pesticides', s.pesticides);
    setValueIfExist('temp', s.temp);
    setValueIfExist('soil_type', s.soil_type);
    setValueIfExist('water_availability', s.water_availability);
    setValueIfExist('water_quality', s.water_quality);
    setValueIfExist('season', s.season);
    setValueIfExist('market_price', s.market_price);

    triggerPrediction();
}

function setValueIfExist(id, val) {
    const el = document.getElementById(id);
    if (el) {
        el.value = val;
        el.dispatchEvent(new Event('change'));
        el.dispatchEvent(new Event('input'));
    }
}

async function deleteScenarioFromDB(scenarioId) {
    if (!confirm("Are you sure you want to delete this scenario from the database?")) return;

    try {
        const response = await fetch(`/api/scenarios/${scenarioId}`, { method: 'DELETE' });
        const resJson = await response.json();
        if (resJson.status === 'success') {
            loadDatabaseScenarios();
        } else {
            alert('Failed to delete scenario: ' + resJson.message);
        }
    } catch (err) {
        console.error("Delete error:", err);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/[&<>"']/g, function(m) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
    });
}

// Authentication Modal & Handlers
function openAuthModal(defaultTab = 'login') {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'flex';
        switchAuthTab(defaultTab);
    }
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) {
        modal.style.display = 'none';
        hideAuthAlert();
    }
}

function switchAuthTab(tab) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const tabLoginBtn = document.getElementById('tabLoginBtn');
    const tabRegisterBtn = document.getElementById('tabRegisterBtn');

    hideAuthAlert();

    if (tab === 'login') {
        if (loginForm) loginForm.style.display = 'block';
        if (registerForm) registerForm.style.display = 'none';
        if (tabLoginBtn) tabLoginBtn.classList.add('active');
        if (tabRegisterBtn) tabRegisterBtn.classList.remove('active');
    } else {
        if (loginForm) loginForm.style.display = 'none';
        if (registerForm) registerForm.style.display = 'block';
        if (tabLoginBtn) tabLoginBtn.classList.remove('active');
        if (tabRegisterBtn) tabRegisterBtn.classList.add('active');
    }
}

function showAuthAlert(msg, type = 'error') {
    const alertBox = document.getElementById('authAlert');
    if (alertBox) {
        alertBox.innerText = msg;
        alertBox.className = `auth-alert ${type}`;
        alertBox.style.display = 'block';
    }
}

function hideAuthAlert() {
    const alertBox = document.getElementById('authAlert');
    if (alertBox) {
        alertBox.style.display = 'none';
    }
}

async function submitLogin(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const resJson = await response.json();

        if (resJson.status === 'success') {
            showAuthAlert("Login successful! Reloading...", "success");
            setTimeout(() => {
                window.location.reload();
            }, 800);
        } else {
            showAuthAlert(resJson.message, "error");
        }
    } catch (err) {
        showAuthAlert("Server error during login", "error");
    }
}

async function submitRegister(e) {
    e.preventDefault();
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const role = document.getElementById('regRole').value;

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, role })
        });
        const resJson = await response.json();

        if (resJson.status === 'success') {
            showAuthAlert("Account created successfully! Reloading...", "success");
            setTimeout(() => {
                window.location.reload();
            }, 800);
        } else {
            showAuthAlert(resJson.message, "error");
        }
    } catch (err) {
        showAuthAlert("Server error during registration", "error");
    }
}

async function handleLogout() {
    try {
        await fetch('/api/logout');
        window.location.reload();
    } catch (err) {
        console.error("Logout error:", err);
    }
}

// CSV Report Export
async function downloadReportCSV() {
    if (!currentPredictionData) {
        alert("Please run a prediction first before exporting report.");
        return;
    }

    try {
        const response = await fetch('/api/export_csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentPredictionData)
        });

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Crop_Yield_Report_${currentPredictionData.crop}_${currentPredictionData.area}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch (err) {
        console.error("Export failed:", err);
    }
}
