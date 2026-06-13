from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import os
import math
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_crimson_elite_2026")

# --- MUTABLE SYSTEM DATABASE ---
CLINICAL_DATABASE = {
    "sys_admin": {
        "password": "secure2026", 
        "role": "Chief System Architect", 
        "clearance": "Level 5"
    }
}

# --- PREMIUM UI CSS & REALISTIC LUNG SVG ---
BASE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800;900&family=JetBrains+Mono:wght@400;700&display=swap');
    
    body { font-family: 'Inter', sans-serif; background-color: #09090b; color: #e4e4e7; overflow-x: hidden; min-height: 100vh;}
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    
    /* Smooth, Realistic Breathing Animation */
    @keyframes bioBreathe {
        0% { transform: translate(-50%, -50%) scale(0.98); opacity: 0.15; filter: drop-shadow(0 0 30px rgba(225,29,72,0.1)); }
        40% { transform: translate(-50%, -50%) scale(1.06); opacity: 0.4; filter: drop-shadow(0 0 80px rgba(225,29,72,0.4)); }
        100% { transform: translate(-50%, -50%) scale(0.98); opacity: 0.15; filter: drop-shadow(0 0 30px rgba(225,29,72,0.1)); }
    }
    
    .living-lung {
        position: fixed; top: 50%; left: 50%; 
        width: 90vw; max-width: 850px; 
        z-index: 0; pointer-events: none; 
        animation: bioBreathe 4.5s ease-in-out infinite;
    }
    
    /* Dark Premium Glassmorphism */
    .glass-panel {
        background: rgba(24, 24, 27, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(63, 63, 70, 0.4);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.8);
        position: relative;
        z-index: 10;
    }
    .glass-header {
        background: rgba(9, 9, 11, 0.95);
        backdrop-filter: blur(24px);
        border-bottom: 1px solid rgba(63, 63, 70, 0.5);
        position: relative;
        z-index: 50;
    }
    
    /* Professional Input Styling */
    .clinical-input {
        background: #000;
        border: 1px solid #3f3f46;
        color: #fff;
        text-align: right;
        padding: 4px 8px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        width: 100%;
        transition: all 0.2s;
    }
    .clinical-input:focus {
        border-color: #e11d48;
        outline: none;
        box-shadow: 0 0 10px rgba(225,29,72,0.2);
    }
    
    /* Highly Visible Copyright Badge */
    .copyright-badge {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #e11d48;
        color: #ffffff;
        padding: 10px 20px;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 0.1em;
        z-index: 9999;
        box-shadow: 0 10px 25px rgba(225, 29, 72, 0.4);
        border: 2px solid #fda4af;
        text-transform: uppercase;
    }
    
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #09090b; }
    ::-webkit-scrollbar-thumb { background: #e11d48; border-radius: 4px; }
</style>
"""

# Hyper-Realistic Multi-Layered Lung SVG
LUNG_SVG = """
<svg class="living-lung" viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="fleshGradientRight" cx="40%" cy="50%" r="60%">
            <stop offset="0%" stop-color="#fda4af" stop-opacity="0.9"/>
            <stop offset="40%" stop-color="#e11d48" stop-opacity="0.8"/>
            <stop offset="80%" stop-color="#881337" stop-opacity="0.9"/>
            <stop offset="100%" stop-color="#4c0519" stop-opacity="1"/>
        </radialGradient>
        <radialGradient id="fleshGradientLeft" cx="60%" cy="50%" r="60%">
            <stop offset="0%" stop-color="#fda4af" stop-opacity="0.9"/>
            <stop offset="40%" stop-color="#e11d48" stop-opacity="0.8"/>
            <stop offset="80%" stop-color="#881337" stop-opacity="0.9"/>
            <stop offset="100%" stop-color="#4c0519" stop-opacity="1"/>
        </radialGradient>
        <linearGradient id="tracheaGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#9f1239"/>
            <stop offset="50%" stop-color="#f43f5e"/>
            <stop offset="100%" stop-color="#9f1239"/>
        </linearGradient>
        <filter id="organGlow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    </defs>
    
    <g filter="url(#organGlow)">
        <path d="M142 30 h16 v50 h-16 z" fill="url(#tracheaGrad)"/>
        <line x1="142" y1="35" x2="158" y2="35" stroke="#4c0519" stroke-width="2"/>
        <line x1="142" y1="45" x2="158" y2="45" stroke="#4c0519" stroke-width="2"/>
        <line x1="142" y1="55" x2="158" y2="55" stroke="#4c0519" stroke-width="2"/>
        <line x1="142" y1="65" x2="158" y2="65" stroke="#4c0519" stroke-width="2"/>
        <line x1="142" y1="75" x2="158" y2="75" stroke="#4c0519" stroke-width="2"/>

        <path d="M150 80 L110 110 L115 118 L150 90 L185 118 L190 110 Z" fill="url(#tracheaGrad)"/>

        <path d="M130 90 C 70 70, 30 140, 40 220 C 50 250, 100 260, 130 230 C 145 200, 145 130, 130 90 Z" fill="url(#fleshGradientRight)" stroke="#ffe4e6" stroke-width="0.5"/>
        <path d="M135 150 C 100 160, 60 140, 40 160" fill="none" stroke="#4c0519" stroke-width="1.5" opacity="0.6"/>
        <path d="M100 155 C 80 180, 50 200, 43 210" fill="none" stroke="#4c0519" stroke-width="1.5" opacity="0.6"/>

        <path d="M170 90 C 230 70, 270 140, 260 220 C 250 250, 200 260, 170 230 C 160 210, 185 180, 170 140 C 165 125, 160 110, 170 90 Z" fill="url(#fleshGradientLeft)" stroke="#ffe4e6" stroke-width="0.5"/>
        <path d="M170 145 C 200 160, 240 180, 255 200" fill="none" stroke="#4c0519" stroke-width="1.5" opacity="0.6"/>

        <g stroke="#fecdd3" stroke-width="1" opacity="0.3" stroke-linecap="round">
            <path d="M110 110 L80 130 M85 126 L70 115 M85 126 L65 140 M115 135 L90 170 M95 160 L75 180 M100 180 L85 210 M120 170 L110 220"/>
            <path d="M190 110 L220 130 M215 126 L230 115 M215 126 L235 140 M185 135 L210 170 M205 160 L225 180 M200 180 L215 210 M180 170 L190 220"/>
        </g>
    </g>
</svg>
"""

LOGIN_HTML = BASE_CSS + LUNG_SVG + """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>AeroLung | Secure Initialization</title>
</head>
<body class="flex flex-col items-center justify-center h-screen antialiased relative">
    
    <!-- HIGHLY VISIBLE COPYRIGHT BADGE -->
    <div class="copyright-badge">
        © 2026 Created By Shreesh Santoshkumar Rolli
    </div>

    <div class="glass-panel p-10 rounded-2xl w-full max-w-md shadow-2xl relative z-10">
        <div class="text-center mb-8">
            <h1 class="text-4xl font-black tracking-tight text-white">AERO<span class="text-rose-600">LUNG</span></h1>
        </div>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="p-3 rounded mb-6 text-xs font-mono text-center bg-rose-950/50 text-rose-300 border border-rose-800">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        <form method="POST" action="/login" class="space-y-6">
            <div>
                <label class="block text-zinc-400 text-xs font-mono uppercase tracking-widest mb-2">System ID</label>
                <input type="text" name="username" required class="w-full bg-black/50 border border-zinc-700 text-white p-3 rounded focus:border-rose-500 focus:outline-none font-mono">
            </div>
            <div>
                <label class="block text-zinc-400 text-xs font-mono uppercase tracking-widest mb-2">Access Passkey</label>
                <input type="password" name="password" required class="w-full bg-black/50 border border-zinc-700 text-white p-3 rounded focus:border-rose-500 focus:outline-none font-mono">
            </div>
            <button type="submit" class="w-full bg-zinc-100 hover:bg-white text-black font-bold py-4 rounded text-sm uppercase tracking-widest transition mt-4">
                Authenticate
            </button>
        </form>
    </div>
</body>
</html>
"""

MASTER_DASHBOARD_HTML = BASE_CSS + LUNG_SVG + """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <title>AeroLung | Enterprise Dashboard</title>
</head>
<body class="min-h-screen flex flex-col">

    <!-- HIGHLY VISIBLE COPYRIGHT BADGE -->
    <div class="copyright-badge">
        © 2026 Created By Shreesh Santoshkumar Rolli
    </div>

    <!-- NAVIGATION -->
    <nav class="glass-header px-6 py-4 flex justify-between items-center sticky top-0">
        <div class="flex items-center space-x-4">
            <div class="relative flex items-center justify-center w-8 h-8 rounded bg-rose-950 border border-rose-800">
                <span class="w-2 h-2 bg-rose-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(244,63,94,1)]"></span>
            </div>
            <span class="font-black text-2xl tracking-widest text-white">AERO<span class="text-rose-600">LUNG</span></span>
        </div>
        
        <div class="flex items-center space-x-6">
            <div class="text-right pr-4 border-r border-zinc-800">
                <span class="text-white font-bold block text-sm">{{ user_role }}</span>
                <span class="text-[10px] text-zinc-500 uppercase font-mono tracking-widest">Authorized</span>
            </div>
            <a href="?tab=simulator" class="text-xs font-mono text-zinc-300 hover:text-white transition">Dashboard</a>
            <a href="?tab=settings" class="text-xs font-mono text-zinc-300 hover:text-white transition">Config</a>
            <a href="/logout" class="text-xs font-mono text-rose-500 hover:text-rose-400 transition ml-4 border border-rose-900 px-3 py-1 rounded">Logout</a>
        </div>
    </nav>

    <main class="flex-1 p-4 relative w-full max-w-[2000px] mx-auto z-10">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
            <div class="w-full mb-4 p-3 rounded text-sm font-mono text-center bg-rose-950/80 text-rose-200 border border-rose-800">
                {{ messages[0] }}
            </div>
            {% endif %}
        {% endwith %}

        {% if active_tab == 'simulator' %}
        <!-- PROFESSIONAL SIDE-BY-SIDE GRID LAYOUT -->
        <div class="grid grid-cols-1 xl:grid-cols-12 gap-4 items-start">
            
            <!-- COLUMN 1: PROFESSIONAL PARAMETER CONFIGURATION (Span 3) -->
            <div class="xl:col-span-3">
                <div class="glass-panel rounded flex flex-col border border-zinc-800 bg-zinc-900/80">
                    <div class="p-3 border-b border-zinc-800 bg-black/40">
                        <h2 class="text-xs font-bold text-white uppercase tracking-widest flex items-center">
                            <svg class="w-4 h-4 text-zinc-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
                            Control Parameters
                        </h2>
                    </div>
                    
                    <form method="POST" action="/dashboard?tab=simulator" class="p-4 space-y-5">
                        
                        <!-- Mechanics -->
                        <div>
                            <h3 class="text-[10px] text-rose-500 font-bold uppercase tracking-widest mb-3 border-b border-zinc-800 pb-1">Patient Mechanics</h3>
                            <div class="space-y-2">
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-[11px] font-mono">Compliance (C)</label>
                                    <input type="number" step="0.1" name="compliance" value="{{ inputs.compliance if inputs else '60.0' }}" class="clinical-input w-20">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-[11px] font-mono">Resistance (R)</label>
                                    <input type="number" step="1" name="resistance" value="{{ inputs.resistance if inputs else '10' }}" class="clinical-input w-20">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-[11px] font-mono">Dead Space (%)</label>
                                    <input type="number" step="1" name="vd_vt" value="{{ inputs.vd_vt if inputs else '30' }}" class="clinical-input w-20">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-[11px] font-mono">Shunt (%)</label>
                                    <input type="number" step="1" name="shunt" value="{{ inputs.shunt if inputs else '5' }}" class="clinical-input w-20">
                                </div>
                            </div>
                        </div>

                        <!-- Vent Drive -->
                        <div>
                            <h3 class="text-[10px] text-blue-500 font-bold uppercase tracking-widest mb-3 border-b border-zinc-800 pb-1">Ventilator Drive</h3>
                            <div class="space-y-2">
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-[11px] font-mono">PIP (cmH2O)</label>
                                    <input type="number" step="1" name="pip" value="{{ inputs.pip if inputs else '15' }}" class="clinical-input w-20 border-blue-900/50">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-[11px] font-mono">PEEP (cmH2O)</label>
                                    <input type="number" step="1" name="peep" value="{{ inputs.peep if inputs else '5' }}" class="clinical-input w-20 border-blue-900/50">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-[11px] font-mono">Rate (bpm)</label>
                                    <input type="number" step="1" name="rr" value="{{ inputs.rr if inputs else '16' }}" class="clinical-input w-20 border-blue-900/50">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-[11px] font-mono">FiO2 (%)</label>
                                    <input type="number" step="1" name="fio2" value="{{ inputs.fio2 if inputs else '40' }}" class="clinical-input w-20 border-blue-900/50">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-[11px] font-mono">I:E Ratio</label>
                                    <input type="number" step="0.1" name="ie_ratio" value="{{ inputs.ie_ratio if inputs else '2.0' }}" class="clinical-input w-20 border-blue-900/50">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-[11px] font-mono">VCO2 (mL/min)</label>
                                    <input type="number" step="10" name="vco2" value="{{ inputs.vco2 if inputs else '200' }}" class="clinical-input w-20 border-blue-900/50">
                                </div>
                            </div>
                        </div>

                        <button type="submit" class="w-full bg-zinc-100 hover:bg-white text-black font-bold py-3 rounded text-xs uppercase tracking-widest transition mt-4">
                            Apply Parameters
                        </button>
                    </form>
                </div>
            </div>

            <!-- COLUMN 2 & 3 CONTAINER: If no data, show standby -->
            {% if not sim_data %}
            <div class="xl:col-span-9 glass-panel rounded flex flex-col items-center justify-center min-h-[600px] border border-zinc-800 border-dashed">
                <p class="text-sm text-zinc-500 font-mono tracking-[0.3em] uppercase">Awaiting Parameter Application</p>
            </div>
            {% else %}
            
            <!-- COLUMN 2: METRICS & AI INTELLIGENCE (Span 4) -->
            <div class="xl:col-span-4 flex flex-col gap-4">
                
                <!-- AI Diagnostic Box -->
                <div class="glass-panel rounded p-4 border border-zinc-800 bg-gradient-to-br from-zinc-900 to-black">
                    <h3 class="text-[10px] text-rose-500 font-bold uppercase tracking-widest mb-2 border-b border-zinc-800 pb-1">AI Pathological Analysis</h3>
                    <p class="text-lg font-black text-white leading-tight mb-2">{{ sim_data.ai_condition }}</p>
                    <div class="text-[11px] text-zinc-400 font-mono mb-3">
                        <span class="text-zinc-300">Differentials:</span> {{ sim_data.differentials | join(', ') }}
                    </div>
                    <div class="bg-rose-950/30 border border-rose-900/50 p-2 rounded text-xs text-rose-200 font-mono">
                        <strong>Protocol:</strong> {{ sim_data.ai_intervention }}
                    </div>
                </div>

                <!-- High-Density Metrics Grid -->
                <div class="grid grid-cols-2 gap-3">
                    <div class="glass-panel rounded p-3 border border-zinc-800 bg-black/60">
                        <p class="text-[9px] font-mono uppercase text-zinc-500 mb-1">Tidal Volume</p>
                        <p class="text-2xl font-black text-white font-mono">{{ sim_data.peak_volume }}<span class="text-[10px] text-zinc-500 ml-1">mL</span></p>
                        <p class="text-[10px] font-mono text-zinc-400 mt-1">Min: {{ sim_data.minute_vent }} L/m</p>
                    </div>
                    <div class="glass-panel rounded p-3 border border-zinc-800 bg-black/60">
                        <p class="text-[9px] font-mono uppercase text-zinc-500 mb-1">Arterial CO2</p>
                        <p class="text-2xl font-black {% if sim_data.paco2 > 45 or sim_data.paco2 < 35 %}text-amber-400{% else %}text-white{% endif %} font-mono">{{ sim_data.paco2 }}<span class="text-[10px] text-zinc-500 ml-1">mmHg</span></p>
                        <p class="text-[10px] font-mono text-zinc-400 mt-1">Alv: {{ sim_data.alveolar_vent }} L/m</p>
                    </div>
                    <div class="glass-panel rounded p-3 border border-zinc-800 bg-black/60">
                        <p class="text-[9px] font-mono uppercase text-zinc-500 mb-1">Arterial O2</p>
                        <p class="text-2xl font-black {% if sim_data.pao2 < 60 %}text-rose-500{% else %}text-white{% endif %} font-mono">{{ sim_data.pao2 }}<span class="text-[10px] text-zinc-500 ml-1">mmHg</span></p>
                        <p class="text-[10px] font-mono text-zinc-400 mt-1">A-a Grad: {{ sim_data.aa_gradient }}</p>
                    </div>
                    <div class="glass-panel rounded p-3 border border-zinc-800 bg-black/60">
                        <p class="text-[9px] font-mono uppercase text-zinc-500 mb-1">Mech Power</p>
                        <p class="text-2xl font-black {% if sim_data.mech_power > 17 %}text-rose-500{% else %}text-white{% endif %} font-mono">{{ sim_data.mech_power }}<span class="text-[10px] text-zinc-500 ml-1">J/m</span></p>
                        <p class="text-[10px] font-mono text-zinc-400 mt-1">Limit: &lt;17 J/m</p>
                    </div>
                    <div class="glass-panel rounded p-3 border border-zinc-800 bg-black/60">
                        <p class="text-[9px] font-mono uppercase text-zinc-500 mb-1">Est. FEV1/FVC</p>
                        <p class="text-2xl font-black {% if sim_data.fev1_fvc < 70 %}text-red-400{% else %}text-emerald-400{% endif %} font-mono">{{ sim_data.fev1_fvc }}<span class="text-[10px] text-zinc-500 ml-1">%</span></p>
                        <p class="text-[10px] font-mono text-zinc-400 mt-1">{{ sim_data.spirometry_class }}</p>
                    </div>
                    <div class="glass-panel rounded p-3 border border-zinc-800 bg-black/60 flex flex-col justify-center">
                        <p class="text-[9px] font-mono uppercase text-zinc-500 mb-1">Auto-PEEP Risk</p>
                        <p class="text-xl font-black {% if sim_data.auto_peep_risk == 'HIGH' %}text-rose-500{% else %}text-emerald-500{% endif %} font-mono tracking-widest">{{ sim_data.auto_peep_risk }}</p>
                        <p class="text-[10px] font-mono text-zinc-400 mt-1">τ = {{ sim_data.time_const }}s</p>
                    </div>
                </div>
            </div>

            <!-- COLUMN 3: KINEMATIC WAVEFORMS (Span 5) -->
            <div class="xl:col-span-5 flex flex-col gap-3">
                <div class="glass-panel rounded p-3 border border-zinc-800 bg-black/40 h-[180px]">
                    <canvas id="pressureChart"></canvas>
                </div>
                <div class="glass-panel rounded p-3 border border-zinc-800 bg-black/40 h-[180px]">
                    <canvas id="flowChart"></canvas>
                </div>
                <div class="glass-panel rounded p-3 border border-zinc-800 bg-black/40 h-[180px]">
                    <canvas id="volumeChart"></canvas>
                </div>
                <div class="glass-panel rounded p-3 border border-zinc-800 bg-black/40 h-[200px] flex items-center justify-center">
                     <div class="w-full h-full relative">
                         <span class="absolute top-0 left-0 text-[9px] font-mono text-zinc-500 uppercase">P-V Loop Diagnostic</span>
                         <canvas id="pvLoopChart"></canvas>
                     </div>
                </div>

                <script>
                    const waveData = {{ sim_data.waveform_data | safe }};
                    Chart.defaults.color = '#71717a';
                    Chart.defaults.font.family = "'JetBrains Mono', monospace";
                    Chart.defaults.elements.point.radius = 0;
                    Chart.defaults.elements.line.borderWidth = 2;
                    Chart.defaults.elements.line.tension = 0.3;
                    
                    const commonOptions = {
                        responsive: true, maintainAspectRatio: false, animation: false,
                        plugins: { legend: { display: false }, tooltip: { enabled: false } },
                        scales: { x: { grid: { color: 'rgba(63, 63, 70, 0.1)' }, ticks: { display: false } } }
                    };

                    new Chart(document.getElementById('pressureChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.p, borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true }] },
                        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { grid: { color: 'rgba(63, 63, 70, 0.1)' }, title: { display: true, text: 'Paw (cmH2O)', font: {size: 9} } } } }
                    });

                    new Chart(document.getElementById('flowChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.f, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true }] },
                        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { grid: { color: 'rgba(63, 63, 70, 0.1)' }, title: { display: true, text: 'Flow (L/min)', font: {size: 9} } } } }
                    });

                    new Chart(document.getElementById('volumeChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.v, borderColor: '#e11d48', backgroundColor: 'rgba(225, 29, 72, 0.1)', fill: true }] },
                        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { grid: { color: 'rgba(63, 63, 70, 0.1)' }, title: { display: true, text: 'Volume (mL)', font: {size: 9} } } } }
                    });

                    const pvData = waveData.p.map((p, i) => ({x: p, y: waveData.v[i]}));
                    new Chart(document.getElementById('pvLoopChart').getContext('2d'), {
                        type: 'scatter',
                        data: { datasets: [{ data: pvData, borderColor: '#e11d48', backgroundColor: 'transparent', showLine: true }] },
                        options: {
                            responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false } },
                            layout: { padding: { top: 20 } },
                            scales: {
                                x: { grid: { color: 'rgba(63, 63, 70, 0.1)' }, title: { display: true, text: 'Pressure', font: {size: 9} } },
                                y: { grid: { color: 'rgba(63, 63, 70, 0.1)' }, title: { display: true, text: 'Volume', font: {size: 9} } }
                            }
                        }
                    });
                </script>
            </div>
        </div>
        {% endif %}
        
        <!-- SYSTEM CONFIGURATION TAB (CREDENTIALS) -->
        {% if active_tab == 'settings' %}
        <div class="glass-panel max-w-lg mx-auto rounded p-8 mt-10 border border-zinc-800">
            <div class="text-center mb-6">
                <h2 class="text-lg font-black text-white uppercase tracking-widest">System Configuration</h2>
            </div>
            <form method="POST" action="/update_credentials" class="space-y-4">
                <div>
                    <label class="block text-zinc-400 text-xs font-mono uppercase mb-1 tracking-widest">Current Passkey</label>
                    <input type="password" name="current_password" required class="w-full bg-black/50 border border-zinc-700 text-white p-2 rounded focus:border-rose-500 focus:outline-none font-mono text-sm">
                </div>
                <div class="border-t border-zinc-800/50 pt-4 space-y-4">
                    <div>
                        <label class="block text-zinc-400 text-xs font-mono uppercase mb-1 tracking-widest">New System ID</label>
                        <input type="text" name="new_username" required value="{{ session.get('user') }}" class="w-full bg-black/50 border border-zinc-700 text-white p-2 rounded focus:border-rose-500 focus:outline-none font-mono text-sm">
                    </div>
                    <div>
                        <label class="block text-zinc-400 text-xs font-mono uppercase mb-1 tracking-widest">New Passkey</label>
                        <input type="password" name="new_password" required class="w-full bg-black/50 border border-zinc-700 text-white p-2 rounded focus:border-rose-500 focus:outline-none font-mono text-sm">
                    </div>
                </div>
                <button type="submit" class="w-full bg-zinc-100 hover:bg-white text-black font-bold py-3 rounded text-xs uppercase tracking-widest transition mt-4">
                    Commit Changes
                </button>
            </form>
        </div>
        {% endif %}
    </main>
