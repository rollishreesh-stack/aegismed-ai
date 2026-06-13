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

# --- PREMIUM UI CSS & SVG ---
BASE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&family=JetBrains+Mono:wght@400;700&display=swap');
    
    body { font-family: 'Inter', sans-serif; background-color: #020617; color: #e2e8f0; overflow-x: hidden; min-height: 100vh;}
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    
    /* The Breathing Animation for the Real Lung */
    @keyframes bioBreathe {
        0% { transform: translate(-50%, -50%) scale(0.95); opacity: 0.3; filter: drop-shadow(0 0 20px rgba(14,165,233,0.2)); }
        50% { transform: translate(-50%, -50%) scale(1.08); opacity: 0.8; filter: drop-shadow(0 0 60px rgba(14,165,233,0.7)); }
        100% { transform: translate(-50%, -50%) scale(0.95); opacity: 0.3; filter: drop-shadow(0 0 20px rgba(14,165,233,0.2)); }
    }
    
    .living-lung {
        position: fixed; top: 50%; left: 50%; 
        width: 85vw; max-width: 800px; 
        z-index: 0; pointer-events: none; 
        animation: bioBreathe 4s ease-in-out infinite;
    }
    
    /* Enhanced Glassmorphism to let the lung shine through */
    .glass-panel {
        background: rgba(15, 23, 42, 0.45);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(56, 189, 248, 0.15);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        position: relative;
        z-index: 10;
    }
    .glass-header {
        background: rgba(2, 6, 23, 0.85);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(56, 189, 248, 0.2);
        position: relative;
        z-index: 50;
    }
    
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #020617; }
    ::-webkit-scrollbar-thumb { background: #0ea5e9; border-radius: 4px; }
</style>
"""

# Anatomical, neon-glowing lung design
LUNG_SVG = """
<svg class="living-lung" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="lungGlow" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.8"/>
            <stop offset="50%" stop-color="#0284c7" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="#082f49" stop-opacity="0.05"/>
        </linearGradient>
        <filter id="neonGlow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    </defs>
    <path d="M96 20 h8 v30 h-8 z" fill="#7dd3fc" filter="url(#neonGlow)"/>
    <path d="M100 50 L80 70 L83 73 L100 55 L117 73 L120 70 Z" fill="#7dd3fc" filter="url(#neonGlow)"/>
    <path d="M85 65 C 40 50, 20 90, 30 140 C 35 160, 70 170, 85 150 C 95 130, 95 90, 85 65 Z" fill="url(#lungGlow)" stroke="#38bdf8" stroke-width="0.5" filter="url(#neonGlow)"/>
    <path d="M115 65 C 160 50, 180 90, 170 140 C 165 160, 130 170, 115 150 C 110 140, 120 120, 110 100 C 105 90, 105 80, 115 65 Z" fill="url(#lungGlow)" stroke="#38bdf8" stroke-width="0.5" filter="url(#neonGlow)"/>
    <path d="M70 85 L50 95 M75 105 L55 120 M130 85 L150 95 M125 105 L145 120" stroke="#bae6fd" stroke-width="1.5" stroke-linecap="round" opacity="0.4"/>
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
<body class="flex items-center justify-center h-screen antialiased">
    <div class="glass-panel p-10 rounded-2xl w-full max-w-md border-t-4 border-t-sky-500 shadow-[0_0_50px_rgba(14,165,233,0.1)]">
        <div class="text-center mb-8">
            <h1 class="text-4xl font-black tracking-tight text-white">AERO<span class="text-sky-500">LUNG</span></h1>
            <p class="text-sky-400 text-xs mt-2 font-mono uppercase tracking-[0.3em]">Premium UI Matrix</p>
        </div>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="p-3 rounded mb-6 text-xs font-mono text-center bg-red-900/50 text-red-300 border border-red-500/50">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        <form method="POST" action="/login" class="space-y-5">
            <div>
                <label class="block text-slate-400 text-[10px] font-mono uppercase tracking-widest mb-2">System ID</label>
                <input type="text" name="username" required class="w-full p-3 rounded bg-slate-900/80 border border-slate-700 text-white focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition font-mono">
            </div>
            <div>
                <label class="block text-slate-400 text-[10px] font-mono uppercase tracking-widest mb-2">Access Passkey</label>
                <input type="password" name="password" required class="w-full p-3 rounded bg-slate-900/80 border border-slate-700 text-white focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition font-mono">
            </div>
            <button type="submit" class="w-full bg-sky-600 hover:bg-sky-400 text-white font-bold py-4 rounded text-xs uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(14,165,233,0.3)] transition mt-2">
                Initialize System
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
    <title>AeroLung | Live Matrix</title>
</head>
<body class="min-h-screen flex flex-col">
    <nav class="glass-header px-6 py-4 flex justify-between items-center sticky top-0">
        <div class="flex items-center space-x-4">
            <div class="relative flex items-center justify-center w-8 h-8 rounded-full bg-sky-900/50 border border-sky-500/50">
                <span class="w-3 h-3 bg-sky-400 rounded-full animate-pulse shadow-[0_0_15px_rgba(56,189,248,1)]"></span>
            </div>
            <span class="font-black text-2xl tracking-widest text-white">AERO<span class="text-sky-500">LUNG</span> <span class="text-slate-500 font-mono text-xs ml-2 tracking-normal">v7.0.PREMIUM</span></span>
        </div>
        
        <div class="flex items-center space-x-6">
            <div class="hidden md:block text-right pr-4 border-r border-slate-700">
                <span class="text-sky-400 font-bold block text-sm">{{ user_role }}</span>
                <span class="text-[10px] text-slate-500 uppercase font-mono tracking-widest">Active Operator</span>
            </div>
            
            <div class="relative group z-50">
                <button class="flex items-center gap-2 bg-slate-800/80 hover:bg-slate-700 border border-slate-600 px-4 py-2.5 rounded shadow-lg transition font-mono text-xs text-white uppercase tracking-wider">
                    <svg class="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
                    System Menu
                </button>
                <div class="absolute right-0 mt-2 w-56 bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-lg shadow-[0_20px_50px_rgba(0,0,0,0.8)] opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 transform origin-top-right scale-95 group-hover:scale-100 overflow-hidden">
                    <div class="p-4 border-b border-slate-800 bg-slate-800/30">
                        <span class="block text-[10px] text-slate-400 uppercase font-mono mb-1">Session ID</span>
                        <span class="block text-white font-bold truncate">{{ session.get('user') }}</span>
                    </div>
                    <a href="?tab=simulator" class="flex items-center px-4 py-3 text-xs font-mono text-slate-300 hover:text-white hover:bg-sky-900/40 border-l-2 border-transparent hover:border-sky-500 transition-all">
                        <svg class="w-4 h-4 mr-3 text-sky-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                        Live Telemetry
                    </a>
                    <a href="?tab=settings" class="flex items-center px-4 py-3 text-xs font-mono text-slate-300 hover:text-white hover:bg-sky-900/40 border-l-2 border-transparent hover:border-sky-500 transition-all">
                        <svg class="w-4 h-4 mr-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                        Node Settings
                    </a>
                    <div class="border-t border-slate-800"></div>
                    <a href="/logout" class="flex items-center px-4 py-3 text-xs font-mono text-red-400 hover:text-red-300 hover:bg-red-900/30 border-l-2 border-transparent hover:border-red-500 transition-all">
                        <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                        Abort Session
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <main class="flex-1 p-6 relative w-full max-w-[1900px] mx-auto z-10">
        {% if active_tab == 'simulator' %}
        <div class="grid grid-cols-1 xl:grid-cols-12 gap-6">
            
            <div class="xl:col-span-3">
                <div class="glass-panel rounded-xl p-6 h-full border-t-4 border-t-sky-500">
                    <div class="flex items-center mb-6 border-b border-slate-700/50 pb-3">
                        <svg class="w-5 h-5 text-sky-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
                        <h2 class="text-sm font-bold text-white uppercase tracking-widest">Input Matrix</h2>
                    </div>
                    
                    <form method="POST" action="/dashboard?tab=simulator" class="space-y-6">
                        <div class="space-y-3">
                            <span class="text-[10px] text-sky-400 font-bold uppercase tracking-[0.2em] bg-sky-900/30 border border-sky-500/30 px-2 py-1 rounded">1. Mechanics & Metabolism</span>
                            <div class="grid grid-cols-2 gap-3 pt-2">
                                <div>
                                    <label class="block text-slate-400 text-[10px] font-mono mb-1">Compliance</label>
                                    <input type="number" step="0.1" name="compliance" value="{{ inputs.compliance if inputs else '60.0' }}" class="w-full p-2.5 rounded bg-slate-900/80 border border-slate-700 text-white text-xs font-mono focus:border-sky-500 outline-none" title="mL/cmH2O">
                                </div>
                                <div>
                                    <label class="block text-slate-400 text-[10px] font-mono mb-1">Resistance</label>
                                    <input type="number" step="1" name="resistance" value="{{ inputs.resistance if inputs else '10' }}" class="w-full p-2.5 rounded bg-slate-900/80 border border-slate-700 text-white text-xs font-mono focus:border-sky-500 outline-none" title="cmH2O/L/s">
                                </div>
                                <div>
                                    <label class="block text-slate-400 text-[10px] font-mono mb-1">Dead Space %</label>
                                    <input type="number" step="1" name="vd_vt" value="{{ inputs.vd_vt if inputs else '30' }}" class="w-full p-2.5 rounded bg-slate-900/80 border border-slate-700 text-white text-xs font-mono focus:border-sky-500 outline-none">
                                </div>
                                <div>
                                    <label class="block text-slate-400 text-[10px] font-mono mb-1">Shunt %</label>
                                    <input type="number" step="1" name="shunt" value="{{ inputs.shunt if inputs else '5' }}" class="w-full p-2.5 rounded bg-slate-900/80 border border-slate-700 text-white text-xs font-mono focus:border-sky-500 outline-none">
                                </div>
                            </div>
                        </div>

                        <div class="space-y-3">
                            <span class="text-[10px] text-fuchsia-400 font-bold uppercase tracking-[0.2em] bg-fuchsia-900/30 border border-fuchsia-500/30 px-2 py-1 rounded">2. Ventilator Settings</span>
                            <div class="grid grid-cols-2 gap-3 pt-2">
                                <div>
                                    <label class="block text-slate-400 text-[10px] font-mono mb-1">PIP (cmH2O)</label>
                                    <input type="number" step="1" name="pip" value="{{ inputs.pip if inputs else '15' }}" class="w-full p-2.5 rounded bg-slate-900/80 border border-slate-700 text-white text-xs font-mono focus:border-fuchsia-500 outline-none">
                                </div>
                                <div>
                                    <label class="block text-slate-400 text-[10px] font-mono mb-1">PEEP (cmH2O)</label>
                                    <input type="number" step="1" name="peep" value="{{ inputs.peep if inputs else '5' }}" class="w-full p-2.5 rounded bg-slate-900/80 border border-slate-700 text-white text-xs font-mono focus:border-fuchsia-500 outline-none">
                                </div>
                                <div>
                                    <label class="block text-slate-400 text-[10px] font-mono mb-1">Rate (bpm)</label>
                                    <input type="number" step="1" name="rr" value="{{ inputs.rr if inputs else '16' }}" class="w-full p-2.5 rounded bg-slate-900/80 border border-slate-700 text-white text-xs font-mono focus:border-fuchsia-500 outline-none">
                                </div>
                                <div>
                                    <label class="block text-slate-400 text-[10px] font-mono mb-1">FiO2 (%)</label>
                                    <input type="number" step="1" name="fio2" value="{{ inputs.fio2 if inputs else '40' }}" class="w-full p-2.5 rounded bg-slate-900/80 border border-slate-700 text-white text-xs font-mono focus:border-fuchsia-500 outline-none">
                                </div>
                                <div>
                                    <label class="block text-slate-400 text-[10px] font-mono mb-1">I:E Ratio (1:X)</label>
                                    <input type="number" step="0.1" name="ie_ratio" value="{{ inputs.ie_ratio if inputs else '2.0' }}" class="w-full p-2.5 rounded bg-slate-900/80 border border-slate-700 text-white text-xs font-mono focus:border-fuchsia-500 outline-none">
                                </div>
                                <div>
                                    <label class="block text-slate-400 text-[10px] font-mono mb-1">Metabolic VCO2</label>
                                    <input type="number" step="10" name="vco2" value="{{ inputs.vco2 if inputs else '200' }}" class="w-full p-2.5 rounded bg-slate-900/80 border border-slate-700 text-white text-xs font-mono focus:border-fuchsia-500 outline-none">
                                </div>
                            </div>
                        </div>

                        <button type="submit" class="w-full bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white font-black py-4 rounded text-xs uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(14,165,233,0.4)] transition-all">
                            Process Matrix
                        </button>
                    </form>
                </div>
            </div>

            <div class="xl:col-span-9 flex flex-col gap-6">
                {% if not sim_data %}
                <div class="glass-panel flex-1 rounded-xl flex flex-col items-center justify-center min-h-[700px] border border-slate-700/50 border-dashed">
                    <svg class="w-20 h-20 text-sky-500/50 animate-spin mb-6" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p class="text-sm text-sky-400/80 font-mono tracking-[0.3em] uppercase">Awaiting Matrix Input...</p>
                </div>
                {% else %}
                
                <div class="glass-panel rounded-xl p-5 border-l-4 border-l-emerald-500 flex items-start space-x-4 bg-gradient-to-r from-emerald-900/20 to-transparent">
                    <div class="p-3 bg-emerald-900/40 rounded-lg border border-emerald-500/40 text-emerald-400 mt-1 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    </div>
                    <div class="flex-1">
                        <h3 class="text-[10px] text-emerald-400 font-bold uppercase tracking-widest mb-1">AI Pathological Inference Matrix</h3>
                        <p class="text-xl font-black text-white">{{ sim_data.ai_condition }}</p>
                        
                        <div class="mt-3 flex flex-wrap gap-2 items-center">
                            <span class="text-[10px] text-emerald-500 font-bold uppercase tracking-widest mr-1">Differentials:</span>
                            {% for diff in sim_data.differentials %}
                                <span class="px-2 py-1 bg-emerald-900/50 border border-emerald-500/30 rounded text-[10px] text-emerald-200 font-mono">{{ diff }}</span>
                            {% endfor %}
                        </div>

                        <div class="mt-4 text-sm text-emerald-100/80 border-t border-emerald-500/20 pt-3 font-mono">
                            <span class="text-emerald-400 font-bold">Protocol:</span> {{ sim_data.ai_intervention }}
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
                    <div class="glass-panel rounded-xl p-5 border-t border-slate-700/50 relative overflow-hidden group col-span-2 lg:col-span-1 border-t-purple-500">
                        <div class="absolute -right-6 -top-6 w-24 h-24 bg-purple-500/10 rounded-full blur-xl group-hover:bg-purple-500/20 transition"></div>
                        <p class="text-[10px] font-mono uppercase text-slate-400 mb-2 tracking-wider text-purple-400">Est. FEV1/FVC</p>
                        <p class="text-3xl font-black {% if sim_data.fev1_fvc < 70 %}text-red-400{% else %}text-purple-400{% endif %} font-mono">{{ sim_data.fev1_fvc }}<span class="text-sm text-slate-500 ml-1">%</span></p>
                        <div class="mt-3 flex justify-between text-[10px] font-mono border-t border-slate-700/50 pt-2">
                            <span class="text-slate-400">Class:</span>
                            <span class="text-purple-400 font-bold">{{ sim_data.spirometry_class }}</span>
                        </div>
                    </div>

                    <div class="glass-panel rounded-xl p-5 border-t border-slate-700/50 relative overflow-hidden group">
                        <div class="absolute -right-6 -top-6 w-24 h-24 bg-sky-500/10 rounded-full blur-xl group-hover:bg-sky-500/20 transition"></div>
                        <p class="text-[10px] font-mono uppercase text-slate-400 mb-2 tracking-wider">Tidal Volume</p>
                        <p class="text-3xl font-black text-white font-mono">{{ sim_data.peak_volume }}<span class="text-sm text-slate-500 ml-1">mL</span></p>
                        <div class="mt-3 flex justify-between text-[10px] font-mono border-t border-slate-700/50 pt-2">
                            <span class="text-slate-400">Min Vent:</span>
                            <span class="text-sky-400 font-bold">{{ sim_data.minute_vent }} L/m</span>
                        </div>
                    </div>
                    <div class="glass-panel rounded-xl p-5 border-t border-slate-700/50 relative overflow-hidden group">
                        <div class="absolute -right-6 -top-6 w-24 h-24 bg-fuchsia-500/10 rounded-full blur-xl group-hover:bg-fuchsia-500/20 transition"></div>
                        <p class="text-[10px] font-mono uppercase text-slate-400 mb-2 tracking-wider">Mech Power</p>
                        <p class="text-3xl font-black {% if sim_data.mech_power > 17 %}text-red-400{% else %}text-fuchsia-400{% endif %} font-mono">{{ sim_data.mech_power }}<span class="text-sm text-slate-500 ml-1">J/m</span></p>
                        <div class="mt-3 flex justify-between text-[10px] font-mono border-t border-slate-700/50 pt-2">
                            <span class="text-slate-400">VILI Thresh:</span>
                            <span class="text-fuchsia-400 font-bold">&lt; 17 J/m</span>
                        </div>
                    </div>
                    <div class="glass-panel rounded-xl p-5 border-t border-slate-700/50 relative overflow-hidden group">
                        <div class="absolute -right-6 -top-6 w-24 h-24 bg-amber-500/10 rounded-full blur-xl group-hover:bg-amber-500/20 transition"></div>
                        <p class="text-[10px] font-mono uppercase text-slate-400 mb-2 tracking-wider">Arterial CO2</p>
                        <p class="text-3xl font-black {% if sim_data.paco2 > 45 or sim_data.paco2 < 35 %}text-amber-400{% else %}text-white{% endif %} font-mono">{{ sim_data.paco2 }}<span class="text-sm text-slate-500 ml-1">mmHg</span></p>
                        <div class="mt-3 flex justify-between text-[10px] font-mono border-t border-slate-700/50 pt-2">
                            <span class="text-slate-400">Alveolar:</span>
                            <span class="text-amber-400 font-bold">{{ sim_data.alveolar_vent }} L/m</span>
                        </div>
                    </div>
                    <div class="glass-panel rounded-xl p-5 border-t border-slate-700/50 relative overflow-hidden group">
                        <div class="absolute -right-6 -top-6 w-24 h-24 bg-blue-500/10 rounded-full blur-xl group-hover:bg-blue-500/20 transition"></div>
                        <p class="text-[10px] font-mono uppercase text-slate-400 mb-2 tracking-wider">Arterial O2</p>
                        <p class="text-3xl font-black {% if sim_data.pao2 < 60 %}text-red-400{% else %}text-blue-400{% endif %} font-mono">{{ sim_data.pao2 }}<span class="text-sm text-slate-500 ml-1">mmHg</span></p>
                        <div class="mt-3 flex justify-between text-[10px] font-mono border-t border-slate-700/50 pt-2">
                            <span class="text-slate-400">A-a Grad:</span>
                            <span class="text-blue-400 font-bold">{{ sim_data.aa_gradient }}</span>
                        </div>
                    </div>
                </div>

                <div class="glass-panel rounded-xl p-6">
                    <h3 class="text-[10px] font-mono uppercase text-sky-400 mb-5 pb-2 border-b border-slate-700/50 tracking-[0.2em] flex items-center">
                        <span class="w-2 h-2 bg-sky-500 rounded-full mr-2 shadow-[0_0_8px_rgba(14,165,233,1)]"></span> Dynamic Waveform Telemetry
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="bg-slate-900/40 p-3 rounded-xl border border-slate-700/50 h-[220px]">
                            <canvas id="pressureChart"></canvas>
                        </div>
                        <div class="bg-slate-900/40 p-3 rounded-xl border border-slate-700/50 h-[220px]">
                            <canvas id="flowChart"></canvas>
                        </div>
                        <div class="bg-slate-900/40 p-3 rounded-xl border border-slate-700/50 h-[220px]">
                            <canvas id="volumeChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="glass-panel rounded-xl p-6">
                        <h3 class="text-[10px] font-mono uppercase text-fuchsia-400 mb-5 pb-2 border-b border-slate-700/50 tracking-[0.2em]">Pressure-Volume Mechanics</h3>
                        <div class="bg-slate-900/40 p-4 rounded-xl border border-slate-700/50 h-[300px]">
                            <canvas id="pvLoopChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="glass-panel rounded-xl p-6">
                        <h3 class="text-[10px] font-mono uppercase text-amber-400 mb-5 pb-2 border-b border-slate-700/50 tracking-[0.2em]">Kinetic Diagnostics</h3>
                        <div class="space-y-4">
                            <div class="bg-slate-900/40 border border-slate-700/50 p-4 rounded-xl flex justify-between items-center backdrop-blur-sm">
                                <div>
                                    <span class="text-[10px] uppercase text-slate-300 font-bold block mb-1">Time Constant (τ)</span>
                                    <p class="text-[10px] text-slate-500 font-mono">Time for 63% volume change.</p>
                                </div>
                                <span class="text-xl font-mono text-amber-400 font-bold">{{ sim_data.time_const }}s</span>
                            </div>
                            
                            <div class="bg-slate-900/40 border border-slate-700/50 p-4 rounded-xl flex justify-between items-center backdrop-blur-sm">
                                <div>
                                    <span class="text-[10px] uppercase text-slate-300 font-bold block mb-1">Expiratory Time (Te)</span>
                                    <p class="text-[10px] text-slate-500 font-mono">Requires 3-4 τ for complete emptying.</p>
                                </div>
                                <span class="text-xl font-mono text-white font-bold">{{ sim_data.t_e }}s</span>
                            </div>

                            <div class="bg-slate-900/40 border border-slate-700/50 p-4 rounded-xl flex justify-between items-center backdrop-blur-sm">
                                <div>
                                    <span class="text-[10px] uppercase text-slate-300 font-bold block mb-1">Auto-PEEP Risk</span>
                                    <p class="text-[10px] text-slate-500 font-mono">Based on Te vs Time Constant.</p>
                                </div>
                                <span class="text-xl font-mono {% if sim_data.auto_peep_risk == 'HIGH' %}text-red-500{% else %}text-emerald-500{% endif %} font-black tracking-widest">{{ sim_data.auto_peep_risk }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                    const waveData = {{ sim_data.waveform_data | safe }};
                    Chart.defaults.color = '#94a3b8';
                    Chart.defaults.font.family = "'JetBrains Mono', monospace";
                    Chart.defaults.elements.point.radius = 0;
                    Chart.defaults.elements.line.borderWidth = 2;
                    Chart.defaults.elements.line.tension = 0.3;
                    
                    const commonOptions = {
                        responsive: true, maintainAspectRatio: false, animation: false,
                        plugins: { legend: { display: false }, tooltip: { enabled: false } },
                        scales: { x: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, ticks: { display: false } } }
                    };

                    new Chart(document.getElementById('pressureChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.p, borderColor: '#0ea5e9', backgroundColor: 'rgba(14, 165, 233, 0.1)', fill: true }] },
                        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, title: { display: true, text: 'Paw (cmH2O)', font: {size: 10} } } } }
                    });

                    new Chart(document.getElementById('flowChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.f, borderColor: '#d946ef', backgroundColor: 'rgba(217, 70, 239, 0.1)', fill: true }] },
                        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, title: { display: true, text: 'Flow (L/min)', font: {size: 10} } } } }
                    });

                    new Chart(document.getElementById('volumeChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.v, borderColor: '#34d399', backgroundColor: 'rgba(52, 211, 153, 0.1)', fill: true }] },
                        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, title: { display: true, text: 'Volume (mL)', font: {size: 10} } } } }
                    });

                    const pvData = waveData.p.map((p, i) => ({x: p, y: waveData.v[i]}));
                    new Chart(document.getElementById('pvLoopChart').getContext('2d'), {
                        type: 'scatter',
                        data: { datasets: [{ data: pvData, borderColor: '#f59e0b', backgroundColor: 'transparent', showLine: true }] },
                        options: {
                            responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false } },
                            scales: {
                                x: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, title: { display: true, text: 'Pressure (cmH2O)', font: {size: 10} } },
                                y: { grid: { color: 'rgba(51, 65, 85, 0.3)' }, title: { display: true, text: 'Volume (mL)', font: {size: 10} } }
                            }
                        }
                    });
                </script>
                {% endif %}
            </div>
        </div>
        {% endif %}
        
        {% if active_tab == 'settings' %}
        <div class="glass-panel max-w-md mx-auto rounded-xl p-8 mt-10 border-t-4 border-t-sky-500">
            <h2 class="text-xl font-black text-white mb-6 uppercase tracking-widest text-center">Node Security</h2>
            <form method="POST" action="/update_credentials" class="space-y-5">
                <div>
                    <label class="block text-slate-400 text-[10px] font-mono uppercase mb-2 tracking-widest">Current Passkey</label>
                    <input type="password" name="current_password" required class="w-full p-3 rounded bg-slate-900/80 border border-slate-700 text-white font-mono focus:border-sky-500 outline-none">
                </div>
                <div>
                    <label class="block text-slate-400 text-[10px] font-mono uppercase mb-2 tracking-widest">New System ID</label>
                    <input type="text" name="new_username" required value="{{ session.get('user') }}" class="w-full p-3 rounded bg-slate-900/80 border border-slate-700 text-white font-mono focus:border-sky-500 outline-none">
                </div>
                <div>
                    <label class="block text-slate-400 text-[10px] font-mono uppercase mb-2 tracking-widest">New Passkey</label>
                    <input type="password" name="new_password" required class="w-full p-3 rounded bg-slate-900/80 border border-slate-700 text-white font-mono focus:border-sky-500 outline-none">
                </div>
                <button type="submit" class="w-full bg-sky-600 hover:bg-sky-400 text-white font-bold py-3 rounded text-xs uppercase tracking-[0.2em] shadow-[0_0_15px_rgba(14,165,233,0.3)] transition mt-4">Commit Overlay</button>
            </form>
        </div>
        {% endif %}
    </main>
