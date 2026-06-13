from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import os
import math

app = Flask(__name__)
app.secret_key = "aerolung_standalone_fluid_core_2026"

# Clinician Credentials for Presentation
ICU_USERS = {"icu_specialist": "ventilator2026"}

# --- STANDALONE ICU TELEMETRY INTERFACE ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>AeroLung Core | Medical Interface</title>
</head>
<body class="bg-slate-950 flex items-center justify-center h-screen text-slate-100 antialiased">
    <div class="bg-slate-900 border border-emerald-900/40 p-8 rounded-2xl shadow-2xl w-full max-w-md relative">
        <div class="absolute top-0 left-0 w-full h-1 bg-emerald-500"></div>
        <div class="text-center mb-6">
            <span class="bg-emerald-500/10 text-emerald-400 text-[10px] font-mono tracking-widest uppercase px-3 py-1 rounded-full border border-emerald-500/20">
                SDG 3 // No-API Edge Medical Simulation
            </span>
            <h1 class="text-3xl font-black text-white tracking-tight mt-3">AeroLung <span class="text-emerald-400">Core</span></h1>
            <p class="text-slate-400 text-xs mt-1">Neonatal Barotrauma Fluid Simulation Pipeline</p>
        </div>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl mb-4 text-xs font-mono text-center">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        
        <form method="POST" action="/login" class="space-y-4">
            <div>
                <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1">Clinician ID</label>
                <input type="text" name="username" required class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500 transition">
            </div>
            <div>
                <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1">Access Token</label>
                <input type="password" name="password" required class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500 transition">
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl text-xs uppercase tracking-widest transition shadow-lg shadow-emerald-600/10">Initialize Ventilator Module</button>
        </form>
        <p class="mt-4 text-[10px] text-center text-slate-500 font-mono">Demo ID: icu_specialist | Token: ventilator2026</p>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <title>AeroLung Simulation Node</title>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen antialiased">
    <nav class="bg-slate-900 border-b border-slate-800 px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <div class="flex items-center space-x-3">
            <span class="w-2.5 h-2.5 bg-emerald-400 rounded-full animate-pulse"></span>
            <span class="font-black text-lg tracking-wider text-white">AERO<span class="text-emerald-400">LUNG</span> SIM</span>
        </div>
        <div class="flex items-center space-x-4">
            <a href="/logout" class="bg-slate-800 hover:bg-red-950 border border-slate-700 hover:border-red-900 px-4 py-2 rounded-xl text-xs font-mono uppercase tracking-wider transition">Shutdown Simulator</a>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto p-6 lg:p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl h-fit">
            <h2 class="text-base font-bold text-white mb-1">Ventilator Command Configuration</h2>
            <p class="text-xs text-slate-400 mb-6">Modify thermodynamic and physiological variables to recalculate alveoli mechanical loading vectors.</p>
            
            <form method="POST" action="/dashboard" class="space-y-4">
                <div>
                    <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1.5">Peak Inspiratory Pressure (PIP) [cmH2O]</label>
                    <input type="number" name="pip" value="{{ inputs.pip if inputs else '25' }}" min="10" max="45" class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-emerald-500 transition">
                </div>
                <div>
                    <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1.5">Dynamic Lung Compliance [mL/cmH2O]</label>
                    <input type="number" step="0.1" name="compliance" value="{{ inputs.compliance if inputs else '2.5' }}" min="0.5" max="5.0" class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-emerald-500 transition">
                </div>
                <div>
                    <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1.5">Airway Resistance [cmH2O/L/s]</label>
                    <input type="number" name="resistance" value="{{ inputs.resistance if inputs else '50' }}" min="20" max="150" class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-emerald-500 transition">
                </div>
                <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl text-xs uppercase tracking-widest transition shadow-lg">Recalculate Fluid Loop</button>
            </form>
        </div>

        <div class="lg:col-span-2 space-y-6">
            {% if not sim_data %}
            <div class="bg-slate-900/40 border border-slate-800 border-dashed rounded-2xl p-16 text-center flex flex-col items-center justify-center min-h-[400px]">
                <div class="text-3xl mb-3">🌬️</div>
                <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono">Fluid Systems Offline</h3>
                <p class="text-xs text-slate-500 max-w-xs mt-1 mx-auto">Click recalculate to execute the mathematical fluid logic loops locally on the server host hardware.</p>
            </div>
            {% else %}
            
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                    <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Peak Volumetric Target</p>
                    <p class="text-2xl font-black font-mono text-emerald-400">{{ sim_data.peak_volume }} mL</p>
                </div>
                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                    <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Lung Time Constant</p>
                    <p class="text-2xl font-black font-mono text-cyan-400">{{ sim_data.time_constant }} sec</p>
                </div>
                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                    <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Safety Risk Assessment</p>
                    <p class="text-2xl font-black font-mono {% if 'CRITICAL' in sim_data.risk_status %}text-red-500 animate-pulse{% else %}text-emerald-400{% endif %}">
                        {{ sim_data.risk_status }}
                    </p>
                </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h3 class="text-xs font-mono uppercase tracking-wider text-emerald-400 mb-4 pb-2 border-b border-slate-800">Local Mathematical Simulation: Fluid Waveform</h3>
                <div class="h-64">
                    <canvas id="waveformChart"></canvas>
                </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h3 class="text-xs font-mono uppercase tracking-wider text-slate-400 mb-3">Pathophysiological Analysis</h3>
                <p class="text-xs text-slate-300 leading-relaxed font-mono bg-slate-950 border border-slate-800 p-4 rounded-xl">
                    {{ sim_data.clinical_insight }}
                </p>
            </div>

            <script>
                const ctx = document.getElementById('waveformChart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: {{ sim_data.time_points | tojson }},
                        datasets: [{
                            label: 'Alveolar Airway Pressure (cmH2O)',
                            data: {{ sim_data.pressure_points | tojson }},
                            borderColor: 'rgb(52, 211, 153)',
                            backgroundColor: 'rgba(52, 211, 153, 0.05)',
                            borderWidth: 2,
                            tension: 0.3,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'monospace' } } } },
                        scales: {
                            x: { grid: { color: '#334155' }, ticks: { color: '#94a3b8', font: { family: 'monospace' } } },
                            y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8', font: { family: 'monospace' } } }
                        }
                    }
                });
            </script>
            {% endif %}
        </div>
    </main>
