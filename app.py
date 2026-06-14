import os
import math
import json
import sqlite3
import traceback
from flask import Flask, request, redirect, url_for, session, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_clinical_secure_2026")
DB_NAME = "aerolung_clinical.db"

# ==========================================
# 1. DATABASE INITIALIZATION
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
    
    # Create default Admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed_pw = generate_password_hash('admin2026')
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  ('admin', hashed_pw, 'Chief Pulmonologist'))
    
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. CLINICAL CALCULATION ENGINE (Your Original Math)
# ==========================================
class RespiratoryEngine:
    @staticmethod
    def safe_float(val, default):
        try:
            if val is None or str(val).strip() == '': return float(default)
            return float(val)
        except ValueError:
            return float(default)

    @classmethod
    def calculate_simulation(cls, inputs):
        """Processes raw physiological inputs into actionable clinical matrices."""
        vt = max(10.0, inputs['vt_input'])
        pip = max(1.0, inputs['pip'])
        pplat = max(1.0, inputs['pplat'])
        peep = max(0.0, inputs['peep'])
        flow_lmin = max(5.0, inputs['peak_flow'])
        peco2 = max(0.1, inputs['peco2'])
        cao2, cco2, cvo2 = inputs['cao2'], inputs['cco2'], inputs['cvo2']
        hco3_input = max(0.1, inputs['hco3_input'])
        rr = max(1.0, inputs['rr'])
        ie = max(0.1, inputs['ie_ratio'])
        vco2 = max(10.0, inputs['vco2'])
        fio2_val = inputs['fio2']

        # Core Mechanics
        driving_pressure = max(0.1, pplat - peep)
        compliance = vt / driving_pressure
        flow_lsec = flow_lmin / 60.0
        resistance = max(0.1, (pip - pplat) / flow_lsec)
        
        # Ventilation & Gas Exchange
        min_vent_est = (vt * rr) / 1000.0
        paco2_derived = max(1.0, (0.863 * vco2) / max(0.1, min_vent_est * 0.75))
        if peco2 >= paco2_derived: 
            peco2 = max(0.1, paco2_derived - 4.0)
            
        vd_vt_ratio = max(0.01, min(0.95, (paco2_derived - peco2) / paco2_derived))
        shunt_denominator = max(0.1, cco2 - cvo2)
        shunt_ratio = (cco2 - cao2) / shunt_denominator
        shunt_pct = round(max(0.01, min(0.95, shunt_ratio)) * 100, 1)

        alv_vent = max(0.1, ((vt * (1 - vd_vt_ratio)) * rr) / 1000.0)
        paco2 = round((0.863 * vco2) / alv_vent, 1)
        
        # Acid-Base Status
        try: ph = round(6.1 + math.log10(hco3_input / (0.0301 * max(1.0, paco2))), 2)
        except Exception: ph = 7.40

        ai_condition, ai_intervention = cls._generate_ai_diagnostics(compliance, resistance, shunt_pct, paco2, ph)
        acid_base_status, acid_base_delta_text = cls._analyze_acid_base(ph, paco2)

        # Oxygenation
        p_A_O2 = round(((760 - 47) * (fio2_val / 100.0)) - (paco2 / 0.8), 1)
        pao2 = round(max(30, p_A_O2 - (shunt_pct * 1.2)), 1)

        # Waveforms
        t_cycle = 60.0 / rr
        tau = max(0.001, (resistance / 1000.0) * compliance)
        waveform_data = cls._generate_waveforms(t_cycle, ie, pip, peep, vt, tau)

        return {
            'compliance': round(compliance, 1), 
            'resistance': round(resistance, 1),
            'vd_vt': round(vd_vt_ratio * 100, 1), 
            'shunt': shunt_pct,
            'ai_condition': ai_condition, 
            'ai_intervention': ai_intervention, 
            'paco2': paco2, 
            'pao2': pao2, 
            'ph': ph, 
            'hco3': hco3_input, 
            'acid_base_status': acid_base_status, 
            'minute_vent': round(min_vent_est, 2),
            'waveform_data': json.dumps(waveform_data)
        }

    @staticmethod
    def _generate_ai_diagnostics(compliance, resistance, shunt_pct, paco2, ph):
        if compliance < 40:
            return "Restrictive Lung Defect", "Compliance is critically low. Consider lung protective ventilation (low Vt) and titrating PEEP to recruit alveoli."
        elif resistance > 15:
            return "Obstructive Airway Disease", "High airway resistance detected. Risk of Auto-PEEP is high. Administer bronchodilators and prolong expiratory time."
        elif shunt_pct > 20:
            return "Severe Hypoxemic Failure", "Significant intrapulmonary shunting. Increase FiO2 and consider prone positioning if ARDS is suspected."
        else:
            return "Stable Pulmonary Mechanics", "Ventilatory parameters are within acceptable clinical limits. Maintain current support."

    @staticmethod
    def _analyze_acid_base(ph, paco2):
        if ph < 7.35:
            return ("Respiratory Acidosis", "Hypoventilation causing CO2 retention.") if paco2 > 45 else ("Metabolic Acidosis", "Systemic bicarbonate depletion.")
        elif ph > 7.45:
            return ("Respiratory Alkalosis", "Hyperventilation blowing off excessive CO2.") if paco2 < 35 else ("Metabolic Alkalosis", "Accumulation of systemic alkali.")
        return "Normal Acid-Base Balance", "Blood gas parameters are within normal biological thresholds."

    @staticmethod
    def _generate_waveforms(t_cycle, ie, pip, peep, vt, tau):
        t_i = t_cycle * (1 / (1 + ie))
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
        return {'t': t_pts, 'p': p_pts, 'v': v_pts, 'f': f_pts}

