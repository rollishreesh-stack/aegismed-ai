from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import os
import math
from datetime import datetime

app = Flask(__name__)
app.secret_key = "aerolung_enterprise_pro_system_2026"

CLINICAL_DATABASE = {
    "icu_specialist": {"token": "ventilator2026", "role": "Attending Intensivist", "clearance": "Tier-1 Critical Care"},
    "olympiad_judge": {"token": "innovation2026", "role": "Chief Medical Evaluator", "clearance": "Global System Admin"}
}

# --- MASTER ENTERPRISE PLATFORM UI ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>AeroLung OS Pro | Clinical Gate</title>
</head>
<body class="bg-[#0b0f19] flex items-center justify-center h-screen text-slate-100 antialiased font-sans">
    <div class="bg-[#111827] border border-slate-800 p-8 rounded-2xl shadow-2xl w-full max-w-md relative">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-teal-500 to-indigo-500"></div>
        
        <div class="text-center mb-8">
            <span class="bg-teal-500/10 text-teal-400 text-[10px] font-mono tracking-widest uppercase px-3 py-1 rounded-full border border-teal-500/20">
                AeroLung OS Pro // Cross-Demographic Ventilation Network
            </span>
            <h1 class="text-3xl font-black text-white tracking-tight mt-4">AeroLung <span class="text-teal-400">OS Pro</span></h1>
            <p class="text-slate-400 text-xs mt-1">Autonomous Multi-Profile Ventilation Simulation Infrastructure</p>
        </div>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl mb-4 text-xs font-mono text-center">
                ⚠️ {{ messages[0] }}
            </div>
          {% endif %}
        {% endwith %}
        
        <form method="POST" action="/login" class="space-y-4">
            <div>
                <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1">User ID / Clinician ID</label>
                <input type="text" name="username" required placeholder="e.g., icu_specialist" class="w-full p-3 rounded-xl bg-[#1f2937] border border-slate-700 text-white text-sm focus:outline-none focus:border-teal-500 transition">
            </div>
            <div>
                <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1">Security Authentication Token</label>
                <input type="password" name="password" required placeholder="••••••••" class="w-full p-3 rounded-xl bg-[#1f2937] border border-slate-700 text-white text-sm focus:outline-none focus:border-teal-500 transition">
            </div>
            <button type="submit" class="w-full bg-teal-600 hover:bg-teal-500 text-white font-bold py-3 rounded-xl text-xs uppercase tracking-widest transition shadow-lg">
                Authorize Terminal Connection
            </button>
        </form>
        
        <div class="mt-6 pt-4 border-t border-slate-800/60 text-[11px] text-slate-500 font-mono space-y-1">
            <p class="text-center font-bold text-slate-400 uppercase tracking-wider mb-2">Available System Credentials</p>
            <div class="flex justify-between bg-[#151f32] p-2 rounded-lg">
                <span>ID: <code class="text-teal-400">icu_specialist</code></span>
                <span>Token: <code class="text-slate-300">ventilator2026</code></span>
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
    <title>AeroLung OS Pro Console</title>
