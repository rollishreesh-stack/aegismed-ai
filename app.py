import os
import math
import json
import sqlite3
import traceback
from flask import Flask, request, redirect, url_for, session, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_omni_sync_pro_2026")
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
                  ('admin', hashed_pw, 'Chief Pulmonologist'))
    
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. PATHOLOGY DATABASE & MATH ENGINE
# ==========================================

DISEASE_PROFILES = {
    "healthy": {
        "condition": "Stable Pulmonary Homeostasis",
        "description": "Ventilatory mechanics, airway resistance, dynamic compliance, and systemic gas exchange parameters are registering within optimal clinical limits. No acute pathological deviations detected.",
        "solutions": ["Maintain current ventilatory support and oxygenation settings.", "Monitor patient for readiness to wean.", "Perform daily Spontaneous Breathing Trials (SBTs)."]
    },
    "ards": {
        "condition": "Severe Acute Respiratory Distress Syndrome (ARDS)",
        "description": "Profound, refractory hypoxemia secondary to massive intrapulmonary shunting and severely stiffened non-compliant lungs. Indicates diffuse alveolar damage and protein-rich pulmonary edema.",
        "solutions": ["Implement strict lung-protective ventilation (Tidal Volume 4-6 mL/kg Ideal Body Weight).", "Optimize PEEP via ARDSNet high PEEP/FiO2 guidelines.", "Initiate early prone positioning for at least 16 hours per day.", "Evaluate for V-V ECMO if hypoxemia remains refractory."]
    },
    "copd": {
        "condition": "End-Stage COPD / Severe Emphysema",
        "description": "Abnormally high static lung compliance combined with significantly elevated airway resistance. Indicates severe destruction of alveolar septa, loss of elastic recoil, and chronic airflow limitation.",
        "solutions": ["Accept permissive hypercapnia (Target pH > 7.20) to avoid dynamic hyperinflation.", "Apply extrinsic PEEP to match approximately 80% of intrinsic Auto-PEEP.", "Administer scheduled short-acting and long-acting bronchodilators."]
    },
    "asthma": {
        "condition": "Status Asthmaticus",
        "description": "Critically elevated airway resistance indicating severe, refractory bronchospasm, mucosal edema, and mucus plugging. Extremely high risk of dynamic hyperinflation and barotrauma.",
        "solutions": ["Administer continuous nebulized Albuterol and Ipratropium.", "Administer systemic IV corticosteroids immediately.", "Decrease respiratory rate (8-10 breaths/min) to allow prolonged exhalation time."]
    },
    "fibrosis": {
        "condition": "Advanced Pulmonary Fibrosis",
        "description": "Severely restricted lung volumes due to dense parenchymal scarring. Compliance is critically low, rendering the lungs stiff, though primary airway resistance remains unaffected.",
        "solutions": ["Utilize ultra-low tidal volume ventilation to prevent severe volutrauma.", "Titrate PEEP cautiously; fibrotic lungs do not recruit well and high PEEP may cause overdistension.", "Evaluate for acute infectious exacerbation."]
    },
    "pe": {
        "condition": "Massive Pulmonary Embolism",
        "description": "Severe dead-space (Vd/Vt) ventilation anomaly detected. The alveoli are effectively ventilated, but pulmonary capillary blood flow is obstructed. Indicates a massive occlusion in the pulmonary arterial bed.",
        "solutions": ["Initiate immediate systemic anticoagulation (e.g., Heparin infusion).", "Consider systemic thrombolytics (tPA) or catheter-directed embolectomy if hemodynamically unstable.", "Provide aggressive vasopressor support for right ventricular failure."]
    },
    "pneumonia": {
        "condition": "Severe Lobar Pneumonia",
        "description": "A localized alveolar filling process (purulent exudate and inflammation) causing significant right-to-left intrapulmonary shunting, distinct from diffuse ARDS stiffening.",
        "solutions": ["Administer broad-spectrum empiric IV antibiotics immediately post-cultures.", "Target oxygen therapy and moderate PEEP to improve saturation.", "Consider positioning the patient with the 'good lung down' to optimize V/Q matching."]
    },
    "neuro": {
        "condition": "Neuromuscular Pump Failure",
        "description": "Intrinsic lung mechanics (compliance and resistance) are normal, but minute ventilation is grossly inadequate leading to severe hypercapnia. Suggests critical diaphragm weakness or CNS depression.",
        "solutions": ["Provide full mechanical ventilatory support as the patient cannot trigger adequate breaths.", "Assess for reversible neurologic causes (e.g., Guillain-Barré, Myasthenia Gravis crisis).", "Perform regular, aggressive pulmonary hygiene and secretion clearance."]
    },
    "obesity": {
        "condition": "Obesity Hypoventilation Syndrome",
        "description": "Decreased overall respiratory system compliance due to massive adiposity on the chest wall, leading to chronic CO2 retention, basilar lung collapse, and elevated dead space.",
        "solutions": ["Utilize significantly higher PEEP levels to overcome heavy chest wall weight.", "Position the patient in a reverse Trendelenburg or seated upright position.", "Target Ideal Body Weight (IBW) for tidal volume calculations, avoiding actual body weight."]
    },
    "pneumothorax": {
        "condition": "Tension Pneumothorax",
        "description": "Catastrophic loss of lung compliance combined with acute hypercapnia. Suggests complete unilateral lung collapse, pleural air accumulation under pressure, and mediastinal shift.",
        "solutions": ["IMMEDIATE: Perform needle thoracostomy decompression.", "Prepare for urgent chest tube insertion (Tube Thoracostomy).", "Disconnect from positive pressure ventilation briefly if hemodynamic collapse is imminent."]
    },
    "edema": {
        "condition": "Cardiogenic Pulmonary Edema",
        "description": "Reduced lung compliance and elevated shunt fraction indicative of hydrostatic fluid transudation into the alveolar spaces secondary to acute left ventricular failure.",
        "solutions": ["Administer IV loop diuretics (e.g., Furosemide) to actively reduce volume overload.", "Administer vasodilators (e.g., Nitroglycerin infusion) to reduce preload if blood pressure is adequate.", "Apply sufficient PEEP to mechanically displace alveolar fluid and improve gas exchange."]
    },
    "cf": {
        "condition": "Cystic Fibrosis Exacerbation",
        "description": "A complex mixed obstructive and shunting defect. Thick, inspissated, purulent secretions are causing high airway resistance, mucosal plugging, and localized atelectasis.",
        "solutions": ["Administer aggressive inhaled mucolytics (e.g., Dornase alfa) and hypertonic saline.", "Perform intense chest physiotherapy and postural drainage.", "Initiate targeted, broad-spectrum IV antibiotics covering pseudomonas."]
    },
    "kypho": {
        "condition": "Severe Kyphoscoliosis Decompensation",
        "description": "Severe structural chest wall deformity restricting lung expansion, leading to chronic hypercapnia that has acutely decompensated due to increased metabolic demand.",
        "solutions": ["Utilize Non-Invasive Positive Pressure Ventilation (NiPPV/BiPAP) if airway is patent.", "Apply high PEEP to overcome mechanical chest wall resistance.", "Treat acute infectious triggers aggressively."]
    },
    "bronch": {
        "condition": "Acute Bronchiectasis Exacerbation",
        "description": "Chronically dilated, scarred, and flaccid airways filled with purulent sputum causing massive expiratory resistance and hypercapnia.",
        "solutions": ["Implement aggressive pulmonary toilet and suctioning.", "Administer targeted IV antibiotics based on prior sputum cultures.", "Utilize bronchodilators and low respiratory rates to prevent Auto-PEEP."]
    },
    "mild_ards": {
        "condition": "Early / Mild ARDS Progression",
        "description": "Decreasing lung compliance and tachypnea causing a respiratory alkalosis early in the disease process. Inflammatory fluid is beginning to disrupt surfactant production.",
        "solutions": ["Monitor strictly for progression to moderate/severe ARDS.", "Apply moderate PEEP (8-10 cmH2O) to stabilize alveoli early.", "Restrict IV fluids to maintain an even or negative fluid balance."]
    },
    "atelectasis": {
        "condition": "Major Lobar Atelectasis",
        "description": "Acute loss of lung volume due to a collapsed lobe, resulting in decreased compliance and focal dead space. Often caused by an obstructing mucus plug.",
        "solutions": ["Consider therapeutic bronchoscopy to visually identify and extract mucus plugs.", "Institute aggressive chest physiotherapy and deep suctioning.", "Execute careful alveolar recruitment maneuvers to open collapsed dependent lung units."]
    },
    "flail": {
        "condition": "Flail Chest / Blunt Thoracic Trauma",
        "description": "Paradoxical chest wall movement due to sequential rib fractures, leading to severely impaired compliance, pain-induced hypoventilation, and underlying pulmonary contusion.",
        "solutions": ["Provide positive pressure ventilation to mechanically stabilize the chest wall ('pneumatic splinting').", "Ensure aggressive pain control (e.g., epidural analgesia) to prevent hypoventilation.", "Consult thoracic surgery for potential surgical rib fixation."]
    },
    "p_htn": {
        "condition": "Pulmonary Hypertension / Cor Pulmonale",
        "description": "Right-sided heart failure causing poor perfusion to the lungs. Reflected hemodynamically by high dead space (ventilation without perfusion) and stiffened pulmonary vasculature.",
        "solutions": ["Administer inhaled pulmonary vasodilators (e.g., Nitric Oxide or inhaled Epoprostenol).", "Aggressively avoid hypoxia and hypercapnia, which exacerbate pulmonary vasoconstriction.", "Optimize right ventricular preload and provide inotropic support (e.g., Milrinone)."]
    },
    "co_poison": {
        "condition": "Carbon Monoxide Toxicity",
        "description": "Patient displays critical cellular hypoxia despite standard SpO2 probes indicating excellent oxygenation (probes cannot differentiate Oxyhemoglobin from Carboxyhemoglobin).",
        "solutions": ["Maintain 100% FiO2 via mechanical ventilation to drastically decrease the half-life of Carbon Monoxide.", "Obtain a direct arterial blood gas with CO-oximetry.", "Arrange urgent transfer to a hyperbaric oxygen facility if neurologic deficits are present."]
    },
    "ards_mod": {
        "condition": "Moderate ARDS",
        "description": "Significant intrapulmonary shunting and deteriorating compliance. The PaO2/FiO2 ratio has fallen below 200, indicating established acute lung injury.",
        "solutions": ["Strict adherence to ARDSNet low tidal volume protocols (6 mL/kg PBW).", "Maintain plateau pressures strictly below 30 cmH2O.", "Consider paralysis with neuromuscular blocking agents if ventilator dyssynchrony persists."]
    }
}

