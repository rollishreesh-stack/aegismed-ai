from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import os
import math
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_premium_matrix_2026")

# --- MUTABLE SYSTEM DATABASE ---
CLINICAL_DATABASE = {
    "sys_admin": {
        "password": "secure2026", 
        "role": "Chief System Architect", 
        "clearance": "Level 5"
    }
}

# --- DEEP PATHOLOGY MATRIX ---
PATHOLOGY_DATA = {
    'normal': {
        'name': 'Healthy Lungs (Post-Op Baseline)',
        'vco2': 200, 'shunt': 0.05, 'vd_vt': 0.30,
        'short_desc': 'Healthy lung mechanics. Normal metabolic demand and gas exchange.',
        'long_desc': 'Normal pulmonary physiology is characterized by highly compliant alveoli and low airway resistance. Surfactant production is optimal, maintaining alveolar stability during expiration to prevent atelectasis. In a post-operative setting (e.g., recovering from general anesthesia), the primary goal is to maintain physiological functional residual capacity (FRC) and clear metabolic CO2 while the patient regains spontaneous respiratory drive.'
    },
    'ards_mild': {
        'name': 'Mild ARDS (Exudative Phase)',
        'vco2': 250, 'shunt': 0.15, 'vd_vt': 0.45,
        'short_desc': 'Inflammatory fluid in alveoli causing mild shunting.',
        'long_desc': 'Acute Respiratory Distress Syndrome (Mild) presents with bilateral diffuse infiltrates. The exudative phase involves injury to the alveolar capillary endothelial cells, leading to protein-rich fluid leaking into the interstitial and alveolar spaces. This creates a mild intrapulmonary shunt (perfusion without ventilation). Treatment requires low tidal volumes (6-8 mL/kg) and moderate PEEP to keep fluid-filled alveoli open.'
    },
    'ards_severe': {
        'name': 'Severe ARDS (Fibroproliferative)',
        'vco2': 300, 'shunt': 0.35, 'vd_vt': 0.60,
        'short_desc': 'Severe consolidation, massive intrapulmonary shunting, high dead space.',
        'long_desc': 'In Severe ARDS, the lung becomes fundamentally restricted. Extracellular matrix accumulation and severe consolidation reduce the "functional" size of the lungs (the Baby Lung concept). Intrapulmonary shunting often exceeds 30%, making hypoxemia refractory to oxygen therapy alone. Extremely high PEEP, prone positioning, and ultra-low tidal volumes (4-6 mL/kg) are strictly required to prevent sheer-stress volutrauma.'
    },
    'asthma': {
        'name': 'Status Asthmaticus',
        'vco2': 280, 'shunt': 0.10, 'vd_vt': 0.35,
        'short_desc': 'Severe bronchoconstriction. High risk of dynamic hyperinflation.',
        'long_desc': 'Characterized by extreme hyper-reactivity of the bronchial tree, causing smooth muscle spasms, mucosal edema, and mucus plugging. Inspiration is relatively preserved, but expiration is severely prolonged due to airway collapse. If the expiratory time is not adequately extended, gas traps in the alveoli, leading to intrinsic PEEP (Auto-PEEP), which can compress the heart and cause severe hemodynamic collapse.'
    },
    'copd': {
        'name': 'Exacerbation of COPD / Emphysema',
        'vco2': 220, 'shunt': 0.15, 'vd_vt': 0.50,
        'short_desc': 'Destruction of alveolar septa causing trapped gas and high dead space.',
        'long_desc': 'Emphysema destroys the elastin framework of the alveoli, leading to massive, floppy lungs that have lost their recoil capability. Because they cannot passively recoil, patients require highly prolonged expiratory phases. Dead space is elevated due to destroyed capillary beds. Permissive hypercapnia (allowing PaCO2 to rise slightly) is often required to avoid dynamic hyperinflation.'
    },
    'chf': {
        'name': 'Cardiogenic Pulmonary Edema (CHF)',
        'vco2': 220, 'shunt': 0.20, 'vd_vt': 0.35,
        'short_desc': 'Hydrostatic pressure driving fluid into alveoli.',
        'long_desc': 'Left ventricular failure causes blood to back up into the pulmonary circulation. The resulting high hydrostatic pressure forces transudative fluid across the alveolar-capillary membrane, literally drowning the alveoli from the inside. Applied PEEP is highly effective here as it forces the fluid back into the interstitium and decreases venous return to the failing heart.'
    },
    'pe': {
        'name': 'Massive Pulmonary Embolism',
        'vco2': 200, 'shunt': 0.10, 'vd_vt': 0.65,
        'short_desc': 'Vascular occlusion leading to extreme alveolar dead space.',
        'long_desc': 'A mechanical blockage of the pulmonary artery (usually a thrombus). The lungs are receiving adequate oxygen (ventilation), but there is no blood flow to pick it up (perfusion). This represents the ultimate definition of Alveolar Dead Space. The body must increase overall minute ventilation drastically just to clear normal amounts of CO2.'
    },
    'pneumothorax': {
        'name': 'Tension Pneumothorax',
        'vco2': 220, 'shunt': 0.25, 'vd_vt': 0.50,
        'short_desc': 'Pleural rupture causing lung collapse and mediastinal shift.',
        'long_desc': 'Air enters the pleural space but cannot escape, causing complete collapse of the ipsilateral lung and shifting the heart and great vessels to the opposite side. Positive pressure ventilation exacerbates this condition rapidly. It requires immediate needle decompression or chest tube placement. Compliance drops drastically as only one lung is functional.'
    },
    'cf': {
        'name': 'Cystic Fibrosis (Late Stage)',
        'vco2': 260, 'shunt': 0.25, 'vd_vt': 0.55,
        'short_desc': 'Thick secretions causing massive resistance and chronic infection.',
        'long_desc': 'A genetic defect in chloride transport leads to thick, dehydrated mucus that plugs airways, creating extreme airway resistance and serving as a breeding ground for chronic bacterial infections. The lungs exhibit mixed obstructive and restrictive patterns due to bronchiectasis and scarring.'
    },
    'nmd': {
        'name': 'Neuromuscular Disease (e.g., ALS, Guillain-Barré)',
        'vco2': 180, 'shunt': 0.05, 'vd_vt': 0.30,
        'short_desc': 'Failure of the respiratory muscle pump; lungs structurally intact.',
        'long_desc': 'The lung parenchyma is completely healthy, but the neurological drive or muscular strength to expand the chest wall is failing. These patients require full ventilatory support to offset the work of breathing, but they do not typically require high pressures or PEEP, as their lung compliance is largely normal.'
    }
}

