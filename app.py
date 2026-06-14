import os
import math
import json
import sqlite3
import traceback
from flask import Flask, request, redirect, url_for, session, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_omni_max_2026")
DB_NAME = "aerolung_database.db"

# ==========================================
# 1. DATABASE INITIALIZATION
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
    
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed_pw = generate_password_hash('admin2026')
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  ('admin', hashed_pw, 'System Architect'))
    
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. ADVANCED CLINICAL MATH ENGINE
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

        driving_pressure = max(0.1, pplat - peep)
        compliance = vt / driving_pressure
        flow_lsec = flow_lmin / 60.0
        resistance = max(0.1, (pip - pplat) / flow_lsec)
        
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
        
        try: ph = round(6.1 + math.log10(hco3_input / (0.0301 * max(1.0, paco2))), 2)
        except Exception: ph = 7.40

        ai_result = cls._generate_ai_diagnostics(compliance, resistance, shunt_pct, paco2, ph, vd_vt_ratio)
        acid_base_status, acid_base_delta_text = cls._analyze_acid_base(ph, paco2)

        p_A_O2 = round(((760 - 47) * (fio2_val / 100.0)) - (paco2 / 0.8), 1)
        pao2 = round(max(30, p_A_O2 - (shunt_pct * 1.2)), 1)

        t_cycle = 60.0 / rr
        tau = max(0.001, (resistance / 1000.0) * compliance)
        waveform_data = cls._generate_waveforms(t_cycle, ie, pip, peep, vt, tau)

        return {
            'compliance': round(compliance, 1), 
            'resistance': round(resistance, 1),
            'vd_vt': round(vd_vt_ratio * 100, 1), 
            'shunt': shunt_pct,
            'ai_condition': ai_result['condition'], 
            'ai_description': ai_result['description'], 
            'ai_solutions': ai_result['solutions'],
            'paco2': paco2, 
            'pao2': pao2, 
            'ph': ph, 
            'hco3': hco3_input, 
            'acid_base_status': acid_base_status, 
            'minute_vent': round(min_vent_est, 2),
            'waveform_data': json.dumps(waveform_data)
        }

    @staticmethod
    def _generate_ai_diagnostics(compliance, resistance, shunt_pct, paco2, ph, vd_vt_ratio):
        if compliance < 20 and paco2 > 50 and resistance < 15:
            return {"condition": "TENSION PNEUMOTHORAX", "description": "Catastrophic loss of lung compliance combined with acute hypercapnia. Suggests complete lung collapse and mediastinal shift.", "solutions": ["Perform immediate needle decompression.", "Prepare for urgent chest tube thoracostomy."]}
        elif resistance > 25:
            return {"condition": "STATUS ASTHMATICUS", "description": "Critically elevated airway resistance indicating severe bronchospasm and airway inflammation. High risk of dynamic hyperinflation.", "solutions": ["Administer continuous inhaled beta-agonists.", "Decrease respiratory rate to allow lung emptying.", "Consider Heliox therapy."]}
        elif vd_vt_ratio > 0.55:
            return {"condition": "MASSIVE PULMONARY EMBOLISM", "description": "Severe dead-space (Vd/Vt) ventilation detected. Alveoli are ventilated but not perfused due to vascular obstruction.", "solutions": ["Initiate immediate systemic anticoagulation.", "Consider thrombolytic therapy or embolectomy.", "Provide hemodynamic support."]}
        elif compliance < 35 and shunt_pct > 25:
            return {"condition": "SEVERE ARDS", "description": "Profound hypoxemia secondary to massive intrapulmonary shunting and stiff lungs. Indicates diffuse alveolar damage.", "solutions": ["Implement strict lung-protective ventilation (low Vt).", "Optimize PEEP to recruit alveoli.", "Initiate early prone positioning."]}
        elif compliance > 60 and resistance > 15:
            return {"condition": "COPD / EMPHYSEMA", "description": "High static compliance with elevated airway resistance. Indicates destruction of alveolar septa and loss of elastic recoil.", "solutions": ["Accept permissive hypercapnia.", "Set PEEP to ~80% of Auto-PEEP to stent airways.", "Administer bronchodilators."]}
        elif compliance < 40 and shunt_pct > 15 and resistance < 15:
            return {"condition": "CARDIOGENIC PULMONARY EDEMA", "description": "Reduced compliance and elevated shunt indicative of fluid accumulation in the alveolar spaces secondary to heart failure.", "solutions": ["Administer loop diuretics to reduce fluid overload.", "Administer vasodilators if BP allows.", "Apply sufficient PEEP to push fluid out of alveoli."]}
        elif compliance < 35 and shunt_pct < 15:
            return {"condition": "PULMONARY FIBROSIS", "description": "Severely restricted lung volumes due to parenchymal scarring. Compliance is very low, but gas exchange is relatively intact.", "solutions": ["Utilize low tidal volume ventilation to prevent volutrauma.", "Titrate PEEP carefully to avoid overdistension.", "Consider high-dose corticosteroids."]}
        elif compliance > 40 and resistance < 15 and paco2 > 55:
            return {"condition": "NEUROMUSCULAR PUMP FAILURE", "description": "Lung mechanics are normal, but ventilation is grossly inadequate leading to hypercapnia. Suggests severe diaphragm weakness.", "solutions": ["Assess for reversible causes (e.g., Guillain-Barré).", "Provide full ventilatory support.", "Perform aggressive pulmonary hygiene."]}
        elif resistance > 15 and shunt_pct > 15 and paco2 > 45:
            return {"condition": "CYSTIC FIBROSIS EXACERBATION", "description": "Mixed obstructive and shunting defect. Thick purulent secretions are causing high airway resistance and localized atelectasis.", "solutions": ["Administer aggressive mucolytics.", "Perform intense chest physiotherapy.", "Initiate targeted IV antibiotics."]}
        elif compliance < 45 and paco2 > 50 and vd_vt_ratio > 0.40:
            return {"condition": "OBESITY HYPOVENTILATION", "description": "Decreased chest wall compliance due to massive adiposity, leading to chronic CO2 retention and basilar atelectasis.", "solutions": ["Utilize higher PEEP to overcome chest wall weight.", "Position patient in reverse Trendelenburg.", "Target ideal body weight for tidal volume calculations."]}
        elif shunt_pct > 15 and resistance < 12 and compliance > 35:
            return {"condition": "SEVERE PNEUMONIA", "description": "Localized alveolar filling process causing significant right-to-left intrapulmonary shunting.", "solutions": ["Administer broad-spectrum IV antibiotics.", "Target oxygen therapy and moderate PEEP.", "Position patient 'good lung down'."]}
        else:
            return {"condition": "STABLE PULMONARY HOMEOSTASIS", "description": "Ventilatory mechanics and gas exchange parameters are within optimal clinical limits. No acute pathology detected.", "solutions": ["Maintain current ventilatory support settings.", "Perform daily Spontaneous Breathing Trials (SBTs).", "Begin weaning protocols as tolerated."]}

    @staticmethod
    def _analyze_acid_base(ph, paco2):
        if ph < 7.35: return ("Respiratory Acidosis", "Hypoventilation causing CO2 retention.") if paco2 > 45 else ("Metabolic Acidosis", "Systemic bicarbonate depletion.")
        elif ph > 7.45: return ("Respiratory Alkalosis", "Hyperventilation blowing off excessive CO2.") if paco2 < 35 else ("Metabolic Alkalosis", "Accumulation of systemic alkali.")
        return "Normal Acid-Base Balance", "Blood gas parameters are normal."

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
# 3. HTML & CSS TEMPLATES
# ==========================================

