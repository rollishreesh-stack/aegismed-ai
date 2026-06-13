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
        border: 1px solid rgba(225, 29, 72, 0.15);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8);
        position: relative;
        z-index: 10;
    }
    .glass-header {
        background: rgba(9, 9, 11, 0.9);
        backdrop-filter: blur(24px);
        border-bottom: 1px solid rgba(225, 29, 72, 0.2);
        position: relative;
        z-index: 50;
    }
    
    /* Systematic Sidebar Styling */
    .input-group {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(63, 63, 70, 0.5);
        border-radius: 0.5rem;
        padding: 0.75rem;
        transition: all 0.2s;
    }
    .input-group:focus-within {
        border-color: #e11d48;
        background: rgba(225, 29, 72, 0.05);
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
<body class="flex flex-col items-center justify-center h-screen antialiased">
    <div class="glass-panel p-10 rounded-2xl w-full max-w-md border-t-4 border-t-rose-600 shadow-[0_0_50px_rgba(225,29,72,0.15)] relative z-10">
        <div class="text-center mb-10">
            <h1 class="text-4xl font-black tracking-tight text-white">AERO<span class="text-rose-600">LUNG</span></h1>
            <p class="text-rose-400 text-xs mt-2 font-mono uppercase tracking-[0.3em]">Premium Clinical Matrix</p>
        </div>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="p-3 rounded mb-6 text-xs font-mono text-center bg-rose-950/50 text-rose-300 border border-rose-800">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        <form method="POST" action="/login" class="space-y-6">
            <div class="input-group">
                <label class="block text-zinc-400 text-[10px] font-mono uppercase tracking-widest mb-1">System ID</label>
                <input type="text" name="username" required class="w-full bg-transparent text-white focus:outline-none font-mono text-sm">
            </div>
            <div class="input-group">
                <label class="block text-zinc-400 text-[10px] font-mono uppercase tracking-widest mb-1">Access Passkey</label>
                <input type="password" name="password" required class="w-full bg-transparent text-white focus:outline-none font-mono text-sm">
            </div>
            <button type="submit" class="w-full bg-rose-700 hover:bg-rose-600 text-white font-bold py-4 rounded-lg text-xs uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(225,29,72,0.3)] transition mt-4">
                Authenticate Session
            </button>
        </form>
    </div>
    
    <div class="mt-8 text-center relative z-10">
        <p class="text-[9px] text-zinc-600 font-mono tracking-[0.3em] uppercase">© 2026 Created By</p>
        <p class="text-[10px] text-rose-500/70 font-mono font-bold tracking-[0.2em] mt-1 uppercase">Shreesh Santoshkumar Rolli</p>
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
    <title>AeroLung | Enterprise Telemetry</title>
</head>
<body class="min-h-screen flex flex-col">
    <nav class="glass-header px-6 py-4 flex justify-between items-center sticky top-0">
        <div class="flex items-center space-x-4">
            <div class="relative flex items-center justify-center w-8 h-8 rounded-md bg-rose-950 border border-rose-800">
                <span class="w-2 h-2 bg-rose-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(244,63,94,1)]"></span>
            </div>
            <span class="font-black text-2xl tracking-widest text-white">AERO<span class="text-rose-600">LUNG</span> <span class="text-zinc-500 font-mono text-xs ml-2 tracking-normal border border-zinc-700 px-2 py-0.5 rounded">ENTERPRISE</span></span>
        </div>
        
        <div class="flex items-center space-x-6">
            <div class="hidden md:block text-right pr-4 border-r border-zinc-800">
                <span class="text-rose-400 font-bold block text-sm">{{ user_role }}</span>
                <span class="text-[10px] text-zinc-500 uppercase font-mono tracking-widest">Authorized</span>
            </div>
            
            <div class="relative group z-50">
                <button class="flex items-center gap-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 px-4 py-2.5 rounded-lg shadow-lg transition font-mono text-xs text-white uppercase tracking-wider">
                    <svg class="w-4 h-4 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
                    Menu
                </button>
                <div class="absolute right-0 mt-2 w-56 bg-zinc-950/95 backdrop-blur-xl border border-zinc-800 rounded-lg shadow-[0_20px_50px_rgba(0,0,0,0.9)] opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 transform origin-top-right scale-95 group-hover:scale-100 overflow-hidden">
                    <div class="p-4 border-b border-zinc-800/50 bg-zinc-900/30">
                        <span class="block text-[10px] text-zinc-500 uppercase font-mono mb-1">Active User</span>
                        <span class="block text-white font-bold truncate">{{ session.get('user') }}</span>
                    </div>
                    <a href="?tab=simulator" class="flex items-center px-4 py-3 text-xs font-mono text-zinc-300 hover:text-white hover:bg-rose-950/40 border-l-2 border-transparent hover:border-rose-600 transition-all">
                        <svg class="w-4 h-4 mr-3 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                        Telemetry Matrix
                    </a>
                    <a href="?tab=settings" class="flex items-center px-4 py-3 text-xs font-mono text-zinc-300 hover:text-white hover:bg-rose-950/40 border-l-2 border-transparent hover:border-rose-600 transition-all">
                        <svg class="w-4 h-4 mr-3 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                        System Config
                    </a>
                    <div class="border-t border-zinc-800"></div>
                    <a href="/logout" class="flex items-center px-4 py-3 text-xs font-mono text-zinc-400 hover:text-white hover:bg-zinc-800 transition-all">
                        <svg class="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                        Secure Logout
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <main class="flex-1 p-6 relative w-full max-w-[1900px] mx-auto z-10">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
            <div class="max-w-2xl mx-auto mb-6 p-4 rounded-lg text-sm font-mono text-center bg-rose-950/80 text-rose-200 border border-rose-800 backdrop-blur-sm">
                {{ messages[0] }}
            </div>
            {% endif %}
        {% endwith %}

        {% if active_tab == 'simulator' %}
        <div class="grid grid-cols-1 xl:grid-cols-12 gap-6">
            
            <div class="xl:col-span-3">
                <div class="glass-panel rounded-xl flex flex-col h-full border-t-4 border-t-rose-600 overflow-hidden min-h-[700px]">
                    <div class="p-5 border-b border-zinc-800/80 bg-zinc-900/50 flex items-center">
                        <svg class="w-5 h-5 text-rose-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
                        <div>
                            <h2 class="text-sm font-bold text-white uppercase tracking-widest">Parameter Config</h2>
                            <p class="text-[9px] text-zinc-500 font-mono mt-1">SYSTEMATIC INPUT MATRIX</p>
                        </div>
                    </div>
                    
                    <form method="POST" action="/dashboard?tab=simulator" class="p-5 space-y-6 flex-1 overflow-y-auto">
                        
                        <div>
                            <div class="flex items-center mb-3">
                                <span class="w-1.5 h-1.5 rounded-full bg-rose-500 mr-2"></span>
                                <span class="text-[10px] text-zinc-300 font-bold uppercase tracking-[0.1em]">Patient Mechanics</span>
                            </div>
                            <div class="grid grid-cols-2 gap-3">
                                <div class="input-group">
                                    <label class="block text-zinc-500 text-[9px] font-mono mb-1 uppercase">Compliance</label>
                                    <input type="number" step="0.1" name="compliance" value="{{ inputs.compliance if inputs else '60.0' }}" class="w-full bg-transparent text-white text-xs font-mono focus:outline-none">
                                </div>
                                <div class="input-group">
                                    <label class="block text-zinc-500 text-[9px] font-mono mb-1 uppercase">Resistance</label>
                                    <input type="number" step="1" name="resistance" value="{{ inputs.resistance if inputs else '10' }}" class="w-full bg-transparent text-white text-xs font-mono focus:outline-none">
                                </div>
                                <div class="input-group">
                                    <label class="block text-zinc-500 text-[9px] font-mono mb-1 uppercase">Dead Space %</label>
                                    <input type="number" step="1" name="vd_vt" value="{{ inputs.vd_vt if inputs else '30' }}" class="w-full bg-transparent text-white text-xs font-mono focus:outline-none">
                                </div>
                                <div class="input-group">
                                    <label class="block text-zinc-500 text-[9px] font-mono mb-1 uppercase">Shunt %</label>
                                    <input type="number" step="1" name="shunt" value="{{ inputs.shunt if inputs else '5' }}" class="w-full bg-transparent text-white text-xs font-mono focus:outline-none">
                                </div>
                            </div>
                        </div>

                        <div class="pt-2 border-t border-zinc-800/50">
                            <div class="flex items-center mb-3 mt-2">
                                <span class="w-1.5 h-1.5 rounded-full bg-zinc-400 mr-2"></span>
                                <span class="text-[10px] text-zinc-300 font-bold uppercase tracking-[0.1em]">Ventilator Drive</span>
                            </div>
                            <div class="grid grid-cols-2 gap-3">
                                <div class="input-group">
                                    <label class="block text-zinc-500 text-[9px] font-mono mb-1 uppercase">PIP (cmH2O)</label>
                                    <input type="number" step="1" name="pip" value="{{ inputs.pip if inputs else '15' }}" class="w-full bg-transparent text-white text-xs font-mono focus:outline-none">
                                </div>
                                <div class="input-group">
                                    <label class="block text-zinc-500 text-[9px] font-mono mb-1 uppercase">PEEP (cmH2O)</label>
                                    <input type="number" step="1" name="peep" value="{{ inputs.peep if inputs else '5' }}" class="w-full bg-transparent text-white text-xs font-mono focus:outline-none">
                                </div>
                                <div class="input-group">
                                    <label class="block text-zinc-500 text-[9px] font-mono mb-1 uppercase">Rate (bpm)</label>
                                    <input type="number" step="1" name="rr" value="{{ inputs.rr if inputs else '16' }}" class="w-full bg-transparent text-white text-xs font-mono focus:outline-none">
                                </div>
                                <div class="input-group">
                                    <label class="block text-zinc-500 text-[9px] font-mono mb-1 uppercase">FiO2 (%)</label>
                                    <input type="number" step="1" name="fio2" value="{{ inputs.fio2 if inputs else '40' }}" class="w-full bg-transparent text-white text-xs font-mono focus:outline-none">
                                </div>
                                <div class="input-group col-span-2 flex items-center justify-between">
                                    <div class="w-1/2 pr-2">
                                        <label class="block text-zinc-500 text-[9px] font-mono mb-1 uppercase">I:E Ratio</label>
                                        <input type="number" step="0.1" name="ie_ratio" value="{{ inputs.ie_ratio if inputs else '2.0' }}" class="w-full bg-transparent text-white text-xs font-mono focus:outline-none">
                                    </div>
                                    <div class="w-1/2 pl-2 border-l border-zinc-700">
                                        <label class="block text-zinc-500 text-[9px] font-mono mb-1 uppercase">VCO2</label>
                                        <input type="number" step="10" name="vco2" value="{{ inputs.vco2 if inputs else '200' }}" class="w-full bg-transparent text-white text-xs font-mono focus:outline-none">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <button type="submit" class="w-full bg-gradient-to-r from-rose-800 to-rose-600 hover:from-rose-700 hover:to-rose-500 text-white font-black py-4 rounded-lg text-xs uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(225,29,72,0.3)] transition-all mt-4 border border-rose-500/50">
                            Execute Telemetry
                        </button>
                    </form>
                    
                    <div class="p-4 border-t border-zinc-800/80 bg-zinc-950/80 text-center">
                        <p class="text-[8px] text-zinc-600 font-mono tracking-[0.2em] uppercase">© 2026 Created by</p>
                        <p class="text-[9px] text-rose-500/70 font-mono font-bold tracking-widest mt-1 uppercase">Shreesh Santoshkumar Rolli</p>
                    </div>
                </div>
            </div>

            <div class="xl:col-span-9 flex flex-col gap-6">
                {% if not sim_data %}
                <div class="glass-panel flex-1 rounded-xl flex flex-col items-center justify-center min-h-[700px] border border-zinc-800 border-dashed relative">
                    <svg class="w-24 h-24 text-rose-900/50 animate-pulse mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                    </svg>
                    <p class="text-sm text-zinc-500 font-mono tracking-[0.3em] uppercase">Systematic Matrix Ready for Input</p>
                </div>
                {% else %}
                
                <div class="glass-panel rounded-xl p-6 border-l-4 border-l-rose-500 bg-gradient-to-r from-rose-950/40 to-transparent">
                    <div class="flex items-start space-x-4">
                        <div class="p-3 bg-rose-950 rounded-lg border border-rose-800/50 text-rose-500 mt-1 shadow-[0_0_15px_rgba(225,29,72,0.2)]">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                        </div>
                        <div class="flex-1">
                            <h3 class="text-[10px] text-rose-500 font-bold uppercase tracking-widest mb-1">Pathological Analysis</h3>
                            <p class="text-xl font-black text-white">{{ sim_data.ai_condition }}</p>
                            
                            <div class="mt-3 flex flex-wrap gap-2 items-center">
                                <span class="text-[10px] text-zinc-400 font-bold uppercase tracking-widest mr-1">Differentials:</span>
                                {% for diff in sim_data.differentials %}
                                    <span class="px-2 py-1 bg-zinc-900/80 border border-zinc-700 rounded text-[10px] text-zinc-300 font-mono">{{ diff }}</span>
                                {% endfor %}
                            </div>

                            <div class="mt-4 text-sm text-zinc-300 border-t border-zinc-800 pt-3 font-mono">
                                <span class="text-rose-400 font-bold">Protocol Suggestion:</span> {{ sim_data.ai_intervention }}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
                    <div class="glass-panel rounded-xl p-5 border-t border-zinc-700/50 col-span-2 lg:col-span-1 border-t-rose-500">
                        <p class="text-[10px] font-mono uppercase text-zinc-400 mb-2 tracking-wider text-rose-400">Est. FEV1/FVC</p>
                        <p class="text-3xl font-black {% if sim_data.fev1_fvc < 70 %}text-red-400{% else %}text-rose-400{% endif %} font-mono">{{ sim_data.fev1_fvc }}<span class="text-sm text-zinc-500 ml-1">%</span></p>
                        <div class="mt-3 flex justify-between text-[10px] font-mono border-t border-zinc-800/80 pt-2">
                            <span class="text-zinc-500">Class:</span>
                            <span class="text-white font-bold">{{ sim_data.spirometry_class }}</span>
                        </div>
                    </div>

                    <div class="glass-panel rounded-xl p-5 border-t border-zinc-800">
                        <p class="text-[10px] font-mono uppercase text-zinc-400 mb-2 tracking-wider">Tidal Volume</p>
                        <p class="text-3xl font-black text-white font-mono">{{ sim_data.peak_volume }}<span class="text-sm text-zinc-500 ml-1">mL</span></p>
                        <div class="mt-3 flex justify-between text-[10px] font-mono border-t border-zinc-800/80 pt-2">
                            <span class="text-zinc-500">Min Vent:</span>
                            <span class="text-white font-bold">{{ sim_data.minute_vent }} L/m</span>
                        </div>
                    </div>
                    <div class="glass-panel rounded-xl p-5 border-t border-zinc-800">
                        <p class="text-[10px] font-mono uppercase text-zinc-400 mb-2 tracking-wider">Mech Power</p>
                        <p class="text-3xl font-black {% if sim_data.mech_power > 17 %}text-rose-500{% else %}text-white{% endif %} font-mono">{{ sim_data.mech_power }}<span class="text-sm text-zinc-500 ml-1">J/m</span></p>
                        <div class="mt-3 flex justify-between text-[10px] font-mono border-t border-zinc-800/80 pt-2">
                            <span class="text-zinc-500">VILI Limit:</span>
                            <span class="text-white font-bold">&lt; 17 J/m</span>
                        </div>
                    </div>
                    <div class="glass-panel rounded-xl p-5 border-t border-zinc-800">
                        <p class="text-[10px] font-mono uppercase text-zinc-400 mb-2 tracking-wider">Arterial CO2</p>
                        <p class="text-3xl font-black {% if sim_data.paco2 > 45 or sim_data.paco2 < 35 %}text-amber-400{% else %}text-white{% endif %} font-mono">{{ sim_data.paco2 }}<span class="text-sm text-zinc-500 ml-1">mmHg</span></p>
                        <div class="mt-3 flex justify-between text-[10px] font-mono border-t border-zinc-800/80 pt-2">
                            <span class="text-zinc-500">Alveolar:</span>
                            <span class="text-white font-bold">{{ sim_data.alveolar_vent }} L/m</span>
                        </div>
                    </div>
                    <div class="glass-panel rounded-xl p-5 border-t border-zinc-800">
                        <p class="text-[10px] font-mono uppercase text-zinc-400 mb-2 tracking-wider">Arterial O2</p>
                        <p class="text-3xl font-black {% if sim_data.pao2 < 60 %}text-rose-500{% else %}text-white{% endif %} font-mono">{{ sim_data.pao2 }}<span class="text-sm text-zinc-500 ml-1">mmHg</span></p>
                        <div class="mt-3 flex justify-between text-[10px] font-mono border-t border-zinc-800/80 pt-2">
                            <span class="text-zinc-500">A-a Grad:</span>
                            <span class="text-white font-bold">{{ sim_data.aa_gradient }}</span>
                        </div>
                    </div>
                </div>

                <div class="glass-panel rounded-xl p-6">
                    <h3 class="text-[10px] font-mono uppercase text-rose-500 mb-5 pb-2 border-b border-zinc-800 tracking-[0.2em] flex items-center">
                        Telemetry Waveforms
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="bg-zinc-950/50 p-3 rounded-lg border border-zinc-800/50 h-[220px]">
                            <canvas id="pressureChart"></canvas>
                        </div>
                        <div class="bg-zinc-950/50 p-3 rounded-lg border border-zinc-800/50 h-[220px]">
                            <canvas id="flowChart"></canvas>
                        </div>
                        <div class="bg-zinc-950/50 p-3 rounded-lg border border-zinc-800/50 h-[220px]">
                            <canvas id="volumeChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="glass-panel rounded-xl p-6">
                        <h3 class="text-[10px] font-mono uppercase text-zinc-400 mb-5 pb-2 border-b border-zinc-800 tracking-[0.2em]">P-V Loop Analysis</h3>
                        <div class="bg-zinc-950/50 p-4 rounded-lg border border-zinc-800/50 h-[250px]">
                            <canvas id="pvLoopChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="glass-panel rounded-xl p-6 flex flex-col justify-center space-y-4">
                        <div class="bg-zinc-900/40 border border-zinc-800/80 p-4 rounded-lg flex justify-between items-center">
                            <div>
                                <span class="text-[10px] uppercase text-zinc-300 font-bold block mb-1">Time Constant (τ)</span>
                                <p class="text-[9px] text-zinc-500 font-mono">Fill/Empty dynamics.</p>
                            </div>
                            <span class="text-xl font-mono text-white font-bold">{{ sim_data.time_const }}s</span>
                        </div>
                        <div class="bg-zinc-900/40 border border-zinc-800/80 p-4 rounded-lg flex justify-between items-center">
                            <div>
                                <span class="text-[10px] uppercase text-zinc-300 font-bold block mb-1">Auto-PEEP Risk</span>
                                <p class="text-[9px] text-zinc-500 font-mono">Based on exp. time ratio.</p>
                            </div>
                            <span class="text-xl font-mono {% if sim_data.auto_peep_risk == 'HIGH' %}text-rose-500{% else %}text-emerald-500{% endif %} font-black tracking-widest">{{ sim_data.auto_peep_risk }}</span>
                        </div>
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
                        scales: { x: { grid: { color: 'rgba(63, 63, 70, 0.2)' }, ticks: { display: false } } }
                    };

                    new Chart(document.getElementById('pressureChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.p, borderColor: '#e11d48', backgroundColor: 'rgba(225, 29, 72, 0.1)', fill: true }] },
                        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { grid: { color: 'rgba(63, 63, 70, 0.2)' }, title: { display: true, text: 'Paw (cmH2O)', font: {size: 10} } } } }
                    });

                    new Chart(document.getElementById('flowChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.f, borderColor: '#fb7185', backgroundColor: 'rgba(251, 113, 133, 0.1)', fill: true }] },
                        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { grid: { color: 'rgba(63, 63, 70, 0.2)' }, title: { display: true, text: 'Flow (L/min)', font: {size: 10} } } } }
                    });

                    new Chart(document.getElementById('volumeChart').getContext('2d'), {
                        type: 'line',
                        data: { labels: waveData.t, datasets: [{ data: waveData.v, borderColor: '#fda4af', backgroundColor: 'rgba(253, 164, 175, 0.1)', fill: true }] },
                        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { grid: { color: 'rgba(63, 63, 70, 0.2)' }, title: { display: true, text: 'Volume (mL)', font: {size: 10} } } } }
                    });

                    const pvData = waveData.p.map((p, i) => ({x: p, y: waveData.v[i]}));
                    new Chart(document.getElementById('pvLoopChart').getContext('2d'), {
                        type: 'scatter',
                        data: { datasets: [{ data: pvData, borderColor: '#e11d48', backgroundColor: 'transparent', showLine: true }] },
                        options: {
                            responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false } },
                            scales: {
                                x: { grid: { color: 'rgba(63, 63, 70, 0.2)' }, title: { display: true, text: 'Pressure (cmH2O)', font: {size: 10} } },
                                y: { grid: { color: 'rgba(63, 63, 70, 0.2)' }, title: { display: true, text: 'Volume (mL)', font: {size: 10} } }
                            }
                        }
                    });
                </script>
                {% endif %}
            </div>
        </div>
        {% endif %}
        
        {% if active_tab == 'settings' %}
        <div class="glass-panel max-w-lg mx-auto rounded-xl p-8 mt-10 border-t-4 border-t-rose-600">
            <div class="text-center mb-8">
                <h2 class="text-xl font-black text-white uppercase tracking-widest">System Configuration</h2>
                <p class="text-[10px] text-zinc-500 font-mono mt-1">UPDATE ACCESS CREDENTIALS</p>
            </div>
            
            <form method="POST" action="/update_credentials" class="space-y-6">
                <div class="input-group">
                    <label class="block text-zinc-400 text-[10px] font-mono uppercase mb-1 tracking-widest">Current Passkey <span class="text-rose-500">*</span></label>
                    <input type="password" name="current_password" required class="w-full bg-transparent text-white font-mono text-sm focus:outline-none">
                </div>
                <div class="border-t border-zinc-800/50 pt-4">
                    <div class="input-group mb-4">
                        <label class="block text-zinc-400 text-[10px] font-mono uppercase mb-1 tracking-widest">New System ID</label>
                        <input type="text" name="new_username" required value="{{ session.get('user') }}" class="w-full bg-transparent text-white font-mono text-sm focus:outline-none">
                    </div>
                    <div class="input-group">
                        <label class="block text-zinc-400 text-[10px] font-mono uppercase mb-1 tracking-widest">New Passkey</label>
                        <input type="password" name="new_password" required class="w-full bg-transparent text-white font-mono text-sm focus:outline-none">
                    </div>
                </div>
                <button type="submit" class="w-full bg-rose-700 hover:bg-rose-600 text-white font-bold py-4 rounded-lg text-xs uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(225,29,72,0.3)] transition mt-2">
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
            # Preserve role and clearance
            role = CLINICAL_DATABASE[current_user]['role']
            clearance = CLINICAL_DATABASE[current_user]['clearance']
            
            # Delete old entry and create new one
            del CLINICAL_DATABASE[current_user]
            CLINICAL_DATABASE[new_id] = {'password': new_pass, 'role': role, 'clearance': clearance}
            
            # Update active session
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