# --- UI TEMPLATES ---
BASE_CSS = """
<style>
    /* Premium Ambient Breathing Animation */
    @keyframes breathe {
        0% { transform: scale(1); opacity: 0.1; }
        50% { transform: scale(1.05); opacity: 0.25; }
        100% { transform: scale(1); opacity: 0.1; }
    }
    .lung-background {
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: radial-gradient(circle at center, #1e3a8a 0%, #0f172a 60%, #000000 100%);
        z-index: -1;
    }
    .lung-glow {
        position: fixed;
        top: 50%; left: 50%;
        width: 80vw; height: 80vw;
        max-width: 800px; max-height: 800px;
        background: radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, rgba(0,0,0,0) 70%);
        transform: translate(-50%, -50%);
        animation: breathe 5s infinite ease-in-out;
        z-index: -1;
        border-radius: 50%;
        pointer-events: none;
    }
    
    /* Scrollbar formatting */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
"""

LOGIN_HTML = BASE_CSS + """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>AeroLung Premium | Auth</title>
</head>
<body class="bg-transparent flex items-center justify-center h-screen text-slate-200 antialiased font-sans">
    <div class="lung-background"></div>
    <div class="lung-glow"></div>
    
    <div class="bg-[#1e293b]/90 backdrop-blur-md border border-slate-700 p-8 rounded-2xl shadow-2xl w-full max-w-sm relative z-10">
        <div class="text-center mb-6">
            <h1 class="text-3xl font-black text-white tracking-tight">AERO<span class="text-sky-400">LUNG</span></h1>
            <p class="text-sky-200/50 text-[10px] mt-1 font-bold uppercase tracking-widest">Premium Clinical Matrix</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
                <div class="p-3 rounded-lg mb-4 text-xs font-mono text-center {% if category == 'error' %}bg-red-500/10 text-red-400 border border-red-500/20{% else %}bg-green-500/10 text-green-400 border border-green-500/20{% endif %}">
                    {{ message }}
                </div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        
        <form method="POST" action="/login" class="space-y-4">
            <div>
                <label class="block text-slate-400 text-[10px] font-mono uppercase tracking-wider mb-1">System ID</label>
                <input type="text" name="username" required class="w-full p-3 rounded-lg bg-[#0f172a]/80 border border-slate-600 text-white text-sm focus:outline-none focus:border-sky-500 transition font-mono">
            </div>
            <div>
                <label class="block text-slate-400 text-[10px] font-mono uppercase tracking-wider mb-1">Access Passkey</label>
                <input type="password" name="password" required class="w-full p-3 rounded-lg bg-[#0f172a]/80 border border-slate-600 text-white text-sm focus:outline-none focus:border-sky-500 transition font-mono">
            </div>
            <button type="submit" class="w-full bg-gradient-to-r from-sky-600 to-blue-700 hover:from-sky-500 hover:to-blue-600 text-white font-bold py-3 rounded-lg text-xs uppercase tracking-widest shadow-[0_0_15px_rgba(14,165,233,0.3)] transition mt-4">
                Initialize Node
            </button>
        </form>
    </div>
</body>
</html>
"""

