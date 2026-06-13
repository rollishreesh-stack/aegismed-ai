from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_advanced_core_2026")

# --- MUTABLE SYSTEM DATABASE ---
CLINICAL_DATABASE = {
    "sys_admin": {
        "password": "secure2026", 
        "role": "Chief System Architect", 
        "clearance": "Level 5"
    }
}

# --- UI TEMPLATES ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>AeroLung Advanced | Authentication Gate</title>
</head>
<body class="bg-[#0f172a] flex items-center justify-center h-screen text-slate-200 antialiased font-sans">
    <div class="bg-[#1e293b] border border-slate-700 p-8 rounded-xl shadow-2xl w-full max-w-sm">
        <div class="text-center mb-6">
            <h1 class="text-2xl font-black text-white tracking-tight">AeroLung <span class="text-blue-400">Core</span></h1>
            <p class="text-slate-400 text-xs mt-1 font-medium">Advanced Ventilation Telemetry Matrix</p>
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
                <input type="text" name="username" required class="w-full p-2.5 rounded-lg bg-[#0f172a] border border-slate-600 text-white text-sm focus:outline-none focus:border-blue-500 transition font-mono">
            </div>
            <div>
                <label class="block text-slate-400 text-[10px] font-mono uppercase tracking-wider mb-1">Access Passkey</label>
                <input type="password" name="password" required class="w-full p-2.5 rounded-lg bg-[#0f172a] border border-slate-600 text-white text-sm focus:outline-none focus:border-blue-500 transition font-mono">
            </div>
            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 rounded-lg text-xs uppercase tracking-widest transition mt-4">
                Initialize Connection
            </button>
        </form>
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
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <title>AeroLung Core Simulator</title>
</head>
<body class="bg-[#0f172a] text-slate-200 min-h-screen antialiased flex flex-col">

    <nav class="bg-[#1e293b] border-b border-slate-700 px-6 py-3 flex justify-between items-center sticky top-0 z-50">
        <div class="flex items-center space-x-3">
            <span class="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></span>
            <span class="font-black text-lg tracking-wider text-white">AERO<span class="text-blue-400">LUNG</span></span>
        </div>
        
        <div class="flex items-center space-x-4 text-xs font-mono">
            <div class="text-right border-r border-slate-700 pr-4">
                <span class="text-blue-400 font-bold block">{{ user_role }}</span>
                <span class="text-[10px] text-slate-400 uppercase">ID: {{ session.get('user') }}</span>
            </div>
            <a href="?tab=simulator" class="text-slate-300 hover:text-white px-2 {% if active_tab == 'simulator' %}border-b-2 border-blue-500 text-white{% endif %}">Simulator</a>
            <a href="?tab=settings" class="text-slate-300 hover:text-white px-2 {% if active_tab == 'settings' %}border-b-2 border-blue-500 text-white{% endif %}">Settings</a>
            <a href="/logout" class="bg-slate-800 hover:bg-red-900 border border-slate-600 px-3 py-1.5 rounded-md text-xs uppercase transition ml-2">Logout</a>
        </div>
    </nav>

    <main class="flex-1 p-6">
        
        {% if active_tab == 'settings' %}
        <div class="max-w-md mx-auto bg-[#1e293b] border border-slate-700 rounded-xl p-6 mt-10">
            <h2 class="text-lg font-bold text-white mb-2">System Access Configuration</h2>
            <p class="text-xs text-slate-400 mb-6">Update your clinical node credentials. Changes take effect immediately.</p>
            
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
                    <input type="password" name="current_password" required class="w-full p-2.5 rounded-lg bg-[#0f172a] border border-slate-600 text-white text-sm focus:border-blue-500 transition font-mono">
                </div>
                <hr class="border-slate-700 my-4">
                <div>
                    <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">New System ID</label>
                    <input type="text" name="new_username" required value="{{ session.get('user') }}" class="w-full p-2.5 rounded-lg bg-[#0f172a] border border-slate-600 text-white text-sm focus:border-blue-500 transition font-mono">
                </div>
                <div>
                    <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">New Password</label>
                    <input type="password" name="new_password" required class="w-full p-2.5 rounded-lg bg-[#0f172a] border border-slate-600 text-white text-sm focus:border-blue-500 transition font-mono">
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 rounded-lg text-xs uppercase tracking-widest transition mt-4">
                    Commit Changes
                </button>
            </form>
        </div>
        {% endif %}

        {% if active_tab == 'simulator' %}
        <div class="grid grid-cols-1 xl:grid-cols-12 gap-6">
            
            <div class="xl:col-span-4 bg-[#1e293b] border border-slate-700 rounded-xl p-5 h-fit">
                <h2 class="text-sm font-bold text-white mb-4 border-b border-slate-700 pb-2">Multi-Variable Telemetry Control</h2>
                
                <form method="POST" action="/dashboard?tab=simulator" class="space-y-4">
                    <div>
                        <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">Comprehensive Phenotype Matrix</label>
                        <select name="profile_class" id="profile_class" onchange="applyProfilePresets()" class="w-full p-2 rounded-lg bg-[#0f172a] border border-slate-600 text-white text-xs focus:border-blue-500 transition font-mono">
                            <option value="normal" {% if profile_class == 'normal' %}selected{% endif %}>Healthy Lungs (Post-Op)</option>
                            <option value="ards_mild" {% if profile_class == 'ards_mild' %}selected{% endif %}>Mild ARDS (Exudative)</option>
                            <option value="ards_severe" {% if profile_class == 'ards_severe' %}selected{% endif %}>Severe ARDS (Fibroproliferative)</option>
                            <option value="asthma" {% if profile_class == 'asthma' %}selected{% endif %}>Status Asthmaticus</option>
                            <option value="copd" {% if profile_class == 'copd' %}selected{% endif %}>Exacerbation of COPD</option>
                            <option value="chf" {% if profile_class == 'chf' %}selected{% endif %}>Congestive Heart Failure (Pulm. Edema)</option>
                            <option value="pe" {% if profile_class == 'pe' %}selected{% endif %}>Massive Pulmonary Embolism</option>
                            <option value="tbi" {% if profile_class == 'tbi' %}selected{% endif %}>Traumatic Brain Injury (TBI)</option>
                            <option value="fibrosis" {% if profile_class == 'fibrosis' %}selected{% endif %}>Idiopathic Pulmonary Fibrosis</option>
                        </select>
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div class="col-span-2 border-b border-slate-700 pb-2 mb-1">
                            <span class="text-[10px] text-blue-400 font-bold uppercase tracking-wider">Patient & Gas Delivery</span>
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">IBW (kg)</label>
                            <input type="number" id="ibw" name="ibw" value="{{ inputs.ibw if inputs else '70' }}" class="w-full p-2 rounded-lg bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">FiO2 (%)</label>
                            <input type="number" id="fio2" name="fio2" value="{{ inputs.fio2 if inputs else '40' }}" class="w-full p-2 rounded-lg bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>

                        <div class="col-span-2 border-b border-slate-700 pb-2 mt-2 mb-1">
                            <span class="text-[10px] text-blue-400 font-bold uppercase tracking-wider">Lung Mechanics</span>
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">Comp. (mL/cmH2O)</label>
                            <input type="number" step="0.1" id="compliance" name="compliance" value="{{ inputs.compliance if inputs else '60.0' }}" class="w-full p-2 rounded-lg bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">Res. (cmH2O/L/s)</label>
                            <input type="number" id="resistance" name="resistance" value="{{ inputs.resistance if inputs else '10' }}" class="w-full p-2 rounded-lg bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>

                        <div class="col-span-2 border-b border-slate-700 pb-2 mt-2 mb-1">
                            <span class="text-[10px] text-blue-400 font-bold uppercase tracking-wider">Ventilator Settings</span>
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">PIP (cmH2O)</label>
                            <input type="number" id="pip" name="pip" value="{{ inputs.pip if inputs else '15' }}" class="w-full p-2 rounded-lg bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">PEEP (cmH2O)</label>
                            <input type="number" id="peep" name="peep" value="{{ inputs.peep if inputs else '5' }}" class="w-full p-2 rounded-lg bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">Resp Rate (/min)</label>
                            <input type="number" id="rr" name="rr" value="{{ inputs.rr if inputs else '16' }}" class="w-full p-2 rounded-lg bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                        <div>
                            <label class="block text-slate-400 text-[10px] font-mono uppercase mb-1">I:E Ratio (1:X)</label>
                            <input type="number" step="0.1" id="ie_ratio" name="ie_ratio" value="{{ inputs.ie_ratio if inputs else '2.0' }}" class="w-full p-2 rounded-lg bg-[#0f172a] border border-slate-600 text-xs font-mono">
                        </div>
                    </div>
                    <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 rounded-lg text-xs uppercase tracking-widest mt-4">
                        Compute Exchange Dynamics
                    </button>
                </form>
            </div>

            <div class="xl:col-span-8 space-y-6">
                {% if not sim_data %}
                <div class="bg-[#1e293b]/50 border border-slate-700 border-dashed rounded-xl flex flex-col items-center justify-center min-h-[500px]">
                    <span class="text-3xl mb-2 opacity-50">🔬</span>
                    <p class="text-xs text-slate-400 font-mono">Awaiting hemodynamic and ventilatory inputs for complex modeling.</p>
                </div>
                {% else %}
                
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="bg-[#1e293b] border border-slate-700 rounded-xl p-4">
                        <p class="text-[9px] font-mono uppercase text-slate-400 mb-1">Volumetric Target ($V_t$/kg)</p>
                        <p class="text-lg font-bold {% if sim_data.vt_kg > 8 %}text-red-400{% else %}text-blue-400{% endif %} font-mono">{{ sim_data.vt_kg }} mL/kg</p>
                        <p class="text-[8px] text-slate-500 mt-1">Total $V_t$: {{ sim_data.peak_volume }} mL</p>
                    </div>
                    <div class="bg-[#1e293b] border border-slate-700 rounded-xl p-4">
                        <p class="text-[9px] font-mono uppercase text-slate-400 mb-1">Alveolar Vent ($V_A$)</p>
                        <p class="text-lg font-bold text-indigo-400 font-mono">{{ sim_data.alveolar_vent }} L/m</p>
                        <p class="text-[8px] text-slate-500 mt-1">Gross $V_E$: {{ sim_data.minute_vent }} L/m</p>
                    </div>
                    <div class="bg-[#1e293b] border border-slate-700 rounded-xl p-4">
                        <p class="text-[9px] font-mono uppercase text-slate-400 mb-1">Est. Arterial CO2 ($PaCO_2$)</p>
                        <p class="text-lg font-bold {% if sim_data.paco2 > 45 or sim_data.paco2 < 35 %}text-amber-400{% else %}text-green-400{% endif %} font-mono">{{ sim_data.paco2 }} mmHg</p>
                        <p class="text-[8px] text-slate-500 mt-1">Normal: 35-45 mmHg</p>
                    </div>
                    <div class="bg-[#1e293b] border border-slate-700 rounded-xl p-4">
                        <p class="text-[9px] font-mono uppercase text-slate-400 mb-1">Est. Arterial O2 ($PaO_2$)</p>
                        <p class="text-lg font-bold {% if sim_data.pao2 < 60 %}text-red-400{% else %}text-emerald-400{% endif %} font-mono">{{ sim_data.pao2 }} mmHg</p>
                        <p class="text-[8px] text-slate-500 mt-1">Shunt Fraction: {{ sim_data.shunt_percent }}%</p>
                    </div>
                </div>

                <div class="bg-[#1e293b] border border-slate-700 rounded-xl p-5">
                    <h3 class="text-xs font-mono uppercase text-slate-400 mb-2 border-b border-slate-700 pb-2">Pathological Context & Diagnostic Output</h3>
                    <p class="text-xs text-slate-300 mb-3 leading-relaxed"><span class="font-bold text-blue-400">Diagnosis:</span> {{ sim_data.case_description }}</p>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="bg-blue-900/20 border-l-2 border-blue-500 p-3 rounded-r-md">
                            <span class="text-[9px] uppercase text-blue-400 font-bold block mb-1">Volumetric / Pressure Status</span>
                            <p class="text-[11px] font-mono text-blue-300">{{ sim_data.vol_note }}</p>
                        </div>
                        <div class="bg-emerald-900/20 border-l-2 border-emerald-500 p-3 rounded-r-md">
                            <span class="text-[9px] uppercase text-emerald-400 font-bold block mb-1">Gas Exchange Status</span>
                            <p class="text-[11px] font-mono text-emerald-300">{{ sim_data.gas_note }}</p>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-4 gap-4">
                    <div class="bg-slate-800 p-3 rounded-lg border border-slate-700 text-center flex flex-col justify-center">
                        <p class="text-[9px] font-mono uppercase text-slate-400">Mean Airway ($P_{mean}$)</p>
                        <p class="text-sm font-bold text-white font-mono">{{ sim_data.mean_pressure }} cmH2O</p>
                    </div>
                    <div class="bg-slate-800 p-3 rounded-lg border border-slate-700 text-center flex flex-col justify-center">
                        <p class="text-[9px] font-mono uppercase text-slate-400">Auto-PEEP Risk</p>
                        <p class="text-sm font-bold font-mono {% if sim_data.auto_peep_risk == 'HIGH' %}text-red-400{% else %}text-green-400{% endif %}">{{ sim_data.auto_peep_risk }}</p>
                    </div>
                    <div class="bg-slate-800 p-3 rounded-lg border border-slate-700 text-center flex flex-col justify-center">
                        <p class="text-[9px] font-mono uppercase text-slate-400">Inspiratory ($T_i$)</p>
                        <p class="text-sm font-bold text-white font-mono">{{ sim_data.t_i }} s</p>
                    </div>
                    <div class="bg-slate-800 p-3 rounded-lg border border-slate-700 text-center flex flex-col justify-center">
                        <p class="text-[9px] font-mono uppercase text-slate-400">Expiratory ($T_e$)</p>
                        <p class="text-sm font-bold text-white font-mono">{{ sim_data.t_e }} s</p>
                    </div>
                </div>
                
                {% endif %}
            </div>
        </div>
        {% endif %}
    </main>

    <script>
        // Preset injections map to clinical pathologies. Settings adjust to baseline starting points.
        function applyProfilePresets() {
            const profile = document.getElementById('profile_class').value;
            const pip = document.getElementById('pip');
            const peep = document.getElementById('peep');
            const compliance = document.getElementById('compliance');
            const resistance = document.getElementById('resistance');
            const rr = document.getElementById('rr');
            const ie = document.getElementById('ie_ratio');
            
            if (profile === 'normal') {
                pip.value = '15'; peep.value = '5'; compliance.value = '60.0'; resistance.value = '10'; rr.value = '16'; ie.value = '2.0';
            } else if (profile === 'ards_mild') {
                pip.value = '24'; peep.value = '10'; compliance.value = '35.0'; resistance.value = '12'; rr.value = '20'; ie.value = '1.5';
            } else if (profile === 'ards_severe') {
                pip.value = '32'; peep.value = '16'; compliance.value = '20.0'; resistance.value = '15'; rr.value = '28'; ie.value = '1.0';
            } else if (profile === 'asthma') {
                pip.value = '30'; peep.value = '4'; compliance.value = '55.0'; resistance.value = '45'; rr.value = '12'; ie.value = '4.0';
            } else if (profile === 'copd') {
                pip.value = '22'; peep.value = '5'; compliance.value = '75.0'; resistance.value = '25'; rr.value = '14'; ie.value = '3.5';
            } else if (profile === 'chf') {
                pip.value = '25'; peep.value = '12'; compliance.value = '40.0'; resistance.value = '14'; rr.value = '22'; ie.value = '2.0';
            } else if (profile === 'pe') {
                pip.value = '18'; peep.value = '5'; compliance.value = '55.0'; resistance.value = '12'; rr.value = '26'; ie.value = '2.0';
            } else if (profile === 'tbi') {
                pip.value = '18'; peep.value = '5'; compliance.value = '60.0'; resistance.value = '10'; rr.value = '22'; ie.value = '2.0';
            } else if (profile === 'fibrosis') {
                pip.value = '28'; peep.value = '8'; compliance.value = '15.0'; resistance.value = '12'; rr.value = '28'; ie.value = '1.5';
            }
        }
    </script>