</body>
</html>
"""

# --- BACKEND SIMULATION ROUTING MATHEMATICS ---

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in ICU_USERS and ICU_USERS[username] == password:
        session['user'] = username
        return redirect(url_for('dashboard'))
    else:
        flash("ACCESS ERROR: INVALID CLINICIAN TOKEN")
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    sim_data = None
    inputs = None
    
    if request.method == 'POST':
        pip = float(request.form['pip'])
        compliance = float(request.form['compliance'])
        resistance = float(request.form['resistance'])
        
        inputs = {'pip': pip, 'compliance': compliance, 'resistance': resistance}
        
        # --- LOCAL CLINICAL FLUID DYNAMICS MOTOR LOOPS ---
        # Calculate lung filling rate parameter (Time Constant = Resistance * Compliance)
        # Convert resistance from cmH2O/L/s to cmH2O/mL/s by dividing by 1000
        converted_resistance = resistance / 1000.0
        time_constant = round(converted_resistance * compliance, 3)
        
        # Calculate physiological peak air volume captured by lungs
        peak_volume = round(pip * compliance, 1)
        
        # Generate simulation waveform points dynamically (Inspiratory phase simulation cycle)
        time_points = []
        pressure_points = []
        for step in range(0, 11):
            t = (step / 10.0) * 0.5  # 0.5 second total breath phase snapshot window
            time_points.append(f"{round(t, 2)}s")
            
            # Classical fluid load charging envelope calculation loop
            if time_constant > 0:
                current_p = pip * (1.0 - math.exp(-t / time_constant))
            else:
                current_p = pip
            pressure_points.append(round(current_p, 2))
        
        # Calculate dynamic safety state rules locally
        if pip >= 35 or peak_volume > 90:
            risk_status = "CRITICAL: BAROTRAUMA"
            clinical_insight = f"CRITICAL HAZARD WARNING: A Peak Inspiratory Pressure of {pip} cmH2O combined with calculated lung compliance yields an excessive volumetric threshold ({peak_volume} mL). This setup generates massive sheer stress across the neonatal alveolar walls, introducing severe risks of an acute lung collapse or barotrauma. Immediately adjust pressure maximum down below 30 cmH2O."
        else:
            risk_status = "NORMAL: SAFE STEADY STATE"
            clinical_insight = f"SYSTEM STABLE: Calculated mechanical lung time constant sits at {time_constant} seconds. The fluid system displays optimal pulmonary equilibration timing. Alveolar pressure curve climbs gracefully, maximizing oxygen transport indices without applying unsafe strain to the neonatal tissue mesh matrix."
            
        sim_data = {
            'peak_volume': peak_volume,
            'time_constant': time_constant,
            'risk_status': risk_status,
            'time_points': time_points,
            'pressure_points': pressure_points,
            'clinical_insight': clinical_insight
        }
        
    return render_template_string(DASHBOARD_HTML, sim_data=sim_data, inputs=inputs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
