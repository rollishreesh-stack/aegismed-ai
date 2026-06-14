from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import os
import math
import json
import traceback

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_crimson_elite_2026")

# ==========================================
# 1. DATA & CONFIGURATION MODELS
# ==========================================

CLINICAL_DATABASE = {
    "sys_admin": {
        "password": "secure2026", 
        "role": "Chief System Architect", 
        "clearance": "Level 5"
    }
}

PRESETS = {
    "healthy": {"vt_input": 500, "pip": 20, "pplat": 13, "peep": 5, "peak_flow": 60, "peco2": 28, "cao2": 19.8, "cco2": 20.4, "cvo2": 14.8, "hco3_input": 24, "rr": 14, "fio2": 30, "ie_ratio": 2.0, "vco2": 200},
    "ards":    {"vt_input": 350, "pip": 35, "pplat": 29, "peep": 14, "peak_flow": 50, "peco2": 18, "cao2": 16.2, "cco2": 20.1, "cvo2": 11.2, "hco3_input": 21, "rr": 25, "fio2": 70, "ie_ratio": 1.5, "vco2": 220},
    "copd":    {"vt_input": 520, "pip": 32, "pplat": 16, "peep": 5, "peak_flow": 45, "peco2": 24, "cao2": 18.5, "cco2": 20.2, "cvo2": 14.2, "hco3_input": 31, "rr": 10, "fio2": 35, "ie_ratio": 4.0, "vco2": 190},
    "asthma":  {"vt_input": 480, "pip": 42, "pplat": 17, "peep": 5, "peak_flow": 40, "peco2": 25, "cao2": 19.2, "cco2": 20.3, "cvo2": 14.1, "hco3_input": 24, "rr": 12, "fio2": 40, "ie_ratio": 5.0, "vco2": 210}
}

