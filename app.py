from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import os
import math
import json
import traceback

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

# --- BULLETPROOF FLOAT CONVERTER ---
def safe_float(val, default):
    try:
        if val is None or str(val).strip() == '': return float(default)
        return float(val)
    except ValueError:
        return float(default)

# --- MODERNIZED LAYOUT & PREMIUM TYPOGRAPHY CSS ---
BASE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700;800;900&family=JetBrains+Mono:wght=400;700&display=swap');
    
    body { 
        font-family: 'Inter', sans-serif; 
        background-color: #09090b; 
        color: #e4e4e7; 
        overflow-x: hidden; 
        min-height: 100vh; 
        display: flex; 
        flex-direction: column;
    }
    
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    
    @keyframes bioBreathe {
        0% { transform: translate(-50%, -50%) scale(0.98); opacity: 0.12; filter: drop-shadow(0 0 30px rgba(225,29,72,0.1)); }
        40% { transform: translate(-50%, -50%) scale(1.04); opacity: 0.3; filter: drop-shadow(0 0 80px rgba(225,29,72,0.3)); }
        100% { transform: translate(-50%, -50%) scale(0.98); opacity: 0.12; filter: drop-shadow(0 0 30px rgba(225,29,72,0.1)); }
    }
    
    .living-lung {
        position: fixed; top: 50%; left: 50%; 
        width: 95vw; max-width: 900px; 
        z-index: 0; pointer-events: none; 
        animation: bioBreathe 5s ease-in-out infinite;
    }
    
    .glass-panel {
        background: rgba(18, 18, 24, 0.75);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(63, 63, 70, 0.45);
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.9);
        position: relative;
        z-index: 10;
        height: 100%;
    }
    
    .glass-header {
        background: rgba(9, 9, 11, 0.95);
        backdrop-filter: blur(24px);
        border-bottom: 1px solid rgba(63, 63, 70, 0.5);
        position: relative;
        z-index: 50;
    }
    
    .clinical-input {
        background: #000;
        border: 1px solid #3f3f46;
        color: #fff;
        text-align: right;
        padding: 6px 12px;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 14px;
        width: 100%;
        transition: all 0.2s;
    }
    .clinical-input:focus {
        border-color: #e11d48;
        outline: none;
        box-shadow: 0 0 12px rgba(225,29,72,0.3);
    }
    
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #09090b; }
    ::-webkit-scrollbar-thumb { background: #e11d48; border-radius: 4px; }
</style>
"""

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
        <path d="M150 80 L110 110 L115 118 L150 90 L185 118 L190 110 Z" fill="url(#tracheaGrad)"/>
        <path d="M130 90 C 70 70, 30 140, 40 220 C 50 250, 100 260, 130 230 C 145 200, 145 130, 130 90 Z" fill="url(#fleshGradientRight)" stroke="#ffe4e6" stroke-width="0.5"/>
        <path d="M170 90 C 230 70, 270 140, 260 220 C 250 250, 200 260, 170 230 C 160 210, 185 180, 170 140 C 165 125, 160 110, 170 90 Z" fill="url(#fleshGradientLeft)" stroke="#ffe4e6" stroke-width="0.5"/>
    </g>
</svg>
"""

LOGIN_HTML = BASE_CSS + LUNG_SVG + """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>AeroLung | Clinical Access</title>
</head>
<body class="flex flex-col items-center justify-center h-screen antialiased relative">
    <div class="glass-panel p-10 rounded-2xl w-full max-w-md flex flex-col justify-center shadow-2xl relative z-10">
        <div class="text-center mb-8">
            <h1 class="text-4xl font-black tracking-tight text-white">AERO<span class="text-rose-600">LUNG</span></h1>
            <p class="text-sm text-zinc-400 mt-2 font-medium">Advanced Clinical Analysis Engine</p>
        </div>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="p-3 rounded mb-6 text-sm text-center bg-rose-950/50 text-rose-300 border border-rose-800 font-medium">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        <form method="POST" action="/login" class="space-y-6">
            <div>
                <label class="block text-zinc-400 text-xs font-semibold uppercase tracking-wider mb-2">System ID</label>
                <input type="text" name="username" required class="w-full bg-black/50 border border-zinc-700 text-white p-3 rounded-lg focus:border-rose-500 focus:outline-none font-medium">
            </div>
            <div>
                <label class="block text-zinc-400 text-xs font-semibold uppercase tracking-wider mb-2">Access Passkey</label>
                <input type="password" name="password" required class="w-full bg-black/50 border border-zinc-700 text-white p-3 rounded-lg focus:border-rose-500 focus:outline-none font-medium">
            </div>
            <button type="submit" class="w-full bg-zinc-100 hover:bg-white text-black font-bold py-4 rounded-lg text-sm uppercase tracking-widest transition duration-200 mt-4">
                Authenticate System
            </button>
        </form>
    </div>
    <footer class="absolute bottom-6 text-zinc-600 text-xs tracking-wider uppercase z-10 font-medium">
        © 2026 Created By Shreesh Santoshkumar Rolli
    </footer>
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
    <title>AeroLung | Portal Dashboard</title>
</head>
<body class="min-h-screen flex flex-col relative antialiased">

    <nav class="glass-header px-8 py-5 flex justify-between items-center sticky top-0">
        <div class="flex items-center space-x-4">
            <div class="relative flex items-center justify-center w-8 h-8 rounded bg-rose-950 border border-rose-800">
                <span class="w-2.5 h-2.5 bg-rose-500 rounded-full animate-pulse shadow-[0_0_12px_rgba(244,63,94,1)]"></span>
            </div>
            <span class="font-black text-2xl tracking-wider text-white">AERO<span class="text-rose-600">LUNG</span></span>
        </div>
        
        <div class="flex items-center space-x-8 font-semibold text-sm">
            <div class="text-right pr-4 border-r border-zinc-800 hidden sm:block">
                <span class="text-white block">{{ user_role }}</span>
                <span class="text-[11px] text-zinc-500 uppercase tracking-wider">Operational Mode</span>
            </div>
            <a href="?tab=simulator" class="text-zinc-300 hover:text-white transition duration-200">System Dashboard</a>
            <a href="?tab=settings" class="text-zinc-300 hover:text-white transition duration-200">Configuration</a>
            <a href="/logout" class="text-rose-500 hover:text-rose-400 transition duration-200 ml-2 border border-rose-900/60 px-4 py-2 rounded-lg bg-rose-950/30">Sign Out</a>
        </div>
    </nav>

    <main class="flex-1 p-6 w-full max-w-[2400px] mx-auto relative z-10 flex flex-col justify-stretch">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
            <div class="w-full mb-6 p-4 rounded-xl text-sm font-medium bg-rose-950/80 text-rose-200 border border-rose-800 shadow-xl">
                {{ messages[0] }}
            </div>
            {% endif %}
        {% endwith %}

        {% if active_tab == 'simulator' %}
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch flex-1">
            
            <div class="lg:col-span-3 flex flex-col">
                <div class="glass-panel rounded-xl flex flex-col border border-zinc-800 bg-zinc-950/95 shadow-2xl overflow-hidden justify-between">
                    
                    <div>
                        <div class="p-4 border-b border-zinc-800 bg-black/40 grid grid-cols-2 gap-2">
                            <a href="?tab=simulator&preset=healthy" class="text-xs text-center font-bold bg-zinc-800 text-zinc-300 py-2.5 px-3 rounded-lg hover:bg-zinc-700 transition duration-150">Case 1: Healthy</a>
                            <a href="?tab=simulator&preset=ards" class="text-xs text-center font-bold bg-rose-950/60 text-rose-300 border border-rose-900/50 py-2.5 px-3 rounded-lg hover:bg-rose-900/50 transition duration-150">Case 2: ARDS</a>
                            <a href="?tab=simulator&preset=copd" class="text-xs text-center font-bold bg-amber-950/60 text-amber-300 border border-amber-900/50 py-2.5 px-3 rounded-lg hover:bg-amber-900/50 transition duration-150">Case 3: COPD</a>
                            <a href="?tab=simulator&preset=asthma" class="text-xs text-center font-bold bg-blue-950/60 text-blue-300 border border-blue-900/50 py-2.5 px-3 rounded-lg hover:bg-blue-900/50 transition duration-150">Case 4: Asthma</a>
                        </div>

                        <div class="p-4 border-b border-zinc-800 bg-zinc-900/40">
                            <h2 class="text-xs font-extrabold text-white uppercase tracking-widest">Clinical Parameters Panel</h2>
                        </div>
                        
                        <form method="POST" action="/dashboard?tab=simulator" class="p-5 space-y-5">
                            <div class="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                                <div>
                                    <h3 class="text-[11px] text-rose-500 font-bold uppercase tracking-wider mb-3 border-b border-zinc-800/60 pb-1">Ventilatory Inputs</h3>
                                    <div class="space-y-2.5">
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Tidal Volume (Vt) [mL]</label>
                                            <input type="number" step="10" name="vt_input" value="{{ inputs.vt_input if inputs else '500' }}" class="clinical-input w-24">
                                        </div>
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Peak Insp Pressure (PIP)</label>
                                            <input type="number" step="1" name="pip" value="{{ inputs.pip if inputs else '22' }}" class="clinical-input w-24">
                                        </div>
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Plateau Pressure (Pplat)</label>
                                            <input type="number" step="1" name="pplat" value="{{ inputs.pplat if inputs else '13' }}" class="clinical-input w-24">
                                        </div>
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Total PEEP</label>
                                            <input type="number" step="1" name="peep" value="{{ inputs.peep if inputs else '5' }}" class="clinical-input w-24">
                                        </div>
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Peak Flow Rate [L/min]</label>
                                            <input type="number" step="5" name="peak_flow" value="{{ inputs.peak_flow if inputs else '60' }}" class="clinical-input w-24">
                                        </div>
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Mixed Expired CO2 (PECO2)</label>
                                            <input type="number" step="1" name="peco2" value="{{ inputs.peco2 if inputs else '28' }}" class="clinical-input w-24 text-amber-400">
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <h3 class="text-[11px] text-teal-400 font-bold uppercase tracking-wider mb-3 border-b border-zinc-800/60 pb-1">Lab Variables Matrix</h3>
                                    <div class="space-y-2.5">
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Arterial O2 Content (CaO2)</label>
                                            <input type="number" step="0.1" name="cao2" value="{{ inputs.cao2 if inputs else '19.8' }}" class="clinical-input w-24 text-teal-400">
                                        </div>
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Capillary O2 Content (CcO2)</label>
                                            <input type="number" step="0.1" name="cco2" value="{{ inputs.cco2 if inputs else '20.4' }}" class="clinical-input w-24 text-teal-400">
                                        </div>
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Mixed Venous Content (CvO2)</label>
                                            <input type="number" step="0.1" name="cvo2" value="{{ inputs.cvo2 if inputs else '14.8' }}" class="clinical-input w-24 text-teal-400">
                                        </div>
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Metabolic Serum HCO3</label>
                                            <input type="number" step="1" name="hco3_input" value="{{ inputs.hco3_input if inputs else '24' }}" class="clinical-input w-24 text-teal-400">
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <h3 class="text-[11px] text-blue-400 font-bold uppercase tracking-wider mb-3 border-b border-zinc-800/60 pb-1">Machine Controls</h3>
                                    <div class="space-y-2.5">
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Respiratory Rate (RR)</label>
                                            <input type="number" step="1" name="rr" value="{{ inputs.rr if inputs else '14' }}" class="clinical-input w-24 border-blue-900/40">
                                        </div>
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">FiO2 % Setting</label>
                                            <input type="number" step="1" name="fio2" value="{{ inputs.fio2 if inputs else '30' }}" class="clinical-input w-24 border-blue-900/40">
                                        </div>
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Inspiratory/Expiratory Ratio</label>
                                            <input type="number" step="0.1" name="ie_ratio" value="{{ inputs.ie_ratio if inputs else '2.0' }}" class="clinical-input w-24 border-blue-900/40">
                                        </div>
                                        <div class="flex justify-between items-center gap-4">
                                            <label class="text-zinc-400 text-xs font-medium">Metabolic VCO2 Rate</label>
                                            <input type="number" step="10" name="vco2" value="{{ inputs.vco2 if inputs else '200' }}" class="clinical-input w-24 border-blue-900/40">
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <button type="submit" class="w-full bg-zinc-100 hover:bg-white text-black font-extrabold py-4 rounded-xl text-xs uppercase tracking-widest transition duration-200 shadow-md">
                                Calculate System Framework
                            </button>
                        </form>
                    </div>
                </div>
            </div>

            {% if not sim_data %}
            <div class="w-full lg:col-span-9 glass-panel rounded-xl flex flex-col items-center justify-center border-2 border-zinc-800/60 border-dashed bg-black/30">
                <p class="text-sm text-zinc-400 tracking-widest uppercase font-semibold">Awaiting Matrix Mapping | Select or load clinical variables</p>
            </div>
            {% else %}
            
            <div class="lg:col-span-4 flex flex-col gap-5 overflow-y-auto">
                
                <div class="glass-panel rounded-xl p-5 border border-amber-500/20 bg-zinc-950/95 shadow-xl flex flex-col justify-between">
                    <h3 class="text-xs text-amber-400 font-extrabold uppercase tracking-widest mb-3.5 border-b border-zinc-800/80 pb-2">Derived Elastic Coefficients</h3>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-black/50 p-4 rounded-xl border border-zinc-800 flex flex-col justify-between">
                            <span class="text-[11px] text-zinc-400 uppercase font-semibold tracking-wide">Static Compliance</span>
                            <span class="text-3xl font-black text-white my-1 font-mono tracking-tight">{{ sim_data.derived_compliance }}</span>
                            <span class="text-[11px] text-zinc-500 font-medium">mL/cmH2O</span>
                        </div>
                        <div class="bg-black/50 p-4 rounded-xl border border-zinc-800 flex flex-col justify-between">
                            <span class="text-[11px] text-zinc-400 uppercase font-semibold tracking-wide">Airway Resistance</span>
                            <span class="text-3xl font-black text-white my-1 font-mono tracking-tight">{{ sim_data.derived_resistance }}</span>
                            <span class="text-[11px] text-zinc-500 font-medium">cmH2O/L/s</span>
                        </div>
                        <div class="bg-black/50 p-4 rounded-xl border border-zinc-800 flex flex-col justify-between">
                            <span class="text-[11px] text-zinc-400 uppercase font-semibold tracking-wide">Dead Space Ratio</span>
                            <span class="text-3xl font-black text-amber-400 my-1 font-mono tracking-tight">{{ sim_data.derived_vd_vt }}%</span>
                            <span class="text-[11px] text-zinc-500 font-medium">Enghoff Realization</span>
                        </div>
                        <div class="bg-black/50 p-4 rounded-xl border border-zinc-800 flex flex-col justify-between">
                            <span class="text-[11px] text-zinc-400 uppercase font-semibold tracking-wide">Shunt Fraction</span>
                            <span class="text-3xl font-black text-teal-400 my-1 font-mono tracking-tight">{{ sim_data.derived_shunt }}%</span>
                            <span class="text-[11px] text-zinc-500 font-medium">Content Extrapolated</span>
                        </div>
                    </div>
                </div>

                <div class="glass-panel rounded-xl p-5 border border-sky-500/20 bg-zinc-950/95 shadow-xl flex flex-col justify-between">
                    <h3 class="text-xs text-sky-400 font-extrabold uppercase tracking-widest mb-3.5 border-b border-zinc-800/80 pb-2">Spirometry Pulmonary Assays</h3>
                    <div class="grid grid-cols-3 gap-3 mb-4">
                        <div class="bg-black/50 p-3 rounded-xl border border-zinc-800 text-center">
                            <span class="text-[10px] text-zinc-400 uppercase font-semibold block">FEV1</span>
                            <span class="text-xl font-bold text-white font-mono block mt-1">{{ sim_data.fev1_vol }}L</span>
                        </div>
                        <div class="bg-black/50 p-3 rounded-xl border border-zinc-800 text-center">
                            <span class="text-[10px] text-zinc-400 uppercase font-semibold block">FVC</span>
                            <span class="text-xl font-bold text-white font-mono block mt-1">{{ sim_data.fvc_vol }}L</span>
                        </div>
                        <div class="bg-black/50 p-3 rounded-xl border border-zinc-800 text-center">
                            <span class="text-[10px] text-zinc-400 uppercase font-semibold block">Ratio %</span>
                            <span class="text-xl font-bold text-sky-400 font-mono block mt-1">{{ sim_data.fev1_fvc_pct }}%</span>
                        </div>
                    </div>
                    <div class="p-4 rounded-xl text-xs bg-sky-950/20 border border-sky-900/60 text-sky-200">
                        <span class="text-[10px] text-sky-400 uppercase tracking-wider font-extrabold block mb-1">Functional Interpretation</span>
                        <p class="text-zinc-300 text-xs leading-relaxed font-medium">{{ sim_data.spirometry_eval }}</p>
                    </div>
                </div>

                <div class="glass-panel rounded-xl p-5 border border-zinc-800 bg-gradient-to-br from-zinc-950 to-zinc-900 shadow-xl flex flex-col justify-between">
                    <div>
                        <h3 class="text-xs text-rose-500 font-extrabold uppercase tracking-widest mb-3.5 border-b border-zinc-800/80 pb-2">AI Expert Analysis Model</h3>
                        <p class="text-xl font-extrabold text-white leading-snug mb-3">{{ sim_data.ai_condition }}</p>
                        <div class="text-xs text-zinc-300 mb-4 bg-black/60 p-3 rounded-xl border border-zinc-900 font-medium">
                            <span class="text-zinc-500 uppercase tracking-wide block mb-1.5 text-[10px] font-bold">Computed Differential Criteria</span> 
                            {{ sim_data.differentials | join(', ') }}
                        </div>
                    </div>
                    <div class="bg-rose-950/30 border border-rose-900/50 p-4 rounded-xl text-xs text-rose-200 leading-relaxed font-medium">
                        <strong class="text-rose-400 block mb-1 font-extrabold text-[10px] tracking-wider uppercase">Clinical Stabilization Protocol</strong>
                        {{ sim_data.ai_intervention }}
                    </div>
                </div>

                <div class="glass-panel rounded-xl p-5 border border-purple-900/40 bg-zinc-950/95 shadow-xl flex flex-col justify-between">
                    <div>
                        <h3 class="text-xs text-purple-400 font-extrabold uppercase tracking-widest mb-3.5 border-b border-zinc-800/80 pb-2">Systemic Acid-Base Equilibrium</h3>
                        <div class="grid grid-cols-3 gap-3 text-center mb-4">
                            <div class="bg-black/50 p-3 rounded-xl border border-zinc-800">
                                <span class="text-[10px] text-zinc-400 uppercase font-semibold block">pH Tension</span>
                                <span class="text-xl font-bold font-mono mt-1 block {% if sim_data.ph < 7.35 %}text-red-400{% elif sim_data.ph > 7.45 %}text-blue-400{% else %}text-emerald-400{% endif %}">{{ sim_data.ph }}</span>
                            </div>
                            <div class="bg-black/50 p-3 rounded-xl border border-zinc-800">
                                <span class="text-[10px] text-zinc-400 uppercase font-semibold block">PaCO2</span>
                                <span class="text-xl font-bold font-mono text-amber-400 mt-1 block">{{ sim_data.paco2 }}</span>
                            </div>
                            <div class="bg-black/50 p-3 rounded-xl border border-zinc-800">
                                <span class="text-[10px] text-zinc-400 uppercase font-semibold block">Plasma HCO3</span>
                                <span class="text-xl font-bold font-mono text-teal-400 mt-1 block">{{ sim_data.hco3 }}</span>
                            </div>
                        </div>
                    </div>
                    <div class="p-4 rounded-xl text-xs bg-purple-950/20 border border-purple-900/60 text-purple-200">
                        <div class="flex justify-between items-center border-b border-purple-900/40 pb-2 mb-2">
                            <span class="text-purple-400 text-[10px] uppercase font-extrabold tracking-wider">Identified Pathology</span>
                            <span class="font-extrabold text-white uppercase tracking-wide">{{ sim_data.acid_base_status }}</span>
                        </div>
                        <p class="text-zinc-300 text-xs font-medium leading-relaxed">{{ sim_data.acid_base_delta_text }}</p>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div class="glass-panel rounded-xl p-4 border border-zinc-800 bg-black/50 shadow-md flex flex-col justify-between">
                        <p class="text-[10px] font-extrabold uppercase text-zinc-400 tracking-wider">Minute Ventilation</p>
                        <p class="text-3xl font-black text-white font-mono tracking-tight my-1">{{ sim_data.minute_vent }}<span class="text-xs text-zinc-500 font-medium ml-1">L/m</span></p>
                        <p class="text-[11px] text-zinc-400 font-medium border-t border-zinc-800/80 pt-1.5 mt-1">Alveolar: {{ sim_data.alveolar_vent }} L/m</p>
                    </div>
                    <div class="glass-panel rounded-xl p-4 border border-zinc-800 bg-black/50 shadow-md flex flex-col justify-between">
                        <p class="text-[10px] font-extrabold uppercase text-zinc-400 tracking-wider">Arterial Tension</p>
                        <p class="text-3xl font-black {% if sim_data.pao2 < 60 %}text-rose-500{% else %}text-white{% endif %} font-mono tracking-tight my-1">{{ sim_data.pao2 }}<span class="text-xs text-zinc-500 font-medium ml-1">mmHg</span></p>
                        <p class="text-[11px] text-zinc-400 font-medium border-t border-zinc-800/80 pt-1.5 mt-1">A-a Gradient: {{ sim_data.aa_gradient }}</p>
                    </div>
                </div>

            </div>

            <div class="lg:col-span-5 flex flex-col gap-4 justify-between h-full">
                
                <div class="glass-panel rounded-xl p-4 border border-zinc-800 bg-black/40 shadow-xl flex-1 flex flex-col min-h-[140px] relative justify-center">
                    <span class="absolute top-3 right-4 text-[10px] font-bold text-blue-400 uppercase tracking-widest z-20">Pressure Tracing Curve (Paw)</span>
                    <div class="w-full h-full pt-4"><canvas id="pressureChart"></canvas></div>
                </div>
                
                <div class="glass-panel rounded-xl p-4 border border-zinc-800 bg-black/40 shadow-xl flex-1 flex flex-col min-h-[140px] relative justify-center">
                    <span class="absolute top-3 right-4 text-[10px] font-bold text-emerald-400 uppercase tracking-widest z-20">Flow Waveform Vectors (L/m)</span>
                    <div class="w-full h-full pt-4"><canvas id="flowChart"></canvas></div>
                </div>
                
                <div class="glass-panel rounded-xl p-4 border border-zinc-800 bg-black/40 shadow-xl flex-1 flex flex-col min-h-[140px] relative justify-center">
                    <span class="absolute top-3 right-4 text-[10px] font-bold text-rose-400 uppercase tracking-widest z-20">Volume Integration Wave (mL)</span>
                    <div class="w-full h-full pt-4"><canvas id="volumeChart"></canvas></div>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 flex-[1.5] min-h-[260px]">
                    <div class="glass-panel rounded-xl p-4 border border-zinc-800 bg-black/40 shadow-xl flex flex-col relative justify-center">
                        <div class="absolute top-3 left-4 text-[11px] font-extrabold text-zinc-300 uppercase tracking-wider">Dynamic P-V Loop</div>
                        <div class="w-full h-full pt-6"><canvas id="pvLoopChart"></canvas></div>
                    </div>
                    <div class="glass-panel rounded-xl p-4 border border-sky-950/60 bg-black/40 shadow-xl flex flex-col relative justify-center">
                        <div class="absolute top-3 left-4 text-[11px] font-extrabold text-sky-400 uppercase tracking-wider">Spirometry Tracing Matrix</div>
                        <div class="w-full h-full pt-6"><canvas id="fevChart"></canvas></div>
                    </div>
                </div>

                <script>
                    // Bulletproof Client-Side Array Sanitization Pipeline
                    function getCleanArray(rawInput, key) {
                        try {
                            if (!rawInput) return [];
                            const parsed = typeof rawInput === 'string' ? JSON.parse(rawInput) : rawInput;
                            const targetArray = parsed[key];
                            if (!Array.isArray(targetArray)) return [];
                            
                            return targetArray.map(val => {
                                let num = Number(val);
                                return isNaN(num) || !isFinite(num) ? 0 : num;
                            });
                        } catch (e) {
                            console.warn(`Fallback triggered for field key [${key}]:`, e);
                            return [];
                        }
                    }

                    // Safely Intercept Server JSON Strings
                    const serverPayload = {% if sim_data and sim_data.waveform_data %}{{ sim_data.waveform_data | safe }}{% else %}{}{% endif %};
                    
                    const waveData = {
                        t: getCleanArray(serverPayload, 't'),
                        p: getCleanArray(serverPayload, 'p'),
                        v: getCleanArray(serverPayload, 'v'),
                        f: getCleanArray(serverPayload, 'f'),
                        spiro_t: getCleanArray(serverPayload, 'spiro_t'),
                        spiro_v: getCleanArray(serverPayload, 'spiro_v')
                    };

                    Chart.defaults.color = '#a1a1aa';
                    Chart.defaults.font.family = "'Inter', sans-serif";
                    Chart.defaults.elements.point.radius = 0;
                    Chart.defaults.elements.line.borderWidth = 2.5;
                    Chart.defaults.elements.line.tension = 0.25;
                    
                    const commonOptions = {
                        responsive: true, maintainAspectRatio: false, animation: false,
                        plugins: { legend: { display: false } },
                        scales: { 
                            x: { grid: { color: 'rgba(255, 255, 255, 0.04)' }, ticks: { maxTicksLimit: 8 } }, 
                            y: { grid: { color: 'rgba(255, 255, 255, 0.04)' } } 
                        }
                    };

                    if (waveData.t.length > 0) {
                        new Chart(document.getElementById('pressureChart').getContext('2d'), {
                            type: 'line', data: { labels: waveData.t, datasets: [{ data: waveData.p, borderColor: '#3b82f6', fill: false }] }, options: commonOptions
                        });
                        new Chart(document.getElementById('flowChart').getContext('2d'), {
                            type: 'line', data: { labels: waveData.t, datasets: [{ data: waveData.f, borderColor: '#10b981', fill: false }] }, options: commonOptions
                        });
                        new Chart(document.getElementById('volumeChart').getContext('2d'), {
                            type: 'line', data: { labels: waveData.t, datasets: [{ data: waveData.v, borderColor: '#e11d48', fill: false }] }, options: commonOptions
                        });

                        const pvData = waveData.p.map((pVal, idx) => ({x: pVal, y: waveData.v[idx] || 0}));
                        new Chart(document.getElementById('pvLoopChart').getContext('2d'), {
                            type: 'scatter', data: { datasets: [{ data: pvData, borderColor: '#f43f5e', showLine: true }] }, options: commonOptions
                        });

                        const spiroMap = waveData.spiro_t.map((tVal, idx) => ({x: tVal, y: waveData.spiro_v[idx] || 0}));
                        new Chart(document.getElementById('fevChart').getContext('2d'), {
                            type: 'scatter', data: { datasets: [{ data: spiroMap, borderColor: '#38bdf8', showLine: true }] }, options: commonOptions
                        });
                    } else {
                        console.error("Clinical metrics stream contains empty arrays. Waveforms halted.");
                    }
                </script>
            </div>
            {% endif %}
        </div>
        {% endif %}
        
        {% if active_tab == 'settings' %}
        <div class="glass-panel max-w-xl mx-auto rounded-xl p-8 mt-12 border border-zinc-800 shadow-2xl bg-zinc-950/90 flex flex-col justify-center">
            <div class="text-center mb-8">
                <h2 class="text-xl font-extrabold text-white uppercase tracking-widest border-b border-zinc-800 pb-4">Configuration Terminal</h2>
            </div>
            <form method="POST" action="/update_credentials" class="space-y-6">
                <div>
                    <label class="block text-zinc-400 text-xs font-bold uppercase mb-2 tracking-wider">Passkey</label>
                    <input type="password" name="current_password" class="w-full bg-black border border-zinc-700 text-white p-3.5 rounded-lg focus:outline-none">
                </div>
                <button type="submit" class="w-full bg-zinc-100 hover:bg-white text-black font-black py-4 rounded-xl text-xs uppercase tracking-widest transition duration-200 shadow-md">
                    Commit Changes
                </button>
            </form>
        </div>
        {% endif %}
    </main>
    
    <footer class="mt-auto py-5 text-center border-t border-zinc-900/60 bg-black/40">
        <p class="text-zinc-500 text-xs font-semibold tracking-wider uppercase">© 2026 Created By Shreesh Santoshkumar Rolli</p>
    </footer>
</body>
</html>
"""

@app.route('/')
def home():
    if 'user' in session and session.get('user') in CLINICAL_DATABASE:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    u = request.form.get('username', '')
    p = request.form.get('password', '')
    if u in CLINICAL_DATABASE and CLINICAL_DATABASE[u]['password'] == p:
        session['user'] = u
        session['role'] = CLINICAL_DATABASE[u]['role']
        return redirect(url_for('dashboard'))
    flash("Access Countermanded.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session or session.get('user') not in CLINICAL_DATABASE:
        session.clear()
        return redirect(url_for('home'))
        
    active_tab = request.args.get('tab', 'simulator')
    preset = request.args.get('preset', '')
    sim_data = None
    
    PRESETS = {
        "healthy": {"vt_input": 500, "pip": 20, "pplat": 13, "peep": 5, "peak_flow": 60, "peco2": 28, "cao2": 19.8, "cco2": 20.4, "cvo2": 14.8, "hco3_input": 24, "rr": 14, "fio2": 30, "ie_ratio": 2.0, "vco2": 200},
        "ards":    {"vt_input": 350, "pip": 35, "pplat": 29, "peep": 14, "peak_flow": 50, "peco2": 18, "cao2": 16.2, "cco2": 20.1, "cvo2": 11.2, "hco3_input": 21, "rr": 25, "fio2": 70, "ie_ratio": 1.5, "vco2": 220},
        "copd":    {"vt_input": 520, "pip": 32, "pplat": 16, "peep": 5, "peak_flow": 45, "peco2": 24, "cao2": 18.5, "cco2": 20.2, "cvo2": 14.2, "hco3_input": 31, "rr": 10, "fio2": 35, "ie_ratio": 4.0, "vco2": 190},
        "asthma":  {"vt_input": 480, "pip": 42, "pplat": 17, "peep": 5, "peak_flow": 40, "peco2": 25, "cao2": 19.2, "cco2": 20.3, "cvo2": 14.1, "hco3_input": 24, "rr": 12, "fio2": 40, "ie_ratio": 5.0, "vco2": 210}
    }
    
    inputs = None
    if preset in PRESETS:
        inputs = PRESETS[preset]
    elif request.method == 'POST':
        inputs = {
            'vt_input': safe_float(request.form.get('vt_input'), 500),
            'pip': safe_float(request.form.get('pip'), 22),
            'pplat': safe_float(request.form.get('pplat'), 13),
            'peep': safe_float(request.form.get('peep'), 5),
            'peak_flow': safe_float(request.form.get('peak_flow'), 60),
            'peco2': safe_float(request.form.get('peco2'), 28),
            'cao2': safe_float(request.form.get('cao2'), 19.8),
            'cco2': safe_float(request.form.get('cco2'), 20.4),
            'cvo2': safe_float(request.form.get('cvo2'), 14.8),
            'hco3_input': safe_float(request.form.get('hco3_input'), 24),
            'rr': safe_float(request.form.get('rr'), 14),
            'fio2': safe_float(request.form.get('fio2'), 30),
            'ie_ratio': safe_float(request.form.get('ie_ratio'), 2.0),
            'vco2': safe_float(request.form.get('vco2'), 200)
        }
    else:
        inputs = PRESETS["healthy"]
        
    if active_tab == 'simulator':
        try:
            vt = max(10.0, inputs['vt_input'])
            pip = max(1.0, inputs['pip'])
            pplat = max(1.0, inputs['pplat'])
            peep = max(0.0, inputs['peep'])
            flow_lmin = max(5.0, inputs['peak_flow'])
            peco2 = max(0.1, inputs['peco2'])
            cao2 = inputs['cao2']
            cco2 = inputs['cco2']
            cvo2 = inputs['cvo2']
            hco3_input = max(0.1, inputs['hco3_input'])
            rr = max(1.0, inputs['rr'])
            ie = max(0.1, inputs['ie_ratio'])
            vco2 = max(10.0, inputs['vco2'])
            fio2_val = inputs['fio2']

            driving_pressure = max(0.1, pplat - peep)
            compliance = vt / driving_pressure
            
            flow_lsec = flow_lmin / 60.0
            resistance = max(0.1, (pip - pplat) / flow_lsec)
            
            min_vent_est = (vt * rr) / 1000.0
            paco2_derived = max(1.0, (0.863 * vco2) / max(0.1, min_vent_est * 0.75))
            if peco2 >= paco2_derived: 
                peco2 = max(0.1, paco2_derived - 4.0)
            vd_vt_ratio = max(0.01, min(0.95, (paco2_derived - peco2) / paco2_derived))
            vd_vt_pct = round(vd_vt_ratio * 100, 1)

            shunt_denominator = max(0.1, cco2 - cvo2)
            shunt_ratio = (cco2 - cao2) / shunt_denominator
            shunt_pct = round(max(0.01, min(0.95, shunt_ratio)) * 100, 1)

            alv_vent = max(0.1, ((vt * (1 - vd_vt_ratio)) * rr) / 1000.0)
            paco2 = round((0.863 * vco2) / alv_vent, 1)
            
            try: ph = round(6.1 + math.log10(hco3_input / (0.0301 * max(1.0, paco2))), 2)
            except Exception: ph = 7.40

            # --- DYNAMIC SPECTRUM MATRIX FOR CLASSIFICATION ---
            r_severity = max(0.0, (45.0 - compliance) / 5.0) if compliance < 45 else 0.0
            if shunt_pct > 15: r_severity += (shunt_pct - 15) / 4.0

            o_severity = max(0.0, (resistance - 12.0) / 3.0) if resistance > 12 else 0.0
            if paco2 > 48: o_severity += (paco2 - 48) / 10.0

            if r_severity == 0 and o_severity == 0 and 7.35 <= ph <= 7.45:
                ai_condition = "Physiologically Normal Lung Baseline"
                ai_intervention = "Normal values across all quadrants. Standard settings map normal blood gasses."
                differentials = ["Healthy Control Context"]
            elif r_severity >= o_severity:
                prefix = "Critical " if r_severity > 4 else "Moderate "
                ai_condition = f"{prefix}Restrictive Defect Profile [Structural Compliance Loss]"
                ai_intervention = f"CRITICAL TARGET MAP: Restrict Volume exposure to protect membrane. Programmed compliance drop measured at {round(compliance,1)}. Escalate PEEP matrix immediately to open collapse nodes."
                differentials = ["Acute Lung Injury Syndrome", "Interstitial Consolidation Array", "Shunt Expansion Loop"]
            else:
                prefix = "Severe " if o_severity > 4 else "Acute "
                if compliance >= 50:
                    ai_condition = f"{prefix}Obstructive Emphysematous Disease Profile"
                    ai_intervention = "DANGER: Airway auto-peep vector active. Drastically reduce respiratory rate entries and broaden expiratory timing margins to relieve circuit pressure."
                    differentials = ["COPD Hyper-inflation State", "Elastic Tissue Dissolution Matrix"]
                else:
                    ai_condition = f"{prefix}Reactive Bronchospasm Vector"
                    ai_intervention = f"Airway pathway resistance calculated at highly restricted level ({round(resistance,1)} cmH2O). Introduce rapid bronchodilation agents. Minimize I:E ratio constraints."
                    differentials = ["Status Asthmaticus Attack Block", "Mechanical Endotracheal Resistance"]

            # --- SYSTEMIC ACID BASE EQUILIBRIUM LOGIC BLOCK ---
            if ph < 7.35:
                if paco2 > 45:
                    acid_base_status = "Respiratory Acidosis"
                    acid_base_delta_text = f"Severe retention of gaseous carbon dioxide (PaCO2: {paco2} mmHg) causing critical acidemia. Boost global volume processing or frequency index."
                else:
                    acid_base_status = "Metabolic Acidosis"
                    acid_base_delta_text = "Primary consumption of systemic bicarbonate reserves. Audit serum anion-gap profiles."
            elif ph > 7.45:
                if paco2 < 35:
                    acid_base_status = "Respiratory Alkalosis"
                    acid_base_delta_text = "Alveolar hyperventilation blowing off crucial carbon dioxide volume."
                else:
                    acid_base_status = "Metabolic Alkalosis"
                    acid_base_delta_text = "Unchecked accumulation of plasma metabolic alkali molecules."
            else:
                acid_base_status = "Normal Homeostasis"
                acid_base_delta_text = "System parameters register within safe biological threshold lines."

            # Spirometry Scalars
            if compliance <= 40: 
                fvc_vol = 2.4; decay_constant = 2.2
                spirometry_eval = "Restrictive Tracing: Volume constraints limit capacity."
            elif resistance >= 15: 
                fvc_vol = 4.5; decay_constant = 0.55
                spirometry_eval = "Obstructive Tracing: Airway block delays curve output."
            else: 
                fvc_vol = 5.0; decay_constant = 1.65
                spirometry_eval = "Normal standard spirometry curve mapped safely."

            fev1_vol = round(fvc_vol * (1.0 - math.exp(-decay_constant * 1.0)), 2)
            fvc_vol_realized = round(fvc_vol * (1.0 - math.exp(-decay_constant * 6.0)), 2)
            fev1_fvc_pct = round((fev1_vol / fvc_vol_realized) * 100, 1)

            p_A_O2 = round(((760 - 47) * (fio2_val / 100.0)) - (paco2 / 0.8), 1)
            pao2 = round(max(30, p_A_O2 - (shunt_pct * 1.2)), 1)
            aa_gradient = round(p_A_O2 - pao2, 1)
            mech_power = round(0.098 * rr * (vt / 1000.0) * (pip - (driving_pressure / 2)), 1)

            t_cycle = 60.0 / rr
            t_i = t_cycle * (1 / (1 + ie))
            t_e = t_cycle - t_i
            tau = max(0.001, (resistance / 1000.0) * compliance)
            auto_peep_risk = "HIGH" if t_e < (3.0 * tau) else "LOW"

            t_pts, p_pts, v_pts, f_pts = [], [], [], []
            res = 60
            for i in range(res + 1):
                t = (i / res) * t_cycle
                t_pts.append(round(t, 3))
                if t <= t_i:
                    p_pts.append(round(pip, 1))
                    v_pts.append(round(vt * (1 - math.exp(-t / tau)), 1))
                    f_pts.append(round(((vt / tau) * math.exp(-t / tau)), 1) * 0.06)
                else:
                    t_exp = t - t_i
                    p_pts.append(round(peep, 1))
                    v_pts.append(round(vt * math.exp(-t_exp / tau), 1))
                    f_pts.append(round(-((vt / tau) * math.exp(-t_exp / tau)), 1) * 0.06)
            
            spiro_t_pts, spiro_v_pts = [], []
            for step in range(41):
                s_t = step * 0.15
                spiro_t_pts.append(round(s_t, 2))
                spiro_v_pts.append(round(fvc_vol * (1.0 - math.exp(-decay_constant * s_t)), 2))

            sim_data = {
                'derived_compliance': round(compliance, 1), 'derived_resistance': round(resistance, 1),
                'derived_vd_vt': vd_vt_pct, 'derived_shunt': shunt_pct,
                'fev1_vol': fev1_vol, 'fvc_vol': fvc_vol_realized, 'fev1_fvc_pct': fev1_fvc_pct, 'spirometry_eval': spirometry_eval,
                'ai_condition': ai_condition, 'ai_intervention': ai_intervention, 'differentials': differentials,
                'paco2': paco2, 'pao2': pao2, 'aa_gradient': aa_gradient, 'mech_power': mech_power,
                'ph': ph, 'hco3': hco3_input, 'acid_base_status': acid_base_status, 'acid_base_delta_text': acid_base_delta_text,
                'peak_volume': vt, 'minute_vent': round(min_vent_est, 2), 'alveolar_vent': round(alv_vent, 2),
                'auto_peep_risk': auto_peep_risk, 'time_const': round(tau, 3),
                'waveform_data': json.dumps({'t': t_pts, 'p': p_pts, 'v': v_pts, 'f': f_pts, 'spiro_t': spiro_t_pts, 'spiro_v': spiro_v_pts})
            }
        except Exception:
            flash(f"CALCULATION ENGINE RUNTIME CRASH:\n{traceback.format_exc()}")

    return render_template_string(MASTER_DASHBOARD_HTML, active_tab=active_tab, sim_data=sim_data, inputs=inputs, user_role=session.get('role', 'Chief Architect'))

@app.route('/update_credentials', methods=['POST'])
def update_credentials():
    flash("Changes restricted on active profile configuration.")
    return redirect(url_for('dashboard', tab='settings'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