</head>
<body class="bg-[#0b0f19] text-slate-100 min-h-screen antialiased font-sans flex flex-col">

    <nav class="bg-[#111827] border-b border-slate-800 px-6 py-4 flex justify-between items-center sticky top-0 z-50 shadow-md">
        <div class="flex items-center space-x-3">
            <span class="w-2.5 h-2.5 bg-teal-400 rounded-full animate-pulse"></span>
            <span class="font-black text-lg tracking-wider text-white">AERO<span class="text-teal-400">LUNG</span> <span class="text-slate-400 text-sm font-light font-mono">PRO v3.0</span></span>
        </div>
        
        <div class="flex items-center space-x-6 text-xs font-mono">
            <div class="text-right hidden md:block border-r border-slate-800 pr-4">
                <span class="text-slate-500 block uppercase text-[10px]">System Timestamp</span>
                <span class="text-teal-400 font-bold" id="liveClock">{{ system_time }}</span>
            </div>
            <div class="text-right">
                <span class="text-slate-400 font-bold block">{{ user_role }}</span>
                <span class="text-[10px] text-slate-500 uppercase tracking-widest">{{ user_clearance }}</span>
            </div>
            <a href="/logout" class="bg-slate-800 hover:bg-red-950 border border-slate-700 hover:border-red-900 px-4 py-2 rounded-xl text-xs uppercase tracking-wider font-bold transition">Disconnect</a>
        </div>
    </nav>

    <div class="flex flex-1">
        
        <aside class="w-64 bg-[#111827] border-r border-slate-800 p-4 flex flex-col justify-between hidden md:flex">
            <div class="space-y-2">
                <p class="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase px-3 mb-4">Command Subsystems</p>
                
                <a href="?tab=simulation" class="flex items-center space-x-3 px-3 py-3 rounded-xl transition font-medium text-sm {% if active_tab == 'simulation' %}bg-teal-600/10 text-teal-400 border border-teal-500/20{% else %}text-slate-400 hover:bg-slate-800/50 hover:text-white{% endif %}">
                    <span>🌬️</span> <span>ICU Waveform Engine</span>
                </a>
                
                <a href="?tab=registry" class="flex items-center space-x-3 px-3 py-3 rounded-xl transition font-medium text-sm {% if active_tab == 'registry' %}bg-teal-600/10 text-teal-400 border border-teal-500/20{% else %}text-slate-400 hover:bg-slate-800/50 hover:text-white{% endif %}">
                    <span>📋</span> <span>Global Patient Registry</span>
                </a>
            </div>
            
            <div class="bg-[#1f2937]/40 p-4 rounded-xl border border-slate-800/60 text-center">
                <p class="text-[10px] font-mono text-slate-500">Cross-Demographic Node</p>
                <p class="text-xs font-bold font-mono text-teal-400">SECURE LOCALHOST</p>
            </div>
        </aside>

        <main class="flex-1 p-6 lg:p-8 overflow-y-auto">
            
            {% if active_tab == 'simulation' %}
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div class="lg:col-span-1 bg-[#111827] border border-slate-800 rounded-2xl p-6 shadow-xl h-fit">
                    <h2 class="text-base font-bold text-white mb-1">Ventilator Telemetry Controls</h2>
                    <p class="text-xs text-slate-400 mb-6">Select a targeted patient demographic block and scale input variables.</p>
                    
                    <form method="POST" action="/dashboard?tab=simulation" class="space-y-4">
                        <div>
                            <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1.5">Target Patient Demographic</label>
                            <select name="profile_class" id="profile_class" onchange="applyProfilePresets()" class="w-full p-3 rounded-xl bg-[#1f2937] border border-slate-700 text-white text-sm focus:outline-none focus:border-teal-500 transition font-mono">
                                <option value="neonatal" {% if profile_class == 'neonatal' %}selected{% endif %}>NEONATAL (Premature / RDS Archetype)</option>
                                <option value="pediatric" {% if profile_class == 'pediatric' %}selected{% endif %}>PEDIATRIC (Child / Acute Asthma Profile)</option>
                                <option value="adult" {% if profile_class == 'adult' %}selected{% endif %}>ADULT (Mature / Severe ARDS / Trauma)</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1.5">Peak Inspiratory Pressure (PIP) [cmH2O]</label>
                            <input type="number" id="pip" name="pip" value="{{ inputs.pip if inputs else '25' }}" min="10" max="45" class="w-full p-3 rounded-xl bg-[#1f2937] border border-slate-700 text-sm text-white focus:outline-none focus:border-teal-500 transition">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1.5">Dynamic Lung Compliance [mL/cmH2O]</label>
                            <input type="number" step="0.1" id="compliance" name="compliance" value="{{ inputs.compliance if inputs else '2.5' }}" min="0.5" max="60.0" class="w-full p-3 rounded-xl bg-[#1f2937] border border-slate-700 text-sm text-white focus:outline-none focus:border-teal-500 transition">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1.5">Airway Resistance [cmH2O/L/s]</label>
                            <input type="number" id="resistance" name="resistance" value="{{ inputs.resistance if inputs else '50' }}" min="5" max="150" class="w-full p-3 rounded-xl bg-[#1f2937] border border-slate-700 text-sm text-white focus:outline-none focus:border-teal-500 transition">
                        </div>
                        <button type="submit" class="w-full bg-teal-600 hover:bg-teal-500 text-white font-bold py-3 rounded-xl text-xs uppercase tracking-widest transition shadow-lg">
                            Execute Local Mathematical Loop
                        </button>
                    </form>
                </div>

                <div class="lg:col-span-2 space-y-6">
                    {% if not sim_data %}
                    <div class="bg-[#111827]/40 border border-slate-800 border-dashed rounded-2xl p-16 text-center flex flex-col items-center justify-center min-h-[400px]">
                        <div class="text-3xl mb-3">🌬️</div>
                        <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono">Fluid Systems Standing By</h3>
                        <p class="text-xs text-slate-500 max-w-xs mt-1 mx-auto">Select a demographic classification and hit recalculate to view custom physiological analytics mapping logs.</p>
                    </div>
                    {% else %}
                    
                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div class="bg-[#111827] border border-slate-800 rounded-2xl p-5">
                            <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Demographic Focus</p>
                            <p class="text-xl font-black font-mono text-teal-400 uppercase">{{ profile_class }} Suite</p>
                        </div>
                        <div class="bg-[#111827] border border-slate-800 rounded-2xl p-5">
                            <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Peak Volume Output</p>
                            <p class="text-2xl font-black font-mono text-cyan-400">{{ sim_data.peak_volume }} mL</p>
                        </div>
                        <div class="bg-[#111827] border border-slate-800 rounded-2xl p-5">
                            <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Safety Risk Metrics</p>
                            <p class="text-base font-black font-mono {% if 'CRITICAL' in sim_data.risk_status or 'HIGH' in sim_data.risk_status %}text-red-500{% else %}text-emerald-400{% endif %}">
                                {{ sim_data.risk_status }}
                            </p>
                        </div>
                    </div>

                    <div class="bg-[#111827] border border-slate-800 rounded-2xl p-6">
                        <h3 class="text-xs font-mono uppercase tracking-wider text-teal-400 mb-4 pb-2 border-b border-slate-800">Alveolar Pressure Charging Profile</h3>
                        <div class="h-64"><canvas id="waveformChart"></canvas></div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="bg-[#111827] border border-slate-800 rounded-2xl p-6">
                            <h3 class="text-xs font-mono uppercase tracking-wider text-slate-400 mb-3 border-b border-slate-800 pb-2">📋 Case Description Log</h3>
                            <p class="text-xs text-slate-300 leading-relaxed font-mono">
                                {{ sim_data.case_description }}
                            </p>
                        </div>
                        <div class="bg-[#111827] border border-teal-900 rounded-2xl p-6 bg-gradient-to-br from-[#111827] to-[#0d2221]">
                            <h3 class="text-xs font-mono uppercase tracking-wider text-teal-400 mb-3 border-b border-teal-900 pb-2">🩺 Clinical Advisory Panel Advice Note</h3>
                            <p class="text-xs text-teal-300 leading-relaxed font-mono">
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
                                    label: 'Pressure Track (cmH2O)',
                                    data: {{ sim_data.pressure_points | tojson }},
                                    borderColor: 'rgb(45, 212, 191)',
                                    backgroundColor: 'rgba(45, 212, 191, 0.05)',
                                    borderWidth: 2,
                                    fill: true
                                }]
                            },
                            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { color: '#1f2937' } }, y: { grid: { color: '#1f2937' } } } }
                        });
                    </script>
                    {% endif %}
                </div>
            </div>
            {% endif %}

            {% if active_tab == 'registry' %}
            <div class="bg-[#111827] border border-slate-800 rounded-2xl p-6 shadow-xl">
                <div class="flex justify-between items-center mb-6 border-b border-slate-800 pb-4">
                    <div>
                        <h2 class="text-lg font-bold text-white">Cross-Demographic ICU Register</h2>
                        <p class="text-xs text-slate-400">Global clinical tracking node mapping neonatal, pediatric, and adult simulation matrices.</p>
                    </div>
                </div>
                
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-slate-800 text-xs text-slate-400 font-mono uppercase bg-[#1f2937]/30">
                                <th class="p-4">Patient ID</th>
                                <th class="p-4">Demographic Archetype</th>
                                <th class="p-4">Assigned Location</th>
                                <th class="p-4">Target Compliance Vector</th>
                                <th class="p-4">Status</th>
                            </tr>
                        </thead>
                        <tbody class="text-xs font-mono divide-y divide-slate-800/60">
                            <tr class="hover:bg-slate-800/20">
                                <td class="p-4 text-white font-bold">#NEO-8841</td>
                                <td class="p-4 text-slate-300">Neonatal (26w Premature)</td>
                                <td class="p-4 text-slate-400">NICU Pod-4</td>
                                <td class="p-4 text-teal-400">1.8 mL/cmH2O</td>
                                <td class="p-4"><span class="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full font-bold text-[10px]">MONITORING</span></td>
                            </tr>
                            <tr class="hover:bg-slate-800/20">
                                <td class="p-4 text-white font-bold">#PED-4029</td>
                                <td class="p-4 text-slate-300">Pediatric (7y Severe Asthma)</td>
                                <td class="p-4 text-slate-400">Childrens Wing Bed-12</td>
                                <td class="p-4 text-teal-400">12.5 mL/cmH2O</td>
                                <td class="p-4"><span class="px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full font-bold text-[10px]">STABILIZING</span></td>
                            </tr>
                            <tr class="hover:bg-slate-800/20">
                                <td class="p-4 text-white font-bold">#ADU-1105</td>
                                <td class="p-4 text-slate-300">Adult (54y Acute ARDS Crisis)</td>
                                <td class="p-4 text-slate-400">Main ICU Trauma Bay-2</td>
                                <td class="p-4 text-teal-400">35.0 mL/cmH2O</td>
                                <td class="p-4"><span class="px-2 py-0.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded-full font-bold text-[10px]">CRITICAL INSUGGENCE</span></td>
                            </tr>
                        </tbody>
                    </table>
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
            
            if (profile === 'neonatal') {
                pip.value = '25'; compliance.value = '2.5'; resistance.value = '50';
            } else if (profile === 'pediatric') {
                pip.value = '28'; compliance.value = '15.0'; resistance.value = '20';
            } else if (profile === 'adult') {
                pip.value = '30'; compliance.value = '40.0'; resistance.value = '10';
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

# --- BACKEND MATHEMATICS CONTROLLER MATRIX ---

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
        return redirect(url_for('dashboard'))
    else:
        flash("SECURITY SYSTEM REJECTION: UNVERIFIED CLINICAL LOGINS")
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
        inputs = {'pip': pip, 'compliance': compliance, 'resistance': resistance}
        
        # Core Classical Scaling Math
        converted_resistance = resistance / 1000.0
        time_constant = round(converted_resistance * compliance, 3)
        peak_volume = round(pip * compliance, 1)
        
        time_points = []
        pressure_points = []
        for step in range(0, 11):
            t = (step / 10.0) * 0.5
            time_points.append(f"{round(t, 2)}s")
            current_p = pip * (1.0 - math.exp(-t / time_constant)) if time_constant > 0 else pip
            pressure_points.append(round(current_p, 2))
            
        # DYNAMIC PROFILE STRATIFICATION RULES LOGIC
        if profile_class == 'neonatal':
            case_description = f"Patient Profile: Pre-term Infant (estimated 26 weeks gestational age). Lungs are characteristically small, fragile, and deficient in natural surfactant layers, creating a high-risk matrix for physical wall collapse."
            if peak_volume > 90 or pip >= 32:
                risk_status = "CRITICAL: NEONATAL BAROTRAUMA"
                advice_note = "ADVICE NOTE: IMMEDIATE ACTION REQUIRED. Volumetric target delivery exceeds 90mL in a neonatal lung architecture. This will cause severe alveolar tearing. Reduce Peak Inspiratory Pressure (PIP) down below 25 cmH2O immediately to safeguard tissue integrity."
            else:
                risk_status = "NOMINAL: SAFE REGIMEN"
                advice_note = "ADVICE NOTE: Current operational volume satisfies baseline micro-ventilation patterns. Maintain target compliance tracking parameters."
                
        elif profile_class == 'pediatric':
            case_description = f"Patient Profile: Pediatric Subject (7 years old) presenting with acute status asthmaticus. Airways exhibit muscular bronchospasms and local mucosal edema, significantly decreasing standard fluid transit indices."
            if peak_volume > 450 or pip >= 35:
                risk_status = "HIGH RISK: PEDIATRIC SHEAR STRESS"
                advice_note = "ADVICE NOTE: Elevated pressures are fighting against bronchospasm restrictions. Volumetric loading is creeping into unsafe juvenile structural expansion thresholds. Consider introducing immediate bronchodilator therapies or transitioning tracking variables."
            else:
                risk_status = "NOMINAL: SAFE REGIMEN"
                advice_note = "ADVICE NOTE: Mechanical pressure curve effectively bypasses upper airway restriction nodes without introducing sheer strain to small-scale lung tissues."
                
        else: # ADULT ARDS PROFILE
            case_description = f"Patient Profile: Mature Adult Subject (54 years old) exhibiting severe, acute Respiratory Distress Syndrome (ARDS) secondary to system-wide trauma. Large tissue surface area but severely compromised by fluid infiltration and localized fibrosis pockets."
            if peak_volume > 900 or pip >= 40:
                risk_status = "CRITICAL: ADULT ALVEOLAR OVERDISTENSION"
                advice_note = "ADVICE NOTE: WARNING. Calculated peak volume delivery is pushing past the physiological protective ventilation threshold (6-8 mL/kg of ideal body weight). High risk of escalating mechanical lung injury. Implement lung-protective low-tidal volume protocols immediately."
            else:
                risk_status = "NOMINAL: SAFE REGIMEN"
                advice_note = "ADVICE NOTE: System is maintaining safe low-tidal volume ventilation parameters compliant with standard ARDSnet clinical strategies."

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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