class RespiratoryEngine:
    @staticmethod
    def safe_float(val, default):
        try:
            if val is None or str(val).strip() == '': return float(default)
            return float(val)
        except ValueError:
            return float(default)

    @classmethod
    def calculate_simulation(cls, inputs, preset_id=""):
        vt = max(10.0, inputs['vt_input'])
        peep = max(0.0, inputs['peep'])
        pplat = max(peep + 1.0, inputs['pplat'])
        pip = max(pplat + 1.0, inputs['pip'])
        flow_lmin = max(5.0, inputs['peak_flow'])
        peco2 = max(0.1, inputs['peco2'])
        cao2 = max(0.1, inputs['cao2'])
        cco2 = max(cao2 + 0.1, inputs['cco2'])
        cvo2 = min(cao2 - 0.1, inputs['cvo2'])
        hco3_input = max(0.1, inputs['hco3_input'])
        rr = max(1.0, inputs['rr'])
        ie = max(0.1, inputs['ie_ratio'])
        vco2 = max(10.0, inputs['vco2'])
        fio2_val = inputs['fio2']

        driving_pressure = pplat - peep
        compliance = vt / driving_pressure
        flow_lsec = flow_lmin / 60.0
        resistance = (pip - pplat) / flow_lsec
        min_vent_est = (vt * rr) / 1000.0
        
        vd_base = 0.35
        if compliance < 45: vd_base += (45.0 - compliance) * 0.012
        if resistance > 12: vd_base += (resistance - 12.0) * 0.008
        vd_vt_ratio = max(0.15, min(0.75, vd_base))
        
        alv_vent = max(0.5, min_vent_est * (1.0 - vd_vt_ratio))
        paco2 = round((0.863 * vco2) / alv_vent, 1)

        shunt_denominator = max(0.1, cco2 - cvo2)
        shunt_ratio = (cco2 - cao2) / shunt_denominator
        shunt_pct = round(max(0.01, min(0.95, shunt_ratio)) * 100, 1)
        
        try: ph = round(6.1 + math.log10(hco3_input / (0.0301 * paco2)), 2)
        except Exception: ph = 7.40

        if preset_id in DISEASE_PROFILES:
            ai_result = DISEASE_PROFILES[preset_id]
        else:
            ai_result = cls._fallback_ai_diagnostics(compliance, resistance, shunt_pct, paco2, ph, vd_vt_ratio)
            
        acid_base_status = cls._analyze_acid_base(ph, paco2)

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
    def _fallback_ai_diagnostics(compliance, resistance, shunt_pct, paco2, ph, vd_vt_ratio):
        if compliance < 30 and shunt_pct > 25: return DISEASE_PROFILES['ards']
        elif resistance > 20: return DISEASE_PROFILES['asthma']
        elif vd_vt_ratio > 0.50: return DISEASE_PROFILES['pe']
        elif compliance > 50 and resistance > 12: return DISEASE_PROFILES['copd']
        elif compliance < 35 and shunt_pct < 15: return DISEASE_PROFILES['fibrosis']
        else: return DISEASE_PROFILES['healthy']

    @staticmethod
    def _analyze_acid_base(ph, paco2):
        if ph < 7.35: return "Respiratory Acidosis" if paco2 > 45 else "Metabolic Acidosis"
        elif ph > 7.45: return "Respiratory Alkalosis" if paco2 < 35 else "Metabolic Alkalosis"
        return "Normal Acid-Base Equilibrium"

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
# 3. PREMIUM UI, CSS, & ANIMATIONS
# ==========================================