</body>
</html>
"""

# --- BACKEND LOGIC ---

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
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
        fio2 = float(request.form['fio2']) / 100.0 # Convert to decimal
        
        inputs = {'pip': pip, 'peep': peep, 'compliance': compliance, 'resistance': resistance, 'rr': rr, 'ie_ratio': ie_ratio, 'ibw': ibw, 'fio2': int(fio2*100)}
        
        # --- PATHOLOGY HIDDEN VARIABLES ---
        # vco2 = Metabolic CO2 production (mL/min)
        # shunt = Right-to-Left blood shunt fraction
        # vd_vt = Dead space to tidal volume ratio
        path_vars = {
            'normal':      {'vco2': 200, 'shunt': 0.05, 'vd_vt': 0.30, 'desc': 'Healthy lung mechanics. Normal metabolic demand and gas exchange.'},
            'ards_mild':   {'vco2': 250, 'shunt': 0.15, 'vd_vt': 0.45, 'desc': 'Exudative phase ARDS. Inflammatory fluid in alveoli causing mild shunting.'},
            'ards_severe': {'vco2': 300, 'shunt': 0.35, 'vd_vt': 0.60, 'desc': 'Fibroproliferative ARDS. Severe consolidation, massive intrapulmonary shunting, and high dead space.'},
            'asthma':      {'vco2': 280, 'shunt': 0.10, 'vd_vt': 0.35, 'desc': 'Status Asthmaticus. Severe bronchoconstriction increasing airway resistance. High risk of dynamic hyperinflation.'},
            'copd':        {'vco2': 220, 'shunt': 0.15, 'vd_vt': 0.50, 'desc': 'COPD Exacerbation. Destruction of alveolar septa causing trapped gas and elevated baseline dead space.'},
            'chf':         {'vco2': 220, 'shunt': 0.20, 'vd_vt': 0.35, 'desc': 'Pulmonary Edema. Hydrostatic pressure driving fluid into alveoli. PEEP required to offset alveolar flooding.'},
            'pe':          {'vco2': 200, 'shunt': 0.10, 'vd_vt': 0.65, 'desc': 'Pulmonary Embolism. Vascular occlusion leading to extreme alveolar dead space (ventilation without perfusion).'},
            'tbi':         {'vco2': 200, 'shunt': 0.05, 'vd_vt': 0.30, 'desc': 'Traumatic Brain Injury. Lungs are healthy, but strict PaCO2 targeting (35-38 mmHg) is required to manage intracranial pressure.'},
            'fibrosis':    {'vco2': 250, 'shunt': 0.20, 'vd_vt': 0.40, 'desc': 'Pulmonary Fibrosis. Interstitial scarring causing severe restriction and diffusion impairment.'}
        }
        
        p_data = path_vars[profile_class]
        
        # --- MECHANICAL MATHEMATICS ---
        driving_pressure = max(0.1, pip - peep)
        peak_volume = round(driving_pressure * compliance, 1) # V_t in mL
        vt_kg = round(peak_volume / ibw, 1)
        
        minute_vent = (peak_volume * rr) / 1000.0 # L/min
        
        # Dead space and Alveolar Ventilation
        dead_space_vol = peak_volume * p_data['vd_vt']
        alveolar_vent = ((peak_volume - dead_space_vol) * rr) / 1000.0
        
        # Time constraints
        t_cycle = 60.0 / rr
        t_i = round(t_cycle * (1 / (1 + ie_ratio)), 2)
        t_e = round(t_cycle - t_i, 2)
        mean_pressure = round(((pip * t_i) + (peep * t_e)) / t_cycle, 1)
        
        time_constant = (resistance / 1000.0) * compliance
        auto_peep_risk = "HIGH" if t_e < (3.0 * time_constant) else "LOW"

        # --- ARTERIAL GAS ESTIMATIONS ---
        # PaCO2 Estimate
        paco2 = round((0.863 * p_data['vco2']) / max(0.1, alveolar_vent), 1)
        
        # PaO2 Estimate (Alveolar Gas Equation approximation)
        p_atm = 760
        p_h2o = 47
        rq = 0.8
        p_A_O2 = ((p_atm - p_h2o) * fio2) - (paco2 / rq)
        
        # Shunt effect: Roughly 10-20 mmHg drop per 5% shunt over baseline
        shunt_penalty = (p_data['shunt'] * 100) * 12 
        pao2 = round(max(30, p_A_O2 - shunt_penalty), 1)
        
        # --- CLINICAL NOTES LOGIC ---
        vol_note = ""
        gas_note = ""
        
        if vt_kg > 8.0:
            vol_note = f"WARNING: Tidal volume is {vt_kg} mL/kg. This exceeds protective lung thresholds (<8 mL/kg). High risk of volutrauma. Decrease PIP."
        elif vt_kg < 4.0:
            vol_note = f"Volume is heavily restricted ({vt_kg} mL/kg). May promote widespread atelectasis unless PEEP is optimized."
        else:
            vol_note = f"Volumetric targeting is nominal at {vt_kg} mL/kg. Lung protection strategies are maintained."
            
        if profile_class == 'tbi':
            if paco2 > 40: gas_note = "CRITICAL TBI ALERT: Patient is hypercapnic. CO2 vasodilation will cause lethal increases in Intracranial Pressure (ICP). Increase Minute Ventilation immediately."
            elif paco2 < 34: gas_note = "WARNING: Excessive hypocapnia. Severe cerebral vasoconstriction risk causing brain ischemia. Decrease RR."
            else: gas_note = "Target PaCO2 achieved for neuro-protection."
        else:
            if paco2 > 50 and profile_class not in ['copd', 'asthma']:
                gas_note = "Respiratory Acidosis evident. Alveolar ventilation is insufficient to clear metabolic CO2 production."
            elif profile_class == 'pe':
                gas_note = f"Massive dead space ({int(p_data['vd_vt']*100)}%) requires exceptionally high Minute Ventilation just to achieve normal PaCO2."
            elif pao2 < 60:
                gas_note = "Hypoxemic failure. Intrapulmonary shunting is too severe for current FiO2/PEEP settings. Consider PEEP titration or prone positioning."
            else:
                gas_note = "Gas exchange parameters are currently within acceptable physiological limits."

        sim_data = {
            'peak_volume': peak_volume,
            'vt_kg': vt_kg,
            'minute_vent': round(minute_vent, 2),
            'alveolar_vent': round(alveolar_vent, 2),
            'mean_pressure': mean_pressure,
            'auto_peep_risk': auto_peep_risk,
            'paco2': paco2,
            'pao2': pao2,
            'shunt_percent': int(p_data['shunt'] * 100),
            't_i': t_i,
            't_e': t_e,
            'case_description': p_data['desc'],
            'vol_note': vol_note,
            'gas_note': gas_note
        }

    return render_template_string(
        MASTER_DASHBOARD_HTML,
        active_tab=active_tab,
        sim_data=sim_data,
        inputs=inputs,
        profile_class=profile_class,
        user_role=session.get('role')
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