MASTER_DASHBOARD_HTML = BASE_CSS + """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <title>AeroLung Premium Workspace</title>
</head>
<body class="bg-transparent text-slate-200 min-h-screen antialiased flex flex-col">
    <div class="lung-background"></div>
    <div class="lung-glow"></div>

    <nav class="bg-[#0f172a]/90 backdrop-blur-xl border-b border-slate-700 px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <div class="flex items-center space-x-3">
            <span class="w-2.5 h-2.5 bg-sky-400 rounded-full animate-pulse shadow-[0_0_10px_rgba(56,189,248,0.8)]"></span>
            <span class="font-black text-xl tracking-wider text-white">AERO<span class="text-sky-400">LUNG</span></span>
        </div>
        
        <div class="flex items-center space-x-1 text-xs font-mono">
            <div class="text-right border-r border-slate-700 pr-4 mr-2">
                <span class="text-sky-400 font-bold block">{{ user_role }}</span>
                <span class="text-[10px] text-slate-400 uppercase">ID: {{ session.get('user') }}</span>
            </div>
            <a href="?tab=simulator" class="px-4 py-2 rounded-md transition {% if active_tab == 'simulator' %}bg-sky-500/20 text-sky-300 font-bold{% else %}text-slate-400 hover:bg-slate-800 hover:text-white{% endif %}">Simulator</a>
            <a href="?tab=analytics" class="px-4 py-2 rounded-md transition {% if active_tab == 'analytics' %}bg-sky-500/20 text-sky-300 font-bold{% else %}text-slate-400 hover:bg-slate-800 hover:text-white{% endif %}">Analytics</a>
            <a href="?tab=library" class="px-4 py-2 rounded-md transition {% if active_tab == 'library' %}bg-sky-500/20 text-sky-300 font-bold{% else %}text-slate-400 hover:bg-slate-800 hover:text-white{% endif %}">Pathology Library</a>
            <a href="?tab=settings" class="px-4 py-2 rounded-md transition {% if active_tab == 'settings' %}bg-sky-500/20 text-sky-300 font-bold{% else %}text-slate-400 hover:bg-slate-800 hover:text-white{% endif %}">Settings</a>
            <a href="/logout" class="bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 px-4 py-2 rounded-md transition ml-4 uppercase tracking-widest">Logout</a>
        </div>
    </nav>

    <main class="flex-1 p-6 relative z-10 max-w-[1600px] mx-auto w-full">
        
        {% if active_tab == 'settings' %}
        <div class="max-w-md mx-auto bg-[#1e293b]/90 backdrop-blur-md border border-slate-700 rounded-xl p-6 mt-10 shadow-2xl">
            <h2 class="text-xl font-black text-white mb-2">Access Configuration</h2>
            <p class="text-xs text-slate-400 mb-6">Modify node credentials securely.</p>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                    <div class="p-3 rounded-lg mb-4 text-xs font-mono text-center {% if category == 'error' %}bg-red-500/10 text-red-400 border border-red-500/20{% else %}bg-green-500/10 text-green-400 border border-green-500/20{% endif %}">
                        {{ message }}
                    </div>
                {% endfor %}
              {% endif %}
            {% endwith %}

            <form method="POST" action="/update_credentials" class="space-y-4">
                <div>
                    <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">Current Password</label>
                    <input type="password" name="current_password" required class="w-full p-2.5 rounded-lg bg-[#0f172a] border border-slate-600 text-white text-sm focus:border-sky-500 transition font-mono">
                </div>
                <hr class="border-slate-700 my-4">
                <div>
                    <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">New System ID</label>
                    <input type="text" name="new_username" required value="{{ session.get('user') }}" class="w-full p-2.5 rounded-lg bg-[#0f172a] border border-slate-600 text-white text-sm focus:border-sky-500 transition font-mono">
                </div>
                <div>
                    <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">New Password</label>
                    <input type="password" name="new_password" required class="w-full p-2.5 rounded-lg bg-[#0f172a] border border-slate-600 text-white text-sm focus:border-sky-500 transition font-mono">
                </div>
                <button type="submit" class="w-full bg-sky-600 hover:bg-sky-500 text-white font-bold py-3 rounded-lg text-xs uppercase tracking-widest transition mt-4">
                    Commit Updates
                </button>
            </form>
        </div>
        {% endif %}

        {% if active_tab == 'library' %}
        <div class="bg-[#1e293b]/80 backdrop-blur-md border border-slate-700 rounded-xl p-8 shadow-2xl">
            <h2 class="text-2xl font-black text-white mb-2">Comprehensive Pathology Database</h2>
            <p class="text-sm text-slate-400 mb-8">In-depth physiological profiles and mechanical intervention strategies.</p>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {% for key, path in path_data.items() %}
                <div class="bg-[#0f172a] border border-slate-700 rounded-xl p-5 hover:border-sky-500/50 transition">
                    <h3 class="text-sky-400 font-bold text-lg mb-2 border-b border-slate-700 pb-2">{{ path.name }}</h3>
                    <div class="space-y-3 mt-3">
                        <div class="flex justify-between text-[10px] font-mono bg-slate-800/50 p-2 rounded">
                            <span class="text-slate-400">VCO2: <span class="text-white">{{ path.vco2 }} mL/min</span></span>
                            <span class="text-slate-400">Shunt: <span class="text-white">{{ (path.shunt * 100)|int }}%</span></span>
                            <span class="text-slate-400">Vd/Vt: <span class="text-white">{{ (path.vd_vt * 100)|int }}%</span></span>
                        </div>
                        <p class="text-xs text-slate-300 leading-relaxed text-justify">{{ path.long_desc }}</p>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        {% if active_tab == 'analytics' %}
        <div class="space-y-6">
            <div class="bg-[#1e293b]/80 backdrop-blur-md border border-slate-700 rounded-xl p-6 shadow-2xl">
                <h2 class="text-xl font-black text-white mb-1">Comparative Population Statistics</h2>
                <p class="text-xs text-slate-400 mb-6">Analyzing mechanical trends across key respiratory diseases.</p>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div class="bg-[#0f172a] p-4 rounded-xl border border-slate-700">
                        <h3 class="text-xs font-mono uppercase text-slate-400 text-center mb-4">Static Compliance Margins (mL/cmH2O)</h3>
                        <canvas id="complianceChart" height="200"></canvas>
                    </div>
                    <div class="bg-[#0f172a] p-4 rounded-xl border border-slate-700">
                        <h3 class="text-xs font-mono uppercase text-slate-400 text-center mb-4">Airway Resistance Profiles (cmH2O/L/s)</h3>
                        <canvas id="resistanceChart" height="200"></canvas>
                    </div>
                </div>
            </div>
        </div>
        <script>
            // Static Comparative Analytics
            const compCtx = document.getElementById('complianceChart').getContext('2d');
            new Chart(compCtx, {
                type: 'bar',
                data: {
                    labels: ['Normal', 'Severe ARDS', 'COPD', 'Fibrosis', 'Asthma'],
                    datasets: [{
                        label: 'Avg Compliance',
                        data: [60, 20, 80, 15, 55],
                        backgroundColor: ['#38bdf8', '#f87171', '#fbbf24', '#c084fc', '#34d399'],
                        borderWidth: 1, borderColor: '#1e293b'
                    }]
                },
                options: { plugins: { legend: { display: false } }, scales: { y: { grid: { color: '#334155' } }, x: { grid: { display: false } } } }
            });

            const resCtx = document.getElementById('resistanceChart').getContext('2d');
            new Chart(resCtx, {
                type: 'bar',
                data: {
                    labels: ['Normal', 'Severe ARDS', 'COPD', 'Fibrosis', 'Asthma'],
                    datasets: [{
                        label: 'Avg Resistance',
                        data: [10, 15, 25, 12, 50],
                        backgroundColor: ['#38bdf8', '#f87171', '#fbbf24', '#c084fc', '#34d399'],
                        borderWidth: 1, borderColor: '#1e293b'
                    }]
                },
                options: { plugins: { legend: { display: false } }, scales: { y: { grid: { color: '#334155' } }, x: { grid: { display: false } } } }
            });
        </script>
        {% endif %}

        {% if active_tab == 'simulator' %}
        <div class="grid grid-cols-1 xl:grid-cols-12 gap-6">
            
            <div class="xl:col-span-3 bg-[#1e293b]/90 backdrop-blur-md border border-slate-700 rounded-xl p-5 shadow-2xl h-fit">
                <h2 class="text-sm font-black text-white mb-4 border-b border-slate-700 pb-2">Control Matrix</h2>
                
                <form method="POST" action="/dashboard?tab=simulator" class="space-y-4">
                    <div>
                        <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">Select Patient Profile</label>
                        <select name="profile_class" id="profile_class" onchange="applyProfilePresets()" class="w-full p-2 rounded-lg bg-[#0f172a] border border-slate-600 text-white text-xs focus:border-sky-500 transition font-mono">
                            {% for key, path in path_data.items() %}
                                <option value="{{ key }}" {% if profile_class == key %}selected{% endif %}>{{ path.name }}</option>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div class="col-span-2 border-b border-slate-700 pb-1 mb-1 mt-2">
                            <span class="text-[9px] text-sky-400 font-bold uppercase tracking-widest">Demographics & Gas</span>
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[9px] font-mono uppercase mb-1">IBW (kg)</label>
                            <input type="number" id="ibw" name="ibw" value="{{ inputs.ibw if inputs else '70' }}" class="w-full p-2 rounded bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[9px] font-mono uppercase mb-1">FiO2 (%)</label>
                            <input type="number" id="fio2" name="fio2" value="{{ inputs.fio2 if inputs else '40' }}" class="w-full p-2 rounded bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>

                        <div class="col-span-2 border-b border-slate-700 pb-1 mt-2 mb-1">
                            <span class="text-[9px] text-sky-400 font-bold uppercase tracking-widest">Lung Mechanics</span>
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[9px] font-mono uppercase mb-1">C (mL/cmH2O)</label>
                            <input type="number" step="0.1" id="compliance" name="compliance" value="{{ inputs.compliance if inputs else '60.0' }}" class="w-full p-2 rounded bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[9px] font-mono uppercase mb-1">R (cmH2O/L/s)</label>
                            <input type="number" id="resistance" name="resistance" value="{{ inputs.resistance if inputs else '10' }}" class="w-full p-2 rounded bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>

                        <div class="col-span-2 border-b border-slate-700 pb-1 mt-2 mb-1">
                            <span class="text-[9px] text-sky-400 font-bold uppercase tracking-widest">Ventilator Settings</span>
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[9px] font-mono uppercase mb-1">PIP (cmH2O)</label>
                            <input type="number" id="pip" name="pip" value="{{ inputs.pip if inputs else '15' }}" class="w-full p-2 rounded bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[9px] font-mono uppercase mb-1">PEEP (cmH2O)</label>
                            <input type="number" id="peep" name="peep" value="{{ inputs.peep if inputs else '5' }}" class="w-full p-2 rounded bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[9px] font-mono uppercase mb-1">Rate (/min)</label>
                            <input type="number" id="rr" name="rr" value="{{ inputs.rr if inputs else '16' }}" class="w-full p-2 rounded bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[9px] font-mono uppercase mb-1">I:E (1:X)</label>
                            <input type="number" step="0.1" id="ie_ratio" name="ie_ratio" value="{{ inputs.ie_ratio if inputs else '2.0' }}" class="w-full p-2 rounded bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                    </div>
                    <button type="submit" class="w-full bg-gradient-to-r from-sky-600 to-blue-700 hover:from-sky-500 hover:to-blue-600 text-white font-bold py-3 rounded-lg text-xs uppercase tracking-widest shadow-[0_0_10px_rgba(14,165,233,0.3)] transition mt-4">
                        Compute Physics
                    </button>
                </form>
            </div>

            <div class="xl:col-span-9 space-y-6">
                {% if not sim_data %}
                <div class="bg-[#1e293b]/50 backdrop-blur-sm border border-slate-700 border-dashed rounded-xl flex flex-col items-center justify-center min-h-[600px] shadow-2xl">
                    <span class="w-16 h-16 border-4 border-sky-500/20 border-t-sky-500 rounded-full animate-spin mb-4"></span>
                    <p class="text-xs text-slate-400 font-mono tracking-widest uppercase">System Standby. Awaiting Input.</p>
                </div>
                {% else %}
                
                <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div class="bg-[#1e293b]/90 border border-slate-700 rounded-xl p-3 shadow-lg">
                        <p class="text-[8px] font-mono uppercase text-slate-400 mb-1">Target ($V_t$/kg)</p>
                        <p class="text-xl font-black {% if sim_data.vt_kg > 8 %}text-red-400{% else %}text-sky-400{% endif %} font-mono">{{ sim_data.vt_kg }}</p>
                        <p class="text-[8px] text-slate-500">{{ sim_data.peak_volume }} mL total</p>
                    </div>
                    <div class="bg-[#1e293b]/90 border border-slate-700 rounded-xl p-3 shadow-lg">
                        <p class="text-[8px] font-mono uppercase text-slate-400 mb-1">Alv Vent ($V_A$)</p>
                        <p class="text-xl font-black text-indigo-400 font-mono">{{ sim_data.alveolar_vent }}</p>
                        <p class="text-[8px] text-slate-500">{{ sim_data.minute_vent }} L/m total</p>
                    </div>
                    <div class="bg-[#1e293b]/90 border border-slate-700 rounded-xl p-3 shadow-lg">
                        <p class="text-[8px] font-mono uppercase text-slate-400 mb-1">Est. $PaCO_2$</p>
                        <p class="text-xl font-black {% if sim_data.paco2 > 45 or sim_data.paco2 < 35 %}text-amber-400{% else %}text-emerald-400{% endif %} font-mono">{{ sim_data.paco2 }}</p>
                        <p class="text-[8px] text-slate-500">mmHg</p>
                    </div>
                    <div class="bg-[#1e293b]/90 border border-slate-700 rounded-xl p-3 shadow-lg">
                        <p class="text-[8px] font-mono uppercase text-slate-400 mb-1">Est. $PaO_2$</p>
                        <p class="text-xl font-black {% if sim_data.pao2 < 60 %}text-red-400{% else %}text-sky-300{% endif %} font-mono">{{ sim_data.pao2 }}</p>
                        <p class="text-[8px] text-slate-500">mmHg</p>
                    </div>
                    <div class="bg-[#1e293b]/90 border border-slate-700 rounded-xl p-3 shadow-lg">
                        <p class="text-[8px] font-mono uppercase text-slate-400 mb-1">Auto-PEEP Risk</p>
                        <p class="text-xl font-black font-mono {% if sim_data.auto_peep_risk == 'HIGH' %}text-red-500{% else %}text-emerald-500{% endif %}">{{ sim_data.auto_peep_risk }}</p>
                        <p class="text-[8px] text-slate-500">Te: {{ sim_data.t_e }}s</p>
                    </div>
                </div>

                <div class="bg-[#1e293b]/90 backdrop-blur-md border border-slate-700 rounded-xl p-5 shadow-2xl">
                    <h3 class="text-xs font-mono uppercase text-slate-400 mb-4 border-b border-slate-700 pb-2">Real-Time Kinematic Waveforms (Idealized PCV)</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="bg-[#0f172a] p-3 rounded-lg border border-slate-700">
                            <canvas id="pressureTimeChart" height="150"></canvas>
                        </div>
                        <div class="bg-[#0f172a] p-3 rounded-lg border border-slate-700">
                            <canvas id="volumeTimeChart" height="150"></canvas>
                        </div>
                    </div>
                </div>

                <div class="bg-[#1e293b]/90 backdrop-blur-md border border-slate-700 rounded-xl p-5 shadow-2xl">
                    <h3 class="text-xs font-mono uppercase text-slate-400 mb-3 border-b border-slate-700 pb-2">Clinical Interpretation: {{ path_data[profile_class].name }}</h3>
                    <p class="text-xs text-slate-300 mb-4 leading-relaxed">{{ path_data[profile_class].short_desc }}</p>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="bg-gradient-to-r from-blue-900/40 to-transparent border-l-4 border-blue-500 p-3 rounded-r-md">
                            <span class="text-[9px] uppercase text-blue-400 font-bold block mb-1">Volumetric Dynamics</span>
                            <p class="text-xs font-mono text-blue-200">{{ sim_data.vol_note }}</p>
                        </div>
                        <div class="bg-gradient-to-r from-emerald-900/40 to-transparent border-l-4 border-emerald-500 p-3 rounded-r-md">
                            <span class="text-[9px] uppercase text-emerald-400 font-bold block mb-1">Gas Exchange Efficiency</span>
                            <p class="text-xs font-mono text-emerald-200">{{ sim_data.gas_note }}</p>
                        </div>
                    </div>
                </div>

                <script>
                    const waveData = {{ sim_data.waveform_data | safe }};
                    
                    // Chart Config Basics
                    Chart.defaults.color = '#94a3b8';
                    Chart.defaults.font.family = 'monospace';
                    
                    const commonOptions = {
                        animation: false,
                        elements: { point: { radius: 0 }, line: { tension: 0.3 } },
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { title: { display: true, text: 'Time (s)', font: {size: 10} }, grid: { color: '#334155' } },
                            y: { grid: { color: '#334155' } }
                        }
                    };

                    // Pressure-Time Chart
                    new Chart(document.getElementById('pressureTimeChart').getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: waveData.t,
                            datasets: [{
                                label: 'Pressure (cmH2O)',
                                data: waveData.p,
                                borderColor: '#38bdf8',
                                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                                fill: true, borderWidth: 2
                            }]
                        },
                        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, title: { display: true, text: 'Paw', font: {size: 10} } } } }
                    });

                    // Volume-Time Chart
                    new Chart(document.getElementById('volumeTimeChart').getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: waveData.t,
                            datasets: [{
                                label: 'Volume (mL)',
                                data: waveData.v,
                                borderColor: '#34d399',
                                backgroundColor: 'rgba(52, 211, 153, 0.1)',
                                fill: true, borderWidth: 2
                            }]
                        },
                        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, title: { display: true, text: 'Vol', font: {size: 10} } } } }
                    });
                </script>
                
                {% endif %}
            </div>
        </div>
        {% endif %}
    </main>

    <script>
        // Preset injections map to clinical pathologies
        function applyProfilePresets() {
            const profile = document.getElementById('profile_class').value;
            const pip = document.getElementById('pip');
            const peep = document.getElementById('peep');
            const compliance = document.getElementById('compliance');
            const resistance = document.getElementById('resistance');
            const rr = document.getElementById('rr');
            const ie = document.getElementById('ie_ratio');
            
            const presets = {
                'normal':       {pip: '15', peep: '5',  c: '60.0', r: '10', rr: '16', ie: '2.0'},
                'ards_mild':    {pip: '24', peep: '10', c: '35.0', r: '12', rr: '20', ie: '1.5'},
                'ards_severe':  {pip: '32', peep: '16', c: '20.0', r: '15', rr: '28', ie: '1.0'},
                'asthma':       {pip: '30', peep: '4',  c: '55.0', r: '45', rr: '12', ie: '4.0'},
                'copd':         {pip: '22', peep: '5',  c: '75.0', r: '25', rr: '14', ie: '3.5'},
                'chf':          {pip: '25', peep: '12', c: '40.0', r: '14', rr: '22', ie: '2.0'},
                'pe':           {pip: '18', peep: '5',  c: '55.0', r: '12', rr: '26', ie: '2.0'},
                'pneumothorax': {pip: '25', peep: '5',  c: '30.0', r: '15', rr: '20', ie: '2.0'},
                'cf':           {pip: '28', peep: '8',  c: '45.0', r: '35', rr: '18', ie: '3.0'},
                'nmd':          {pip: '16', peep: '5',  c: '60.0', r: '10', rr: '16', ie: '2.0'}
            };
            
            if(presets[profile]) {
                pip.value = presets[profile].pip; peep.value = presets[profile].peep;
                compliance.value = presets[profile].c; resistance.value = presets[profile].r;
                rr.value = presets[profile].rr; ie.value = presets[profile].ie;
            }
        }
    </script>
</body>
</html>
"""