BACKGROUND_SVG = """
<svg class="living-lung" viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="cyanGrad" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.7"/>
            <stop offset="50%" stop-color="#0891b2" stop-opacity="0.9"/>
            <stop offset="100%" stop-color="#164e63" stop-opacity="1"/>
        </radialGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="6" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>
    <g filter="url(#glow)">
        <path d="M245 40 h10 v80 h-10 z" fill="#06b6d4"/>
        <path d="M250 120 L190 160 L195 170 L250 135 L305 170 L310 160 Z" fill="#06b6d4"/>
        <path d="M230 135 C 130 90, 50 210, 70 330 C 90 390, 190 390, 230 330 C 250 270, 240 180, 230 135 Z" fill="url(#cyanGrad)"/>
        <path d="M270 135 C 370 90, 450 210, 430 330 C 410 390, 310 390, 270 330 C 250 270, 260 180, 270 135 Z" fill="url(#cyanGrad)"/>
    </g>
</svg>
"""

GLOBAL_CSS = """
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Inter', sans-serif; background-color: #020617; color: #f8fafc; overflow-x: hidden; min-height: 100vh; display: flex; flex-direction: column; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    
    @keyframes holographicBreathe {
        0% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.25; filter: drop-shadow(0 0 20px rgba(6,182,212,0.3)); }
        50% { transform: translate(-50%, -50%) scale(1.03); opacity: 0.65; filter: drop-shadow(0 0 50px rgba(6,182,212,0.7)); }
        100% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.25; filter: drop-shadow(0 0 20px rgba(6,182,212,0.3)); }
    }
    .living-lung { position: fixed; top: 50%; left: 50%; width: 100vw; max-width: 900px; z-index: 0; pointer-events: none; animation: holographicBreathe 5s ease-in-out infinite; }
    
    .glass-panel { 
        background: rgba(15, 23, 42, 0.65); 
        backdrop-filter: blur(20px); 
        -webkit-backdrop-filter: blur(20px); 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        position: relative; z-index: 10;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6); 
    }
    
    .glass-input { background: rgba(0, 0, 0, 0.6); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; transition: all 0.3s ease; }
    .glass-input:focus { outline: none; border-color: #22d3ee; box-shadow: 0 0 15px rgba(34, 211, 238, 0.4); background: rgba(0, 0, 0, 0.9); }

    /* Siri-like Lyra Orb Animation */
    @keyframes siriWave {
        0% { box-shadow: 0 0 10px #c084fc, 0 0 20px #e879f9, inset 0 0 15px #c084fc; transform: scale(0.95); }
        100% { box-shadow: 0 0 20px #c084fc, 0 0 40px #e879f9, inset 0 0 25px #e879f9; transform: scale(1.05); }
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .siri-active {
        background: linear-gradient(135deg, #c084fc, #e879f9, #60a5fa);
        background-size: 200% 200%;
        animation: siriWave 1s ease-in-out infinite alternate, gradientShift 3s ease infinite;
    }
    .siri-inactive { background: #334155; }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
</style>
<script>
    function updateClock() {
        const now = new Date();
        const dateString = now.toLocaleDateString(document.getElementById('ui-lang')?.value || 'en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
        const timeString = now.toLocaleTimeString(document.getElementById('ui-lang')?.value || 'en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const clockEl = document.getElementById('live-clock');
        if(clockEl) {
            clockEl.innerHTML = `<div class="text-cyan-400 font-bold text-[13px] tracking-wider text-right leading-none">${timeString}</div><div class="text-slate-400 text-[9px] uppercase tracking-widest text-right mt-1">${dateString}</div>`;
        }
    }
    setInterval(updateClock, 1000);
    window.onload = updateClock;
</script>
"""

COPYRIGHT_FOOTER = """
<footer class="mt-auto py-5 text-center relative z-20 border-t border-slate-800 bg-slate-950/90">
    <div class="text-[11px] text-slate-500 font-medium tracking-wide">
        &copy; 2026 Shreesh Santoshkumar Rolli &nbsp;|&nbsp; <span data-i18n="footer_text">AeroLung Clinical Architecture</span>
    </div>
</footer>
"""

LOGIN_HTML = GLOBAL_CSS + BACKGROUND_SVG + """
<body class="flex items-center justify-center relative min-h-screen">
    <div class="glass-panel rounded-3xl p-10 w-full max-w-md text-center shadow-[0_0_40px_rgba(6,182,212,0.15)]">
        <h1 class="text-5xl font-black tracking-tighter text-white mb-2">AERO<span class="text-cyan-400">LUNG</span></h1>
        <p class="text-xs font-mono text-cyan-500/80 uppercase tracking-[0.3em] mb-10">Clinical Gateway</p>
        
        {% if get_flashed_messages() %}
            <div class="mb-6 p-3 text-xs text-rose-400 bg-rose-950/30 border border-rose-900/50 rounded uppercase tracking-wide">
                {% for msg in get_flashed_messages() %} {{ msg }} {% endfor %}
            </div>
        {% endif %}

        <form action="/login" method="POST" class="space-y-5 text-left">
            <div>
                <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1">Practitioner ID</label>
                <input type="text" name="username" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm" placeholder="Enter ID..." required>
            </div>
            <div>
                <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1">Secure Passkey</label>
                <input type="password" name="password" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm" placeholder="••••••••" required>
            </div>
            <button type="submit" class="w-full mt-4 py-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-sm uppercase tracking-[0.2em] transition-all shadow-[0_0_20px_rgba(6,182,212,0.4)]">
                Authenticate Uplink
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
        <div class="flex items-center gap-4">
            <div id="live-clock" class="hidden lg:block bg-black/50 border border-slate-800 px-4 py-2 rounded-xl shadow-inner text-right min-w-[120px]"></div>
            <a href="/dashboard" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold uppercase tracking-wider transition-colors border border-slate-600">Return to Dashboard</a>
        </div>
    </nav>

    <div class="glass-panel rounded-3xl p-10 w-full max-w-lg text-center mt-20 shadow-[0_0_40px_rgba(6,182,212,0.15)]">
        <h2 class="text-3xl font-black tracking-tighter text-white mb-2 uppercase">System Configuration</h2>
        <p class="text-xs font-mono text-cyan-500/80 uppercase tracking-[0.2em] mb-8">Modify Access Credentials</p>
        
        {% if get_flashed_messages() %}
            <div class="mb-6 p-3 text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-900/50 rounded uppercase tracking-wide">
                {% for msg in get_flashed_messages() %} {{ msg }} {% endfor %}
            </div>
        {% endif %}

        <form action="/settings" method="POST" class="space-y-5 text-left">
            <div>
                <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Current ID (Locked)</label>
                <input type="text" value="{{ session.user }}" disabled class="w-full bg-slate-900/50 text-slate-500 border border-white/5 px-5 py-4 rounded-xl font-mono text-sm cursor-not-allowed">
            </div>
            <div>
                <label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2 ml-1">New ID Override</label>
                <input type="text" name="new_username" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm" placeholder="Enter new ID">
            </div>
            <div>
                <label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2 ml-1">New Secure Passkey</label>
                <input type="password" name="new_password" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm" placeholder="Enter new password">
            </div>
            <button type="submit" class="w-full mt-4 py-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-sm uppercase tracking-[0.2em] transition-all shadow-[0_0_20px_rgba(6,182,212,0.4)]">
                Commit Changes
            </button>
        </form>
    </div>
    {{ COPYRIGHT_FOOTER | safe }}
</body>
"""