# ==========================================
# 3. CLEAN PROFESSIONAL UI TEMPLATES
# ==========================================

GLOBAL_CSS = """
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Inter', sans-serif; background-color: #f1f5f9; color: #334155; }
    .card { background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); border: 1px solid #e2e8f0; }
    .input-field { width: 100%; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; color: #0f172a; transition: border-color 0.2s; }
    .input-field:focus { outline: none; border-color: #0284c7; box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.1); }
</style>
"""

LOGIN_HTML = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>AeroLung | Login</title>{GLOBAL_CSS}</head>
<body class="h-screen flex items-center justify-center bg-slate-100">
    <div class="card p-8 w-full max-w-sm">
        <div class="text-center mb-8">
            <h1 class="text-3xl font-bold text-slate-800 tracking-tight">Aero<span class="text-sky-600">Lung</span></h1>
            <p class="text-sm text-slate-500 mt-1">Clinical Assessment Portal</p>
        </div>
        
        {{% if get_flashed_messages() %}}
            <div class="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-md border border-red-200">
                {{% for msg in get_flashed_messages() %}} {{ msg }} {{% endfor %}}
            </div>
        {{% endif %}}

        <form action="/login" method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">User ID</label>
                <input type="text" name="username" class="input-field" required>
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
                <input type="password" name="password" class="input-field" required>
            </div>
            <button type="submit" class="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-2.5 rounded-md transition-colors mt-2">
                Sign In
            </button>
        </form>
    </div>