# --- BACKEND LOGIC ---

@app.route('/')
def home():
    if 'user' in session: return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in CLINICAL_DATABASE and CLINICAL_DATABASE[username]['password'] == password:
        session['user'] = username
        session['role'] = CLINICAL_DATABASE[username]['role']
        return redirect(url_for('dashboard'))
    flash("Authentication Failed: Credentials Unmatched.", "error")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/update_credentials', methods=['POST'])
def update_credentials():
    if 'user' not in session: return redirect(url_for('home'))
    current_user = session['user']
    if CLINICAL_DATABASE[current_user]['password'] != request.form['current_password']:
        flash("Current password validation failed.", "error")
        return redirect(url_for('dashboard', tab='settings'))
    
    new_user = request.form['new_username']
    if new_user != current_user and new_user in CLINICAL_DATABASE:
        flash("System ID already in use.", "error")
        return redirect(url_for('dashboard', tab='settings'))
        
    user_data = CLINICAL_DATABASE[current_user]
    user_data['password'] = request.form['new_password']
    del CLINICAL_DATABASE[current_user]
    CLINICAL_DATABASE[new_user] = user_data
    session['user'] = new_user
    flash(f"Credentials updated. New ID: {new_user}", "success")
    return redirect(url_for('dashboard', tab='settings'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    
    active_tab = request.args.get('tab', 'simulator')
    sim_data = None
    inputs = None
    profile_class = 'normal'
    
    if request.method == 'POST' and active_tab == 'simulator':
        profile_class = request.form['profile_class']
        pip = float(request.form['pip'])
        peep = float(request.form['peep'])
        compliance = float(request.form['compliance'])
        resistance = float(request.form['resistance'])
        rr = float(request.form['rr'])
        ie_ratio = float(request.form['ie_ratio'])
        ibw = float(request.form['ibw'])
        fio2 = float(request.form['fio2']) / 100.0 
        
        inputs = {'pip': pip, 'peep': peep, 'compliance': compliance, 'resistance': resistance, 'rr': rr, 'ie_ratio': ie_ratio, 'ibw': ibw, 'fio2': int(fio2*100)}
        p_data = PATHOLOGY_DATA[profile_class]
        
        # --- MECHANICAL & PHYSICS CALCULATIONS ---
        driving_pressure = max(0.1, pip - peep)
        peak_volume = round(driving_pressure * compliance, 1) # V_t
        vt_kg = round(peak_volume / ibw, 1)
        
        minute_vent = (peak_volume * rr) / 1000.0
        alveolar_vent = ((peak_volume - (peak_volume * p_data['vd_vt'])) * rr) / 1000.0
        
        t_cycle = 60.0 / rr
        t_i = round(t_cycle * (1 / (1 + ie_ratio)), 2)
        t_e = round(t_cycle - t_i, 2)
        mean_pressure = round(((pip * t_i) + (peep * t_e)) / t_cycle, 1)
        
        time_constant = (resistance / 1000.0) * compliance
        auto_peep_risk = "HIGH" if t_e < (3.0 * time_constant) else "LOW"

        # --- ARTERIAL GAS MATH ---
        paco2 = round((0.863 * p_data['vco2']) / max(0.1, alveolar_vent), 1)
        p_A_O2 = ((760 - 47) * fio2) - (paco2 / 0.8)
        pao2 = round(max(30, p_A_O2 - ((p_data['shunt'] * 100) * 12)), 1)
        
        # --- IDEALIZED WAVEFORM GENERATION (Pressure Control Approximation) ---
        t_points = []
        p_points = []
        v_points = []
        
        steps = 50
        for i in range(steps + 1):
            t = round((i / steps) * t_cycle, 3)
            t_points.append(t)
            
            # Simple exponential models for visual representation
            if t <= t_i:
                # Inspiratory phase
                p_val = peep + (pip - peep) * (1 - math.exp(-t / max(0.05, time_constant/2)))
                v_val = peak_volume * (1 - math.exp(-t / max(0.05, time_constant)))
            else:
                # Expiratory phase
                t_exp = t - t_i
                p_val = peep + (pip - peep) * math.exp(-t_exp / max(0.05, time_constant/3))
                v_val = peak_volume * math.exp(-t_exp / max(0.05, time_constant))
                
            p_points.append(round(p_val, 1))
            v_points.append(round(v_val, 1))
            
        waveform_data = json.dumps({'t': t_points, 'p': p_points, 'v': v_points})

        # --- CLINICAL INTELLIGENCE NOTES ---
        vol_note = "Volumetric targeting is nominal. Lung protection achieved."
        if vt_kg > 8.0: vol_note = f"WARNING: Tidal volume is {vt_kg} mL/kg. High risk of volutrauma. Decrease PIP."
        elif vt_kg < 4.0: vol_note = f"Volume is heavily restricted ({vt_kg} mL/kg). May promote widespread atelectasis."
            
        gas_note = "Gas exchange parameters are within physiological limits."
        if paco2 > 50 and profile_class not in ['copd', 'asthma', 'cf']:
            gas_note = "Respiratory Acidosis evident. Alveolar ventilation insufficient."
        elif pao2 < 60:
            gas_note = "Hypoxemic failure. Intrapulmonary shunting is too severe for current FiO2/PEEP."

        sim_data = {
            'peak_volume': peak_volume, 'vt_kg': vt_kg, 'minute_vent': round(minute_vent, 2),
            'alveolar_vent': round(alveolar_vent, 2), 'auto_peep_risk': auto_peep_risk,
            'paco2': paco2, 'pao2': pao2, 't_i': t_i, 't_e': t_e,
            'vol_note': vol_note, 'gas_note': gas_note, 'waveform_data': waveform_data
        }

    return render_template_string(
        MASTER_DASHBOARD_HTML,
        active_tab=active_tab, sim_data=sim_data, inputs=inputs,
        profile_class=profile_class, user_role=session.get('role'),
        path_data=PATHOLOGY_DATA
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