DASHBOARD_HTML = GLOBAL_CSS + BACKGROUND_SVG + """
<body class="min-h-screen flex flex-col relative">
    
    <nav class="glass-panel sticky top-0 z-50 border-b border-slate-800 rounded-none bg-slate-950/90 shadow-2xl">
        <div class="max-w-[1800px] mx-auto px-6 py-4 flex justify-between items-center">
            <div class="flex items-center gap-6">
                <h1 class="text-3xl font-black tracking-tighter text-white">AERO<span class="text-cyan-400">LUNG</span></h1>
                
                <select id="ui-lang" onchange="changeLanguage(this.value)" class="bg-black/50 border border-slate-700 text-slate-300 text-[10px] font-bold uppercase tracking-wider rounded-lg px-3 py-2 cursor-pointer focus:outline-none focus:border-cyan-500">
                    <option value="en" selected>English</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                    <option value="de">Deutsch</option>
                    <option value="zh">中文 (Chinese)</option>
                    <option value="hi">हिन्दी (Hindi)</option>
                </select>
            </div>
            
            <div class="flex items-center gap-6">
                <div id="live-clock" class="hidden lg:block bg-black/50 border border-slate-800 px-4 py-2 rounded-xl shadow-inner text-right min-w-[130px]"></div>

                <div class="text-[10px] font-mono text-slate-400 uppercase tracking-widest border-l border-r border-slate-700 px-5 hidden md:block">
                    <span data-i18n="nav_user">Practitioner:</span> <span class="text-cyan-400 font-bold block">{{ session.user }}</span>
                </div>
                <a href="/settings" data-i18n="nav_settings" class="px-4 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-600/50 text-[10px] font-bold uppercase tracking-wider transition-colors">Settings</a>
                <a href="/logout" data-i18n="nav_logout" class="px-4 py-2 rounded-lg bg-rose-900/40 hover:bg-rose-800/60 text-rose-300 border border-rose-800/50 text-[10px] font-bold uppercase tracking-wider transition-colors">Logout</a>
            </div>
        </div>
    </nav>

    <main class="w-full max-w-[1800px] mx-auto p-6 flex flex-col lg:flex-row gap-8 items-start relative z-10 flex-1">
        
        <div class="w-full lg:w-[480px] xl:w-[500px] flex flex-col gap-6 shrink-0 h-full">
            
            <div class="glass-panel rounded-2xl p-4 border-l-4 border-l-purple-500 shadow-xl flex items-center justify-between gap-4">
                <div class="flex items-center gap-4 flex-1">
                    <div id="lyra-orb" class="w-10 h-10 rounded-full siri-inactive flex-shrink-0 transition-all duration-300"></div>
                    <div class="flex-1 overflow-hidden">
                        <h3 class="text-[11px] font-bold text-purple-400 uppercase tracking-widest m-0" data-i18n="lyra_title">Lyra Voice AI</h3>
                        <div id="lyra-transcript" class="text-[10px] text-slate-400 font-mono italic truncate w-full" data-i18n="lyra_resting">Resting... Click activate.</div>
                    </div>
                </div>
                <button id="lyra-toggle-btn" onclick="toggleLyra()" class="bg-purple-600/80 hover:bg-purple-500 border border-purple-500 text-white font-bold px-4 py-2 rounded-lg text-[10px] uppercase tracking-wider transition-all shadow-[0_0_15px_rgba(147,51,234,0.3)] w-24">
                    Activate
                </button>
            </div>

            <div class="glass-panel rounded-2xl p-6 border-t-2 border-t-cyan-500">
                <h2 class="text-[11px] font-bold uppercase tracking-widest text-cyan-400 mb-2" data-i18n="db_title">Clinical Pathology Matrix</h2>
                <p class="text-[10px] text-slate-400 mb-5" data-i18n="db_desc">Select a validated condition from the master database to synchronize clinical hemodynamics.</p>
                
                <select id="preset-dropdown" onchange="if(this.value) loadPreset(this.value);" class="w-full glass-input px-4 py-3.5 rounded-xl text-sm font-semibold text-slate-200 cursor-pointer shadow-inner">
                    <option value="" disabled {% if not current_preset %}selected{% endif %}>-- Select a Clinical Pathology --</option>
                    <optgroup label="Baseline & Obstructive Defaults">
                        <option value="healthy" {% if current_preset == 'healthy' %}selected{% endif %}>Healthy Baseline Homeostasis</option>
                        <option value="copd" {% if current_preset == 'copd' %}selected{% endif %}>End-Stage COPD / Emphysema</option>
                        <option value="asthma" {% if current_preset == 'asthma' %}selected{% endif %}>Status Asthmaticus</option>
                        <option value="cf" {% if current_preset == 'cf' %}selected{% endif %}>Cystic Fibrosis Exacerbation</option>
                        <option value="bronch" {% if current_preset == 'bronch' %}selected{% endif %}>Acute Bronchiectasis</option>
                    </optgroup>
                    <optgroup label="Restrictive & ARDS Spectra">
                        <option value="mild_ards" {% if current_preset == 'mild_ards' %}selected{% endif %}>Early / Mild ARDS</option>
                        <option value="ards_mod" {% if current_preset == 'ards_mod' %}selected{% endif %}>Moderate ARDS</option>
                        <option value="ards" {% if current_preset == 'ards' %}selected{% endif %}>Severe ARDS Defect</option>
                        <option value="fibrosis" {% if current_preset == 'fibrosis' %}selected{% endif %}>Advanced Pulmonary Fibrosis</option>
                        <option value="atelectasis" {% if current_preset == 'atelectasis' %}selected{% endif %}>Major Lobar Atelectasis</option>
                    </optgroup>
                    <optgroup label="Vascular & Fluid Accumulation">
                        <option value="pe" {% if current_preset == 'pe' %}selected{% endif %}>Massive Pulmonary Embolism</option>
                        <option value="p_htn" {% if current_preset == 'p_htn' %}selected{% endif %}>Pulmonary HTN / Cor Pulmonale</option>
                        <option value="edema" {% if current_preset == 'edema' %}selected{% endif %}>Cardiogenic Pulmonary Edema</option>
                        <option value="pneumonia" {% if current_preset == 'pneumonia' %}selected{% endif %}>Severe Lobar Pneumonia</option>
                    </optgroup>
                    <optgroup label="Chest Wall & Systemic Toxicities">
                        <option value="neuro" {% if current_preset == 'neuro' %}selected{% endif %}>Neuromuscular Pump Failure</option>
                        <option value="obesity" {% if current_preset == 'obesity' %}selected{% endif %}>Obesity Hypoventilation Syndrome</option>
                        <option value="pneumothorax" {% if current_preset == 'pneumothorax' %}selected{% endif %}>Tension Pneumothorax</option>
                        <option value="kypho" {% if current_preset == 'kypho' %}selected{% endif %}>Severe Kyphoscoliosis</option>
                        <option value="flail" {% if current_preset == 'flail' %}selected{% endif %}>Flail Chest / Blunt Trauma</option>
                        <option value="co_poison" {% if current_preset == 'co_poison' %}selected{% endif %}>Carbon Monoxide Toxicity</option>
                    </optgroup>
                    <option value="custom" {% if current_preset == 'custom' %}selected{% endif %} hidden>Custom Telemetry Override Active</option>
                </select>
            </div>

            <div class="glass-panel rounded-2xl flex flex-col shadow-2xl flex-1">
                <form id="calc-form" method="POST" action="/dashboard" class="p-6 flex-1 flex flex-col justify-between">
                    <input type="hidden" name="preset_id" id="preset_id" value="{{ current_preset }}">
                    <h3 class="text-[11px] font-bold text-cyan-400 uppercase tracking-widest border-b border-white/10 pb-2 mb-4" data-i18n="manual_override">Manual Telemetry Override</h3>
                    
                    <div class="text-[9px] text-slate-500 uppercase tracking-widest mb-2 font-bold" data-i18n="vent_mechanics">Ventilation Mechanics</div>
                    <div class="grid grid-cols-4 gap-2 mb-5 bg-black/40 p-4 rounded-xl border border-white/5">
                        <div title="Tidal Volume in mL"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1">Vt (mL)</label><input type="number" name="vt_input" id="vt_input" value="{{ inputs.vt_input|default(500) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono" oninput="resetPreset()"></div>
                        <div title="Respiratory Rate"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1">Rate</label><input type="number" name="rr" id="rr" value="{{ inputs.rr|default(14) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono" oninput="resetPreset()"></div>
                        <div title="Peak Inspiratory Pressure"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1">PIP</label><input type="number" name="pip" id="pip" value="{{ inputs.pip|default(20) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-rose-300" oninput="resetPreset()"></div>
                        <div title="Plateau Pressure"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1">Pplat</label><input type="number" name="pplat" id="pplat" value="{{ inputs.pplat|default(14) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-rose-300" oninput="resetPreset()"></div>
                        <div title="Positive End-Expiratory Pressure"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1">PEEP</label><input type="number" name="peep" id="peep" value="{{ inputs.peep|default(5) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-cyan-300" oninput="resetPreset()"></div>
                        <div title="Peak Flow in L/min"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1">Flow</label><input type="number" name="peak_flow" id="peak_flow" value="{{ inputs.peak_flow|default(60) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono" oninput="resetPreset()"></div>
                        <div title="Fraction of Inspired Oxygen"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1">FiO2 %</label><input type="number" name="fio2" id="fio2" value="{{ inputs.fio2|default(30) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono" oninput="resetPreset()"></div>
                        <div title="Inspiratory:Expiratory Ratio"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1">I:E</label><input type="number" step="0.1" name="ie_ratio" id="ie_ratio" value="{{ inputs.ie_ratio|default(2.0) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono" oninput="resetPreset()"></div>
                    </div>
                    
                    <div class="text-[9px] text-slate-500 uppercase tracking-widest mb-2 font-bold" data-i18n="blood_labs">Systemic Blood Labs</div>
                    <div class="grid grid-cols-3 gap-3 mb-6 bg-black/40 p-4 rounded-xl border border-white/5">
                        <div title="Arterial Oxygen Content"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1">CaO2</label><input type="number" step="0.1" name="cao2" id="cao2" value="{{ inputs.cao2|default(19.8) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-emerald-300" oninput="resetPreset()"></div>
                        <div title="Venous Oxygen Content"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1">CvO2</label><input type="number" step="0.1" name="cvo2" id="cvo2" value="{{ inputs.cvo2|default(14.8) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-emerald-300" oninput="resetPreset()"></div>
                        <div title="Capillary Oxygen Content"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1">CcO2</label><input type="number" step="0.1" name="cco2" id="cco2" value="{{ inputs.cco2|default(20.4) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-emerald-300" oninput="resetPreset()"></div>
                        <div title="Exhaled CO2"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1 mt-1">PECO2</label><input type="number" name="peco2" id="peco2" value="{{ inputs.peco2|default(28) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-amber-300" oninput="resetPreset()"></div>
                        <div title="CO2 Production"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1 mt-1">VCO2</label><input type="number" name="vco2" id="vco2" value="{{ inputs.vco2|default(200) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-amber-300" oninput="resetPreset()"></div>
                        <div title="Systemic Bicarbonate"><label class="text-[9px] font-bold text-slate-400 uppercase block mb-1 mt-1">HCO3</label><input type="number" name="hco3_input" id="hco3_input" value="{{ inputs.hco3_input|default(24) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-purple-300" oninput="resetPreset()"></div>
                    </div>

                    <button type="submit" class="w-full py-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-black text-xs uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(34,211,238,0.4)] transition-all mt-auto" data-i18n="synthesize_btn">
                        Synthesize Clinical Telemetry
                    </button>
                </form>
            </div>
        </div>

        <div class="flex-1 flex flex-col gap-6 w-full min-w-0 h-full">
            {% if not sim_data %}
            <div class="glass-panel rounded-3xl flex-1 flex flex-col items-center justify-center min-h-[600px] border-dashed border-slate-600/50">
                <div class="w-24 h-24 border-4 border-slate-700 border-t-cyan-400 rounded-full animate-spin mb-6 shadow-[0_0_30px_rgba(34,211,238,0.4)]"></div>
                <h3 class="text-2xl font-black text-white mb-2 uppercase tracking-widest" data-i18n="standby_title">Diagnostic Standby</h3>
                <p class="text-sm text-slate-400 font-mono text-center max-w-sm" data-i18n="standby_desc">Select a pathology profile from the matrix, or activate Lyra AI to command parameters via voice.</p>
            </div>
            {% else %}
            
            <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <div class="glass-panel p-6 rounded-2xl border-l-4 border-l-cyan-400 bg-gradient-to-br from-slate-900/95 to-black flex-1">
                    <h3 class="text-[11px] text-cyan-400 font-black uppercase tracking-[0.2em] mb-2" data-i18n="expert_sys">Expert Diagnostic System</h3>
                    <div class="text-2xl font-black text-white leading-tight tracking-tight mb-4 uppercase drop-shadow-md">{{ sim_data.ai_condition }}</div>
                    
                    <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1 border-b border-white/10 pb-1" data-i18n="physio_breakdown">Pathophysiological Breakdown</div>
                    <div class="text-sm text-slate-300 bg-black/40 p-4 rounded-lg border border-white/5 leading-relaxed mb-4 shadow-inner">
                        {{ sim_data.ai_description }}
                    </div>

                    <div class="text-[10px] font-bold text-emerald-400 uppercase tracking-widest mb-1 border-b border-white/10 pb-1" data-i18n="action_plan">Required Clinical Action Plan</div>
                    <ul class="space-y-2">
                        {% for solution in sim_data.ai_solutions %}
                        <li class="flex items-start gap-2 bg-emerald-950/20 p-2.5 rounded-lg border border-emerald-900/30 text-xs text-slate-200">
                            <span class="text-emerald-500 font-bold mt-0.5">⯈</span> <span>{{ solution }}</span>
                        </li>
                        {% endfor %}
                    </ul>
                </div>

                <div class="flex flex-col gap-6">
                    <div class="glass-panel p-6 rounded-2xl border-t-4 border-t-purple-500 flex flex-col justify-center">
                        <h3 class="text-[11px] text-purple-400 font-black uppercase tracking-[0.2em] mb-4 text-center" data-i18n="abg_analysis">Arterial Blood Gas Analysis</h3>
                        <div class="grid grid-cols-3 gap-2 mb-4 bg-black/40 p-5 rounded-2xl border border-white/5 text-center shadow-inner">
                            <div>
                                <span class="text-[10px] text-slate-500 font-bold uppercase block mb-1">Blood pH</span>
                                <span class="text-3xl font-black font-mono {% if sim_data.ph < 7.35 %}text-rose-500{% elif sim_data.ph > 7.45 %}text-cyan-400{% else %}text-emerald-400{% endif %}">{{ sim_data.ph }}</span>
                            </div>
                            <div class="border-l border-white/10">
                                <span class="text-[10px] text-slate-500 font-bold uppercase block mb-1">PaCO2</span>
                                <span class="text-3xl font-black font-mono text-amber-400">{{ sim_data.paco2 }}</span>
                            </div>
                            <div class="border-l border-white/10">
                                <span class="text-[10px] text-slate-500 font-bold uppercase block mb-1">HCO3</span>
                                <span class="text-3xl font-black font-mono text-purple-400">{{ sim_data.hco3 }}</span>
                            </div>
                        </div>
                        <div class="text-sm font-bold text-white uppercase tracking-wider bg-purple-950/50 block text-center py-3 rounded-lg border border-purple-800">{{ sim_data.acid_base_status }}</div>
                    </div>
                    
                    <div class="glass-panel rounded-2xl p-5 border-t-2 border-t-emerald-500 shadow-xl flex-1">
                        <h3 class="text-[11px] font-bold text-emerald-400 uppercase tracking-widest border-b border-white/10 pb-2 mb-3" data-i18n="ref_targets">Reference Targets</h3>
                        <ul class="space-y-3 text-xs font-mono text-slate-300">
                            <li class="flex justify-between items-center"><span class="font-sans font-semibold text-slate-400 uppercase tracking-wider text-[10px]">Compliance</span><span class="text-emerald-400 bg-emerald-950/30 px-2 py-1 rounded border border-emerald-900/50">60-80</span></li>
                            <li class="flex justify-between items-center"><span class="font-sans font-semibold text-slate-400 uppercase tracking-wider text-[10px]">Resistance</span><span class="text-emerald-400 bg-emerald-950/30 px-2 py-1 rounded border border-emerald-900/50">5-10</span></li>
                            <li class="flex justify-between items-center"><span class="font-sans font-semibold text-slate-400 uppercase tracking-wider text-[10px]">Vd/Vt Ratio</span><span class="text-emerald-400 bg-emerald-950/30 px-2 py-1 rounded border border-emerald-900/50">< 30 %</span></li>
                            <li class="flex justify-between items-center"><span class="font-sans font-semibold text-slate-400 uppercase tracking-wider text-[10px]">Shunt %</span><span class="text-emerald-400 bg-emerald-950/30 px-2 py-1 rounded border border-emerald-900/50">< 5 %</span></li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="glass-panel p-5 rounded-2xl">
                <h3 class="text-[11px] text-slate-400 font-black uppercase tracking-[0.2em] mb-3 border-b border-white/10 pb-2" data-i18n="mech_engine">Diagnostic Mechanics Engine</h3>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5 shadow-inner">
                        <span class="text-[10px] text-cyan-400 font-bold uppercase tracking-widest block mb-2">Lung Compliance</span>
                        <div class="text-3xl font-black text-white font-mono mb-1">{{ sim_data.compliance }}</div>
                        <div class="text-[9px] text-slate-500 uppercase font-bold mb-3">mL/cmH2O</div>
                        <div class="text-[10px] text-slate-400 leading-snug border-t border-white/10 pt-2">Measures Lung Elasticity. Normal is ~60-80. Lower numbers indicate stiffer lungs.</div>
                    </div>
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5 shadow-inner">
                        <span class="text-[10px] text-rose-400 font-bold uppercase tracking-widest block mb-2">Airway Resistance</span>
                        <div class="text-3xl font-black text-white font-mono mb-1">{{ sim_data.resistance }}</div>
                        <div class="text-[9px] text-slate-500 uppercase font-bold mb-3">cmH2O/L/s</div>
                        <div class="text-[10px] text-slate-400 leading-snug border-t border-white/10 pt-2">Measures Airway Blockage. Normal is ~5-10. Higher numbers indicate bronchospasm.</div>
                    </div>
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5 shadow-inner">
                        <span class="text-[10px] text-amber-400 font-bold uppercase tracking-widest block mb-2">Vd/Vt (Dead Space)</span>
                        <div class="text-3xl font-black text-white font-mono mb-1">{{ sim_data.vd_vt }}<span class="text-lg text-slate-500">%</span></div>
                        <div class="text-[9px] text-slate-500 uppercase font-bold mb-3">Percentage</div>
                        <div class="text-[10px] text-slate-400 leading-snug border-t border-white/10 pt-2">Wasted ventilation not participating in gas exchange. Severely high in Embolisms.</div>
                    </div>
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5 shadow-inner">
                        <span class="text-[10px] text-emerald-400 font-bold uppercase tracking-widest block mb-2">Shunt Fraction</span>
                        <div class="text-3xl font-black text-white font-mono mb-1">{{ sim_data.shunt }}<span class="text-lg text-slate-500">%</span></div>
                        <div class="text-[9px] text-slate-500 uppercase font-bold mb-3">Percentage</div>
                        <div class="text-[10px] text-slate-400 leading-snug border-t border-white/10 pt-2">Blood bypassing ventilated alveoli. High levels cause severe refractory hypoxemia.</div>
                    </div>
                </div>
            </div>

            <div class="glass-panel p-6 rounded-2xl flex flex-col relative flex-1 min-h-[350px] w-full">
                <div class="flex justify-between items-center mb-4 border-b border-white/10 pb-2">
                    <h3 class="text-[11px] text-slate-400 font-black uppercase tracking-[0.2em]" data-i18n="wave_analytics">Ventilator Waveform Analytics</h3>
                    <div class="text-[10px] text-slate-300 flex gap-4 font-mono bg-black/50 px-3 py-1.5 rounded-lg border border-white/5">
                        <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded bg-[#22d3ee]"></span><span class="font-bold">Paw:</span> Pressure</div>
                        <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded bg-[#10b981]"></span><span class="font-bold">Vol:</span> Volume</div>
                        <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded bg-[#f43f5e]"></span><span class="font-bold">Flow:</span> Velocity</div>
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
                            { label: 'Pressure (cmH2O)', data: waveData.p, borderColor: '#22d3ee', backgroundColor: 'rgba(34, 211, 238, 0.1)', fill: true, borderWidth: 2.5, tension: 0.3, pointRadius: 0 },
                            { label: 'Volume (mL)', data: waveData.v, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.05)', fill: true, borderWidth: 2.5, tension: 0.3, pointRadius: 0 },
                            { label: 'Flow (L/m)', data: waveData.f, borderColor: '#f43f5e', backgroundColor: 'rgba(244, 63, 94, 0.05)', fill: true, borderWidth: 2.5, tension: 0.3, pointRadius: 0 }
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
    </main>

    <script>
        // ----------------------------------------------------
        // 1. I18N GLOBAL LANGUAGE DICTIONARY
        // ----------------------------------------------------
        const I18N = {
            "en": {
                "nav_user": "Practitioner:", "nav_settings": "Settings", "nav_logout": "Logout",
                "lyra_title": "Lyra Voice AI", "lyra_resting": "Resting... Click activate.", "lyra_btn_on": "Activate", "lyra_btn_off": "Rest",
                "db_title": "Clinical Pathology Matrix", "db_desc": "Select a condition to synchronize hemodynamics.",
                "manual_override": "Manual Telemetry Override", "vent_mechanics": "Ventilation Mechanics", "blood_labs": "Systemic Blood Labs",
                "synthesize_btn": "Synthesize Clinical Telemetry", "standby_title": "Diagnostic Standby", "standby_desc": "Select a pathology profile or activate Lyra.",
                "expert_sys": "Expert Diagnostic System", "physio_breakdown": "Pathophysiological Breakdown", "action_plan": "Clinical Action Plan",
                "abg_analysis": "Arterial Blood Gas Analysis", "ref_targets": "Reference Targets", "mech_engine": "Diagnostic Mechanics Engine",
                "wave_analytics": "Ventilator Waveform Analytics", "footer_text": "AeroLung Clinical Architecture"
            },
            "es": {
                "nav_user": "Médico:", "nav_settings": "Ajustes", "nav_logout": "Salir",
                "lyra_title": "Lyra IA de Voz", "lyra_resting": "Descansando... Haz clic para activar.", "lyra_btn_on": "Activar", "lyra_btn_off": "Descansar",
                "db_title": "Matriz de Patología Clínica", "db_desc": "Seleccione una condición para sincronizar la hemodinámica.",
                "manual_override": "Anulación de Telemetría", "vent_mechanics": "Mecánica de Ventilación", "blood_labs": "Laboratorios de Sangre",
                "synthesize_btn": "Sintetizar Telemetría", "standby_title": "Espera de Diagnóstico", "standby_desc": "Seleccione un perfil o active Lyra.",
                "expert_sys": "Sistema de Diagnóstico Experto", "physio_breakdown": "Desglose Fisiopatológico", "action_plan": "Plan de Acción Clínico",
                "abg_analysis": "Análisis de Gases en Sangre", "ref_targets": "Objetivos de Referencia", "mech_engine": "Motor de Mecánica Diagnóstica",
                "wave_analytics": "Análisis de Forma de Onda", "footer_text": "Arquitectura Clínica AeroLung"
            },
            "fr": {
                "nav_user": "Praticien:", "nav_settings": "Paramètres", "nav_logout": "Quitter",
                "lyra_title": "Lyra IA Vocale", "lyra_resting": "En repos... Cliquez pour activer.", "lyra_btn_on": "Activer", "lyra_btn_off": "Repos",
                "db_title": "Matrice de Pathologie", "db_desc": "Sélectionnez une condition pour synchroniser.",
                "manual_override": "Remplacement de Télémétrie", "vent_mechanics": "Mécanique de Ventilation", "blood_labs": "Analyses Sanguines",
                "synthesize_btn": "Synthétiser la Télémétrie", "standby_title": "Attente de Diagnostic", "standby_desc": "Sélectionnez un profil ou activez Lyra.",
                "expert_sys": "Système de Diagnostic", "physio_breakdown": "Analyse Physiopathologique", "action_plan": "Plan d'action",
                "abg_analysis": "Gazométrie Sanguine", "ref_targets": "Cibles de Référence", "mech_engine": "Moteur Mécanique",
                "wave_analytics": "Analyse des Ondes", "footer_text": "Architecture Clinique AeroLung"
            },
            "de": {
                "nav_user": "Arzt:", "nav_settings": "Einstellungen", "nav_logout": "Abmelden",
                "lyra_title": "Lyra Sprach-KI", "lyra_resting": "Ruht... Klicken zum Aktivieren.", "lyra_btn_on": "Aktivieren", "lyra_btn_off": "Ruhe",
                "db_title": "Pathologie-Matrix", "db_desc": "Wählen Sie eine Bedingung zur Synchronisierung.",
                "manual_override": "Manuelle Telemetrie", "vent_mechanics": "Beatmungsmechanik", "blood_labs": "Blutlabore",
                "synthesize_btn": "Telemetrie Synthetisieren", "standby_title": "Diagnose-Standby", "standby_desc": "Wählen Sie ein Profil oder aktivieren Sie Lyra.",
                "expert_sys": "Experten-Diagnosesystem", "physio_breakdown": "Pathophysiologische Analyse", "action_plan": "Klinischer Aktionsplan",
                "abg_analysis": "Blutgasanalyse", "ref_targets": "Referenzziele", "mech_engine": "Diagnostischer Mechanik-Motor",
                "wave_analytics": "Wellenform-Analyse", "footer_text": "AeroLung Klinische Architektur"
            },
            "zh": {
                "nav_user": "医生:", "nav_settings": "设置", "nav_logout": "退出",
                "lyra_title": "Lyra 语音 AI", "lyra_resting": "休息中... 点击激活。", "lyra_btn_on": "激活", "lyra_btn_off": "休息",
                "db_title": "临床病理矩阵", "db_desc": "选择一个条件以同步血流动力学。",
                "manual_override": "手动遥测覆盖", "vent_mechanics": "通气力学", "blood_labs": "全身血液化验",
                "synthesize_btn": "合成临床遥测", "standby_title": "诊断待机", "standby_desc": "选择病理配置文件或激活 Lyra。",
                "expert_sys": "专家诊断系统", "physio_breakdown": "病理生理分析", "action_plan": "临床行动计划",
                "abg_analysis": "动脉血气分析", "ref_targets": "参考目标", "mech_engine": "诊断力学引擎",
                "wave_analytics": "呼吸机波形分析", "footer_text": "AeroLung 临床架构"
            },
            "hi": {
                "nav_user": "चिकित्सक:", "nav_settings": "सेटिंग्स", "nav_logout": "लॉग आउट",
                "lyra_title": "Lyra वॉयस AI", "lyra_resting": "विश्राम... सक्रिय करने के लिए क्लिक करें।", "lyra_btn_on": "सक्रिय करें", "lyra_btn_off": "विश्राम",
                "db_title": "क्लीनिकल पैथोलॉजी मैट्रिक्स", "db_desc": "हेमोडायनामिक्स सिंक्रनाइज़ करने के लिए एक शर्त चुनें।",
                "manual_override": "मैनुअल टेलीमेट्री", "vent_mechanics": "वेंटिलेशन मैकेनिक्स", "blood_labs": "रक्त परीक्षण",
                "synthesize_btn": "टेलीमेट्री सिंथेसाइज़ करें", "standby_title": "डायग्नोस्टिक स्टैंडबाय", "standby_desc": "प्रोफ़ाइल चुनें या Lyra को सक्रिय करें।",
                "expert_sys": "विशेषज्ञ निदान प्रणाली", "physio_breakdown": "पैथोफिजियोलॉजिकल ब्रेकडाउन", "action_plan": "क्लीनिकल एक्शन प्लान",
                "abg_analysis": "आर्टेरियल ब्लड गैस", "ref_targets": "संदर्भ लक्ष्य", "mech_engine": "मैकेनिक्स इंजन",
                "wave_analytics": "वेवफॉर्म एनालिटिक्स", "footer_text": "AeroLung क्लीनिकल आर्किटेक्चर"
            }
        };

        const LYRA_LANG_MAP = { "en": "en-US", "es": "es-ES", "fr": "fr-FR", "de": "de-DE", "zh": "zh-CN", "hi": "hi-IN" };

        function changeLanguage(langCode) {
            const dict = I18N[langCode];
            if (!dict) return;
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (dict[key]) el.innerText = dict[key];
            });
            if (recognition) {
                recognition.lang = LYRA_LANG_MAP[langCode];
                if (lyraActive) { recognition.stop(); } // Auto-restarts via onend with new language
            }
            updateClock();
        }

        // ----------------------------------------------------
        // 2. 20 PRESETS DATABASE
        // ----------------------------------------------------
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
            if (!type || type === "custom") return;
            const data = PRESETS[type];
            document.getElementById('preset_id').value = type;
            document.getElementById('preset-dropdown').value = type;
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
        function resetPreset() {
            document.getElementById('preset-dropdown').value = "custom";
            document.getElementById('preset_id').value = "custom";
        }

        // ----------------------------------------------------
        // 3. LYRA AI SIRI-LIKE VOICE ENGINE
        // ----------------------------------------------------
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition;
        let lyraActive = false;

        const LYRA_VOICE_MAP = {
            "healthy": "healthy", "baseline": "healthy", "normal": "healthy",
            "ards": "ards", "distress syndrome": "ards", "severe ards": "ards",
            "copd": "copd", "emphysema": "copd",
            "asthma": "asthma", "status asthmaticus": "asthma",
            "fibrosis": "fibrosis", "pulmonary fibrosis": "fibrosis",
            "embolism": "pe", "pulmonary embolism": "pe",
            "pneumonia": "pneumonia", "lobar pneumonia": "pneumonia",
            "neuromuscular": "neuro", "pump failure": "neuro",
            "obesity": "obesity", "obesity hypoventilation": "obesity",
            "pneumothorax": "pneumothorax", "tension pneumothorax": "pneumothorax",
            "edema": "edema", "cardiogenic": "edema",
            "cystic fibrosis": "cf",
            "kyphoscoliosis": "kypho", "kypho": "kypho",
            "bronchiectasis": "bronch",
            "mild ards": "mild_ards", "early ards": "mild_ards",
            "atelectasis": "atelectasis", "lobar atelectasis": "atelectasis",
            "flail": "flail", "flail chest": "flail", "chest trauma": "flail",
            "hypertension": "p_htn", "pulmonary hypertension": "p_htn", "cor pulmonale": "p_htn",
            "carbon monoxide": "co_poison", "poisoning": "co_poison",
            "moderate ards": "ards_mod"
        };

        function initLyra() {
            if (!SpeechRecognition) {
                document.getElementById('lyra-transcript').innerText = "Voice API not supported in this browser. Use Chrome/Edge.";
                return;
            }
            recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.lang = LYRA_LANG_MAP[document.getElementById('ui-lang').value] || "en-US";

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase();
                document.getElementById('lyra-transcript').innerText = "Lyra heard: " + transcript;
                
                if (transcript.includes("lyra")) {
                    let matched = false;
                    for (let key in LYRA_VOICE_MAP) {
                        if (transcript.includes(key)) {
                            const presetKey = LYRA_VOICE_MAP[key];
                            speakLyra(`Confirmed. Loading clinical matrix for ${key}.`);
                            setTimeout(() => loadPreset(presetKey), 2500); // delay allows Lyra to finish speaking
                            matched = true;
                            break;
                        }
                    }
                    if (!matched) {
                        speakLyra("I am listening. Please state a valid pathology name to synchronize.");
                    }
                }
            };

            recognition.onend = function() {
                if (lyraActive) recognition.start(); // Auto-restart listening if turned on
            };
        }

        function speakLyra(text) {
            const synth = window.speechSynthesis;
            const utterThis = new SpeechSynthesisUtterance(text);
            utterThis.lang = LYRA_LANG_MAP[document.getElementById('ui-lang').value] || "en-US";
            synth.speak(utterThis);
        }

        function toggleLyra() {
            if (!SpeechRecognition) {
                alert("Your browser does not support the Web Speech API. Please try Google Chrome, Edge, or Safari.");
                return;
            }
            
            const btn = document.getElementById('lyra-toggle-btn');
            const orb = document.getElementById('lyra-orb');
            const transcript = document.getElementById('lyra-transcript');
            const langCode = document.getElementById('ui-lang').value;

            if (!lyraActive) {
                if(!recognition) initLyra();
                recognition.lang = LYRA_LANG_MAP[langCode];
                recognition.start();
                lyraActive = true;
                btn.innerText = I18N[langCode]?.lyra_btn_off || "Rest";
                btn.className = "bg-slate-700 hover:bg-slate-600 border border-slate-600 text-white font-bold px-4 py-2 rounded-lg text-[10px] uppercase tracking-wider transition-all w-24";
                orb.className = "w-10 h-10 rounded-full siri-active flex-shrink-0 transition-all duration-300";
                transcript.innerText = "Lyra is actively listening... Say 'Hey Lyra'";
                speakLyra("Lyra AI activated. Awaiting your clinical command.");
            } else {
                lyraActive = false;
                recognition.stop();
                btn.innerText = I18N[langCode]?.lyra_btn_on || "Activate";
                btn.className = "bg-purple-600/80 hover:bg-purple-500 border border-purple-500 text-white font-bold px-4 py-2 rounded-lg text-[10px] uppercase tracking-wider transition-all shadow-[0_0_15px_rgba(147,51,234,0.3)] w-24";
                orb.className = "w-10 h-10 rounded-full siri-inactive flex-shrink-0 transition-all duration-300";
                transcript.innerText = I18N[langCode]?.lyra_resting || "Resting... Click activate.";
            }
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
    return render_template_string(LOGIN_HTML, COPYRIGHT_FOOTER=COPYRIGHT_FOOTER)

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

    return render_template_string(SETTINGS_HTML, COPYRIGHT_FOOTER=COPYRIGHT_FOOTER)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    
    sim_data = None
    inputs = {}
    preset = request.form.get('preset_id', '')
    
    if request.method == 'POST':
        inputs = {k: request.form.get(k) for k in request.form if k != 'preset_id'}
        clean_inputs = {k: RespiratoryEngine.safe_float(v, 0) for k, v in inputs.items()}
        try:
            sim_data = RespiratoryEngine.calculate_simulation(clean_inputs, preset)
        except Exception:
            flash(f"Error calculating metrics: {traceback.format_exc()}")

    return render_template_string(DASHBOARD_HTML, sim_data=sim_data, inputs=inputs, current_preset=preset, COPYRIGHT_FOOTER=COPYRIGHT_FOOTER)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
