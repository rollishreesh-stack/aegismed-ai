from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import os
import math
from datetime import datetime

app = Flask(__name__)
# Production-ready configurable secret key
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_nexus_elite_quantum_2026")

# --- ENTERPRISE CLINICAL ACCESS CONTROL ---
CLINICAL_DATABASE = {
    "admin_evaluator": {
        "token": "nexus2026", 
        "role": "Chief Medical Evaluator", 
        "clearance": "Tier-3 Global Admin",
        "facility": "AeroLung Quantum Hub"
    },
    "icu_director": {
        "token": "clinical2026", 
        "role": "Director of Critical Care", 
        "clearance": "Tier-2 Clinical Supervisor",
        "facility": "Metropolitan ICU Matrix"
    }
}

# --- PREMIUM METROPOLIS UI STRINGS ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>AeroLung OS Nexus Elite | Clinical Gateway</title>
</head>
<body class="bg-[#030712] flex items-center justify-center h-screen text-slate-100 antialiased font-sans selection:bg-cyan-500/30">
    <div class="bg-[#0b1329] border border-slate-800/80 p-8 rounded-2xl shadow-2xl w-full max-w-md relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-cyan-500 via-indigo-500 to-emerald-500"></div>
        
        <div class="text-center mb-8">
            <span class="bg-cyan-500/10 text-cyan-400 text-[10px] font-mono tracking-widest uppercase px-3 py-1 rounded-full border border-cyan-500/20 shadow-inner">
                NEXUS ELITE // ENTERPRISE INFRASTRUCTURE
            </span>
            <h1 class="text-3xl font-black text-white tracking-tight mt-4">AeroLung <span class="text-cyan-400">OS Nexus</span></h1>
            <p class="text-slate-400 text-xs mt-1 font-medium">Predictive Fluid-Dynamic Ventilation Network Simulation</p>
        </div>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-3 rounded-xl mb-4 text-xs font-mono text-center">
                ⚠️ {{ messages[0] }}
            </div>
          {% endif %}
        {% endwith %}
        
        <form method="POST" action="/login" class="space-y-4">
            <div>
                <label class="block text-slate-400 text-[11px] font-mono uppercase tracking-wider mb-1.5">Clinician Identifier</label>
                <input type="text" name="username" required placeholder="e.g., admin_evaluator" class="w-full p-3 rounded-xl bg-[#111c40] border border-slate-700 text-white text-sm focus:outline-none focus:border-cyan-500 transition font-mono placeholder:text-slate-600">
            </div>
            <div>
                <label class="block text-slate-400 text-[11px] font-mono uppercase tracking-wider mb-1.5">Security Auth Token</label>
                <input type="password" name="password" required placeholder="••••••••" class="w-full p-3 rounded-xl bg-[#111c40] border border-slate-700 text-white text-sm focus:outline-none focus:border-cyan-500 transition font-mono placeholder:text-slate-600">
            </div>
            <button type="submit" class="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-3 rounded-xl text-xs uppercase tracking-widest transition shadow-lg shadow-cyan-950/50 mt-2">
                Authorize Core Initialization
            </button>
        </form>
        
        <div class="mt-6 pt-4 border-t border-slate-800/60 text-[11px] text-slate-500 font-mono">
            <p class="text-center font-bold text-slate-400 uppercase tracking-wider mb-2">Default Node Credentials</p>
            <div class="space-y-1">
                <div class="flex justify-between bg-[#070d1e] p-2 rounded-lg border border-slate-900">
                    <span>ID: <code class="text-cyan-400">admin_evaluator</code></span>
                    <span>Token: <code class="text-slate-300">nexus2026</code></span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

