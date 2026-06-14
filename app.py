import os
import math
import json
import sqlite3
import traceback
from flask import Flask, request, redirect, url_for, session, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_omni_max_premium_2026")
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
# 2. SEAMLESS RESPIRATORY MATH ENGINE
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

        # Core Mechanical Metrics
        driving_pressure = max(0.1, pplat - peep)
        compliance = vt / driving_pressure
        flow_lsec = flow_lmin / 60.0
        resistance = max(0.1, (pip - pplat) / flow_lsec)
        
        # Dead Space Gas Exchange Fractions
        min_vent_est = (vt * rr) / 1000.0
        paco2_derived = max(1.0, (0.863 * vco2) / max(0.1, min_vent_est * 0.75))
        if peco2 >= paco2_derived: 
            peco2 = max(0.1, paco2_derived - 4.0)
            
        vd_vt_ratio = max(0.01, min(0.95, (paco2_derived - peco2) / paco2_derived))
        
        # Shunt Calculations
        shunt_denominator = max(0.1, cco2 - cvo2)
        shunt_ratio = (cco2 - cao2) / shunt_denominator
        shunt_pct = round(max(0.01, min(0.95, shunt_ratio)) * 100, 1)

        alv_vent = max(0.1, ((vt * (1 - vd_vt_ratio)) * rr) / 1000.0)
        paco2 = round((0.863 * vco2) / alv_vent, 1)
        
        # pH Acid-Base Profiles
        try: ph = round(6.1 + math.log10(hco3_input / (0.0301 * max(1.0, paco2))), 2)
        except Exception: ph = 7.40

        ai_result = cls._generate_ai_diagnostics(compliance, resistance, shunt_pct, paco2, ph, vd_vt_ratio)
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
    def _generate_ai_diagnostics(compliance, resistance, shunt_pct, paco2, ph, vd_vt_ratio):
        if compliance < 20 and paco2 > 50 and resistance < 15:
            return {
                "condition": "TENSION PNEUMOTHORAX", 
                "description": "Catastrophic loss of lung compliance combined with acute hypercapnia. Suggests complete unilateral lung collapse, pleural air accumulation, and mediastinal shift.", 
                "solutions": ["IMMEDIATE: Perform needle thoracostomy at 2nd intercostal space.", "Prepare for urgent chest tube insertion.", "Obtain stat portable Chest X-Ray post-decompression."]
            }
        elif resistance > 25 and paco2 > 45:
            return {
                "condition": "STATUS ASTHMATICUS", 
                "description": "Critically elevated airway resistance indicating severe, refractory bronchospasm, mucosal edema, and mucus plugging. High risk of dynamic hyperinflation.", 
                "solutions": ["Administer continuous nebulized Albuterol and Ipratropium.", "Administer systemic IV corticosteroids.", "Decrease respiratory rate to allow complete exhalation."]
            }
        elif vd_vt_ratio > 0.55 and shunt_pct < 15:
            return {
                "condition": "MASSIVE PULMONARY EMBOLISM", 
                "description": "Severe dead-space (Vd/Vt) ventilation detected. The alveoli are perfectly ventilated, but blood flow is blocked.", 
                "solutions": ["Initiate immediate systemic anticoagulation.", "Consider systemic thrombolytics (tPA) if hemodynamically unstable.", "Provide vasopressor support for right ventricular failure."]
            }
        elif compliance < 30 and shunt_pct > 25:
            return {
                "condition": "SEVERE ARDS (ACUTE RESPIRATORY DISTRESS)", 
                "description": "Profound, refractory hypoxemia secondary to massive intrapulmonary shunting and severely stiffened lungs. Indicates diffuse alveolar damage.", 
                "solutions": ["Implement strict lung-protective ventilation (Tidal Volume 4-6 mL/kg).", "Optimize PEEP via ARDSNet high PEEP/FiO2 table.", "Initiate early prone positioning."]
            }
        elif compliance > 60 and resistance > 15:
            return {
                "condition": "END-STAGE COPD / EMPHYSEMA", 
                "description": "Abnormally high static lung compliance with elevated airway resistance. Indicates severe destruction of alveolar septa and loss of natural elastic recoil.", 
                "solutions": ["Accept permissive hypercapnia (Target pH > 7.20).", "Apply extrinsic PEEP to match approx 80% of intrinsic Auto-PEEP.", "Administer scheduled bronchodilators."]
            }
        elif compliance < 40 and shunt_pct > 15 and resistance < 15:
            return {
                "condition": "CARDIOGENIC PULMONARY EDEMA", 
                "description": "Reduced lung compliance and elevated shunt fraction indicative of hydrostatic fluid accumulation in the alveolar spaces secondary to acute left ventricular failure.", 
                "solutions": ["Administer IV loop diuretics (e.g., Furosemide).", "Administer vasodilators if blood pressure is adequate.", "Apply sufficient PEEP to mechanically clear alveoli."]
            }
        else:
            return {
                "condition": "STABLE PULMONARY HOMEOSTASIS", 
                "description": "Ventilatory mechanics, resistance, compliance, and gas exchange parameters are currently registering within normal, optimal clinical limits.", 
                "solutions": ["Maintain current ventilatory support and oxygenation settings.", "Monitor patient for readiness to wean."]
            }

    @staticmethod
    def _analyze_acid_base(ph, paco2):
        if ph < 7.35: return "Respiratory Acidosis" if paco2 > 45 else "Metabolic Acidosis"
        elif ph > 7.45: return "Respiratory Alkalosis" if paco2 < 35 else "Metabolic Alkalosis"
        return "Normal Acid-Base Equilibrium"

    @staticmethod
    def _generate_waveforms(t_cycle, ie, pip, peep, vt, tau):
        t_i = t_cycle * (1 / (1 + ie))
        t_pts, p_pts, v_pts, f_pts = [], [], [], []
        res = 40
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
# 3. INTERACTIVE UI RENDERING CODE ENGINE
# ==========================================

