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

# --- PREMIUM UI CSS & REALISTIC LUNG SVG ---
BASE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;600;800;900&family=JetBrains+Mono:wght=400;700&display=swap');
    
    body { font-family: 'Inter', sans-serif; background-color: #09090b; color: #e4e4e7; overflow-x: hidden; min-height: 100vh; display: flex; flex-direction: column;}
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    
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
    
    .clinical-input {
        background: #000;
        border: 1px solid #3f3f46;
        color: #fff;
        text-align: right;
        padding: 4px 8px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        width: 100%;
        transition: all 0.2s;
    }
    .clinical-input:focus {
        border-color: #e11d48;
        outline: none;
        box-shadow: 0 0 10px rgba(225,29,72,0.2);
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
    <footer class="absolute bottom-6 text-zinc-600 text-[10px] font-mono tracking-widest uppercase z-10">
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
    <title>AeroLung | Enterprise Dashboard</title>
</head>
<body class="min-h-screen flex flex-col relative">

    <nav class="glass-header px-6 py-4 flex justify-between items-center sticky top-0">
        <div class="flex items-center space-x-4">
            <div class="relative flex items-center justify-center w-8 h-8 rounded bg-rose-950 border border-rose-800">
                <span class="w-2 h-2 bg-rose-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(244,63,94,1)]"></span>
            </div>
            <span class="font-black text-2xl tracking-widest text-white">AERO<span class="text-rose-600">LUNG</span></span>
        </div>
        
        <div class="flex items-center space-x-6">
            <div class="text-right pr-4 border-r border-zinc-800 hidden sm:block">
                <span class="text-white font-bold block text-sm">{{ user_role }}</span>
                <span class="text-[10px] text-zinc-500 uppercase font-mono tracking-widest">Authorized</span>
            </div>
            <a href="?tab=simulator" class="text-xs font-mono text-zinc-300 hover:text-white transition">Dashboard</a>
            <a href="?tab=settings" class="text-xs font-mono text-zinc-300 hover:text-white transition">Config</a>
            <a href="/logout" class="text-xs font-mono text-rose-500 hover:text-rose-400 transition ml-4 border border-rose-900 px-3 py-1 rounded bg-rose-950/30">Logout</a>
        </div>
    </nav>

    <main class="flex-1 p-4 md:p-6 w-full max-w-[2000px] mx-auto relative z-10">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
            <div class="w-full mb-6 p-3 rounded text-sm font-mono text-left bg-rose-950/80 text-rose-200 border border-rose-800 whitespace-pre-wrap shadow-lg">
                {{ messages[0] }}
            </div>
            {% endif %}
        {% endwith %}

        {% if active_tab == 'simulator' %}
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            
            <div class="lg:col-span-3">
                <div class="glass-panel rounded-lg flex flex-col border border-zinc-800 bg-zinc-950/90 shadow-2xl overflow-hidden">
                    
                    <div class="p-4 border-b border-zinc-800 bg-black/40 grid grid-cols-2 gap-2">
                        <a href="?tab=simulator&preset=healthy" class="text-[10px] text-center font-mono font-bold bg-zinc-800 text-zinc-300 py-1.5 px-2 rounded hover:bg-zinc-700 transition">Case 1: Healthy Control</a>
                        <a href="?tab=simulator&preset=ards" class="text-[10px] text-center font-mono font-bold bg-rose-950/60 text-rose-300 border border-rose-900/50 py-1.5 px-2 rounded hover:bg-rose-900/50 transition">Case 2: Severe ARDS</a>
                        <a href="?tab=simulator&preset=copd" class="text-[10px] text-center font-mono font-bold bg-amber-950/60 text-amber-300 border border-amber-900/50 py-1.5 px-2 rounded hover:bg-amber-900/50 transition">Case 3: Floppy COPD</a>
                        <a href="?tab=simulator&preset=asthma" class="text-[10px] text-center font-mono font-bold bg-blue-950/60 text-blue-300 border border-blue-900/50 py-1.5 px-2 rounded hover:bg-blue-900/50 transition">Case 4: Severe Asthma</a>
                    </div>

                    <div class="p-4 border-b border-zinc-800/80 bg-zinc-900/50">
                        <h2 class="text-xs font-black text-white uppercase tracking-widest flex items-center">Clinical Metrics Intake</h2>
                    </div>
                    
                    <form method="POST" action="/dashboard?tab=simulator" class="p-5 space-y-6">
                        <div>
                            <h3 class="text-[10px] text-rose-500 font-black uppercase tracking-widest mb-3 border-b border-zinc-800/50 pb-2">Physiological Telemetry</h3>
                            <div class="space-y-3">
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Tidal Volume (Vt) [mL]</label>
                                    <input type="number" step="10" name="vt_input" value="{{ inputs.vt_input if inputs else '500' }}" class="clinical-input w-24">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Peak Insp Pressure (PIP)</label>
                                    <input type="number" step="1" name="pip" value="{{ inputs.pip if inputs else '22' }}" class="clinical-input w-24">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Plateau Pressure (Pplat)</label>
                                    <input type="number" step="1" name="pplat" value="{{ inputs.pplat if inputs else '13' }}" class="clinical-input w-24">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Total PEEP</label>
                                    <input type="number" step="1" name="peep" value="{{ inputs.peep if inputs else '5' }}" class="clinical-input w-24">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Peak Flow Rate [L/min]</label>
                                    <input type="number" step="5" name="peak_flow" value="{{ inputs.peak_flow if inputs else '60' }}" class="clinical-input w-24">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Mixed Expired CO2 (PECO2)</label>
                                    <input type="number" step="1" name="peco2" value="{{ inputs.peco2 if inputs else '28' }}" class="clinical-input w-24 text-amber-500">
                                </div>
                            </div>
                        </div>

                        <div>
                            <h3 class="text-[10px] text-teal-400 font-black uppercase tracking-widest mb-3 border-b border-zinc-800/50 pb-2">Lab Values / ABG Matrix</h3>
                            <div class="space-y-3">
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Arterial O2 Content (CaO2)</label>
                                    <input type="number" step="0.1" name="cao2" value="{{ inputs.cao2 if inputs else '19.8' }}" class="clinical-input w-24 text-teal-400">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Capillary O2 Content (CcO2)</label>
                                    <input type="number" step="0.1" name="cco2" value="{{ inputs.cco2 if inputs else '20.4' }}" class="clinical-input w-24 text-teal-400">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Mixed Venous Content (CvO2)</label>
                                    <input type="number" step="0.1" name="cvo2" value="{{ inputs.cvo2 if inputs else '14.8' }}" class="clinical-input w-24 text-teal-400">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Metabolic Serum HCO3</label>
                                    <input type="number" step="1" name="hco3_input" value="{{ inputs.hco3_input if inputs else '24' }}" class="clinical-input w-24 text-teal-400">
                                </div>
                            </div>
                        </div>

                        <div>
                            <h3 class="text-[10px] text-blue-500 font-black uppercase tracking-widest mb-3 border-b border-zinc-800/50 pb-2">Ventilator Settings</h3>
                            <div class="space-y-3">
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Respiratory Rate (RR)</label>
                                    <input type="number" step="1" name="rr" value="{{ inputs.rr if inputs else '14' }}" class="clinical-input w-24 border-blue-900/50">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">FiO2 %</label>
                                    <input type="number" step="1" name="fio2" value="{{ inputs.fio2 if inputs else '30' }}" class="clinical-input w-24 border-blue-900/50">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">I:E Ratio</label>
                                    <input type="number" step="0.1" name="ie_ratio" value="{{ inputs.ie_ratio if inputs else '2.0' }}" class="clinical-input w-24 border-blue-900/50">
                                </div>
                                <div class="flex justify-between items-center">
                                    <label class="text-zinc-400 text-xs font-mono">Metabolic VCO2 Output</label>
                                    <input type="number" step="10" name="vco2" value="{{ inputs.vco2 if inputs else '200' }}" class="clinical-input w-24 border-blue-900/50">
                                </div>
                            </div>
                        </div>

                        <button type="submit" class="w-full bg-zinc-200 hover:bg-white text-black font-black py-4 rounded text-xs uppercase tracking-widest transition mt-4">
                            Process Calculations
                        </button>
                    </form>
                </div>
            </div>

            {% if not sim_data %}
            <div class="lg:col-span-9 glass-panel rounded-lg flex flex-col items-center justify-center min-h-[600px] border border-zinc-800/50 border-dashed bg-black/40">
                <div class="w-12 h-12 border-2 border-rose-900 border-t-rose-500 rounded-full animate-spin mb-4"></div>
                <p class="text-sm text-zinc-500 font-mono tracking-[0.3em] uppercase">System Ready | Map a patient medical report to begin</p>
            </div>
            {% else %}
            
            <div class="lg:col-span-4 flex flex-col gap-4">
                
                <div class="glass-panel rounded-lg p-5 border border-amber-500/30 bg-zinc-950/90 shadow-xl">
                    <h3 class="text-[10px] text-amber-400 font-black uppercase tracking-widest mb-3 border-b border-zinc-800/50 pb-2">Report Formula Realizations</h3>
                    <div class="grid grid-cols-2 gap-3 text-left">
                        <div class="bg-black/40 p-3 rounded border border-zinc-800">
                            <span class="text-[9px] text-zinc-500 font-mono block uppercase">1. Derived Compliance</span>
                            <span class="text-2xl font-mono font-black text-white">{{ sim_data.derived_compliance }}</span>
                            <span class="text-[9px] text-zinc-600 font-mono block mt-1">mL/cmH2O</span>
                        </div>
                        <div class="bg-black/40 p-3 rounded border border-zinc-800">
                            <span class="text-[9px] text-zinc-500 font-mono block uppercase">2. Airway Resistance</span>
                            <span class="text-2xl font-mono font-black text-white">{{ sim_data.derived_resistance }}</span>
                            <span class="text-[9px] text-zinc-600 font-mono block mt-1">cmH2O/L/s</span>
                        </div>
                        <div class="bg-black/40 p-3 rounded border border-zinc-800">
                            <span class="text-[9px] text-zinc-500 font-mono block uppercase">3. Dead Space % (Vd/Vt)</span>
                            <span class="text-2xl font-mono font-black text-amber-400">{{ sim_data.derived_vd_vt }}%</span>
                            <span class="text-[9px] text-zinc-600 font-mono block mt-1">Enghoff Realized</span>
                        </div>
                        <div class="bg-black/40 p-3 rounded border border-zinc-800">
                            <span class="text-[9px] text-zinc-500 font-mono block uppercase">4. Shunt Fraction %</span>
                            <span class="text-2xl font-mono font-black text-teal-400">{{ sim_data.derived_shunt }}%</span>
                            <span class="text-[9px] text-zinc-600 font-mono block mt-1">Content Calculated</span>
                        </div>
                    </div>
                </div>

                <div class="glass-panel rounded-lg p-5 border border-sky-500/30 bg-zinc-950/90 shadow-xl">
                    <h3 class="text-[10px] text-sky-400 font-black uppercase tracking-widest mb-3 border-b border-zinc-800/50 pb-2">Spirometry Assay Diagnostics</h3>
                    <div class="grid grid-cols-3 gap-2 text-center mb-3">
                        <div class="bg-black/40 p-2 rounded border border-zinc-800">
                            <span class="text-[9px] text-zinc-500 font-mono block uppercase">FEV1 Volume</span>
                            <span class="text-lg font-mono font-black text-white">{{ sim_data.fev1_vol }} L</span>
                        </div>
                        <div class="bg-black/40 p-2 rounded border border-zinc-800">
                            <span class="text-[9px] text-zinc-500 font-mono block uppercase">FVC Capacity</span>
                            <span class="text-lg font-mono font-black text-white">{{ sim_data.fvc_vol }} L</span>
                        </div>
                        <div class="bg-black/40 p-2 rounded border border-zinc-800">
                            <span class="text-[9px] text-zinc-500 font-mono block uppercase">FEV1/FVC Ratio</span>
                            <span class="text-lg font-mono font-black text-sky-400">{{ sim_data.fev1_fvc_pct }}%</span>
                        </div>
                    </div>
                    <div class="p-3 rounded text-xs font-mono bg-sky-950/30 border border-sky-800 text-sky-200">
                        <span class="text-[9px] text-sky-400 uppercase tracking-widest font-bold block mb-1">Pulmonary Function Interpretation:</span>
                        <p class="text-zinc-300 text-[11px] leading-relaxed">{{ sim_data.spirometry_eval }}</p>
                    </div>
                </div>

                <div class="glass-panel rounded-lg p-5 border border-zinc-800/80 bg-gradient-to-br from-zinc-950 to-black shadow-xl">
                    <h3 class="text-[10px] text-rose-500 font-black uppercase tracking-widest mb-3 border-b border-zinc-800/50 pb-2">AI Diagnostics Engine</h3>
                    <p class="text-xl font-black text-white leading-tight mb-3">{{ sim_data.ai_condition }}</p>
                    <div class="text-[11px] text-zinc-400 font-mono mb-4 bg-black/50 p-2 rounded border border-zinc-900">
                        <span class="text-zinc-500 uppercase tracking-wider block mb-1 text-[9px]">Computed Differentials</span> 
                        {{ sim_data.differentials | join(', ') }}
                    </div>
                    <div class="bg-rose-950/40 border border-rose-900/50 p-3 rounded text-xs text-rose-200 font-mono leading-relaxed">
                        <strong class="text-rose-400 block mb-1">RECOMMENDED PROTOCOL:</strong>
                        {{ sim_data.ai_intervention }}
                    </div>
                </div>

                <div class="glass-panel rounded-lg p-5 border border-purple-900/60 bg-zinc-950/90 shadow-xl">
                    <h3 class="text-[10px] text-purple-400 font-black uppercase tracking-widest mb-3 border-b border-zinc-800/50 pb-2">Acid-Base Diagnostic Suite</h3>
                    <div class="grid grid-cols-3 gap-2 text-center mb-4">
                        <div class="bg-black/40 p-2 rounded border border-zinc-800">
                            <span class="text-[9px] text-zinc-500 font-mono block uppercase">Computed pH</span>
                            <span class="text-lg font-mono font-black {% if sim_data.ph < 7.35 %}text-red-400{% elif sim_data.ph > 7.45 %}text-blue-400{% else %}text-emerald-400{% endif %}">{{ sim_data.ph }}</span>
                        </div>
                        <div class="bg-black/40 p-2 rounded border border-zinc-800">
                            <span class="text-[9px] text-zinc-500 font-mono block uppercase">PaCO2</span>
                            <span class="text-lg font-mono font-black text-amber-400">{{ sim_data.paco2 }}</span>
                        </div>
                        <div class="bg-black/40 p-2 rounded border border-zinc-800">
                            <span class="text-[9px] text-zinc-500 font-mono block uppercase">Serum HCO3</span>
                            <span class="text-lg font-mono font-black text-teal-400">{{ sim_data.hco3 }}</span>
                        </div>
                    </div>
                    <div class="p-3 rounded text-xs font-mono bg-purple-950/30 border border-purple-800 text-purple-200">
                        <div class="flex justify-between items-center border-b border-purple-900/50 pb-1.5 mb-1.5">
                            <span class="text-purple-400 text-[10px] uppercase font-bold tracking-wider">Primary State:</span>
                            <span class="font-bold text-white uppercase">{{ sim_data.acid_base_status }}</span>
                        </div>
                        <div class="text-[11px] leading-relaxed text-zinc-300">
                            {{ sim_data.acid_base_delta_text }}
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div class="glass-panel rounded-lg p-4 border border-zinc-800/80 bg-black/60 shadow-lg">
                        <p class="text-[10px] font-mono font-bold uppercase text-zinc-500 mb-1 tracking-wider">Minute Ventilation</p>
                        <p class="text-3xl font-black text-white font-mono">{{ sim_data.minute_vent }}<span class="text-xs text-zinc-600 ml-1">L/m</span></p>
                        <p class="text-[10px] font-mono text-zinc-400 mt-2 border-t border-zinc-800/50 pt-1">Alv Vent: {{ sim_data.alveolar_vent }} L/m</p>
                    </div>
                    <div class="glass-panel rounded-lg p-4 border border-zinc-800/80 bg-black/60 shadow-lg">
                        <p class="text-[10px] font-mono font-bold uppercase text-zinc-500 mb-1 tracking-wider">Arterial Tension</p>
                        <p class="text-3xl font-black {% if sim_data.pao2 < 60 %}text-rose-500{% else %}text-white{% endif %} font-mono">{{ sim_data.pao2 }}<span class="text-xs text-zinc-600 ml-1">mmHg</span></p>
                        <p class="text-[10px] font-mono text-zinc-400 mt-2 border-t border-zinc-800/50 pt-1">A-a Grad: {{ sim_data.aa_gradient }}</p>
                    </div>
                    <div class="glass-panel rounded-lg p-4 border border-zinc-800/80 bg-black/60 shadow-lg">
                        <p class="text-[10px] font-mono font-bold uppercase text-zinc-500 mb-1 tracking-wider">Mech Power</p>
                        <p class="text-3xl font-black {% if sim_data.mech_power > 17 %}text-rose-500{% else %}text-white{% endif %} font-mono">{{ sim_data.mech_power }}<span class="text-xs text-zinc-600 ml-1">J/m</span></p>
                        <p class="text-[10px] font-mono text-zinc-400 mt-2 border-t border-zinc-800/50 pt-1">Threshold: &lt;17 J/m</p>
                    </div>
                    <div class="glass-panel rounded-lg p-4 border border-zinc-800/80 bg-black/60 shadow-lg flex flex-col justify-center">
                        <p class="text-[10px] font-mono font-bold uppercase text-zinc-500 mb-1 tracking-wider">Auto-PEEP Risk</p>
                        <p class="text-2xl font-black {% if sim_data.auto_peep_risk == 'HIGH' %}text-rose-500{% else %}text-emerald-500{% endif %} font-mono tracking-widest mt-1">{{ sim_data.auto_peep_risk }}</p>
                        <p class="text-[10px] font-mono text-zinc-400 mt-2 border-t border-zinc-800/50 pt-1">RC τ = {{ sim_data.time_const }}s</p>
                    </div>
                </div>
            </div>

            <div class="lg:col-span-5 flex flex-col gap-4">
                <div class="glass-panel rounded-lg p-3 border border-zinc-800/80 bg-black/50 shadow-lg h-[130px] relative">
                    <span class="absolute top-2 right-3 text-[9px] font-mono text-blue-400 uppercase tracking-widest z-20">Pressure Waveform (Paw)</span>
                    <canvas id="pressureChart"></canvas>
                </div>
                <div class="glass-panel rounded-lg p-3 border border-zinc-800/80 bg-black/50 shadow-lg h-[130px] relative">
                    <span class="absolute top-2 right-3 text-[9px] font-mono text-emerald-400 uppercase tracking-widest z-20">Airflow Dynamics (L/m)</span>
                    <canvas id="flowChart"></canvas>
                </div>
                <div class="glass-panel rounded-lg p-3 border border-zinc-800/80 bg-black/50 shadow-lg h-[130px] relative">
                    <span class="absolute top-2 right-3 text-[9px] font-mono text-rose-400 uppercase tracking-widest z-20">Volume Accumulation (mL)</span>
                    <canvas id="volumeChart"></canvas>
                </div>
                
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div class="glass-panel rounded-lg p-4 border border-zinc-800/80 bg-black/50 h-[220px] flex items-center justify-center relative">
                        <div class="absolute top-3 left-4 text-[10px] font-mono font-bold text-zinc-400 uppercase tracking-wider">Dynamic P-V Loop</div>
                        <div class="w-full h-full pt-6">
                            <canvas id="pvLoopChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="glass-panel rounded-lg p-4 border border-sky-900/60 bg-black/50 h-[220px] flex items-center justify-center relative">
                        <div class="absolute top-3 left-4 text-[10px] font-mono font-bold text-sky-400 uppercase tracking-wider">FEV1 / FVC Spirogram Loop</div>
                        <div class="w-full h-full pt-6">
                            <canvas id="fevChart"></canvas>
                        </div>
                    </div>
                </div>

                <script>
                    const waveData = {{ sim_data.waveform_data | safe }};
                    
                    Chart.defaults.color = '#e4e4e7';
                    Chart.defaults.font.family = "'JetBrains Mono', monospace";
                    Chart.defaults.elements.point.radius = 0;
                    Chart.defaults.elements.line.borderWidth = 2.0;
                    Chart.defaults.elements.line.tension = 0.3;
                    
                    const commonOptions = {
                        responsive: true, maintainAspectRatio: false, animation: false,
                        plugins: { legend: { display: false }, tooltip: { enabled: false } },
                        layout: { padding: { left: 10, right: 10, top: 15, bottom: 5 } },
                        scales: { 
                            x: { 
                                grid: { color: 'rgba(228, 228, 231, 0.1)' }, 
                                ticks: { color: '#a1a1aa', font: {size: 10} } 
                            },
                            y: {
                                grid: { color: 'rgba(228, 228, 231, 0.1)' },
                                ticks: { color: '#a1a1aa', font: {size: 10}, maxTicksLimit: 5 }
                            }
                        }
                    };

                    new Chart(document.getElementById('pressureChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.p, borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true }] },
                        options: commonOptions
                    });

                    new Chart(document.getElementById('flowChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.f, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true }] },
                        options: commonOptions
                    });

                    new Chart(document.getElementById('volumeChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.v, borderColor: '#e11d48', backgroundColor: 'rgba(225, 29, 72, 0.1)', fill: true }] },
                        options: commonOptions
                    });

                    const pvData = waveData.p.map((p, i) => ({x: p, y: waveData.v[i]}));
                    new Chart(document.getElementById('pvLoopChart').getContext('2d'), {
                        type: 'scatter',
                        data: { datasets: [{ data: pvData, borderColor: '#e11d48', backgroundColor: 'transparent', showLine: true }] },
                        options: {
                            responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false } },
                            scales: {
                                x: { grid: { color: 'rgba(228, 228, 231, 0.1)' }, title: { display: true, text: 'Pressure (cmH2O)', font: {size: 9}, color: '#e4e4e7' }, ticks: { color: '#a1a1aa', font: {size: 9} } },
                                y: { grid: { color: 'rgba(228, 228, 231, 0.1)' }, title: { display: true, text: 'Volume (mL)', font: {size: 9}, color: '#e4e4e7' }, ticks: { color: '#a1a1aa', font: {size: 9} } }
                            }
                        }
                    });

                    // Spirometry Graph Vector Generation Mapping
                    const spiroTime = waveData.spiro_t;
                    const spiroVol = waveData.spiro_v;
                    const spiroMap = spiroTime.map((t, i) => ({x: t, y: spiroVol[i]}));
                    
                    new Chart(document.getElementById('fevChart').getContext('2d'), {
                        type: 'scatter',
                        data: { datasets: [{ data: spiroMap, borderColor: '#38bdf8', backgroundColor: 'rgba(56, 189, 248, 0.05)', showLine: true, fill: true }] },
                        options: {
                            responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false } },
                            scales: {
                                x: { grid: { color: 'rgba(228, 228, 231, 0.1)' }, title: { display: true, text: 'Expiratory Time (Seconds)', font: {size: 9}, color: '#e4e4e7' }, ticks: { color: '#a1a1aa', font: {size: 9} } },
                                y: { grid: { color: 'rgba(228, 228, 231, 0.1)' }, title: { display: true, text: 'Exhaled Volume (Liters)', font: {size: 9}, color: '#e4e4e7' }, ticks: { color: '#a1a1aa', font: {size: 9} } }
                            }
                        }
                    });
                </script>
            </div>
            {% endif %}
        </div>
        {% endif %}
        
        {% if active_tab == 'settings' %}
        <div class="glass-panel max-w-lg mx-auto rounded-lg p-8 mt-10 border border-zinc-800/80 shadow-2xl bg-black/80">
            <div class="text-center mb-8">
                <h2 class="text-xl font-black text-white uppercase tracking-widest border-b border-zinc-800/50 pb-4">System Configuration</h2>
            </div>
            <form method="POST" action="/update_credentials" class="space-y-5">
                <div>
                    <label class="block text-zinc-400 text-xs font-mono uppercase mb-2 tracking-widest">Current Passkey</label>
                    <input type="password" name="current_password" required class="w-full bg-black border border-zinc-700 text-white p-3 rounded focus:border-rose-500 focus:outline-none font-mono text-sm">
                </div>
                <div class="border-t border-zinc-800/50 pt-5 space-y-5">
                    <div>
                        <label class="block text-zinc-400 text-xs font-mono uppercase mb-2 tracking-widest">New System ID</label>
                        <input type="text" name="new_username" required value="{{ session.get('user') }}" class="w-full bg-black border border-zinc-700 text-white p-3 rounded focus:border-rose-500 focus:outline-none font-mono text-sm">
                    </div>
                    <div>
                        <label class="block text-zinc-400 text-xs font-mono uppercase mb-2 tracking-widest">New Passkey</label>
                        <input type="password" name="new_password" required class="w-full bg-black border border-zinc-700 text-white p-3 rounded focus:border-rose-500 focus:outline-none font-mono text-sm">
                    </div>
                </div>
                <button type="submit" class="w-full bg-zinc-200 hover:bg-white text-black font-black py-4 rounded text-xs uppercase tracking-widest transition mt-6">
                    Commit Changes
                </button>
            </form>
        </div>
        {% endif %}
    </main>
    
    <footer class="mt-auto py-5 text-center border-t border-zinc-900/50 bg-black/20 backdrop-blur-sm relative z-10">
        <p class="text-zinc-600 text-[10px] font-mono tracking-[0.2em] uppercase">© 2026 Created By Shreesh Santoshkumar Rolli</p>
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
    flash("Authentication Rejected: Invalid ID or Passkey.")
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
        request.method = 'POST' 
        
    if request.method == 'POST' and active_tab == 'simulator':
        try:
            if not preset:
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

            vt = inputs['vt_input']
            pip = inputs['pip']
            pplat = inputs['pplat']
            peep = inputs['peep']
            flow_lmin = inputs['peak_flow']
            peco2 = inputs['peco2']
            cao2 = inputs['cao2']
            cco2 = inputs['cco2']
            cvo2 = inputs['cvo2']
            hco3_input = inputs['hco3_input']
            rr = max(1.0, inputs['rr'])
            ie = max(0.1, inputs['ie_ratio'])
            vco2 = inputs['vco2']
            fio2_val = inputs['fio2']

            # 1. Compliance
            driving_pressure = max(1.0, pplat - peep)
            compliance = vt / driving_pressure
            
            # 2. Airway Resistance
            flow_lsec = max(5.0, flow_lmin) / 60.0
            resistance = (pip - pplat) / flow_lsec
            
            # 3. Dead Space Fraction
            min_vent_est = (vt * rr) / 1000.0
            paco2_derived = round((0.863 * vco2) / (min_vent_est * 0.75), 1)
            if peco2 >= paco2_derived: 
                peco2 = paco2_derived - 4.0
            vd_vt_ratio = (paco2_derived - peco2) / paco2_derived
            vd_vt_pct = round(vd_vt_ratio * 100, 1)

            # 4. Shunt Fraction
            shunt_denominator = cco2 - cvo2
            if shunt_denominator <= 0: 
                shunt_denominator = 5.0
            shunt_ratio = (cco2 - cao2) / shunt_denominator
            shunt_pct = round(max(0.01, min(0.95, shunt_ratio)) * 100, 1)

            # Circuit execution maps
            alv_vent = ((vt * (1 - vd_vt_ratio)) * rr) / 1000.0
            paco2 = round((0.863 * vco2) / max(0.1, alv_vent), 1)
            p_A_O2 = round(((760 - 47) * (fio2_val / 100.0)) - (paco2 / 0.8), 1)
            pao2 = round(max(30, p_A_O2 - (shunt_pct * 12)), 1)
            aa_gradient = round(p_A_O2 - pao2, 1)
            mech_power = round(0.098 * rr * (vt / 1000.0) * (pip - (driving_pressure / 2)), 1)
            
            # --- SPIROMETRY MODELLING LOGIC ENGINE ---
            # Set structural theoretical Forced Vital Capacity constants based on scenario data
            if compliance <= 30: # Restrictive disease context
                fvc_vol = 2.4
                decay_constant = 2.2 # Rapid opening, small ceiling volume
                spirometry_eval = "Restrictive Curve Pattern: Preserved proportional FEV1/FVC ratio alongside marked baseline losses in total Forced Vital Capacity volumes."
            elif resistance >= 25: # Obstructive disease context
                fvc_vol = 4.5
                decay_constant = 0.55 if resistance >= 30 else 0.72 # Long drawn out exhalation curves
                spirometry_eval = "Obstructive Curve Pattern: Scooped expiratory tracing present. Marked deceleration of mid-expiratory flows, dropping total ratio clearly below normal clinical targets."
            else: # Normal health context
                fvc_vol = 5.0
                decay_constant = 1.65
                spirometry_eval = "Unremarkable Spirometry Curve: Forced Expiratory Volume metrics track cleanly above threshold values. Airway dimensions are pristine."

            # Calculate dynamic volumes at t=1.0s and t=6.0s (FVC total duration profile)
            fev1_vol = round(fvc_vol * (1.0 - math.exp(-decay_constant * 1.0)), 2)
            fvc_vol_realized = round(fvc_vol * (1.0 - math.exp(-decay_constant * 6.0)), 2)
            fev1_fvc_pct = round((fev1_vol / fvc_vol_realized) * 100, 1)

            # Differential classifications
            ai_condition = "Physiologically Normal Lung Baseline"
            ai_intervention = "Normal values across all quadrants. Standard settings map normal blood gasses."
            differentials = ["Healthy Control Context"]

            if compliance <= 30 and shunt_pct >= 20:
                ai_condition = "Severe Restrictive Defect with Intrapulmonary Shunting"
                ai_intervention = "CRITICAL: Lung-protective ventilation active. Vt limited to 4-6 mL/kg PBW. Elevate PEEP profile to recover shunt alveoli collapse structural regions."
                differentials = ["Severe ARDS", "Bilateral Infiltrates", "Sepsis Shock Inundation"]
            elif resistance >= 25 and compliance >= 75:
                ai_condition = "High-Compliance Obstructive Disease Profile"
                ai_intervention = "DANGER: Airway auto-peep trapping vector active. Drop respiratory frequency inputs and lengthen exhalation window constraints safely."
                differentials = ["COPD Exacerbation", "Emphysema Air-Trapping Matrix"]
            elif resistance >= 30 and compliance < 75:
                ai_condition = "Acute Severe Reactive Airway Bronchospasm"
                ai_intervention = "Airway path resistance is heavily restrictive. Deliver direct bronchodilation therapeutics. Alter ventilation setting variables to expand expiratory cycle space."
                differentials = ["Status Asthmaticus Attack", "Anaphylaxis Spasmodic Airway Closure"]

            # Henderson Hasselbalch
            try: ph = round(6.1 + math.log10(hco3_input / (0.0301 * paco2)), 2)
            except Exception: ph = 7.40
            
            acid_base_status = "Normal Balance"
            acid_base_delta_text = "System homeostatically stable. No clinical intervention requested."
            
            if ph < 7.35:
                if paco2 > 45:
                    acid_base_status = "Respiratory Acidosis"
                    acid_base_delta_text = "Acute retention of CO2 causing acidemia. Increase minute ventilation or respiratory rate."
                else:
                    acid_base_status = "Metabolic Acidosis"
                    acid_base_delta_text = "Serum bicarbonate depletion. Check anion gap status."
            elif ph > 7.45:
                if paco2 < 35:
                    acid_base_status = "Respiratory Alkalosis"
                    acid_base_delta_text = "Alveolar hyperventilation causing systemic alkalemia."
                else:
                    acid_base_status = "Metabolic Alkalosis"
                    acid_base_delta_text = "Elevated metabolic bicarbonate accumulation."

            # Render wave loops
            t_cycle = 60.0 / rr
            t_i = t_cycle * (1 / (1 + ie))
            t_e = t_cycle - t_i
            tau = (resistance / 1000.0) * compliance
            auto_peep_risk = "HIGH" if t_e < (3.0 * tau) else "LOW"

            t_pts, p_pts, v_pts, f_pts = [], [], [], []
            res = 100
            for i in range(res + 1):
                t = (i / res) * t_cycle
                t_pts.append(round(t, 3))
                if t <= t_i:
                    p_pts.append(round(pip, 1))
                    v_pts.append(round(vt * (1 - math.exp(-t / max(0.01, tau))), 1))
                    f_pts.append(round(((vt / max(0.01, tau)) * math.exp(-t / max(0.01, tau))), 1) * 0.06)
                else:
                    t_exp = t - t_i
                    p_pts.append(round(peep, 1))
                    v_pts.append(round(vt * math.exp(-t_exp / max(0.01, tau)), 1))
                    f_pts.append(round(-((vt / max(0.01, tau)) * math.exp(-t_exp / max(0.01, tau))), 1) * 0.06)
            
            # Formulate coordinates array specifically mapping the Spirogram curve loop
            spiro_t_pts, spiro_v_pts = [], []
            for step in range(61):
                s_t = step * 0.1
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
    flash("Demo Architecture Configuration Blocked.")
    return redirect(url_for('dashboard', tab='settings'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