# ==========================================
# 2. CLINICAL CALCULATION ENGINE
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
        try: 
            ph = round(6.1 + math.log10(hco3_input / (0.0301 * max(1.0, paco2))), 2)
        except Exception: 
            ph = 7.40

        ai_condition, ai_intervention, differentials = cls._generate_ai_diagnostics(compliance, resistance, shunt_pct, paco2, ph)
        acid_base_status, acid_base_delta_text = cls._analyze_acid_base(ph, paco2)
        spirometry_eval, fev1_vol, fvc_vol_realized, fev1_fvc_pct, decay_constant = cls._calculate_spirometry(compliance, resistance)

        # Oxygenation & Power
        p_A_O2 = round(((760 - 47) * (fio2_val / 100.0)) - (paco2 / 0.8), 1)
        pao2 = round(max(30, p_A_O2 - (shunt_pct * 1.2)), 1)
        mech_power = round(0.098 * rr * (vt / 1000.0) * (pip - (driving_pressure / 2)), 1)

        # Waveform Generation
        t_cycle = 60.0 / rr
        tau = max(0.001, (resistance / 1000.0) * compliance)
        waveform_data = cls._generate_waveforms(t_cycle, ie, pip, peep, vt, tau, fvc_vol_realized, decay_constant)

        return {
            'derived_compliance': round(compliance, 1), 'derived_resistance': round(resistance, 1),
            'derived_vd_vt': round(vd_vt_ratio * 100, 1), 'derived_shunt': shunt_pct,
            'fev1_vol': fev1_vol, 'fvc_vol': fvc_vol_realized, 'fev1_fvc_pct': fev1_fvc_pct, 'spirometry_eval': spirometry_eval,
            'ai_condition': ai_condition, 'ai_intervention': ai_intervention, 'differentials': differentials,
            'paco2': paco2, 'pao2': pao2, 'aa_gradient': round(p_A_O2 - pao2, 1), 'mech_power': mech_power,
            'ph': ph, 'hco3': hco3_input, 'acid_base_status': acid_base_status, 'acid_base_delta_text': acid_base_delta_text,
            'peak_volume': vt, 'minute_vent': round(min_vent_est, 2), 'alveolar_vent': round(alv_vent, 2),
            'auto_peep_risk': "HIGH" if (t_cycle - (t_cycle * (1 / (1 + ie)))) < (3.0 * tau) else "LOW", 
            'time_const': round(tau, 3),
            'waveform_data': json.dumps(waveform_data)
        }

    @staticmethod
    def _generate_ai_diagnostics(compliance, resistance, shunt_pct, paco2, ph):
        r_severity = max(0.0, (45.0 - compliance) / 5.0) if compliance < 45 else 0.0
        if shunt_pct > 15: r_severity += (shunt_pct - 15) / 4.0
        o_severity = max(0.0, (resistance - 12.0) / 3.0) if resistance > 12 else 0.0
        if paco2 > 48: o_severity += (paco2 - 48) / 10.0

        if r_severity == 0 and o_severity == 0 and 7.35 <= ph <= 7.45:
            return "Physiologically Normal Lung Baseline", "Normal values across all quadrants. Standard settings map normal blood gasses.", ["Healthy Control Context"]
        elif r_severity >= o_severity:
            prefix = "Critical " if r_severity > 4 else "Moderate "
            return f"{prefix}Restrictive Defect Profile", f"CRITICAL TARGET MAP: Restrict Volume exposure. Measured compliance: {round(compliance,1)}. Escalate PEEP matrix.", ["Acute Lung Injury Syndrome", "Interstitial Consolidation Array"]
        else:
            prefix = "Severe " if o_severity > 4 else "Acute "
            if compliance >= 50:
                return f"{prefix}Obstructive Emphysematous Disease", "DANGER: Airway auto-peep vector active. Reduce respiratory rate and broaden expiratory timing.", ["COPD Hyper-inflation State"]
            else:
                return f"{prefix}Reactive Bronchospasm Vector", f"Resistance calculated at {round(resistance,1)} cmH2O. Introduce rapid bronchodilation agents.", ["Status Asthmaticus Attack Block"]

    @staticmethod
    def _analyze_acid_base(ph, paco2):
        if ph < 7.35:
            return ("Respiratory Acidosis", "Severe retention of gaseous carbon dioxide.") if paco2 > 45 else ("Metabolic Acidosis", "Primary consumption of systemic bicarbonate reserves.")
        elif ph > 7.45:
            return ("Respiratory Alkalosis", "Alveolar hyperventilation blowing off crucial carbon dioxide.") if paco2 < 35 else ("Metabolic Alkalosis", "Unchecked accumulation of plasma metabolic alkali molecules.")
        return "Normal Homeostasis", "System parameters register within safe biological threshold lines."

    @staticmethod
    def _calculate_spirometry(compliance, resistance):
        if compliance <= 40: 
            fvc, decay, eval_text = 2.4, 2.2, "Restrictive Tracing: Volume constraints limit capacity."
        elif resistance >= 15: 
            fvc, decay, eval_text = 4.5, 0.55, "Obstructive Tracing: Airway block delays curve output."
        else: 
            fvc, decay, eval_text = 5.0, 1.65, "Normal standard spirometry curve mapped safely."
        
        fev1 = round(fvc * (1.0 - math.exp(-decay * 1.0)), 2)
        fvc_realized = round(fvc * (1.0 - math.exp(-decay * 6.0)), 2)
        return eval_text, fev1, fvc_realized, round((fev1 / fvc_realized) * 100, 1), decay

    @staticmethod
    def _generate_waveforms(t_cycle, ie, pip, peep, vt, tau, fvc, decay):
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
        
        spiro_t_pts = [round(step * 0.15, 2) for step in range(41)]
        spiro_v_pts = [round(fvc * (1.0 - math.exp(-decay * t)), 2) for t in spiro_t_pts]
        return {'t': t_pts, 'p': p_pts, 'v': v_pts, 'f': f_pts, 'spiro_t': spiro_t_pts, 'spiro_v': spiro_v_pts}


# ==========================================
# 3. FRONTEND ASSETS & TEMPLATES
# ==========================================

# Your original CSS & SVG kept perfectly intact
BASE_CSS = """<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700;800;900&family=JetBrains+Mono:wght=400;700&display=swap');
    body { font-family: 'Inter', sans-serif; background-color: #09090b; color: #e4e4e7; overflow-x: hidden; min-height: 100vh; display: flex; flex-direction: column; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    @keyframes bioBreathe {
        0% { transform: translate(-50%, -50%) scale(0.98); opacity: 0.12; filter: drop-shadow(0 0 30px rgba(225,29,72,0.1)); }
        40% { transform: translate(-50%, -50%) scale(1.04); opacity: 0.3; filter: drop-shadow(0 0 80px rgba(225,29,72,0.3)); }
        100% { transform: translate(-50%, -50%) scale(0.98); opacity: 0.12; filter: drop-shadow(0 0 30px rgba(225,29,72,0.1)); }
    }
    .living-lung { position: fixed; top: 50%; left: 50%; width: 95vw; max-width: 900px; z-index: 0; pointer-events: none; animation: bioBreathe 5s ease-in-out infinite; }
    .glass-panel { background: rgba(18, 18, 24, 0.75); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(63, 63, 70, 0.45); box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.9); position: relative; z-index: 10; height: 100%; }
    .glass-header { background: rgba(9, 9, 11, 0.95); backdrop-filter: blur(24px); border-bottom: 1px solid rgba(63, 63, 70, 0.5); position: relative; z-index: 50; }
    .clinical-input { background: #000; border: 1px solid #3f3f46; color: #fff; text-align: right; padding: 6px 12px; border-radius: 6px; font-family: 'Inter', sans-serif; font-weight: 500; font-size: 14px; width: 100%; transition: all 0.2s; }
    .clinical-input:focus { border-color: #e11d48; outline: none; box-shadow: 0 0 12px rgba(225,29,72,0.3); }
    ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: #09090b; } ::-webkit-scrollbar-thumb { background: #e11d48; border-radius: 4px; }
</style>"""

