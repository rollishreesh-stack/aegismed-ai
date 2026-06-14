from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import os
import math
import json
import traceback

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_ultimate_matrix_2026")

# ==========================================
# 1. DATABASE & PRESETS
# ==========================================

CLINICAL_DATABASE = {
    "sys_admin": {
        "password": "secure2026", 
        "role": "Chief Systems Architect", 
        "clearance": "Level 5 Omni-Access"
    }
}

PRESETS = {
    "healthy": {"vt_input": 500, "pip": 20, "pplat": 13, "peep": 5, "peak_flow": 60, "peco2": 28, "cao2": 19.8, "cco2": 20.4, "cvo2": 14.8, "hco3_input": 24, "rr": 14, "fio2": 30, "ie_ratio": 2.0, "vco2": 200},
    "ards":    {"vt_input": 350, "pip": 35, "pplat": 29, "peep": 14, "peak_flow": 50, "peco2": 18, "cao2": 16.2, "cco2": 20.1, "cvo2": 11.2, "hco3_input": 21, "rr": 25, "fio2": 70, "ie_ratio": 1.5, "vco2": 220},
    "copd":    {"vt_input": 520, "pip": 32, "pplat": 16, "peep": 5, "peak_flow": 45, "peco2": 24, "cao2": 18.5, "cco2": 20.2, "cvo2": 14.2, "hco3_input": 31, "rr": 10, "fio2": 35, "ie_ratio": 4.0, "vco2": 190},
    "asthma":  {"vt_input": 480, "pip": 42, "pplat": 17, "peep": 5, "peak_flow": 40, "peco2": 25, "cao2": 19.2, "cco2": 20.3, "cvo2": 14.1, "hco3_input": 24, "rr": 12, "fio2": 40, "ie_ratio": 5.0, "vco2": 210}
}

# ==========================================
# 2. ADVANCED CLINICAL ENGINE
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
            'auto_peep_risk': "CRITICAL" if (t_cycle - (t_cycle * (1 / (1 + ie)))) < (3.0 * tau) else "LOW", 
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
            return "NORMAL PHYSIOLOGY BASELINE", "System stable. Maintain current ventilator parameters. Continue to monitor blood gases.", ["Healthy Control", "No Intervention Required"]
        elif r_severity >= o_severity:
            return "RESTRICTIVE LUNG DEFECT", f"TARGET MAP: Restrict Volume. Compliance critically low at {round(compliance,1)}. Escalate PEEP to recruit collapsed alveoli.", ["ARDS", "Pulmonary Fibrosis", "Atelectasis"]
        else:
            if compliance >= 50:
                return "OBSTRUCTIVE EMPHYSEMATOUS DISEASE", "DANGER: High risk of Auto-PEEP. Decrease respiratory rate to allow full exhalation. Broaden I:E ratio.", ["COPD", "Hyperinflation State"]
            else:
                return "ACUTE BRONCHOSPASM", f"Resistance severely elevated at {round(resistance,1)} cmH2O. Administer bronchodilators immediately. Monitor peak pressures.", ["Status Asthmaticus", "Airway Inflammation"]

    @staticmethod
    def _analyze_acid_base(ph, paco2):
        if ph < 7.35:
            return ("Respiratory Acidosis", "Hypoventilation causing CO2 retention.") if paco2 > 45 else ("Metabolic Acidosis", "Systemic bicarbonate depletion.")
        elif ph > 7.45:
            return ("Respiratory Alkalosis", "Hyperventilation blowing off excessive CO2.") if paco2 < 35 else ("Metabolic Alkalosis", "Accumulation of systemic alkali.")
        return "Normal Homeostasis", "Blood gas parameters are within normal biological thresholds."

    @staticmethod
    def _calculate_spirometry(compliance, resistance):
        if compliance <= 40: fvc, decay, eval_text = 2.4, 2.2, "Restrictive pattern: Decreased FVC."
        elif resistance >= 15: fvc, decay, eval_text = 4.5, 0.55, "Obstructive pattern: Delayed exhalation."
        else: fvc, decay, eval_text = 5.0, 1.65, "Normal spirometry tracing."
        
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
# 3. PREMIUM HTML/CSS TEMPLATES
# ==========================================