GLOBAL_CSS_SCRIPTS = """
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Outfit', sans-serif; background-color: #030712; color: #f3f4f6; min-height: 100vh; overflow-x: hidden; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    .glass-panel { background: rgba(17, 24, 39, 0.6); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.06); }
    .glass-input { background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); color: #fff; }
    .glass-input:focus { border-color: #06b6d4; box-shadow: 0 0 12px rgba(6, 182, 212, 0.3); }
</style>
<script>
    function runLiveClock() {
        const d = new Date();
        const dayStr = d.toLocaleDateString(undefined, { weekday: 'long' });
        const dateStr = d.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
        const timeStr = d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        
        const target = document.getElementById('sidebar-clock-container');
        if (target) {
            target.innerHTML = `
                <div class="text-cyan-400 font-mono font-bold text-lg tracking-wider">${timeStr}</div>
                <div class="text-[11px] text-slate-300 font-bold uppercase tracking-widest mt-1">${dayStr}</div>
                <div class="text-[10px] text-slate-500 font-mono mt-0.5">${dateStr}</div>
            `;
        }
    }
    setInterval(runLiveClock, 1000);

    // SPEECH SYNTHESIS ENGINE
    function lyraSpeakNative(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            const selectedLang = localStorage.getItem('selectedLang') || 'en';
            if(selectedLang === 'es') u.lang = 'es-ES';
            else if(selectedLang === 'fr') u.lang = 'fr-FR';
            else u.lang = 'en-US';
            u.rate = 1.0;
            u.pitch = 1.1;
            window.speechSynthesis.speak(u);
        }
    }

    // HANDS-FREE AUTOMATED SPEECH RECOGNITION (LYRA VOICE RECEPTION)
    let recognition;
    function initHandsFreeLyra() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRec();
            recognition.continuous = true;
            recognition.interimResults = false;
            
            const selectedLang = localStorage.getItem('selectedLang') || 'en';
            if(selectedLang === 'es') recognition.lang = 'es-ES';
            else if(selectedLang === 'fr') recognition.lang = 'fr-FR';
            else recognition.lang = 'en-US';

            recognition.onresult = function(event) {
                const currentResultIndex = event.resultIndex;
                const transcript = event.results[currentResultIndex][0].transcript.toLowerCase().trim();
                console.log("Lyra Heard: " + transcript);
                
                let matched = null;
                if (transcript.includes('healthy') || transcript.includes('saludable') || transcript.includes('sain')) matched = 'healthy';
                else if (transcript.includes('ards') || transcript.includes('sdra')) matched = 'ards';
                else if (transcript.includes('copd') || transcript.includes('epoc') || transcript.includes('bpco')) matched = 'copd';
                else if (transcript.includes('asthma') || transcript.includes('asma') || transcript.includes('asthme')) matched = 'asthma';
                else if (transcript.includes('pneumothorax') || transcript.includes('neumotorax')) matched = 'pneumothorax';
                else if (transcript.includes('embolia') || transcript.includes('embolism') || transcript.includes('pe')) matched = 'pe';
                else if (transcript.includes('edema') || transcript.includes('oedeme')) matched = 'edema';

                if (matched) {
                    lyraSpeakNative("Loading pathology matrix parameters for " + matched.toUpperCase());
                    setTimeout(() => { triggerPresetSubmit(matched); }, 1200);
                }
            };

            recognition.onerror = function() { console.log("Recognition gap encountered... auto-resetting pipeline."); };
            recognition.onend = function() { recognition.start(); }; // Keep listening actively
            recognition.start();
        }
    }

    function triggerPresetSubmit(type) {
        const PRESETS = {
            healthy:      {vt: 500, rr: 14, pip: 20, pplat: 14, peep: 5,  fio2: 30},
            ards:         {vt: 350, rr: 28, pip: 38, pplat: 32, peep: 14, fio2: 80},
            copd:         {vt: 520, rr: 10, pip: 32, pplat: 16, peep: 5,  fio2: 35},
            asthma:       {vt: 450, rr: 12, pip: 45, pplat: 17, peep: 5,  fio2: 40},
            pneumothorax: {vt: 300, rr: 30, pip: 45, pplat: 40, peep: 5,  fio2: 90},
            pe:           {vt: 500, rr: 28, pip: 22, pplat: 15, peep: 5,  fio2: 50},
            edema:        {vt: 400, rr: 24, pip: 30, pplat: 25, peep: 12, fio2: 50}
        };
        const data = PRESETS[type];
        if(!data) return;
        document.getElementById('vt_input').value = data.vt;
        document.getElementById('rr').value = data.rr;
        document.getElementById('pip').value = data.pip;
        document.getElementById('pplat').value = data.pplat;
        document.getElementById('peep').value = data.peep;
        document.getElementById('fio2').value = data.fio2;
        document.getElementById('calc-form').submit();
    }

    window.addEventListener('DOMContentLoaded', () => {
        runLiveClock();
        initHandsFreeLyra();
    });
</script>
"""