</body>
</html>
"""

# --- BACKEND PHYSICS ENGINE & AI LOGIC ---
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
    flash("Telemetry Error: Authentication failure.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    active_tab = request.args.get('tab', 'simulator')
    sim_data = None
    inputs = None
    
    if request.method == 'POST' and active_tab == 'simulator':
        # Retrieve Raw Variables
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
        
        # --- PATHOLOGY MATRIX ---
        ai_condition = "Normal / Compensated Respiratory Mechanics"
        ai_intervention = "Maintain lung-protective strategy. Monitor driving pressure and hemodynamics."
        differentials = ["Healthy Lungs", "Post-operative monitoring", "Mild transient atelectasis"]
        
        if c <= 40 and shunt >= 0.15:
            ai_condition = "Acute Restrictive Defect with Shunt (Alveolar Filling)"
            ai_intervention = "Limit Vt to 4-6 mL/kg PBW. Optimize PEEP. Consider proning."
            differentials = ["ARDS", "Cardiogenic Pulmonary Edema", "Severe Bilateral Pneumonia", "Massive Atelectasis"]
        elif c <= 40 and r < 15 and shunt < 0.15:
            ai_condition = "Chronic / Dry Restrictive Defect"
            ai_intervention = "Target low tidal volumes. Avoid excessive PEEP which may cause overdistension and reduce venous return."
            differentials = ["Pulmonary Fibrosis", "Interstitial Lung Disease (ILD)", "Kyphoscoliosis", "Neuromuscular Weakness", "Morbid Obesity"]
        elif r >= 20 and c >= 60:
            ai_condition = "High-Compliance Obstructive Defect"
            ai_intervention = "High risk for Auto-PEEP. Prolong Te, minimize minute ventilation, allow permissive hypercapnia."
            differentials = ["COPD", "Emphysema", "Severe Bronchiectasis"]
        elif r >= 25 and c < 60:
            ai_condition = "Acute Obstructive Defect (Bronchospasm)"
            ai_intervention = "Maximize Expiratory Time (Te). Administer systemic/inhaled bronchodilators and corticosteroids."
            differentials = ["Status Asthmaticus", "Anaphylaxis", "Acute Bronchiolitis"]
        elif vd_vt >= 0.50 and c >= 45:
            ai_condition = "Vascular / Dead-Space Defect"
            ai_intervention = "Ventilation is occurring without perfusion. Assess hemodynamics immediately (CT-Angio / Echo)."
            differentials = ["Massive Pulmonary Embolism", "Severe Low Cardiac Output / Shock", "Pulmonary Hypertension"]
        elif r >= 20 and c <= 40:
            ai_condition = "Mixed Obstructive & Restrictive Defect"
            ai_intervention = "Complex mechanics. Balance PEEP to avoid worsening obstruction while preventing alveolar collapse."
            differentials = ["COPD with superimposed Pneumonia/ARDS", "Cystic Fibrosis in acute exacerbation", "Severe inhalation injury"]

        # --- CORE MECHANICS & VIRTUAL SPIROMETRY (FEV1/FVC) ---
        dp = max(0.1, pip - peep)
        peak_volume = dp * c  # in mL
        min_vent = (peak_volume * rr) / 1000.0
        alv_vent = ((peak_volume * (1 - vd_vt)) * rr) / 1000.0
        
        t_cycle = 60.0 / rr
        t_i = t_cycle * (1 / (1 + ie))
        t_e = t_cycle - t_i
        
        tau = (r / 1000.0) * c # Time constant in seconds
        auto_peep_risk = "HIGH" if t_e < (3.0 * tau) else "LOW"
        
        fev1_fvc_ratio = round((1 - math.exp(-1 / max(0.01, tau))) * 100, 1)
        if fev1_fvc_ratio >= 70:
            spirometry_class = "Restrictive/Normal"
        else:
            spirometry_class = "Obstructive"
            
        mech_power = round(0.098 * rr * (peak_volume/1000.0) * (pip - (dp/2)), 1)
        paco2 = round((0.863 * vco2) / max(0.1, alv_vent), 1)
        p_A_O2 = round(((760 - 47) * fio2) - (paco2 / 0.8), 1)
        pao2 = round(max(30, p_A_O2 - ((shunt * 100) * 12)), 1)
        aa_gradient = round(p_A_O2 - pao2, 1)
        
        # Generate Waveforms
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