MASTER_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <title>AeroLung OS Nexus Elite Console</title>
</head>
<body class="bg-[#030712] text-slate-100 min-h-screen antialiased font-sans flex flex-col selection:bg-cyan-500/30">

    <nav class="bg-[#0b1329] border-b border-slate-800/80 px-6 py-4 flex justify-between items-center sticky top-0 z-50 shadow-xl">
        <div class="flex items-center space-x-3">
            <span class="w-2.5 h-2.5 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.7)]"></span>
            <span class="font-black text-lg tracking-wider text-white">AERO<span class="text-cyan-400">LUNG</span> <span class="text-slate-500 text-xs font-mono font-bold tracking-tight bg-slate-950 px-2 py-0.5 rounded-md border border-slate-800">NEXUS ELITE v4.2</span></span>
        </div>
        
        <div class="flex items-center space-x-6 text-xs font-mono">
            <div class="text-right hidden lg:block border-r border-slate-800 pr-4">
                <span class="text-slate-500 block uppercase text-[9px] tracking-wider">Synchronized Telemetry Time</span>
                <span class="text-cyan-400 font-bold" id="liveClock">{{ system_time }}</span>
            </div>
            <div class="text-right border-r border-slate-800 pr-4 hidden sm:block">
                <span class="text-slate-500 block uppercase text-[9px] tracking-wider">Active Workspace Node</span>
                <span class="text-slate-300 font-semibold">{{ session.get('facility', 'Remote Console') }}</span>
            </div>
            <div class="text-right">
                <span class="text-emerald-400 font-bold block">{{ user_role }}</span>
                <span class="text-[9px] text-slate-500 uppercase tracking-widest font-bold">{{ user_clearance }}</span>
            </div>
            <a href="/logout" class="bg-slate-950 hover:bg-rose-950/40 border border-slate-800 hover:border-rose-900/60 px-4 py-2 rounded-xl text-xs uppercase tracking-wider font-bold transition duration-200">Disconnect</a>
        </div>
    </nav>

    <div class="flex flex-1">
        <aside class="w-64 bg-[#0b1329] border-r border-slate-800/80 p-4 flex flex-col justify-between hidden md:flex">
            <div class="space-y-1.5">
                <p class="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase px-3 mb-3">Core Subsystems</p>
                
                <a href="?tab=simulation" class="flex items-center space-x-3 px-3 py-3 rounded-xl transition font-medium text-sm {% if active_tab == 'simulation' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-sm{% else %}text-slate-400 hover:bg-slate-900 hover:text-white{% endif %}">
                    <span>🌬️</span> <span>Quantum Sim Matrix</span>
                </a>
                
                <a href="?tab=registry" class="flex items-center space-x-3 px-3 py-3 rounded-xl transition font-medium text-sm {% if active_tab == 'registry' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-sm{% else %}text-slate-400 hover:bg-slate-900 hover:text-white{% endif %}">
                    <span>📋</span> <span>Global Patient Registry</span>
                </a>

                <a href="?tab=marketplace" class="flex items-center space-x-3 px-3 py-3 rounded-xl transition font-medium text-sm {% if active_tab == 'marketplace' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-sm{% else %}text-slate-400 hover:bg-slate-900 hover:text-white{% endif %}">
                    <span>💎</span> <span>AeroLung Core Market</span>
                </a>
            </div>
            
            <div class="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center">
                <p class="text-[9px] font-mono tracking-widest text-slate-500 uppercase">Licensing Architecture</p>
                <p class="text-xs font-black font-mono text-amber-400 mt-1 uppercase tracking-wider">PREMIUM ENTERPRISE</p>
            </div>
        </aside>

        <main class="flex-1 p-6 lg:p-8 overflow-y-auto">
            
            {% if active_tab == 'simulation' %}
            <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
                <div class="xl:col-span-1 bg-[#0b1329] border border-slate-800/80 rounded-2xl p-6 shadow-xl h-fit">
                    <h2 class="text-base font-bold text-white mb-1">Ventilator Telemetry Engine</h2>
                    <p class="text-xs text-slate-400 mb-6 leading-relaxed">Modify lung dynamics modeling loops via demographic-mapped physical presets.</p>
                    
                    <form method="POST" action="/dashboard?tab=simulation" class="space-y-4">
                        <div>
                            <label class="block text-slate-400 text-[11px] font-mono uppercase tracking-wider mb-1.5">Demographic Target Profile</label>
                            <select name="profile_class" id="profile_class" onchange="applyProfilePresets()" class="w-full p-3 rounded-xl bg-[#111c40] border border-slate-700 text-white text-sm focus:outline-none focus:border-cyan-500 transition font-mono">
                                <option value="neonatal" {% if profile_class == 'neonatal' %}selected{% endif %}>NEONATAL (Surfactant Deficient Loop)</option>
                                <option value="pediatric" {% if profile_class == 'pediatric' %}selected{% endif %}>PEDIATRIC (Bronchospasm Pathogen)</option>
                                <option value="adult" {% if profile_class == 'adult' %}selected{% endif %}>ADULT (Severe Infiltration ARDS)</option>
                            </select>
                        </div>
                        <div>
                            <div class="flex justify-between items-center mb-1.5">
                                <label class="block text-slate-400 text-[11px] font-mono uppercase tracking-wider">Peak Inspiratory Pressure ($PIP$)</label>
                                <span class="text-[10px] font-mono text-cyan-400">cmH2O</span>
                            </div>
                            <input type="number" id="pip" name="pip" value="{{ inputs.pip if inputs else '24' }}" min="10" max="50" class="w-full p-3 rounded-xl bg-[#111c40] border border-slate-700 text-sm text-white focus:outline-none focus:border-cyan-500 transition font-mono">
                        </div>
                        <div>
                            <div class="flex justify-between items-center mb-1.5">
                                <label class="block text-slate-400 text-[11px] font-mono uppercase tracking-wider">Dynamic Compliance ($C_{dyn}$)</label>
                                <span class="text-[10px] font-mono text-cyan-400">mL/cmH2O</span>
                            </div>
                            <input type="number" step="0.1" id="compliance" name="compliance" value="{{ inputs.compliance if inputs else '3.0' }}" min="0.5" max="100.0" class="w-full p-3 rounded-xl bg-[#111c40] border border-slate-700 text-sm text-white focus:outline-none focus:border-cyan-500 transition font-mono">
                        </div>
                        <div>
                            <div class="flex justify-between items-center mb-1.5">
                                <label class="block text-slate-400 text-[11px] font-mono uppercase tracking-wider">Airway Resistance ($R_{aw}$)</label>
                                <span class="text-[10px] font-mono text-cyan-400">cmH2O/L/s</span>
                            </div>
                            <input type="number" id="resistance" name="resistance" value="{{ inputs.resistance if inputs else '45' }}" min="2" max="200" class="w-full p-3 rounded-xl bg-[#111c40] border border-slate-700 text-sm text-white focus:outline-none focus:border-cyan-500 transition font-mono">
                        </div>
                        <div>
                            <div class="flex justify-between items-center mb-1.5">
                                <label class="block text-slate-400 text-[11px] font-mono uppercase tracking-wider">Set PEEP Vector</label>
                                <span class="text-[10px] font-mono text-cyan-400">cmH2O</span>
                            </div>
                            <input type="number" id="peep" name="peep" value="{{ inputs.peep if inputs else '5' }}" min="0" max="25" class="w-full p-3 rounded-xl bg-[#111c40] border border-slate-700 text-sm text-white focus:outline-none focus:border-cyan-500 transition font-mono">
                        </div>
                        <button type="submit" class="w-full bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-bold py-3 rounded-xl text-xs uppercase tracking-widest transition shadow-lg mt-2">
                            Compute Advanced Telemetry Loop
                        </button>
                    </form>
                </div>

                <div class="xl:col-span-2 space-y-6">
                    {% if not sim_data %}
                    <div class="bg-[#0b1329]/30 border border-slate-800 border-dashed rounded-2xl p-16 text-center flex flex-col items-center justify-center min-h-[450px]">
                        <div class="text-4xl mb-4 opacity-70 animate-bounce">🌬️</div>
                        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest font-mono">Mathematical Processor Idle</h3>
                        <p class="text-xs text-slate-500 max-w-xs mt-2 mx-auto leading-relaxed">Choose a patient profile dynamic and trigger the loop processing core to project advanced airway analytics charting records.</p>
                    </div>
                    {% else %}
                    
                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div class="bg-[#0b1329] border border-slate-800 rounded-2xl p-5 shadow-md">
                            <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Target Archetype</p>
                            <p class="text-xl font-black font-mono text-cyan-400 uppercase tracking-tight">{{ profile_class }} Class</p>
                        </div>
                        <div class="bg-[#0b1329] border border-slate-800 rounded-2xl p-5 shadow-md">
                            <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Dynamic Tidal Volume ($V_t$)</p>
                            <p class="text-2xl font-black font-mono text-indigo-400 tracking-tight">{{ sim_data.peak_volume }} mL</p>
                        </div>
                        <div class="bg-[#0b1329] border border-slate-800 rounded-2xl p-5 shadow-md">
                            <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Safety Risk Evaluation</p>
                            <p class="text-xs font-bold font-mono py-0.5 {% if 'CRITICAL' in sim_data.risk_status or 'HIGH' in sim_data.risk_status %}text-rose-400 animate-pulse{% else %}text-emerald-400{% endif %}">
                                🛡️ {{ sim_data.risk_status }}
                            </p>
                        </div>
                    </div>

                    <div class="bg-[#0b1329] border border-slate-800 rounded-2xl p-6 shadow-lg">
                        <div class="flex justify-between items-center mb-4 pb-2 border-b border-slate-800/60">
                            <h3 class="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold">Dynamic Alveolar Pressure Ascent Curve ($P_{alv}(t)$)</h3>
                            <span class="text-[10px] font-mono text-slate-500">Inspiratory Delta Time (0.5s)</span>
                        </div>
                        <div class="h-64"><canvas id="waveformChart"></canvas></div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="bg-[#0b1329] border border-slate-800 rounded-2xl p-5 shadow-md">
                            <h3 class="text-xs font-mono uppercase tracking-wider text-slate-400 mb-3 border-b border-slate-800 pb-2 font-bold">📋 Case Demographics Narrative</h3>
                            <p class="text-xs text-slate-300 leading-relaxed font-mono">
                                {{ sim_data.case_description }}
                            </p>
                        </div>
                        <div class="bg-[#0b1329] border border-cyan-950 rounded-2xl p-5 bg-gradient-to-br from-[#0b1329] to-[#04161a] shadow-md border-l-4 border-l-cyan-500">
                            <h3 class="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-3 border-b border-cyan-900/60 pb-2 font-bold">🩺 Automation Advisory Directives</h3>
                            <p class="text-xs text-cyan-300 leading-relaxed font-mono">
                                {{ sim_data.advice_note }}
                            </p>
                        </div>
                    </div>

                    <script>
                        const ctx = document.getElementById('waveformChart').getContext('2d');
                        new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: {{ sim_data.time_points | tojson }},
                                datasets: [{
                                    label: 'Alveolar Pressure Curve (cmH2O)',
                                    data: {{ sim_data.pressure_points | tojson }},
                                    borderColor: 'rgb(34, 211, 238)',
                                    backgroundColor: 'rgba(34, 211, 238, 0.03)',
                                    borderWidth: 2.5,
                                    pointRadius: 3,
                                    pointBackgroundColor: 'rgb(99, 102, 241)',
                                    fill: true,
                                    tension: 0.2
                                }]
                            },
                            options: { 
                                responsive: true, 
                                maintainAspectRatio: false, 
                                plugins: { legend: { display: false } }, 
                                scales: { 
                                    x: { grid: { color: '#111c40' }, ticks: { color: '#64748b', font: { family: 'monospace' } } }, 
                                    y: { grid: { color: '#111c40' }, ticks: { color: '#64748b', font: { family: 'monospace' } } } 
                                } 
                            }
                        });
                    </script>
                    {% endif %}
                </div>
            </div>
            {% endif %}

            {% if active_tab == 'registry' %}
            <div class="bg-[#0b1329] border border-slate-800 rounded-2xl p-6 shadow-xl animate-fadeIn">
                <div class="flex justify-between items-center mb-6 border-b border-slate-800 pb-4">
                    <div>
                        <h2 class="text-lg font-bold text-white tracking-tight">Cross-Demographic ICU Register</h2>
                        <p class="text-xs text-slate-400 mt-0.5">Enterprise tracking repository linking live physical matrices to anonymized target parameters.</p>
                    </div>
                </div>
                
                <div class="overflow-x-auto rounded-xl border border-slate-800">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-slate-800 text-xs text-slate-400 font-mono uppercase bg-slate-900/50">
                                <th class="p-4">Anonymized Matrix ID</th>
                                <th class="p-4">Demographic Stratification Vector</th>
                                <th class="p-4">Assigned Deployment Hub</th>
                                <th class="p-4">Target Compliance Index</th>
                                <th class="p-4">System Status Node</th>
                            </tr>
                        </thead>
                        <tbody class="text-xs font-mono divide-y divide-slate-800/40">
                            <tr class="hover:bg-slate-900/40 transition">
                                <td class="p-4 text-white font-bold tracking-wider">#NEX-NEO-01</td>
                                <td class="p-4 text-slate-300">Infant Clinical Phenotype A</td>
                                <td class="p-4 text-slate-400">NICU Hyperbaric Pod-2</td>
                                <td class="p-4 text-cyan-400">1.8 mL/cmH2O</td>
                                <td class="p-4"><span class="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-md font-bold text-[10px]">STEADY LOGICAL FLOW</span></td>
                            </tr>
                            <tr class="hover:bg-slate-900/40 transition">
                                <td class="p-4 text-white font-bold tracking-wider">#NEX-PED-04</td>
                                <td class="p-4 text-slate-300">Juvenile Asthma Phenotype B</td>
                                <td class="p-4 text-slate-400">Pediatric High-Care Suite-9</td>
                                <td class="p-4 text-cyan-400">14.2 mL/cmH2O</td>
                                <td class="p-4"><span class="px-2.5 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-md font-bold text-[10px]">DYNAMIC BALANCING</span></td>
                            </tr>
                            <tr class="hover:bg-slate-900/40 transition">
                                <td class="p-4 text-white font-bold tracking-wider">#NEX-ADU-11</td>
                                <td class="p-4 text-slate-300">Adult Trauma ARDS Phenotype F</td>
                                <td class="p-4 text-slate-400">Main Trauma Resuscitation Bay-1</td>
                                <td class="p-4 text-cyan-400">38.5 mL/cmH2O</td>
                                <td class="p-4"><span class="px-2.5 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-md font-bold text-[10px] animate-pulse">OVERDISTENSION RISK</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            {% endif %}

            {% if active_tab == 'marketplace' %}
            <div class="space-y-6 animate-fadeIn">
                <div class="bg-[#0b1329] border border-slate-800 rounded-2xl p-6 shadow-xl">
                    <h2 class="text-xl font-bold text-white tracking-tight">AeroLung Enterprise Core Market</h2>
                    <p class="text-xs text-slate-400 mt-1">Upgrade local system telemetry nodes with modular plugins, artificial intelligence overlays, and advanced physical hardware simulations.</p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="bg-[#0b1329] border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-md relative overflow-hidden group hover:border-slate-700 transition">
                        <div>
                            <div class="flex justify-between items-start mb-4">
                                <span class="p-3 bg-cyan-500/10 text-cyan-400 rounded-xl text-xl">🧠</span>
                                <span class="bg-cyan-500/10 text-cyan-400 text-[9px] font-bold uppercase tracking-widest font-mono px-2 py-0.5 rounded border border-cyan-500/20">Telemetry Alpha</span>
                            </div>
                            <h3 class="text-sm font-bold text-white mb-1.5 font-mono">Neural Predictive Weave</h3>
                            <p class="text-xs text-slate-400 leading-relaxed font-mono">Injects real-time predictive algorithm tracks to instantly counteract dynamic resistance spikes before barotrauma manifests.</p>
                        </div>
                        <button class="w-full bg-slate-950 border border-slate-800 text-slate-400 font-bold py-2.5 rounded-xl text-[11px] font-mono uppercase tracking-wider mt-6 cursor-not-allowed">
                            Node Implemented
                        </button>
                    </div>

                    <div class="bg-[#0b1329] border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-md relative overflow-hidden group hover:border-cyan-500/40 transition">
                        <div class="absolute top-0 right-0 bg-cyan-600 text-white font-black text-[8px] font-mono tracking-widest uppercase px-3 py-1 rounded-bl-xl shadow-md">UPGRADE</div>
                        <div>
                            <div class="flex justify-between items-start mb-4">
                                <span class="p-3 bg-indigo-500/10 text-indigo-400 rounded-xl text-xl">🫁</span>
                                <span class="bg-indigo-500/10 text-indigo-400 text-[9px] font-bold uppercase tracking-widest font-mono px-2 py-0.5 rounded border border-indigo-500/20">Physics Beta</span>
                            </div>
                            <h3 class="text-sm font-bold text-white mb-1.5 font-mono">Multi-Compartment Lung Matrix</h3>
                            <p class="text-xs text-slate-400 leading-relaxed font-mono">Expands simple mathematical compliance into single-alveoli dependent asynchronous tissue models for targeted regional analysis.</p>
                        </div>
                        <button class="w-full bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-bold py-2.5 rounded-xl text-[11px] font-mono uppercase tracking-wider mt-6 shadow transition">
                            Procure Node License
                        </button>
                    </div>

                    <div class="bg-[#0b1329] border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-md relative overflow-hidden group hover:border-amber-500/40 transition">
                        <div>
                            <div class="flex justify-between items-start mb-4">
                                <span class="p-3 bg-amber-500/10 text-amber-400 rounded-xl text-xl">📡</span>
                                <span class="bg-amber-500/10 text-amber-400 text-[9px] font-bold uppercase tracking-widest font-mono px-2 py-0.5 rounded border border-amber-500/20">Hardware Max</span>
                            </div>
                            <h3 class="text-sm font-bold text-white mb-1.5 font-mono">HFNC Flow Pipeline Adapter</h3>
                            <p class="text-xs text-slate-400 leading-relaxed font-mono">Links algorithmic infrastructure directly to physical High-Flow Nasal Cannula baseline drivers for real-world laboratory deployment.</p>
                        </div>
                        <button class="w-full bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white font-bold py-2.5 rounded-xl text-[11px] font-mono uppercase tracking-wider mt-6 shadow transition">
                            Unlock Module ($1,450 / Year)
                        </button>
                    </div>
                </div>
            </div>
            {% endif %}

        </main>
    </div>

    <script>
        function applyProfilePresets() {
            const profile = document.getElementById('profile_class').value;
            const pip = document.getElementById('pip');
            const compliance = document.getElementById('compliance');
            const resistance = document.getElementById('resistance');
            const peep = document.getElementById('peep');
            
            if (profile === 'neonatal') {
                pip.value = '24'; compliance.value = '3.0'; resistance.value = '45'; peep.value = '5';
            } else if (profile === 'pediatric') {
                pip.value = '28'; compliance.value = '16.0'; resistance.value = '22'; peep.value = '6';
            } else if (profile === 'adult') {
                pip.value = '32'; compliance.value = '42.0'; resistance.value = '12'; peep.value = '8';
            }
        }
        function updateClock() {
            const now = new Date();
            document.getElementById('liveClock').innerText = now.toLocaleString();
        }
        setInterval(updateClock, 1000);
    </script>