LOGIN_HTML = GLOBAL_CSS_SCRIPTS + """
<body class="flex items-center justify-center min-h-screen bg-slate-950">
    <div class="glass-panel p-10 rounded-3xl w-full max-w-md border border-cyan-500/20 shadow-2xl text-center">
        <h1 class="text-4xl font-extrabold tracking-tighter text-white mb-2">AERO<span class="text-cyan-400">LUNG</span></h1>
        <p class="text-[10px] font-mono tracking-widest text-slate-400 uppercase mb-8">Architect Telemetry Entry</p>
        <form action="/login" method="POST" class="space-y-4 text-left">
            <div><label class="block text-[9px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-1">Architect Username</label><input type="text" name="username" class="w-full glass-input px-4 py-3 rounded-xl font-mono text-xs" required></div>
            <div><label class="block text-[9px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-1">Secure Passkey</label><input type="password" name="password" class="w-full glass-input px-4 py-3 rounded-xl font-mono text-xs" required></div>
            <button type="submit" class="w-full py-3 bg-cyan-600 rounded-xl font-bold uppercase text-xs text-white tracking-widest mt-2">Initialize Secure Link</button>
        </form>
    </div>
</body>
"""

DASHBOARD_HTML = GLOBAL_CSS_SCRIPTS + """
<body class="min-h-screen flex bg-[#030712] text-slate-100">

    <!-- LATERAL HUD SIDEBAR MATRIX -->
    <aside class="w-[320px] shrink-0 border-r border-slate-800/80 bg-slate-950/70 p-6 flex flex-col justify-between sticky top-0 h-screen z-40">
        <div class="space-y-6">
            <div>
                <h1 class="text-2xl font-black text-white tracking-tighter">AERO<span class="text-cyan-400">LUNG</span></h1>
                <p class="text-[9px] font-mono text-slate-500 uppercase tracking-widest">Omni Premium Clinical Lab</p>
            </div>
            
            <!-- SIDEBAR LIVE CLOCK AND DAY PANEL -->
            <div id="sidebar-clock-container" class="bg-black/40 border border-slate-800 p-4 rounded-xl"></div>

            <!-- GLOBAL DATABASE DROP-DOWN SELECTOR -->
            <div class="space-y-2">
                <label class="text-[10px] font-bold uppercase tracking-wider text-cyan-400 block">Pathology Matrix Select</label>
                <select id="preset-select-element" onchange="if(this.value) triggerPresetSubmit(this.value);" class="w-full glass-input px-3 py-2.5 rounded-lg text-xs font-mono">
                    <option value="" disabled selected>-- Select Pathology --</option>
                    <option value="healthy">Healthy Baseline</option>
                    <option value="ards">Severe ARDS</option>
                    <option value="copd">End-Stage COPD</option>
                    <option value="asthma">Status Asthmaticus</option>
                    <option value="pneumothorax">Tension Pneumothorax</option>
                    <option value="pe">Massive Pulm Embolism</option>
                    <option value="edema">Cardiogenic Edema</option>
                </select>
            </div>

            <!-- MANUAL TELEMETRY SUBMISSION MATRIX -->
            <div class="pt-4 border-t border-slate-800">
                <form id="calc-form" method="POST" action="/dashboard" class="space-y-3">
                    <label class="text-[10px] font-bold uppercase tracking-wider text-cyan-400 block">Manual Configuration Override</label>
                    <div class="grid grid-cols-2 gap-2">
                        <div><label class="text-[8px] font-mono block text-slate-400">Vt (mL)</label><input type="number" name="vt_input" id="vt_input" value="{{ inputs.vt_input|default(500) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                        <div><label class="text-[8px] font-mono block text-slate-400">RR (min)</label><input type="number" name="rr" id="rr" value="{{ inputs.rr|default(14) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                        <div><label class="text-[8px] font-mono block text-slate-400">PIP</label><input type="number" name="pip" id="pip" value="{{ inputs.pip|default(20) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                        <div><label class="text-[8px] font-mono block text-slate-400">Pplat</label><input type="number" name="pplat" id="pplat" value="{{ inputs.pplat|default(14) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                        <div><label class="text-[8px] font-mono block text-slate-400">PEEP</label><input type="number" name="peep" id="peep" value="{{ inputs.peep|default(5) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                        <div><label class="text-[8px] font-mono block text-slate-400">FiO2 %</label><input type="number" name="fio2" id="fio2" value="{{ inputs.fio2|default(30) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                    </div>
                    <input type="hidden" name="peak_flow" id="peak_flow" value="{{ inputs.peak_flow|default(60) }}">
                    <input type="hidden" name="ie_ratio" id="ie_ratio" value="{{ inputs.ie_ratio|default(2.0) }}">
                    <input type="hidden" name="cao2" id="cao2" value="{{ inputs.cao2|default(19.8) }}">
                    <input type="hidden" name="cvo2" id="cvo2" value="{{ inputs.cvo2|default(14.8) }}">
                    <input type="hidden" name="cco2" id="cco2" value="{{ inputs.cco2|default(20.4) }}">
                    <input type="hidden" name="peco2" id="peco2" value="{{ inputs.peco2|default(28) }}">
                    <input type="hidden" name="vco2" id="vco2" value="{{ inputs.vco2|default(200) }}">
                    <input type="hidden" name="hco3_input" id="hco3_input" value="{{ inputs.hco3_input|default(24) }}">
                    <button type="submit" class="w-full py-2 bg-cyan-600 rounded text-xs font-bold uppercase tracking-wider text-white">Execute Sync</button>
                </form>
            </div>
            
            <!-- LIVE HANDS-FREE LYRA STATUS DISPLAY -->
            <div class="p-3 bg-amber-950/20 border border-amber-500/20 rounded-xl text-center">
                <div class="text-[9px] font-black text-amber-400 uppercase tracking-widest">🎙️ Lyra Voice Sync Active</div>
                <div class="text-[10px] text-slate-400 mt-1">Speak natively: <span class="text-white font-bold">"Hey Lyra load COPD"</span> to control hands-free!</div>
            </div>
        </div>

        <!-- REPOSITIONED COPYRIGHT MATRIX LINK -->
        <div class="border-t border-slate-800/80 pt-4 text-center">
            <a href="/logout" class="block w-full py-2 bg-rose-950/30 text-rose-400 border border-rose-900/40 text-[10px] uppercase font-bold tracking-wider rounded-lg mb-3">Terminate Session</a>
            <p class="text-[10px] text-slate-500 font-medium tracking-wide">&copy; 2026 Shreesh Santoshkumar Rolli<br>AeroLung Medical System</p>
        </div>
    </aside>

    <!-- CORE ANALYTICS MONITOR MATRIX -->
    <main class="flex-1 p-8 overflow-y-auto space-y-6 max-w-[1500px] mx-auto w-full">
        
        {% if not sim_data %}
        <div class="glass-panel rounded-3xl h-[600px] flex flex-col items-center justify-center text-center p-8 border border-white/5 shadow-2xl">
            <h2 class="text-3xl font-black text-white uppercase tracking-tight mb-2">System Live Status Standby</h2>
            <p class="text-xs text-slate-400 font-mono">Use the sidebar parameters matrix, select a drop-down option, or speak out loud directly to Lyra.</p>
        </div>
        {% else %}
        
        <!-- ROW 1: AI DIAGNOSIS AND BLOOD LAB TESTS -->
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div class="glass-panel p-6 rounded-2xl border-l-4 border-l-cyan-400 xl:col-span-2 space-y-4">
                <div>
                    <h3 class="text-[10px] font-mono tracking-widest uppercase text-cyan-400">Primary AI Analytical Diagnostics</h3>
                    <div class="text-3xl font-black text-white mt-1 uppercase">{{ sim_data.ai_condition }}</div>
                </div>
                <div class="text-xs text-slate-300 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                    {{ sim_data.ai_description }}
                </div>
                <div class="space-y-1.5">
                    <h4 class="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Required Care Strategy</h4>
                    {% for sol in sim_data.ai_solutions %}
                    <div class="flex items-center gap-2 bg-emerald-950/20 border border-emerald-900/30 text-xs px-3 py-2 rounded-lg text-slate-200">
                        <span class="text-emerald-500 font-bold">⯈</span> <span>{{ sol }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- ARTERIAL GAS ANALYSIS METRICS -->
            <div class="glass-panel p-6 rounded-2xl flex flex-col justify-between">
                <div class="text-center">
                    <h3 class="text-[10px] font-mono tracking-widest uppercase text-purple-400 mb-4">Arterial Blood Gas Analysis</h3>
                    <div class="grid grid-cols-3 gap-1.5 bg-black/30 p-4 rounded-xl border border-slate-800 font-mono text-center mb-4">
                        <div><div class="text-[9px] text-slate-500 font-bold uppercase">pH</div><div class="text-xl font-bold text-emerald-400">{{ sim_data.ph }}</div></div>
                        <div><div class="text-[9px] text-slate-500 font-bold uppercase">PaCO2</div><div class="text-xl font-bold text-amber-400">{{ sim_data.paco2 }}</div></div>
                        <div><div class="text-[9px] text-slate-500 font-bold uppercase">HCO3</div><div class="text-xl font-bold text-purple-400">{{ sim_data.hco3 }}</div></div>
                    </div>
                </div>
                <div class="text-center py-3 bg-purple-950/20 border border-purple-900/40 rounded-xl text-xs font-mono uppercase font-bold text-purple-200">
                    {{ sim_data.acid_base_status }}
                </div>
            </div>
        </div>

        <!-- ROW 2: PULMONARY PHYSIOLOGICAL COMPLIANCE PARAMETERS -->
        <div class="glass-panel p-5 rounded-2xl">
            <h3 class="text-[10px] font-mono tracking-widest uppercase text-slate-400 mb-3 border-b border-slate-800 pb-2">Calculated Pulmonary Mechanics Matrix</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-black/30 p-4 rounded-xl text-center border border-slate-800/60"><span class="text-[9px] text-cyan-400 font-bold block mb-1">Lung Compliance</span><div class="text-2xl font-black font-mono text-white">{{ sim_data.compliance }}</div></div>
                <div class="bg-black/30 p-4 rounded-xl text-center border border-slate-800/60"><span class="text-[9px] text-rose-400 font-bold block mb-1">Airway Resistance</span><div class="text-2xl font-black font-mono text-white">{{ sim_data.resistance }}</div></div>
                <div class="bg-black/30 p-4 rounded-xl text-center border border-slate-800/60"><span class="text-[9px] text-amber-400 font-bold block mb-1">Vd/Vt Dead Space</span><div class="text-2xl font-black font-mono text-white">{{ sim_data.dead_space }}%</div></div>
                <div class="bg-black/30 p-4 rounded-xl text-center border border-slate-800/60"><span class="text-[9px] text-emerald-400 font-bold block mb-1">Shunt Fraction</span><div class="text-2xl font-black font-mono text-white">{{ sim_data.shunt }}%</div></div>
            </div>
        </div>

        <!-- ROW 3: RE-IMPLEMENTED HIGH-PRECISION VENTILATOR GRAPH CYCLES -->
        <div class="glass-panel p-6 rounded-2xl">
            <h3 class="text-[10px] font-mono tracking-widest uppercase text-cyan-400 mb-4 border-b border-slate-800 pb-2">Ventilator Waveform Analytics Charting</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 h-64">
                <div class="bg-black/20 p-2 rounded-xl border border-slate-800"><canvas id="pressChart"></canvas></div>
                <div class="bg-black/20 p-2 rounded-xl border border-slate-800"><canvas id="volChart"></canvas></div>
                <div class="bg-black/20 p-2 rounded-xl border border-slate-800"><canvas id="flowChart"></canvas></div>
            </div>
        </div>

        <script>
            // Real-Time Waveform Parsing Matrix Sync Engine
            const rawWf = {{ sim_data.waveform_data | safe }};
            const ctxOptions = (title, color) => ({
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, title: { display: true, text: title, color: '#94a3b8', font: { size: 10, family: 'JetBrains Mono' } } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#64748b', font: { size: 8 } } },
                    y: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#64748b', font: { size: 8 } } }
                }
            });

            new Chart(document.getElementById('pressChart').getContext('2d'), {
                type: 'line',
                data: { labels: rawWf.t, datasets: [{ data: rawWf.p, borderColor: '#f59e0b', borderWidth: 2, pointRadius: 0, fill: false }] },
                options: ctxOptions('Pressure Cycle (cmH2O)', '#f59e0b')
            });
            new Chart(document.getElementById('volChart').getContext('2d'), {
                type: 'line',
                data: { labels: rawWf.t, datasets: [{ data: rawWf.v, borderColor: '#06b6d4', borderWidth: 2, pointRadius: 0, fill: false }] },
                options: ctxOptions('Volume Output Loop (mL)', '#06b6d4')
            });
            new Chart(document.getElementById('flowChart').getContext('2d'), {
                type: 'line',
                data: { labels: rawWf.t, datasets: [{ data: rawWf.f, borderColor: '#10b981', borderWidth: 2, pointRadius: 0, fill: false }] },
                options: ctxOptions('Expiratory Flow Metrics (L/s)', '#10b981')
            });

            // Dictate Lyra Vocal Responses Instantly
            window.addEventListener('DOMContentLoaded', () => {
                setTimeout(() => {
                    lyraSpeakNative("Simulation verified. Diagnostics indicating {{ sim_data.ai_condition }}. Balance reports {{ sim_data.acid_base_status }}.");
                }, 800);
            });
        </script>
        {% endif %}
    </main>
</body>
"""

# ==========================================
# 4. FLASK ROUTING GATEWAYS
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
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

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
    return render_template_string(DASHBOARD_HTML, sim_data=sim_data, inputs=inputs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