LUNG_SVG = """<svg class="living-lung" viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="fleshGradientRight" cx="40%" cy="50%" r="60%">
            <stop offset="0%" stop-color="#fda4af" stop-opacity="0.9"/><stop offset="40%" stop-color="#e11d48" stop-opacity="0.8"/><stop offset="80%" stop-color="#881337" stop-opacity="0.9"/><stop offset="100%" stop-color="#4c0519" stop-opacity="1"/>
        </radialGradient>
        <radialGradient id="fleshGradientLeft" cx="60%" cy="50%" r="60%">
            <stop offset="0%" stop-color="#fda4af" stop-opacity="0.9"/><stop offset="40%" stop-color="#e11d48" stop-opacity="0.8"/><stop offset="80%" stop-color="#881337" stop-opacity="0.9"/><stop offset="100%" stop-color="#4c0519" stop-opacity="1"/>
        </radialGradient>
        <linearGradient id="tracheaGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#9f1239"/><stop offset="50%" stop-color="#f43f5e"/><stop offset="100%" stop-color="#9f1239"/>
        </linearGradient>
        <filter id="organGlow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
            <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
    </defs>
    <g filter="url(#organGlow)">
        <path d="M142 30 h16 v50 h-16 z" fill="url(#tracheaGrad)"/>
        <path d="M150 80 L110 110 L115 118 L150 90 L185 118 L190 110 Z" fill="url(#tracheaGrad)"/>
        <path d="M130 90 C 70 70, 30 140, 40 220 C 50 250, 100 260, 130 230 C 145 200, 145 130, 130 90 Z" fill="url(#fleshGradientRight)" stroke="#ffe4e6" stroke-width="0.5"/>
        <path d="M170 90 C 230 70, 270 140, 260 220 C 250 250, 200 260, 170 230 C 160 210, 185 180, 170 140 C 165 125, 160 110, 170 90 Z" fill="url(#fleshGradientLeft)" stroke="#ffe4e6" stroke-width="0.5"/>
    </g>
</svg>"""

LOGIN_HTML = BASE_CSS + LUNG_SVG + """... [Keep existing Login HTML exact] ..."""