</body>
</html>
"""

# --- BACKEND PHYSICS ENGINE & CREDENTIAL LOGIC ---
@app.route('/')
def home():
    if 'user' in session: return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    u = request.form['username']
    p = request.form['password']
    if u in CLINICAL_DATABASE and CLINICAL_DATABASE[u]['password'] == p:
        session['user'] = u
        session['role'] = CLINICAL_DATABASE[u]['role']
        return redirect(url_for('dashboard'))
    flash("Authentication Rejected: Invalid ID or Passkey.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/update_credentials', methods=['POST'])
def update_credentials():
    if 'user' not in session: return redirect(url_for('home'))
    
    current_user = session['user']
    old_pass = request.form['current_password']
    new_id = request.form['new_username'].strip()
    new_pass = request.form['new_password'].strip()
    
    if CLINICAL_DATABASE[current_user]['password'] == old_pass:
        if new_id != current_user and new_id in CLINICAL_DATABASE:
            flash("System Error: New System ID is already taken.")
        else:
            role = CLINICAL_DATABASE[current_user]['role']
            clearance = CLINICAL_DATABASE[current_user]['clearance']
            del CLINICAL_DATABASE[current_user]
            CLINICAL_DATABASE[new_id] = {'password': new_pass, 'role': role, 'clearance': clearance}
            session['user'] = new_id
            flash("Success: System Credentials Updated.")
    else:
        flash("Authorization Error: Incorrect current passkey.")
        
    return redirect(url_for('dashboard', tab='settings'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    active_tab = request.args.get('tab', 'simulator')
    sim_data = None
    inputs = None
    
    if request.method == 'POST' and active_tab == 'simulator':
        vd_vt = float(request.form['vd_vt']) / 100.0
        shunt = float(request.form['shunt']) / 100.0
        vco2 = float(request.form['vco2'])
        c = float(request.form['compliance'])
        r = float(request.form['resistance'])
        pip = float(request.form['pip'])
        peep = float(request.form['peep'])
        rr = float(request.form['rr'])
        ie = float(request.form['ie_ratio'])
        fio2 = float(request.form['fio2']) / 100.0
        
        inputs = {
            'vd_vt': int(vd_vt*100), 'shunt': int(shunt*100), 'vco2': vco2,
            'compliance': c, 'resistance': r, 'pip': pip, 'peep': peep,
            'rr': rr, 'ie_ratio': ie, 'fio2': int(fio2*100)
        }
        
        # PATHOLOGY LOGIC
        ai_condition = "Normal / Compensated Respiratory Mechanics"
        ai_intervention = "Maintain lung-protective strategy. Monitor driving pressure."
        differentials = ["Healthy Lungs", "Post-operative monitoring"]
        
        if c <= 40 and shunt >= 0.15:
            ai_condition = "Acute Restrictive Defect with Shunt"
            ai_intervention = "Limit Vt to 4-6 mL/kg PBW. Optimize PEEP. Consider proning."
            differentials = ["ARDS", "Cardiogenic Pulmonary Edema", "Severe Pneumonia"]
        elif c <= 40 and r < 15 and shunt < 0.15:
            ai_condition = "Chronic / Dry Restrictive Defect"
            ai_intervention = "Target low tidal volumes. Avoid excessive PEEP."
            differentials = ["Pulmonary Fibrosis", "Interstitial Lung Disease", "Kyphoscoliosis"]
        elif r >= 20 and c >= 60:
            ai_condition = "High-Compliance Obstructive Defect"
            ai_intervention = "High risk for Auto-PEEP. Prolong Te, permissive hypercapnia."
            differentials = ["COPD", "Emphysema"]
        elif r >= 25 and c < 60:
            ai_condition = "Acute Obstructive Defect (Bronchospasm)"
            ai_intervention = "Maximize Expiratory Time (Te). Administer bronchodilators."
            differentials = ["Status Asthmaticus", "Anaphylaxis"]

        # KINEMATICS
        dp = max(0.1, pip - peep)
        peak_volume = dp * c 
        min_vent = (peak_volume * rr) / 1000.0
        alv_vent = ((peak_volume * (1 - vd_vt)) * rr) / 1000.0
        
        t_cycle = 60.0 / rr
        t_i = t_cycle * (1 / (1 + ie))
        t_e = t_cycle - t_i
        
        tau = (r / 1000.0) * c 
        auto_peep_risk = "HIGH" if t_e < (3.0 * tau) else "LOW"
        
        fev1_fvc_ratio = round((1 - math.exp(-1 / max(0.01, tau))) * 100, 1)
        spirometry_class = "Restrictive/Normal" if fev1_fvc_ratio >= 70 else "Obstructive"
            
        mech_power = round(0.098 * rr * (peak_volume/1000.0) * (pip - (dp/2)), 1)
        paco2 = round((0.863 * vco2) / max(0.1, alv_vent), 1)
        p_A_O2 = round(((760 - 47) * fio2) - (paco2 / 0.8), 1)
        pao2 = round(max(30, p_A_O2 - ((shunt * 100) * 12)), 1)
        aa_gradient = round(p_A_O2 - pao2, 1)
        
        # WAVEFORMS
        t_pts, p_pts, v_pts, f_pts = [], [], [], []
        res = 100
        for i in range(res + 1):
            t = (i / res) * t_cycle
            t_pts.append(round(t, 3))
            if t <= t_i:
                p_pts.append(round(pip, 1))
                v_pts.append(round(peak_volume * (1 - math.exp(-t / max(0.01, tau))), 1))
                f_pts.append(round(((peak_volume / max(0.01, tau)) * math.exp(-t / max(0.01, tau))) * 0.06, 1))
            else:
                t_exp = t - t_i
                p_pts.append(round(peep, 1))
                v_pts.append(round(peak_volume * math.exp(-t_exp / max(0.01, tau)), 1))
                f_pts.append(round(-((peak_volume / max(0.01, tau)) * math.exp(-t_exp / max(0.01, tau))) * 0.06, 1))
                
        waveform_data = json.dumps({'t': t_pts, 'p': p_pts, 'v': v_pts, 'f': f_pts})

        sim_data = {
            'ai_condition': ai_condition, 'ai_intervention': ai_intervention,
            'differentials': differentials,
            'peak_volume': round(peak_volume, 1), 'minute_vent': round(min_vent, 2),
            'alveolar_vent': round(alv_vent, 2), 'paco2': paco2, 'pao2': pao2,
            'aa_gradient': aa_gradient, 'mech_power': mech_power,
            't_i': round(t_i, 2), 't_e': round(t_e, 2), 'time_const': round(tau, 3),
            'auto_peep_risk': auto_peep_risk, 'waveform_data': waveform_data,
            'fev1_fvc': fev1_fvc_ratio, 'spirometry_class': spirometry_class
        }

    return render_template_string(
        MASTER_DASHBOARD_HTML, active_tab=active_tab, sim_data=sim_data,
        inputs=inputs, user_role=session.get('role')
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