# A deeply translucent UI to make the glowing Cyan lung visible
GLOBAL_CSS = """
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Outfit', sans-serif; background-color: #020617; color: #f8fafc; overflow-x: hidden; min-height: 100vh; display: flex; flex-direction: column; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    
    /* Glowing Cyan Holographic Lung */
    @keyframes holographicBreathe {
        0% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.2; filter: drop-shadow(0 0 20px rgba(6,182,212,0.2)); }
        50% { transform: translate(-50%, -50%) scale(1.03); opacity: 0.5; filter: drop-shadow(0 0 50px rgba(6,182,212,0.6)); }
        100% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.2; filter: drop-shadow(0 0 20px rgba(6,182,212,0.2)); }
    }
    .living-lung { position: fixed; top: 50%; left: 50%; width: 100vw; max-width: 900px; z-index: 0; pointer-events: none; animation: holographicBreathe 5s ease-in-out infinite; }
    
    /* Highly transparent Smoked Glass so the lung is visible */
    .glass-panel { 
        background: rgba(15, 23, 42, 0.4); 
        backdrop-filter: blur(12px); 
        -webkit-backdrop-filter: blur(12px); 
        border: 1px solid rgba(255, 255, 255, 0.05); 
        position: relative; z-index: 10;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); 
    }
    .glass-input { background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.1); color: #fff; transition: all 0.3s ease; }
    .glass-input:focus { outline: none; border-color: #06b6d4; box-shadow: 0 0 15px rgba(6, 182, 212, 0.3); }
    
    .preset-btn { transition: all 0.2s; cursor: pointer; }
    .preset-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.4); border-color: #06b6d4; }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
</style>
<script>
    function updateClock() {
        const now = new Date();
        const dateString = now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
        const timeString = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const clockEl = document.getElementById('live-clock');
        if(clockEl) clockEl.innerHTML = `<span class="text-cyan-400 font-bold">${timeString}</span> <span class="text-slate-400 text-[10px] uppercase ml-2 tracking-widest">${dateString}</span>`;
    }
    setInterval(updateClock, 1000);
    window.onload = updateClock;
</script>
"""

BACKGROUND_SVG = """
<svg class="living-lung" viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="cyanGrad" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.6"/>
            <stop offset="50%" stop-color="#0891b2" stop-opacity="0.8"/>
            <stop offset="100%" stop-color="#164e63" stop-opacity="1"/>
        </radialGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="8" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>
    <g filter="url(#glow)">
        <path d="M245 40 h10 v80 h-10 z" fill="#0891b2"/>
        <path d="M250 120 L190 160 L195 170 L250 135 L305 170 L310 160 Z" fill="#0891b2"/>
        <path d="M230 135 C 130 90, 50 210, 70 330 C 90 390, 190 390, 230 330 C 250 270, 240 180, 230 135 Z" fill="url(#cyanGrad)"/>
        <path d="M270 135 C 370 90, 450 210, 430 330 C 410 390, 310 390, 270 330 C 250 270, 260 180, 270 135 Z" fill="url(#cyanGrad)"/>
    </g>
</svg>
"""