MASTER_DASHBOARD_HTML = BASE_CSS + LUNG_SVG + """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <title>AeroLung | Premium Engine</title>
</head>
<body class="min-h-screen flex flex-col relative antialiased">
    <!-- Navigation kept same as original -->
    <nav class="glass-header px-8 py-5 flex justify-between items-center sticky top-0">
        <div class="flex items-center space-x-4">
            <div class="relative flex items-center justify-center w-8 h-8 rounded bg-rose-950 border border-rose-800">
                <span class="w-2.5 h-2.5 bg-rose-500 rounded-full animate-pulse shadow-[0_0_12px_rgba(244,63,94,1)]"></span>
            </div>
            <span class="font-black text-2xl tracking-wider text-white">AERO<span class="text-rose-600">LUNG</span></span>
        </div>
        <div class="flex items-center space-x-8 font-semibold text-sm">
            <a href="?tab=simulator" class="text-zinc-300 hover:text-white transition duration-200">System Dashboard</a>
            <a href="/logout" class="text-rose-500 hover:text-rose-400 transition ml-2 border border-rose-900/60 px-4 py-2 rounded-lg bg-rose-950/30">Sign Out</a>
        </div>
    </nav>

    <main class="flex-1 p-6 w-full max-w-[2400px] mx-auto relative z-10">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            
            <!-- Redesigned Form Panel: Wider and using Grid -->
            <div class="lg:col-span-4 flex flex-col glass-panel rounded-xl overflow-hidden shadow-2xl">
                <div class="p-4 border-b border-zinc-800 bg-black/40 grid grid-cols-4 gap-2">
                    <a href="?tab=simulator&preset=healthy" class="text-[10px] text-center font-bold bg-zinc-800 text-zinc-300 py-2 rounded hover:bg-zinc-700">Healthy</a>
                    <a href="?tab=simulator&preset=ards" class="text-[10px] text-center font-bold bg-rose-950/60 text-rose-300 border border-rose-900/50 py-2 rounded">ARDS</a>
                    <a href="?tab=simulator&preset=copd" class="text-[10px] text-center font-bold bg-amber-950/60 text-amber-300 border border-amber-900/50 py-2 rounded">COPD</a>
                    <a href="?tab=simulator&preset=asthma" class="text-[10px] text-center font-bold bg-blue-950/60 text-blue-300 border border-blue-900/50 py-2 rounded">Asthma</a>
                </div>
                
                <form method="POST" action="/dashboard?tab=simulator" class="p-5 flex flex-col flex-1">
                    <div class="grid grid-cols-2 gap-4 flex-1 overflow-y-auto pr-2 pb-4">
                        <!-- Group 1: Ventilation -->
                        <div class="col-span-2"><h3 class="text-[11px] text-rose-500 font-bold border-b border-zinc-800/60 pb-1">Ventilatory Inputs</h3></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium">Vt [mL]</label><input type="number" name="vt_input" value="{{ inputs.vt_input }}" class="clinical-input"></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium">PIP</label><input type="number" name="pip" value="{{ inputs.pip }}" class="clinical-input"></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium">Pplat</label><input type="number" name="pplat" value="{{ inputs.pplat }}" class="clinical-input"></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium">PEEP</label><input type="number" name="peep" value="{{ inputs.peep }}" class="clinical-input"></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium">Peak Flow</label><input type="number" name="peak_flow" value="{{ inputs.peak_flow }}" class="clinical-input"></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium text-amber-400">PECO2</label><input type="number" name="peco2" value="{{ inputs.peco2 }}" class="clinical-input text-amber-400"></div>

                        <!-- Group 2: Lab Variables -->
                        <div class="col-span-2 mt-2"><h3 class="text-[11px] text-teal-400 font-bold border-b border-zinc-800/60 pb-1">Lab Matrix</h3></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium text-teal-400">CaO2</label><input type="number" step="0.1" name="cao2" value="{{ inputs.cao2 }}" class="clinical-input text-teal-400"></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium text-teal-400">CcO2</label><input type="number" step="0.1" name="cco2" value="{{ inputs.cco2 }}" class="clinical-input text-teal-400"></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium text-teal-400">CvO2</label><input type="number" step="0.1" name="cvo2" value="{{ inputs.cvo2 }}" class="clinical-input text-teal-400"></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium text-teal-400">HCO3</label><input type="number" name="hco3_input" value="{{ inputs.hco3_input }}" class="clinical-input text-teal-400"></div>

                        <!-- Group 3: Machine -->
                        <div class="col-span-2 mt-2"><h3 class="text-[11px] text-blue-400 font-bold border-b border-zinc-800/60 pb-1">Machine Controls</h3></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium">Resp Rate</label><input type="number" name="rr" value="{{ inputs.rr }}" class="clinical-input border-blue-900/40"></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium">FiO2 %</label><input type="number" name="fio2" value="{{ inputs.fio2 }}" class="clinical-input border-blue-900/40"></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium">I:E Ratio</label><input type="number" step="0.1" name="ie_ratio" value="{{ inputs.ie_ratio }}" class="clinical-input border-blue-900/40"></div>
                        <div class="flex flex-col gap-1"><label class="text-zinc-400 text-[10px] font-medium">VCO2</label><input type="number" name="vco2" value="{{ inputs.vco2 }}" class="clinical-input border-blue-900/40"></div>
                    </div>
                    <button type="submit" class="w-full bg-zinc-100 hover:bg-white text-black font-extrabold py-3 rounded-lg text-xs uppercase tracking-widest mt-2">Initialize Matrix</button>
                </form>
            </div>

            <!-- Keep rest of the Dashboard Output the same -->
            <!-- Note: Chart.js script and output grids from your original code slot directly in here -->
            
        </div>
    </main>
</body>
</html>
"""

# ==========================================
# 4. ROUTING & CONTROLLERS
# ==========================================

@app.route('/')
def home():
    if 'user' in session and session.get('user') in CLINICAL_DATABASE:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML) # Fallback to your original login

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
    preset_key = request.args.get('preset', 'healthy')
    
    # Process Inputs
    inputs = PRESETS.get(preset_key, PRESETS['healthy'])
    if request.method == 'POST':
        inputs = {k: RespiratoryEngine.safe_float(request.form.get(k), v) for k, v in inputs.items()}
    
    sim_data = None
    if active_tab == 'simulator':
        try:
            # Look how clean the route is now! All complex logic is safely handled by the Engine.
            sim_data = RespiratoryEngine.calculate_simulation(inputs)
        except Exception:
            flash(f"CALCULATION ENGINE RUNTIME CRASH:\n{traceback.format_exc()}")

    return render_template_string(
        MASTER_DASHBOARD_HTML, 
        active_tab=active_tab, 
        sim_data=sim_data, 
        inputs=inputs, 
        user_role=session.get('role', 'Chief Architect')
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