</body>
</html>
"""

# --- ADVANCED FLUID DYNAMICS ENGINE MATHEMATICS CONTROLLER ---

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    if username in CLINICAL_DATABASE and CLINICAL_DATABASE[username]['token'] == password:
        session['user'] = username
        session['role'] = CLINICAL_DATABASE[username]['role']
        session['clearance'] = CLINICAL_DATABASE[username]['clearance']
        session['facility'] = CLINICAL_DATABASE[username]['facility']
        return redirect(url_for('dashboard'))
    else:
        flash("SECURITY NODE REJECTION: CREDENTIAL ARCHETYPE UNMATCHED")
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    active_tab = request.args.get('tab', 'simulation')
    sim_data = None
    inputs = None
    profile_class = 'neonatal'
    
    if request.method == 'POST':
        profile_class = request.form['profile_class']
        pip = float(request.form['pip'])
        compliance = float(request.form['compliance'])
        resistance = float(request.form['resistance'])
        peep = float(request.form['peep'])
        inputs = {'pip': pip, 'compliance': compliance, 'resistance': resistance, 'peep': peep}
        
        # --- SCIENTIFIC PHYSIOLOGICAL COMPLEMENT PHYSICS ---
        # Converted metric to scale resistance into standard L/s metrics
        converted_resistance = resistance / 1000.0
        time_constant = round(converted_resistance * compliance, 3)
        
        # Driving Pressure Formula: Delta P = PIP - PEEP
        driving_pressure = max(0.1, pip - peep)
        peak_volume = round(driving_pressure * compliance, 1)
        
        time_points = []
        pressure_points = []
        
        # Dynamic Exponential Charging Profiler Loop
        for step in range(0, 11):
            t = (step / 10.0) * 0.5
            time_points.append(f"{round(t, 2)}s")
            if time_constant > 0:
                # Alveolar pressure exponential equalization logic
                current_p = peep + driving_pressure * (1.0 - math.exp(-t / time_constant))
            else:
                current_p = pip
            pressure_points.append(round(current_p, 2))
            
        # --- METROPOLIS CLASSIFICATION STRATIFICATION LOGIC ---
        if profile_class == 'neonatal':
            case_description = "Phenotype Profile: Pre-term Infant Archetype. Lungs present minimal surface matrix structure and severe surfactant layering deficiency. High risk of mechanical physical wall tearing under traditional volumetric load matrices."
            if peak_volume > 85 or pip >= 30:
                risk_status = "CRITICAL: HIGH INFANT BAROTRAUMA RISK"
                advice_note = "DIRECTIVE ALERT: Dynamic volume delivery exceeds micro-structural thresholds. High risk of immediate alveolar tearing. Lower Peak Inspiratory Pressure (PIP) configurations below 25 cmH2O immediately to mitigate shear trauma."
            else:
                risk_status = "NOMINAL: STEADY MICRO-REGIMEN"
                advice_note = "DIRECTIVE NOTE: Current charging metrics correspond optimally with safe neonatal protective tracking metrics."
                
        elif profile_class == 'pediatric':
            case_description = "Phenotype Profile: Pediatric Subject manifesting acute hyper-reactive bronchial inflammation loops. Muscular tissue spasms increase upper airway fluid restriction metrics while baseline compliance remains elastic."
            if peak_volume > 380 or pip >= 34:
                risk_status = "HIGH RISK: JUVENILE SHEAR TRAUMA"
                advice_note = "DIRECTIVE ALERT: Elevating mechanical ventilation tracks against active spasms risks hyper-inflating baseline healthy tissue fields. Review bronchodilator pipeline components or adjust structural settings downward."
            else:
                risk_status = "NOMINAL: REBALANCED EQUALIZATION"
                advice_note = "DIRECTIVE NOTE: Safe pressure-gradient execution allows the target volume loop to bypass restriction zones smoothly."
                
        else: # ADULT ARDS PROFILE
            case_description = "Phenotype Profile: Mature Adult Subject presenting severe Respiratory Distress Syndrome (ARDS). Alveolar micro-pockets are compromised by heavy fluid infiltration, consolidation, and dense fibrous restrictive patches."
            if peak_volume > 850 or driving_pressure > 18:
                risk_status = "CRITICAL: ADULT ALVEOLAR OVERDISTENSION"
                advice_note = "DIRECTIVE ALERT: Current settings exceed protective ventilation targets (6-8 mL/kg of Ideal Body Weight). Elevated driving pressure risks compounding secondary mechanical lung damage. Enforce strict ARDSnet volume restriction tracking immediately."
            else:
                risk_status = "NOMINAL: PROTECTIVE STRATEGY SATISFIED"
                advice_note = "DIRECTIVE NOTE: System loops are actively maintaining modern low-tidal volume guidelines for protective critical infrastructure care."

        sim_data = {
            'peak_volume': peak_volume,
            'time_constant': time_constant,
            'risk_status': risk_status,
            'time_points': time_points,
            'pressure_points': pressure_points,
            'case_description': case_description,
            'advice_note': advice_note
        }

    return render_template_string(
        MASTER_DASHBOARD_HTML,
        active_tab=active_tab,
        sim_data=sim_data,
        inputs=inputs,
        profile_class=profile_class,
        user_role=session.get('role'),
        user_clearance=session.get('clearance'),
        system_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