</body></html>
"""

DASHBOARD_HTML = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>AeroLung | Dashboard</title>{GLOBAL_CSS}</head>
<body class="min-h-screen flex flex-col">
    <header class="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center">
        <div class="text-xl font-bold text-slate-800 tracking-tight">Aero<span class="text-sky-600">Lung</span></div>
        <div class="flex items-center gap-4">
            <span class="text-sm font-medium text-slate-600">Dr. {{ session.user }}</span>
            <a href="/logout" class="text-sm text-slate-500 hover:text-slate-800 border border-slate-300 px-3 py-1.5 rounded hover:bg-slate-50 transition-colors">Sign Out</a>
        </div>
    </header>

    <main class="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <div class="lg:col-span-4 flex flex-col gap-6">
            <div class="card p-5">
                <h2 class="text-lg font-semibold text-slate-800 mb-4 border-b pb-2">Clinical Inputs</h2>
                <form method="POST" action="/dashboard" class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">Vt (mL)</label><input type="number" name="vt_input" value="500" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">Resp Rate</label><input type="number" name="rr" value="14" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">PIP</label><input type="number" name="pip" value="25" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">Pplat</label><input type="number" name="pplat" value="18" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">PEEP</label><input type="number" name="peep" value="5" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">Flow (L/m)</label><input type="number" name="peak_flow" value="60" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">FiO2 (%)</label><input type="number" name="fio2" value="40" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">I:E Ratio</label><input type="number" step="0.1" name="ie_ratio" value="2.0" class="input-field"></div>
                        
                        <div class="col-span-2 pt-2"><h3 class="text-sm font-medium text-slate-700 border-b pb-1">Blood Gas / Labs</h3></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">CaO2</label><input type="number" step="0.1" name="cao2" value="19.8" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">CvO2</label><input type="number" step="0.1" name="cvo2" value="14.8" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">CcO2</label><input type="number" step="0.1" name="cco2" value="20.4" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">PECO2</label><input type="number" name="peco2" value="28" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">VCO2</label><input type="number" name="vco2" value="200" class="input-field"></div>
                        <div><label class="block text-xs font-medium text-slate-500 mb-1">HCO3</label><input type="number" name="hco3_input" value="24" class="input-field"></div>
                    </div>
                    <button type="submit" class="w-full bg-sky-600 hover:bg-sky-700 text-white font-medium py-2.5 rounded-md transition-colors mt-4">
                        Calculate Mechanics
                    </button>
                </form>
            </div>
        </div>

        <div class="lg:col-span-8 flex flex-col gap-6">
            {{% if not sim_data %}}
            <div class="card flex-1 flex items-center justify-center min-h-[400px] bg-slate-50">
                <p class="text-slate-500 font-medium">Input clinical parameters to generate assessment.</p>
            </div>
            {{% else %}}
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="card p-6 border-l-4 border-sky-500">
                    <h3 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">Clinical Assessment</h3>
                    <div class="text-xl font-bold text-slate-800 mb-2">{{ sim_data.ai_condition }}</div>
                    <p class="text-sm text-slate-600 leading-relaxed">{{ sim_data.ai_intervention }}</p>
                </div>
                
                <div class="card p-6 border-l-4 border-indigo-500">
                    <h3 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">Acid-Base Balance</h3>
                    <div class="flex gap-6 mb-2">
                        <div><span class="block text-xs text-slate-500">pH</span><span class="text-xl font-bold text-slate-800">{{ sim_data.ph }}</span></div>
                        <div><span class="block text-xs text-slate-500">PaCO2</span><span class="text-xl font-bold text-slate-800">{{ sim_data.paco2 }}</span></div>
                        <div><span class="block text-xs text-slate-500">HCO3</span><span class="text-xl font-bold text-slate-800">{{ sim_data.hco3 }}</span></div>
                    </div>
                    <div class="text-sm font-medium text-slate-800">{{ sim_data.acid_base_status }}</div>
                </div>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="card p-4 text-center">
                    <div class="text-xs font-semibold text-slate-500 uppercase mb-1">Compliance</div>
                    <div class="text-2xl font-bold text-sky-600">{{ sim_data.compliance }}</div>
                    <div class="text-xs text-slate-400">mL/cmH2O</div>
                </div>
                <div class="card p-4 text-center">
                    <div class="text-xs font-semibold text-slate-500 uppercase mb-1">Resistance</div>
                    <div class="text-2xl font-bold text-rose-500">{{ sim_data.resistance }}</div>
                    <div class="text-xs text-slate-400">cmH2O/L/s</div>
                </div>
                <div class="card p-4 text-center">
                    <div class="text-xs font-semibold text-slate-500 uppercase mb-1">Vd/Vt (Dead Space)</div>
                    <div class="text-2xl font-bold text-slate-700">{{ sim_data.vd_vt }}%</div>
                </div>
                <div class="card p-4 text-center">
                    <div class="text-xs font-semibold text-slate-500 uppercase mb-1">Shunt Fraction</div>
                    <div class="text-2xl font-bold text-slate-700">{{ sim_data.shunt }}%</div>
                </div>
            </div>

            <div class="card p-5 h-[300px] flex flex-col">
                <h3 class="text-sm font-bold text-slate-600 mb-4">Ventilator Waveforms</h3>
                <div class="flex-1 relative"><canvas id="waveChart"></canvas></div>
            </div>

            <script>
                const data = {{ sim_data.waveform_data | safe }};
                new Chart(document.getElementById('waveChart'), {{
                    type: 'line',
                    data: {{
                        labels: data.t,
                        datasets: [
                            {{ label: 'Pressure', data: data.p, borderColor: '#0284c7', borderWidth: 2, pointRadius: 0, tension: 0.1 }},
                            {{ label: 'Volume', data: data.v, borderColor: '#10b981', borderWidth: 2, pointRadius: 0, tension: 0.1 }},
                            {{ label: 'Flow', data: data.f, borderColor: '#f43f5e', borderWidth: 2, pointRadius: 0, tension: 0.1 }}
                        ]
                    }},
                    options: {{
                        responsive: true, maintainAspectRatio: false,
                        interaction: {{ mode: 'index', intersect: false }},
                        scales: {{ 
                            x: {{ grid: {{ display: false }} }}, 
                            y: {{ grid: {{ color: '#f1f5f9' }} }} 
                        }}
                    }}
                }});
            </script>
            {{% endif %}}
        </div>
    </main>
</body></html>
"""

# ==========================================
# 4. ROUTES
# ==========================================

@app.route('/')
def home():
    if 'user' in session: return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row and check_password_hash(row[0], password):
        session['user'] = username
        return redirect(url_for('dashboard'))
    
    flash("Invalid credentials.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    
    sim_data = None
    if request.method == 'POST':
        inputs = {k: RespiratoryEngine.safe_float(request.form.get(k), 0) for k in request.form}
        try:
            sim_data = RespiratoryEngine.calculate_simulation(inputs)
        except Exception:
            flash(f"Error calculating metrics: {traceback.format_exc()}")

    return render_template_string(DASHBOARD_HTML, sim_data=sim_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