COPYRIGHT_FOOTER = """
<footer class="mt-auto py-5 text-center relative z-20 border-t border-white/5 bg-slate-950/80 backdrop-blur-md">
    <div class="flex items-center justify-center gap-2 text-[10px] font-mono tracking-widest text-slate-500 uppercase">
        <span>&copy; 2026</span>
        <span class="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.8)]"></span>
        <span class="text-slate-300 font-bold">Shreesh Santoshkumar Rolli</span>
        <span class="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.8)]"></span>
        <span>AeroLung Medical System</span>
    </div>
</footer>
"""

LOGIN_HTML = GLOBAL_CSS + BACKGROUND_SVG + """
<body class="flex items-center justify-center relative">
    <div class="glass-panel rounded-3xl p-10 w-full max-w-md text-center border-t border-white/10 shadow-[0_0_40px_rgba(6,182,212,0.1)]">
        <h1 class="text-5xl font-black tracking-tighter text-white mb-2">AERO<span class="text-cyan-400">LUNG</span></h1>
        <p class="text-xs font-mono text-cyan-500/80 uppercase tracking-[0.3em] mb-10">Systematic Authentication</p>
        
        {% if get_flashed_messages() %}
            <div class="mb-6 p-3 text-xs text-rose-400 bg-rose-950/30 border border-rose-900/50 rounded uppercase tracking-wide">
                {% for msg in get_flashed_messages() %} {{ msg }} {% endfor %}
            </div>
        {% endif %}

        <form action="/login" method="POST" class="space-y-5 text-left">
            <div>
                <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1">Architect ID</label>
                <input type="text" name="username" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm" placeholder="Enter ID..." required>
            </div>
            <div>
                <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1">Secure Passkey</label>
                <input type="password" name="password" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm" placeholder="••••••••" required>
            </div>
            <button type="submit" class="w-full mt-4 py-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-sm uppercase tracking-[0.2em] transition-all shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:shadow-[0_0_30px_rgba(6,182,212,0.6)]">
                Secure Uplink
            </button>
        </form>
    </div>
    {{ COPYRIGHT_FOOTER | safe }}
</body>
"""

SETTINGS_HTML = GLOBAL_CSS + BACKGROUND_SVG + """
<body class="flex items-center justify-center relative flex-col min-h-screen">
    <nav class="glass-panel w-full border-b-0 border-white/5 rounded-none bg-slate-950/90 py-4 px-6 flex justify-between absolute top-0 z-50">
        <h1 class="text-2xl font-black tracking-tighter text-white">AERO<span class="text-cyan-400">LUNG</span></h1>
        <a href="/dashboard" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold uppercase tracking-wider transition-colors">Return to Dashboard</a>
    </nav>

    <div class="glass-panel rounded-3xl p-10 w-full max-w-lg text-center border-t border-white/10 mt-20">
        <h2 class="text-2xl font-black tracking-tighter text-white mb-2 uppercase">Account Settings</h2>
        <p class="text-xs font-mono text-cyan-500/80 uppercase tracking-[0.2em] mb-8">Modify Access Credentials</p>
        
        {% if get_flashed_messages() %}
            <div class="mb-6 p-3 text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-900/50 rounded uppercase tracking-wide">
                {% for msg in get_flashed_messages() %} {{ msg }} {% endfor %}
            </div>
        {% endif %}

        <form action="/settings" method="POST" class="space-y-5 text-left">
            <div>
                <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Current ID (Display Only)</label>
                <input type="text" value="{{ session.user }}" disabled class="w-full bg-slate-900/50 text-slate-500 border border-white/5 px-5 py-3 rounded-xl font-mono text-sm cursor-not-allowed">
            </div>
            <div>
                <label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2 ml-1">New ID (Optional)</label>
                <input type="text" name="new_username" class="w-full glass-input px-5 py-3 rounded-xl font-mono text-sm" placeholder="Enter new ID">
            </div>
            <div>
                <label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2 ml-1">New Passkey (Optional)</label>
                <input type="password" name="new_password" class="w-full glass-input px-5 py-3 rounded-xl font-mono text-sm" placeholder="Enter new password">
            </div>
            <button type="submit" class="w-full mt-4 py-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-sm uppercase tracking-[0.2em] transition-all">
                Commit Changes
            </button>
        </form>
    </div>
    {{ COPYRIGHT_FOOTER | safe }}
</body>
"""