BASE_CSS_SVG = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700;900&family=JetBrains+Mono:wght=400;700&display=swap');
    body { font-family: 'Inter', sans-serif; background-color: #050505; color: #e4e4e7; overflow-x: hidden; min-height: 100vh; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    
    @keyframes bioBreathe {
        0% { transform: translate(-50%, -50%) scale(0.95); opacity: 0.08; filter: drop-shadow(0 0 20px rgba(225,29,72,0.1)); }
        50% { transform: translate(-50%, -50%) scale(1.05); opacity: 0.25; filter: drop-shadow(0 0 60px rgba(225,29,72,0.4)); }
        100% { transform: translate(-50%, -50%) scale(0.95); opacity: 0.08; filter: drop-shadow(0 0 20px rgba(225,29,72,0.1)); }
    }
    .living-lung { position: fixed; top: 50%; left: 50%; width: 100vw; max-width: 1000px; z-index: 0; pointer-events: none; animation: bioBreathe 6s ease-in-out infinite; }
    
    .glass-card { background: rgba(15, 15, 20, 0.7); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.05); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8); border-radius: 16px; position: relative; z-index: 10; overflow: hidden; }
    .glass-header { background: rgba(5, 5, 5, 0.85); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.05); position: sticky; top: 0; z-index: 50; }
    
    .input-field { background: #000; border: 1px solid #27272a; color: #fff; padding: 8px 12px; border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 13px; text-align: right; width: 100%; transition: all 0.3s; }
    .input-field:focus { border-color: #e11d48; outline: none; box-shadow: 0 0 15px rgba(225,29,72,0.4); background: #18181b; }
    
    .stat-box { background: linear-gradient(180deg, rgba(24,24,27,0.5) 0%, rgba(9,9,11,0.8) 100%); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; transition: transform 0.2s; }
    .stat-box:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.1); }
    
    ::-webkit-scrollbar { width: 8px; } ::-webkit-scrollbar-track { background: #050505; } ::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 4px; } ::-webkit-scrollbar-thumb:hover { background: #e11d48; }
</style>

<svg class="living-lung" viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="fleshGrad" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stop-color="#fda4af" stop-opacity="0.8"/><stop offset="50%" stop-color="#be123c" stop-opacity="0.8"/><stop offset="100%" stop-color="#4c0519" stop-opacity="1"/>
        </radialGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>
    <g filter="url(#glow)">
        <path d="M145 20 h10 v60 h-10 z" fill="#9f1239"/>
        <path d="M150 80 L110 115 L115 125 L150 95 L185 125 L190 115 Z" fill="#9f1239"/>
        <path d="M130 95 C 60 70, 20 150, 35 230 C 50 270, 110 270, 130 230 C 145 190, 140 130, 130 95 Z" fill="url(#fleshGrad)"/>
        <path d="M170 95 C 240 70, 280 150, 265 230 C 250 270, 190 270, 170 230 C 155 190, 160 130, 170 95 Z" fill="url(#fleshGrad)"/>
    </g>
</svg>
"""

LOGIN_HTML = BASE_CSS_SVG + """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>AeroLung | Neural Login</title>
</head>
<body class="flex items-center justify-center h-screen">
    <div class="glass-card p-10 w-full max-w-md shadow-[0_0_80px_rgba(225,29,72,0.15)]">
        <div class="text-center mb-10">
            <h1 class="text-5xl font-black tracking-tighter text-white drop-shadow-lg">AERO<span class="text-rose-600">LUNG</span></h1>
            <p class="text-rose-500/80 mt-2 font-mono text-xs uppercase tracking-[0.3em]">Matrix Initialization</p>
        </div>
        {% if get_flashed_messages() %}
            <div class="mb-6 p-3 text-center text-xs font-mono bg-rose-950/40 text-rose-400 border border-rose-900/50 rounded">{{ get_flashed_messages()[0] }}</div>
        {% endif %}
        <form method="POST" action="/login" class="space-y-5">
            <div>
                <label class="block text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-1.5 ml-1">Architect ID</label>
                <input type="text" name="username" class="input-field text-left" required>
            </div>
            <div>
                <label class="block text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-1.5 ml-1">Secure Passkey</label>
                <input type="password" name="password" class="input-field text-left" required>
            </div>
            <button type="submit" class="w-full bg-rose-600 hover:bg-rose-500 text-white font-bold py-4 rounded-xl text-xs uppercase tracking-[0.2em] transition-all shadow-[0_0_20px_rgba(225,29,72,0.4)] hover:shadow-[0_0_30px_rgba(225,29,72,0.6)] mt-4">
                Uplink Terminal
            </button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = BASE_CSS_SVG + """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <title>AeroLung | Master Command</title>
</head>
<body class="min-h-screen flex flex-col">

    <nav class="glass-header px-8 py-4 flex justify-between items-center">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-600 to-rose-950 flex items-center justify-center shadow-[0_0_20px_rgba(225,29,72,0.4)] border border-rose-500/50">
                <div class="w-3 h-3 bg-white rounded-full animate-ping"></div>
            </div>
            <span class="font-black text-3xl tracking-tighter text-white">AERO<span class="text-rose-600">LUNG</span></span>
        </div>
        <div class="flex items-center space-x-6">
            <div class="text-right hidden md:block border-r border-zinc-800 pr-6">
                <div class="text-white text-sm font-bold">{{ session.get('role', 'Admin') }}</div>
                <div class="text-emerald-500 text-[10px] font-mono tracking-widest uppercase">System Online</div>
            </div>
            <a href="/logout" class="text-xs font-bold text-rose-400 hover:text-white border border-rose-900/50 bg-rose-950/20 px-5 py-2.5 rounded-lg transition-all hover:bg-rose-600">TERMINATE</a>
        </div>
    </nav>

    <main class="flex-1 p-6 w-full max-w-[2560px] mx-auto z-10 grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        
        <div class="xl:col-span-3 flex flex-col gap-4">
            <div class="glass-card">
                <div class="p-4 border-b border-zinc-800/50 flex justify-between items-center bg-black/20">
                    <h2 class="text-xs font-black text-white uppercase tracking-widest flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-blue-500"></span> Input Matrix
                    </h2>
                </div>
                
                <div class="p-3 grid grid-cols-4 gap-2 bg-zinc-900/30 border-b border-zinc-800/50">
                    <a href="?preset=healthy" class="text-[10px] text-center font-bold bg-zinc-800 text-zinc-300 py-2 rounded hover:bg-zinc-700">Norm</a>
                    <a href="?preset=ards" class="text-[10px] text-center font-bold bg-rose-950/40 text-rose-400 border border-rose-900/50 py-2 rounded">ARDS</a>
                    <a href="?preset=copd" class="text-[10px] text-center font-bold bg-amber-950/40 text-amber-400 border border-amber-900/50 py-2 rounded">COPD</a>
                    <a href="?preset=asthma" class="text-[10px] text-center font-bold bg-blue-950/40 text-blue-400 border border-blue-900/50 py-2 rounded">Asthma</a>
                </div>

                <form method="POST" action="/dashboard" class="p-5">
                    <div class="space-y-6 max-h-[60vh] overflow-y-auto pr-2">
                        <div>
                            <h3 class="text-[10px] text-zinc-500 font-bold uppercase tracking-widest mb-3 border-b border-zinc-800/50 pb-1">Mechanics</h3>
                            <div class="grid grid-cols-2 gap-3">
                                <div><label class="text-[9px] text-zinc-400 uppercase font-bold block mb-1">Vt (mL)</label><input type="number" name="vt_input" value="{{ inputs.vt_input }}" class="input-field"></div>
                                <div><label class="text-[9px] text-zinc-400 uppercase font-bold block mb-1">PIP</label><input type="number" name="pip" value="{{ inputs.pip }}" class="input-field"></div>
                                <div><label class="text-[9px] text-zinc-400 uppercase font-bold block mb-1">Pplat</label><input type="number" name="pplat" value="{{ inputs.pplat }}" class="input-field"></div>
                                <div><label class="text-[9px] text-zinc-400 uppercase font-bold block mb-1">PEEP</label><input type="number" name="peep" value="{{ inputs.peep }}" class="input-field"></div>
                                <div><label class="text-[9px] text-zinc-400 uppercase font-bold block mb-1">Flow (L/m)</label><input type="number" name="peak_flow" value="{{ inputs.peak_flow }}" class="input-field"></div>
                                <div><label class="text-[9px] text-amber-500 uppercase font-bold block mb-1">PECO2</label><input type="number" name="peco2" value="{{ inputs.peco2 }}" class="input-field text-amber-400 border-amber-900/30"></div>
                            </div>
                        </div>

                        <div>
                            <h3 class="text-[10px] text-teal-500 font-bold uppercase tracking-widest mb-3 border-b border-zinc-800/50 pb-1">Blood Gas & Labs</h3>
                            <div class="grid grid-cols-2 gap-3">
                                <div><label class="text-[9px] text-teal-500 uppercase font-bold block mb-1">CaO2</label><input type="number" step="0.1" name="cao2" value="{{ inputs.cao2 }}" class="input-field text-teal-400 border-teal-900/30"></div>
                                <div><label class="text-[9px] text-teal-500 uppercase font-bold block mb-1">CcO2</label><input type="number" step="0.1" name="cco2" value="{{ inputs.cco2 }}" class="input-field text-teal-400 border-teal-900/30"></div>
                                <div><label class="text-[9px] text-teal-500 uppercase font-bold block mb-1">CvO2</label><input type="number" step="0.1" name="cvo2" value="{{ inputs.cvo2 }}" class="input-field text-teal-400 border-teal-900/30"></div>
                                <div><label class="text-[9px] text-purple-400 uppercase font-bold block mb-1">HCO3</label><input type="number" step="0.1" name="hco3_input" value="{{ inputs.hco3_input }}" class="input-field text-purple-400 border-purple-900/30"></div>
                            </div>
                        </div>

                        <div>
                            <h3 class="text-[10px] text-blue-500 font-bold uppercase tracking-widest mb-3 border-b border-zinc-800/50 pb-1">Ventilator Settings</h3>
                            <div class="grid grid-cols-2 gap-3">
                                <div><label class="text-[9px] text-blue-400 uppercase font-bold block mb-1">Resp Rate</label><input type="number" name="rr" value="{{ inputs.rr }}" class="input-field border-blue-900/30"></div>
                                <div><label class="text-[9px] text-blue-400 uppercase font-bold block mb-1">FiO2 %</label><input type="number" name="fio2" value="{{ inputs.fio2 }}" class="input-field border-blue-900/30"></div>
                                <div><label class="text-[9px] text-blue-400 uppercase font-bold block mb-1">I:E Ratio</label><input type="number" step="0.1" name="ie_ratio" value="{{ inputs.ie_ratio }}" class="input-field border-blue-900/30"></div>
                                <div><label class="text-[9px] text-zinc-400 uppercase font-bold block mb-1">VCO2</label><input type="number" name="vco2" value="{{ inputs.vco2 }}" class="input-field"></div>
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit" class="w-full mt-6 bg-white hover:bg-zinc-200 text-black font-black py-4 rounded-xl text-xs uppercase tracking-[0.2em] transition-all shadow-[0_0_20px_rgba(255,255,255,0.2)] hover:shadow-[0_0_30px_rgba(255,255,255,0.4)]">
                        Initialize Matrix
                    </button>
                </form>
            </div>
        </div>

        {% if not sim_data %}
        <div class="xl:col-span-9 glass-card flex flex-col items-center justify-center min-h-[60vh] border-dashed border-zinc-700/50 bg-black/20">
            <div class="w-16 h-16 border-4 border-zinc-800 border-t-rose-600 rounded-full animate-spin mb-4"></div>
            <p class="text-zinc-500 font-mono text-sm uppercase tracking-widest">Awaiting Simulation Matrix Initialization...</p>
        </div>
        {% else %}
        
        <div class="xl:col-span-9 grid grid-cols-1 lg:grid-cols-2 gap-6 content-start">
            
            <div class="flex flex-col gap-6">
                
                <div class="glass-card p-6 border-l-4 border-l-rose-600 shadow-[0_10px_40px_rgba(225,29,72,0.1)] bg-gradient-to-br from-zinc-900/90 to-black">
                    <h3 class="text-[10px] text-rose-500 font-black uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                        <span class="w-1.5 h-1.5 bg-rose-500 rounded-full animate-pulse"></span> Neural Diagnostic Engine
                    </h3>
                    <div class="text-2xl font-black text-white leading-tight tracking-tight mb-2">{{ sim_data.ai_condition }}</div>
                    <div class="text-sm font-medium text-rose-200 bg-rose-950/30 p-4 rounded-xl border border-rose-900/50 mb-4 leading-relaxed">
                        {{ sim_data.ai_intervention }}
                    </div>
                    <div class="flex flex-wrap gap-2">
                        {% for diff in sim_data.differentials %}
                            <span class="text-[10px] font-mono bg-black text-zinc-400 border border-zinc-800 px-2 py-1 rounded">{{ diff }}</span>
                        {% endfor %}
                    </div>
                </div>

                <div class="glass-card p-6">
                    <h3 class="text-[10px] text-amber-500 font-black uppercase tracking-[0.2em] mb-4">Derived Pulmonary Mechanics</h3>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="stat-box">
                            <span class="text-[10px] text-zinc-500 font-bold uppercase tracking-widest mb-1">Static Compliance</span>
                            <div class="flex items-end gap-2">
                                <span class="text-4xl font-black text-white font-mono leading-none">{{ sim_data.derived_compliance }}</span>
                                <span class="text-xs text-zinc-500 font-medium pb-1">mL/cmH2O</span>
                            </div>
                        </div>
                        <div class="stat-box">
                            <span class="text-[10px] text-zinc-500 font-bold uppercase tracking-widest mb-1">Airway Resistance</span>
                            <div class="flex items-end gap-2">
                                <span class="text-4xl font-black text-white font-mono leading-none">{{ sim_data.derived_resistance }}</span>
                                <span class="text-xs text-zinc-500 font-medium pb-1">cmH2O/L/s</span>
                            </div>
                        </div>
                        <div class="stat-box border-amber-900/30">
                            <span class="text-[10px] text-amber-500 font-bold uppercase tracking-widest mb-1">Dead Space (Vd/Vt)</span>
                            <div class="flex items-end gap-2">
                                <span class="text-4xl font-black text-amber-400 font-mono leading-none">{{ sim_data.derived_vd_vt }}</span>
                                <span class="text-xs text-amber-600/60 font-medium pb-1">%</span>
                            </div>
                        </div>
                        <div class="stat-box border-teal-900/30">
                            <span class="text-[10px] text-teal-500 font-bold uppercase tracking-widest mb-1">Shunt Fraction</span>
                            <div class="flex items-end gap-2">
                                <span class="text-4xl font-black text-teal-400 font-mono leading-none">{{ sim_data.derived_shunt }}</span>
                                <span class="text-xs text-teal-600/60 font-medium pb-1">%</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="glass-card p-6 border-t-2 border-t-purple-500/50">
                    <h3 class="text-[10px] text-purple-400 font-black uppercase tracking-[0.2em] mb-4">Arterial Blood Gas Equilibrium</h3>
                    <div class="flex justify-between items-end mb-4 bg-black/40 p-4 rounded-xl border border-zinc-800">
                        <div>
                            <span class="text-[10px] text-zinc-500 font-bold uppercase block mb-1">pH Level</span>
                            <span class="text-3xl font-black font-mono {% if sim_data.ph < 7.35 %}text-red-500{% elif sim_data.ph > 7.45 %}text-blue-500{% else %}text-emerald-400{% endif %}">{{ sim_data.ph }}</span>
                        </div>
                        <div class="text-center border-l border-zinc-800 pl-4">
                            <span class="text-[10px] text-zinc-500 font-bold uppercase block mb-1">PaCO2</span>
                            <span class="text-2xl font-bold font-mono text-amber-400">{{ sim_data.paco2 }}</span>
                        </div>
                        <div class="text-right border-l border-zinc-800 pl-4">
                            <span class="text-[10px] text-zinc-500 font-bold uppercase block mb-1">HCO3</span>
                            <span class="text-2xl font-bold font-mono text-purple-400">{{ sim_data.hco3 }}</span>
                        </div>
                    </div>
                    <div class="text-sm font-bold text-white uppercase tracking-wide mb-1">{{ sim_data.acid_base_status }}</div>
                    <div class="text-xs text-zinc-400 leading-relaxed">{{ sim_data.acid_base_delta_text }}</div>
                </div>
            </div>

            <div class="flex flex-col gap-6">
                <div class="grid grid-cols-2 gap-4">
                    <div class="glass-card p-5 border border-sky-900/30 flex justify-between items-center bg-sky-950/10">
                        <div>
                            <span class="text-[9px] font-black uppercase text-sky-500 tracking-widest block mb-1">PaO2 Tension</span>
                            <span class="text-3xl font-black text-white font-mono">{{ sim_data.pao2 }}</span><span class="text-xs text-sky-700 ml-1">mmHg</span>
                        </div>
                        <div class="text-right">
                            <span class="text-[9px] font-bold uppercase text-zinc-500 block">A-a Gradient</span>
                            <span class="text-sm font-mono text-zinc-300">{{ sim_data.aa_gradient }}</span>
                        </div>
                    </div>
                    <div class="glass-card p-5 border border-emerald-900/30 flex justify-between items-center bg-emerald-950/10">
                        <div>
                            <span class="text-[9px] font-black uppercase text-emerald-500 tracking-widest block mb-1">Minute Vent</span>
                            <span class="text-3xl font-black text-white font-mono">{{ sim_data.minute_vent }}</span><span class="text-xs text-emerald-700 ml-1">L/m</span>
                        </div>
                        <div class="text-right">
                            <span class="text-[9px] font-bold uppercase text-zinc-500 block">Mech Power</span>
                            <span class="text-sm font-mono text-zinc-300">{{ sim_data.mech_power }} J/m</span>
                        </div>
                    </div>
                </div>

                <div class="glass-card p-4 h-[220px] flex flex-col relative">
                    <span class="absolute top-4 right-4 text-[9px] font-black text-blue-500 uppercase tracking-widest bg-blue-950/50 px-2 py-1 rounded border border-blue-900/50">Pressure (Paw)</span>
                    <div class="flex-1 w-full"><canvas id="chartP"></canvas></div>
                </div>
                
                <div class="glass-card p-4 h-[220px] flex flex-col relative">
                    <span class="absolute top-4 right-4 text-[9px] font-black text-emerald-500 uppercase tracking-widest bg-emerald-950/50 px-2 py-1 rounded border border-emerald-900/50">Flow (L/m)</span>
                    <div class="flex-1 w-full"><canvas id="chartF"></canvas></div>
                </div>

                <div class="glass-card p-4 h-[220px] flex flex-col relative">
                    <span class="absolute top-4 right-4 text-[9px] font-black text-rose-500 uppercase tracking-widest bg-rose-950/50 px-2 py-1 rounded border border-rose-900/50">Volume (mL)</span>
                    <div class="flex-1 w-full"><canvas id="chartV"></canvas></div>
                </div>
            </div>

            <script>
                const waveData = {{ sim_data.waveform_data | safe }};
                
                Chart.defaults.color = '#71717a';
                Chart.defaults.font.family = "'JetBrains Mono', monospace";
                Chart.defaults.font.size = 9;
                
                const opt = {
                    responsive: true, maintainAspectRatio: false, animation: false,
                    plugins: { legend: { display: false }, tooltip: { enabled: false } },
                    elements: { point: { radius: 0 }, line: { borderWidth: 2, tension: 0.2 } },
                    scales: { 
                        x: { grid: { color: '#27272a', borderDash: [2, 4] }, ticks: { maxTicksLimit: 6 } }, 
                        y: { grid: { color: '#27272a', borderDash: [2, 4] } } 
                    }
                };

                new Chart(document.getElementById('chartP'), { type: 'line', data: { labels: waveData.t, datasets: [{ data: waveData.p, borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true }] }, options: opt });
                new Chart(document.getElementById('chartF'), { type: 'line', data: { labels: waveData.t, datasets: [{ data: waveData.f, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true }] }, options: opt });
                new Chart(document.getElementById('chartV'), { type: 'line', data: { labels: waveData.t, datasets: [{ data: waveData.v, borderColor: '#f43f5e', backgroundColor: 'rgba(244, 63, 94, 0.1)', fill: true }] }, options: opt });
            </script>

        </div>
        {% endif %}
    </main>
</body>
</html>
"""

# ==========================================
# 4. FLASK ROUTING
# ==========================================

@app.route('/')
def home():
    if 'user' in session: return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    u, p = request.form.get('username'), request.form.get('password')
    if u in CLINICAL_DATABASE and CLINICAL_DATABASE[u]['password'] == p:
        session.update({'user': u, 'role': CLINICAL_DATABASE[u]['role']})
        return redirect(url_for('dashboard'))
    flash("ACCESS DENIED: INSUFFICIENT CLEARANCE.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    
    preset = request.args.get('preset', 'healthy')
    inputs = PRESETS.get(preset, PRESETS['healthy'])
    
    if request.method == 'POST':
        inputs = {k: RespiratoryEngine.safe_float(request.form.get(k), v) for k, v in inputs.items()}
        
    sim_data = None
    if request.method == 'POST' or request.args.get('preset'):
        try: sim_data = RespiratoryEngine.calculate_simulation(inputs)
        except Exception: flash(f"ENGINE CRASH: {traceback.format_exc()}")

    return render_template_string(DASHBOARD_HTML, inputs=inputs, sim_data=sim_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