DASHBOARD_HTML = GLOBAL_CSS + BACKGROUND_SVG + """
<body class="min-h-screen flex flex-col relative">
    <nav class="glass-panel sticky top-0 z-50 border-b-0 border-white/5 rounded-none bg-slate-950/90 shadow-xl">
        <div class="max-w-[1800px] mx-auto px-6 py-4 flex justify-between items-center">
            <h1 class="text-2xl font-black tracking-tighter text-white">AERO<span class="text-cyan-400">LUNG</span></h1>
            
            <div id="live-clock" class="hidden lg:block bg-black/40 border border-white/5 px-4 py-2 rounded-lg shadow-inner"></div>

            <div class="flex items-center gap-4">
                <div class="text-[10px] font-mono text-slate-400 uppercase tracking-widest border-r border-slate-700 pr-4 hidden md:block">
                    Session: <span class="text-cyan-400 font-bold">{{ session.user }}</span>
                </div>
                <a href="/settings" class="px-3 py-2 rounded-lg bg-slate-800/50 hover:bg-slate-700 text-slate-300 border border-slate-600/50 text-xs font-bold uppercase tracking-wider transition-colors">Settings</a>
                <a href="/logout" class="px-3 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 text-xs font-bold uppercase tracking-wider transition-colors">Logout</a>
            </div>
        </div>
    </nav>

    <main class="flex-1 max-w-[1800px] mx-auto w-full p-6 relative z-10">
        <div class="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
            
            <div class="xl:col-span-4 flex flex-col gap-6">
                
                <div class="glass-panel rounded-2xl p-5 border border-cyan-900/30">
                    <h2 class="text-[10px] font-bold uppercase tracking-widest text-cyan-400 mb-2 flex items-center gap-2">
                        <span class="w-2 h-2 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,211,238,1)]"></span> 
                        Pathology Matrix (20 Profiles)
                    </h2>
                    <p class="text-[10px] text-slate-400 mb-4">Click a systemic condition to auto-populate hemodynamics.</p>
                    
                    <div class="grid grid-cols-2 gap-2 max-h-[300px] overflow-y-auto pr-2">
                        <div onclick="loadPreset('healthy')" class="preset-btn bg-slate-800/80 border border-slate-600 p-2 rounded flex items-center justify-center"><div class="text-slate-200 font-bold text-[9px] uppercase tracking-wider">Healthy</div></div>
                        <div onclick="loadPreset('ards')" class="preset-btn bg-rose-950/60 border border-rose-800 p-2 rounded flex items-center justify-center"><div class="text-rose-400 font-bold text-[9px] uppercase tracking-wider">Severe ARDS</div></div>
                        <div onclick="loadPreset('copd')" class="preset-btn bg-amber-950/60 border border-amber-800 p-2 rounded flex items-center justify-center"><div class="text-amber-400 font-bold text-[9px] uppercase tracking-wider">COPD</div></div>
                        <div onclick="loadPreset('asthma')" class="preset-btn bg-purple-950/60 border border-purple-800 p-2 rounded flex items-center justify-center"><div class="text-purple-400 font-bold text-[9px] uppercase tracking-wider">Asthma</div></div>
                        <div onclick="loadPreset('fibrosis')" class="preset-btn bg-indigo-950/60 border border-indigo-800 p-2 rounded flex items-center justify-center"><div class="text-indigo-400 font-bold text-[9px] uppercase tracking-wider">Fibrosis</div></div>
                        <div onclick="loadPreset('pe')" class="preset-btn bg-red-950/60 border border-red-800 p-2 rounded flex items-center justify-center"><div class="text-red-400 font-bold text-[9px] uppercase tracking-wider">Pulm Embolism</div></div>
                        <div onclick="loadPreset('pneumonia')" class="preset-btn bg-orange-950/60 border border-orange-800 p-2 rounded flex items-center justify-center"><div class="text-orange-400 font-bold text-[9px] uppercase tracking-wider">Pneumonia</div></div>
                        <div onclick="loadPreset('neuro')" class="preset-btn bg-cyan-950/60 border border-cyan-800 p-2 rounded flex items-center justify-center"><div class="text-cyan-400 font-bold text-[9px] uppercase tracking-wider">Neuro Weakness</div></div>
                        <div onclick="loadPreset('obesity')" class="preset-btn bg-pink-950/60 border border-pink-800 p-2 rounded flex items-center justify-center"><div class="text-pink-400 font-bold text-[9px] uppercase tracking-wider">Obesity Hypo</div></div>
                        <div onclick="loadPreset('pneumothorax')" class="preset-btn bg-zinc-900 border border-zinc-600 p-2 rounded flex items-center justify-center"><div class="text-zinc-300 font-bold text-[9px] uppercase tracking-wider">Pneumothorax</div></div>
                        <div onclick="loadPreset('edema')" class="preset-btn bg-blue-950/60 border border-blue-800 p-2 rounded flex items-center justify-center"><div class="text-blue-400 font-bold text-[9px] uppercase tracking-wider">Cardio Edema</div></div>
                        <div onclick="loadPreset('cf')" class="preset-btn bg-teal-950/60 border border-teal-800 p-2 rounded flex items-center justify-center"><div class="text-teal-400 font-bold text-[9px] uppercase tracking-wider">Cystic Fibrosis</div></div>
                        <div onclick="loadPreset('kypho')" class="preset-btn bg-fuchsia-950/60 border border-fuchsia-800 p-2 rounded flex items-center justify-center"><div class="text-fuchsia-400 font-bold text-[9px] uppercase tracking-wider">Kyphoscoliosis</div></div>
                        <div onclick="loadPreset('bronch')" class="preset-btn bg-lime-950/60 border border-lime-800 p-2 rounded flex items-center justify-center"><div class="text-lime-400 font-bold text-[9px] uppercase tracking-wider">Bronchiectasis</div></div>
                        <div onclick="loadPreset('mild_ards')" class="preset-btn bg-rose-900/40 border border-rose-700/50 p-2 rounded flex items-center justify-center"><div class="text-rose-300 font-bold text-[9px] uppercase tracking-wider">Mild ARDS</div></div>
                        <div onclick="loadPreset('atelectasis')" class="preset-btn bg-slate-700/60 border border-slate-500 p-2 rounded flex items-center justify-center"><div class="text-slate-300 font-bold text-[9px] uppercase tracking-wider">Atelectasis</div></div>
                        <div onclick="loadPreset('flail')" class="preset-btn bg-red-900/60 border border-red-700 p-2 rounded flex items-center justify-center"><div class="text-red-300 font-bold text-[9px] uppercase tracking-wider">Flail Chest</div></div>
                        <div onclick="loadPreset('p_htn')" class="preset-btn bg-violet-950/60 border border-violet-800 p-2 rounded flex items-center justify-center"><div class="text-violet-400 font-bold text-[9px] uppercase tracking-wider">Pulmonary HTN</div></div>
                        <div onclick="loadPreset('co_poison')" class="preset-btn bg-stone-900 border border-stone-600 p-2 rounded flex items-center justify-center"><div class="text-stone-400 font-bold text-[9px] uppercase tracking-wider">CO Poisoning</div></div>
                        <div onclick="loadPreset('ards_mod')" class="preset-btn bg-rose-800/40 border border-rose-600 p-2 rounded flex items-center justify-center"><div class="text-rose-200 font-bold text-[9px] uppercase tracking-wider">Moderate ARDS</div></div>
                    </div>
                </div>

                <div class="glass-panel rounded-2xl flex flex-col shadow-2xl">
                    <form id="calc-form" method="POST" action="/dashboard" class="p-5">
                        <h3 class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest border-b border-white/10 pb-2 mb-4">Manual Telemetry Override</h3>
                        
                        <div class="text-[9px] text-slate-500 uppercase tracking-widest mb-2 font-bold">Ventilation Settings</div>
                        <div class="grid grid-cols-4 gap-2 mb-4 bg-black/30 p-3 rounded-lg border border-white/5">
                            <div title="Tidal Volume in mL"><label class="text-[8px] font-bold text-slate-400 uppercase block">Vt</label><input type="number" name="vt_input" id="vt_input" value="{{ inputs.vt_input|default(500) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                            <div title="Respiratory Rate"><label class="text-[8px] font-bold text-slate-400 uppercase block">Rate</label><input type="number" name="rr" id="rr" value="{{ inputs.rr|default(14) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                            <div title="Peak Inspiratory Pressure"><label class="text-[8px] font-bold text-slate-400 uppercase block">PIP</label><input type="number" name="pip" id="pip" value="{{ inputs.pip|default(20) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono text-rose-300"></div>
                            <div title="Plateau Pressure"><label class="text-[8px] font-bold text-slate-400 uppercase block">Pplat</label><input type="number" name="pplat" id="pplat" value="{{ inputs.pplat|default(14) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono text-rose-300"></div>
                            <div title="Positive End-Expiratory Pressure"><label class="text-[8px] font-bold text-slate-400 uppercase block">PEEP</label><input type="number" name="peep" id="peep" value="{{ inputs.peep|default(5) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono text-cyan-300"></div>
                            <div title="Peak Flow in L/min"><label class="text-[8px] font-bold text-slate-400 uppercase block">Flow</label><input type="number" name="peak_flow" id="peak_flow" value="{{ inputs.peak_flow|default(60) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                            <div title="Fraction of Inspired Oxygen"><label class="text-[8px] font-bold text-slate-400 uppercase block">FiO2</label><input type="number" name="fio2" id="fio2" value="{{ inputs.fio2|default(30) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                            <div title="Inspiratory:Expiratory Ratio"><label class="text-[8px] font-bold text-slate-400 uppercase block">I:E</label><input type="number" step="0.1" name="ie_ratio" id="ie_ratio" value="{{ inputs.ie_ratio|default(2.0) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                        </div>
                        
                        <div class="text-[9px] text-slate-500 uppercase tracking-widest mb-2 font-bold mt-4">Gas Exchange & Labs</div>
                        <div class="grid grid-cols-3 gap-2 mb-4 bg-black/30 p-3 rounded-lg border border-white/5">
                            <div title="Arterial Oxygen Content"><label class="text-[8px] font-bold text-slate-400 uppercase block">CaO2</label><input type="number" step="0.1" name="cao2" id="cao2" value="{{ inputs.cao2|default(19.8) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono text-emerald-300"></div>
                            <div title="Venous Oxygen Content"><label class="text-[8px] font-bold text-slate-400 uppercase block">CvO2</label><input type="number" step="0.1" name="cvo2" id="cvo2" value="{{ inputs.cvo2|default(14.8) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono text-emerald-300"></div>
                            <div title="Capillary Oxygen Content"><label class="text-[8px] font-bold text-slate-400 uppercase block">CcO2</label><input type="number" step="0.1" name="cco2" id="cco2" value="{{ inputs.cco2|default(20.4) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono text-emerald-300"></div>
                            <div title="Exhaled CO2"><label class="text-[8px] font-bold text-slate-400 uppercase block mt-2">PECO2</label><input type="number" name="peco2" id="peco2" value="{{ inputs.peco2|default(28) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono text-amber-300"></div>
                            <div title="CO2 Production"><label class="text-[8px] font-bold text-slate-400 uppercase block mt-2">VCO2</label><input type="number" name="vco2" id="vco2" value="{{ inputs.vco2|default(200) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono text-amber-300"></div>
                            <div title="Systemic Bicarbonate"><label class="text-[8px] font-bold text-slate-400 uppercase block mt-2">HCO3</label><input type="number" name="hco3_input" id="hco3_input" value="{{ inputs.hco3_input|default(24) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono text-purple-300"></div>
                        </div>

                        <button type="submit" class="w-full py-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-black text-[11px] uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(34,211,238,0.4)] transition-all">
                            Initialize Scan
                        </button>
                    </form>
                </div>
            </div>

            <div class="xl:col-span-8 flex flex-col gap-6">
                {% if not sim_data %}
                <div class="glass-panel rounded-3xl flex-1 flex flex-col items-center justify-center min-h-[600px] border-dashed border-slate-600/50">
                    <div class="w-24 h-24 border-4 border-slate-700 border-t-cyan-400 rounded-full animate-spin mb-6 shadow-[0_0_30px_rgba(34,211,238,0.4)]"></div>
                    <h3 class="text-2xl font-black text-white mb-2 uppercase tracking-widest">System Standby</h3>
                    <p class="text-sm text-slate-400 font-mono">Select a pathology profile to render comprehensive analytics.</p>
                </div>
                {% else %}
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="glass-panel p-6 rounded-2xl border-l-4 border-l-cyan-400 bg-gradient-to-br from-slate-900/90 to-black">
                        <h3 class="text-[11px] text-cyan-400 font-black uppercase tracking-[0.2em] mb-2">Neural Diagnosis</h3>
                        <div class="text-2xl font-black text-white leading-tight tracking-tight mb-4 uppercase drop-shadow-md">{{ sim_data.ai_condition }}</div>
                        
                        <div class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Pathophysiology</div>
                        <div class="text-sm text-slate-300 bg-black/40 p-4 rounded-lg border border-white/5 leading-relaxed mb-4">
                            {{ sim_data.ai_description }}
                        </div>

                        <div class="text-[10px] font-bold text-emerald-400 uppercase tracking-widest mb-1">Action Plan</div>
                        <ul class="space-y-1">
                            {% for solution in sim_data.ai_solutions %}
                            <li class="flex items-start gap-2 bg-emerald-950/20 p-2 rounded border border-emerald-900/30 text-xs text-slate-200">
                                <span class="text-emerald-500 font-bold">⯈</span> <span>{{ solution }}</span>
                            </li>
                            {% endfor %}
                        </ul>
                    </div>

                    <div class="glass-panel p-6 rounded-2xl border-t-4 border-t-purple-500">
                        <h3 class="text-[11px] text-purple-400 font-black uppercase tracking-[0.2em] mb-4">Arterial Blood Gas</h3>
                        <div class="grid grid-cols-3 gap-2 mb-4 bg-black/40 p-4 rounded-xl border border-white/5 text-center">
                            <div>
                                <span class="text-[9px] text-slate-500 font-bold uppercase block mb-1">pH</span>
                                <span class="text-xl font-black font-mono {% if sim_data.ph < 7.35 %}text-rose-500{% elif sim_data.ph > 7.45 %}text-cyan-400{% else %}text-emerald-400{% endif %}">{{ sim_data.ph }}</span>
                            </div>
                            <div class="border-l border-white/10">
                                <span class="text-[9px] text-slate-500 font-bold uppercase block mb-1">PaCO2</span>
                                <span class="text-xl font-black font-mono text-amber-400">{{ sim_data.paco2 }}</span>
                            </div>
                            <div class="border-l border-white/10">
                                <span class="text-[9px] text-slate-500 font-bold uppercase block mb-1">HCO3</span>
                                <span class="text-xl font-black font-mono text-purple-400">{{ sim_data.hco3 }}</span>
                            </div>
                        </div>
                        <div class="text-xs font-bold text-white uppercase tracking-wider bg-purple-950/50 block text-center py-2 rounded border border-purple-800">{{ sim_data.acid_base_status }}</div>
                    </div>
                </div>

                <div class="glass-panel p-5 rounded-2xl">
                    <h3 class="text-[11px] text-slate-400 font-black uppercase tracking-[0.2em] mb-4 border-b border-white/10 pb-2">Mechanics Explained</h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-black/30 p-4 rounded-xl text-center border border-white/5 relative group">
                            <span class="text-[10px] text-cyan-400 font-bold uppercase tracking-widest block mb-1">Compliance</span>
                            <div class="text-2xl font-black text-white font-mono">{{ sim_data.compliance }} <span class="text-[10px] text-slate-500">mL/cmH2O</span></div>
                            <div class="text-[9px] text-slate-400 mt-2">Measures Lung Elasticity. Normal: ~60-80. Lower = Stiffer lungs (ARDS, Fibrosis).</div>
                        </div>
                        <div class="bg-black/30 p-4 rounded-xl text-center border border-white/5 relative group">
                            <span class="text-[10px] text-rose-400 font-bold uppercase tracking-widest block mb-1">Resistance</span>
                            <div class="text-2xl font-black text-white font-mono">{{ sim_data.resistance }} <span class="text-[10px] text-slate-500">cmH2O/L/s</span></div>
                            <div class="text-[9px] text-slate-400 mt-2">Measures Airway Blockage. Normal: ~5-10. Higher = Bronchospasm (Asthma).</div>
                        </div>
                        <div class="bg-black/30 p-4 rounded-xl text-center border border-white/5 relative group">
                            <span class="text-[10px] text-amber-400 font-bold uppercase tracking-widest block mb-1">Vd/Vt</span>
                            <div class="text-2xl font-black text-white font-mono">{{ sim_data.vd_vt }}<span class="text-sm text-slate-500">%</span></div>
                            <div class="text-[9px] text-slate-400 mt-2">Dead Space. Wasted ventilation not participating in gas exchange (e.g., Embolism).</div>
                        </div>
                        <div class="bg-black/30 p-4 rounded-xl text-center border border-white/5 relative group">
                            <span class="text-[10px] text-emerald-400 font-bold uppercase tracking-widest block mb-1">Shunt</span>
                            <div class="text-2xl font-black text-white font-mono">{{ sim_data.shunt }}<span class="text-sm text-slate-500">%</span></div>
                            <div class="text-[9px] text-slate-400 mt-2">Blood bypassing ventilated alveoli. Causes refractory hypoxemia (ARDS, Edema).</div>
                        </div>
                    </div>
                </div>

                <div class="glass-panel p-6 rounded-2xl flex flex-col relative h-[380px]">
                    <div class="flex justify-between items-center mb-4 border-b border-white/10 pb-2">
                        <h3 class="text-[11px] text-slate-400 font-black uppercase tracking-[0.2em]">Waveform Analytics</h3>
                        <div class="text-[9px] text-slate-400 flex gap-4 font-mono">
                            <div><span class="text-[#22d3ee] font-bold">Paw:</span> Airway Pressure</div>
                            <div><span class="text-[#10b981] font-bold">Vol:</span> Lung Expansion</div>
                            <div><span class="text-[#f43f5e] font-bold">Flow:</span> Air Velocity</div>
                        </div>
                    </div>
                    <div class="flex-1 w-full relative"><canvas id="matrixChart"></canvas></div>
                </div>

                <script>
                    const waveData = {{ sim_data.waveform_data | safe }};
                    Chart.defaults.color = '#64748b';
                    Chart.defaults.font.family = "'JetBrains Mono', monospace";
                    
                    new Chart(document.getElementById('matrixChart'), {
                        type: 'line',
                        data: {
                            labels: waveData.t,
                            datasets: [
                                { label: 'Pressure (cmH2O)', data: waveData.p, borderColor: '#22d3ee', backgroundColor: 'rgba(34, 211, 238, 0.1)', fill: true, borderWidth: 2, tension: 0.2, pointRadius: 0 },
                                { label: 'Volume (mL)', data: waveData.v, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.05)', fill: true, borderWidth: 2, tension: 0.2, pointRadius: 0 },
                                { label: 'Flow (L/m)', data: waveData.f, borderColor: '#f43f5e', backgroundColor: 'rgba(244, 63, 94, 0.05)', fill: true, borderWidth: 2, tension: 0.2, pointRadius: 0 }
                            ]
                        },
                        options: {
                            responsive: true, maintainAspectRatio: false,
                            plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
                            scales: { 
                                x: { grid: { color: 'rgba(255,255,255,0.05)', borderDash: [5,5] } }, 
                                y: { grid: { color: 'rgba(255,255,255,0.05)', borderDash: [5,5] } } 
                            }
                        }
                    });
                </script>
                {% endif %}
            </div>
        </div>
    </main>
    {{ COPYRIGHT_FOOTER | safe }}

    <script>
        const PRESETS = {
            healthy:      {vt: 500, rr: 14, pip: 20, pplat: 14, peep: 5,  flow: 60, fio2: 30, ie: 2.0, cao2: 19.8, cvo2: 14.8, cco2: 20.4, peco2: 28, vco2: 200, hco3: 24},
            ards:         {vt: 350, rr: 28, pip: 38, pplat: 32, peep: 14, flow: 50, fio2: 80, ie: 1.5, cao2: 15.2, cvo2: 11.2, cco2: 20.1, peco2: 18, vco2: 240, hco3: 20},
            copd:         {vt: 520, rr: 10, pip: 32, pplat: 16, peep: 5,  flow: 45, fio2: 35, ie: 4.0, cao2: 18.5, cvo2: 14.2, cco2: 20.2, peco2: 24, vco2: 190, hco3: 31},
            asthma:       {vt: 450, rr: 12, pip: 45, pplat: 17, peep: 5,  flow: 40, fio2: 40, ie: 5.0, cao2: 19.2, cvo2: 14.1, cco2: 20.3, peco2: 25, vco2: 210, hco3: 24},
            fibrosis:     {vt: 350, rr: 26, pip: 35, pplat: 33, peep: 8,  flow: 55, fio2: 45, ie: 1.5, cao2: 17.5, cvo2: 13.0, cco2: 20.1, peco2: 22, vco2: 220, hco3: 24},
            pe:           {vt: 500, rr: 28, pip: 22, pplat: 15, peep: 5,  flow: 60, fio2: 50, ie: 2.0, cao2: 16.0, cvo2: 11.0, cco2: 20.0, peco2: 12, vco2: 200, hco3: 24},
            pneumonia:    {vt: 400, rr: 22, pip: 28, pplat: 22, peep: 10, flow: 50, fio2: 60, ie: 2.0, cao2: 16.5, cvo2: 12.0, cco2: 20.2, peco2: 20, vco2: 230, hco3: 22},
            neuro:        {vt: 250, rr: 10, pip: 15, pplat: 10, peep: 5,  flow: 40, fio2: 21, ie: 2.0, cao2: 18.0, cvo2: 13.5, cco2: 20.4, peco2: 35, vco2: 180, hco3: 26},
            obesity:      {vt: 400, rr: 18, pip: 30, pplat: 26, peep: 12, flow: 50, fio2: 30, ie: 2.0, cao2: 18.5, cvo2: 14.0, cco2: 20.0, peco2: 35, vco2: 250, hco3: 32},
            pneumothorax: {vt: 300, rr: 30, pip: 45, pplat: 40, peep: 5,  flow: 60, fio2: 90, ie: 1.0, cao2: 14.0, cvo2: 10.0, cco2: 20.0, peco2: 15, vco2: 220, hco3: 20},
            edema:        {vt: 400, rr: 24, pip: 30, pplat: 25, peep: 12, flow: 50, fio2: 50, ie: 2.0, cao2: 16.5, cvo2: 12.0, cco2: 20.0, peco2: 20, vco2: 210, hco3: 24},
            cf:           {vt: 450, rr: 20, pip: 35, pplat: 20, peep: 8,  flow: 50, fio2: 45, ie: 3.0, cao2: 17.0, cvo2: 12.5, cco2: 20.2, peco2: 22, vco2: 220, hco3: 28},
            kypho:        {vt: 250, rr: 24, pip: 35, pplat: 32, peep: 5,  flow: 40, fio2: 30, ie: 2.0, cao2: 18.0, cvo2: 13.5, cco2: 20.4, peco2: 32, vco2: 190, hco3: 29},
            bronch:       {vt: 480, rr: 16, pip: 28, pplat: 18, peep: 5,  flow: 45, fio2: 35, ie: 2.5, cao2: 18.0, cvo2: 13.0, cco2: 20.0, peco2: 24, vco2: 200, hco3: 26},
            mild_ards:    {vt: 400, rr: 20, pip: 28, pplat: 24, peep: 10, flow: 55, fio2: 50, ie: 2.0, cao2: 17.5, cvo2: 13.0, cco2: 20.2, peco2: 22, vco2: 210, hco3: 24},
            atelectasis:  {vt: 380, rr: 20, pip: 26, pplat: 22, peep: 5,  flow: 50, fio2: 40, ie: 2.0, cao2: 18.2, cvo2: 13.8, cco2: 20.3, peco2: 26, vco2: 200, hco3: 24},
            flail:        {vt: 400, rr: 26, pip: 28, pplat: 20, peep: 8,  flow: 50, fio2: 40, ie: 2.0, cao2: 17.8, cvo2: 13.0, cco2: 20.0, peco2: 24, vco2: 210, hco3: 23},
            p_htn:        {vt: 450, rr: 22, pip: 25, pplat: 18, peep: 5,  flow: 55, fio2: 50, ie: 2.0, cao2: 15.0, cvo2: 10.0, cco2: 19.5, peco2: 18, vco2: 180, hco3: 22},
            co_poison:    {vt: 500, rr: 16, pip: 20, pplat: 14, peep: 5,  flow: 60, fio2: 100,ie: 2.0, cao2: 12.0, cvo2: 8.0,  cco2: 20.0, peco2: 30, vco2: 200, hco3: 20},
            ards_mod:     {vt: 380, rr: 24, pip: 32, pplat: 28, peep: 12, flow: 55, fio2: 60, ie: 1.5, cao2: 16.5, cvo2: 12.0, cco2: 20.1, peco2: 20, vco2: 230, hco3: 22}
        };

        function loadPreset(type) {
            const data = PRESETS[type];
            document.getElementById('vt_input').value = data.vt;
            document.getElementById('rr').value = data.rr;
            document.getElementById('pip').value = data.pip;
            document.getElementById('pplat').value = data.pplat;
            document.getElementById('peep').value = data.peep;
            document.getElementById('peak_flow').value = data.flow;
            document.getElementById('fio2').value = data.fio2;
            document.getElementById('ie_ratio').value = data.ie;
            
            document.getElementById('cao2').value = data.cao2;
            document.getElementById('cvo2').value = data.cvo2;
            document.getElementById('cco2').value = data.cco2;
            document.getElementById('peco2').value = data.peco2;
            document.getElementById('vco2').value = data.vco2;
            document.getElementById('hco3_input').value = data.hco3;
            
            document.getElementById('calc-form').submit();
        }
    </script>
</body>
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
    
    flash("ACCESS DENIED. Invalid Credentials.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session: return redirect(url_for('home'))
    if request.method == 'POST':
        curr = session['user']
        nu = request.form.get('new_username').strip()
        np = request.form.get('new_password').strip()
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        if nu:
            c.execute("UPDATE users SET username=? WHERE username=?", (nu, curr))
            session['user'] = nu
            curr = nu
        if np:
            c.execute("UPDATE users SET password=? WHERE username=?", (generate_password_hash(np), curr))
        conn.commit()
        conn.close()
        
        flash("SYSTEM UPDATED: Credentials modified successfully.")
        return redirect(url_for('settings'))

    return render_template_string(SETTINGS_HTML)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    
    sim_data = None
    inputs = {}
    if request.method == 'POST':
        inputs = {k: request.form.get(k) for k in request.form}
        clean_inputs = {k: RespiratoryEngine.safe_float(v, 0) for k, v in inputs.items()}
        try:
            sim_data = RespiratoryEngine.calculate_simulation(clean_inputs)
        except Exception:
            flash(f"Error calculating metrics: {traceback.format_exc()}")

    return render_template_string(DASHBOARD_HTML, sim_data=sim_data, inputs=inputs, COPYRIGHT_FOOTER=COPYRIGHT_FOOTER)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
