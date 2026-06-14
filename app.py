import os
import math
import json
import sqlite3
import traceback
from flask import Flask, request, redirect, url_for, session, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_ultimate_sync_2026")
DB_NAME = "aerolung_database.db"

# ==========================================
# 1. DATABASE INITIALIZATION
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
    
    # Create default admin if no users exist
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed_pw = generate_password_hash('admin2026')
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  ('admin', hashed_pw, 'System Architect'))
    
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. 20 PATHOLOGIES & MATH ENGINE
# ==========================================

DISEASE_PROFILES = {
    "healthy": {"condition": "Stable Pulmonary Homeostasis", "description": "Ventilatory mechanics, airway resistance, and gas exchange are within normal limits.", "solutions": ["Maintain current support.", "Monitor readiness to wean."]},
    "ards": {"condition": "Severe Acute Respiratory Distress Syndrome", "description": "Profound hypoxemia secondary to intrapulmonary shunting and stiff non-compliant lungs.", "solutions": ["Implement lung-protective ventilation (Vt 4-6 mL/kg).", "Optimize PEEP via ARDSNet.", "Prone positioning."]},
    "copd": {"condition": "End-Stage COPD / Emphysema", "description": "High static compliance with elevated airway resistance and loss of elastic recoil.", "solutions": ["Accept permissive hypercapnia (pH > 7.20).", "Apply extrinsic PEEP to match Auto-PEEP.", "Administer bronchodilators."]},
    "asthma": {"condition": "Status Asthmaticus", "description": "Critically elevated airway resistance indicating severe bronchospasm and mucus plugging.", "solutions": ["Administer continuous nebulized Albuterol.", "Decrease respiratory rate to allow exhalation.", "IV corticosteroids."]},
    "fibrosis": {"condition": "Advanced Pulmonary Fibrosis", "description": "Restricted lung volumes due to dense parenchymal scarring. Compliance is critically low.", "solutions": ["Utilize ultra-low tidal volume ventilation.", "Titrate PEEP cautiously.", "Evaluate for acute exacerbation."]},
    "pe": {"condition": "Massive Pulmonary Embolism", "description": "Severe dead-space (Vd/Vt) anomaly. Alveoli are ventilated, but blood flow is obstructed.", "solutions": ["Initiate systemic anticoagulation.", "Consider thrombolytics if unstable.", "Vasopressor support for RV failure."]},
    "pneumonia": {"condition": "Severe Lobar Pneumonia", "description": "Localized alveolar filling causing significant right-to-left intrapulmonary shunting.", "solutions": ["Administer broad-spectrum IV antibiotics.", "Position patient 'good lung down'.", "Moderate PEEP."]},
    "neuro": {"condition": "Neuromuscular Pump Failure", "description": "Lung mechanics are normal, but minute ventilation is grossly inadequate leading to hypercapnia.", "solutions": ["Provide full mechanical ventilatory support.", "Assess for reversible neurologic causes.", "Aggressive pulmonary hygiene."]},
    "obesity": {"condition": "Obesity Hypoventilation Syndrome", "description": "Decreased compliance due to adiposity on the chest wall, leading to CO2 retention.", "solutions": ["Utilize higher PEEP to overcome chest wall weight.", "Position in reverse Trendelenburg.", "Target Ideal Body Weight for Vt."]},
    "pneumothorax": {"condition": "Tension Pneumothorax", "description": "Catastrophic loss of compliance combined with acute hypercapnia and mediastinal shift.", "solutions": ["IMMEDIATE needle thoracostomy.", "Prepare for chest tube insertion.", "Disconnect from positive pressure briefly if unstable."]},
    "edema": {"condition": "Cardiogenic Pulmonary Edema", "description": "Reduced compliance and elevated shunt indicative of fluid transudation from LV failure.", "solutions": ["Administer IV loop diuretics.", "Administer vasodilators to reduce preload.", "Apply sufficient PEEP to displace fluid."]},
    "cf": {"condition": "Cystic Fibrosis Exacerbation", "description": "Mixed obstructive/shunting defect. Purulent secretions causing high resistance.", "solutions": ["Aggressive inhaled mucolytics.", "Chest physiotherapy.", "Targeted IV antibiotics."]},
    "kypho": {"condition": "Severe Kyphoscoliosis Decompensation", "description": "Structural chest wall deformity restricting lung expansion, leading to hypercapnia.", "solutions": ["Utilize NiPPV/BiPAP.", "Apply high PEEP to overcome resistance.", "Treat infectious triggers."]},
    "bronch": {"condition": "Acute Bronchiectasis Exacerbation", "description": "Chronically dilated, scarred airways filled with sputum causing massive resistance.", "solutions": ["Aggressive pulmonary toilet.", "Targeted IV antibiotics.", "Low respiratory rates to prevent Auto-PEEP."]},
    "mild_ards": {"condition": "Early / Mild ARDS", "description": "Decreasing compliance and tachypnea causing respiratory alkalosis early in disease process.", "solutions": ["Monitor strictly for progression.", "Apply moderate PEEP (8-10 cmH2O).", "Restrict IV fluids."]},
    "atelectasis": {"condition": "Major Lobar Atelectasis", "description": "Acute loss of lung volume due to collapsed lobe, resulting in decreased compliance.", "solutions": ["Therapeutic bronchoscopy.", "Aggressive chest physiotherapy.", "Alveolar recruitment maneuvers."]},
    "flail": {"condition": "Flail Chest / Blunt Thoracic Trauma", "description": "Paradoxical chest wall movement due to rib fractures, leading to impaired compliance.", "solutions": ["Positive pressure ventilation ('pneumatic splinting').", "Aggressive pain control.", "Consult thoracic surgery."]},
    "p_htn": {"condition": "Pulmonary Hypertension / Cor Pulmonale", "description": "Right-sided heart failure causing poor perfusion. High dead space and stiff vasculature.", "solutions": ["Inhaled pulmonary vasodilators.", "Avoid hypoxia and hypercapnia.", "Optimize RV preload."]},
    "co_poison": {"condition": "Carbon Monoxide Toxicity", "description": "Critical cellular hypoxia despite standard SpO2 indicating excellent oxygenation.", "solutions": ["Maintain 100% FiO2.", "Obtain ABG with CO-oximetry.", "Arrange hyperbaric oxygen transfer."]},
    "ards_mod": {"condition": "Moderate ARDS", "description": "Significant intrapulmonary shunting. PaO2/FiO2 ratio below 200.", "solutions": ["ARDSNet low tidal volume protocols.", "Maintain plateau pressures below 30 cmH2O.", "Consider paralysis if dyssynchrony persists."]}
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

        # STRICT SYNCHRONIZATION LOCK
        if preset_id in DISEASE_PROFILES:
            ai_result = DISEASE_PROFILES[preset_id]
        else:
            ai_result = cls._fallback_ai_diagnostics(compliance, resistance, shunt_pct, vd_vt_ratio)
            
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
    def _fallback_ai_diagnostics(compliance, resistance, shunt_pct, vd_vt_ratio):
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
# 3. HTML, CSS & JAVASCRIPT
# ==========================================

BACKGROUND_SVG = """
<svg class="living-lung" viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="cyanGrad" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.6"/>
            <stop offset="50%" stop-color="#0891b2" stop-opacity="0.8"/>
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

GLOBAL_CSS_JS = """
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Outfit', sans-serif; background-color: #020617; color: #f8fafc; overflow-x: hidden; min-height: 100vh; display: flex; flex-direction: column; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    @keyframes holographicBreathe { 0% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.2; } 50% { transform: translate(-50%, -50%) scale(1.03); opacity: 0.6; } 100% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.2; } }
    .living-lung { position: fixed; top: 50%; left: 50%; width: 100vw; max-width: 900px; z-index: 0; pointer-events: none; animation: holographicBreathe 5s ease-in-out infinite; }
    .glass-panel { background: rgba(15, 23, 42, 0.55); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); position: relative; z-index: 10; box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
    .glass-input { background: rgba(0, 0, 0, 0.6); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; }
    .glass-input:focus { outline: none; border-color: #22d3ee; box-shadow: 0 0 10px rgba(34,211,238,0.3); }
    ::-webkit-scrollbar { width: 5px; } ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
</style>
<script>
    function updateClock() {
        const d = new Date();
        const lang = localStorage.getItem('selectedLang') || 'en-US';
        const timeStr = d.toLocaleTimeString(lang, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const dayStr = d.toLocaleDateString(lang, { weekday: 'long' });
        const dateStr = d.toLocaleDateString(lang, { year: 'numeric', month: 'long', day: 'numeric' });
        
        const clockTimeEl = document.getElementById('clock-time');
        if(clockTimeEl) {
            clockTimeEl.innerText = timeStr;
            document.getElementById('clock-day').innerText = dayStr;
            document.getElementById('clock-date').innerText = dateStr;
        }
        const graphTimeEl = document.getElementById('graph-timestamp');
        if(graphTimeEl) graphTimeEl.innerText = `${dayStr}, ${dateStr} - ${timeStr}`;
    }
    setInterval(updateClock, 1000);
    window.onload = updateClock;

    const TRANSLATIONS = {
        en: {
            brand: "AERO<span class='text-cyan-400'>LUNG</span>",
            settings: "Settings", logout: "Logout", db_title: "Pathology Matrix",
            select_preset: "-- Select Pathology --", override: "Manual Override",
            btn_scan: "Synchronize Data", standby_title: "System Standby", standby_desc: "Select pathology or activate Lyra.",
            primary_diag: "Primary Diagnosis", physio: "Physiology", action_plan: "Action Plan",
            abg: "Arterial Blood Gas", mech_exp: "Mechanics Explained",
            comp: "Compliance", res: "Resistance", dead: "Dead Space", shunt: "Shunt",
            graphs: "Waveform Analytics", lyra_btn: "Wake Lyra", lyra_status: "Lyra Sleeping", copy_btn: "Copy Config",
            update_title: "Update Credentials"
        },
        es: {
            brand: "AERO<span class='text-cyan-400'>LUNG</span>",
            settings: "Ajustes", logout: "Salir", db_title: "Matriz de Patología",
            select_preset: "-- Seleccionar Patología --", override: "Anulación Manual",
            btn_scan: "Sincronizar Datos", standby_title: "Sistema en Espera", standby_desc: "Seleccione patología o active Lyra.",
            primary_diag: "Diagnóstico Principal", physio: "Fisiología", action_plan: "Plan de Acción",
            abg: "Gases Arteriales", mech_exp: "Mecánica Explicada",
            comp: "Distensibilidad", res: "Resistencia", dead: "Espacio Muerto", shunt: "Cortocircuito",
            graphs: "Análisis de Ondas", lyra_btn: "Despertar Lyra", lyra_status: "Lyra Durmiendo", copy_btn: "Copiar Config",
            update_title: "Actualizar Credenciales"
        },
        fr: {
            brand: "AERO<span class='text-cyan-400'>LUNG</span>",
            settings: "Paramètres", logout: "Quitter", db_title: "Matrice Pathologique",
            select_preset: "-- Choisir Pathologie --", override: "Contrôle Manuel",
            btn_scan: "Synchroniser", standby_title: "En Veille", standby_desc: "Sélectionnez ou activez Lyra.",
            primary_diag: "Diagnostic Principal", physio: "Physiologie", action_plan: "Plan d'Action",
            abg: "Gaz du Sang", mech_exp: "Mécanique Expliquée",
            comp: "Compliance", res: "Résistance", dead: "Espace Mort", shunt: "Shunt",
            graphs: "Analyse des Ondes", lyra_btn: "Réveiller Lyra", lyra_status: "Lyra Dort", copy_btn: "Copier Config",
            update_title: "Mettre à jour"
        }
    };

    function changeLanguage(lang) {
        localStorage.setItem('selectedLang', lang);
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (TRANSLATIONS[lang][key]) el.innerHTML = TRANSLATIONS[lang][key];
        });
        const dd = document.getElementById('preset-dropdown');
        if(dd) dd.options[0].text = TRANSLATIONS[lang]['select_preset'];
    }

    function copyConfiguration() {
        const dd = document.getElementById('preset-dropdown');
        const pathName = dd.options[dd.selectedIndex].text;
        
        const configText = `
--- AEROLUNG SYNC EXPORT ---
Pathology: ${pathName}
Vt: ${document.getElementById('vt_input').value} mL
Rate: ${document.getElementById('rr').value} bpm
PIP: ${document.getElementById('pip').value} cmH2O
Pplat: ${document.getElementById('pplat').value} cmH2O
PEEP: ${document.getElementById('peep').value} cmH2O
FiO2: ${document.getElementById('fio2').value} %
-----------------------------
        `.trim();
        
        navigator.clipboard.writeText(configText).then(() => {
            const btn = document.getElementById('copy-btn');
            const originalText = btn.innerText;
            btn.innerText = "Copied!";
            btn.classList.add('bg-emerald-600');
            setTimeout(() => { 
                btn.innerText = originalText; 
                btn.classList.remove('bg-emerald-600');
            }, 2000);
        });
    }

    // INTERACTIVE LYRA VOICE ENGINE
    let recognition;
    let lyraActive = false;

    function toggleLyra() {
        if (!('webkitSpeechRecognition' in window)) {
            alert("Speech API not supported. Please use Chrome/Edge.");
            return;
        }
        
        const btn = document.getElementById('lyra-btn');
        const status = document.getElementById('lyra-status');
        const langCode = localStorage.getItem('selectedLang') || 'en';

        if (!lyraActive) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = false;
            
            if (langCode === 'es') recognition.lang = 'es-ES';
            else if (langCode === 'fr') recognition.lang = 'fr-FR';
            else recognition.lang = 'en-US';

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase();
                status.innerText = "Heard: " + transcript;
                if (transcript.includes("lyra") || transcript.includes("lira")) {
                    processLyraCommand(transcript, langCode);
                }
            };

            recognition.onend = function() { if (lyraActive) recognition.start(); };
            recognition.start();
            lyraActive = true;
            btn.innerText = "Stop Lyra";
            btn.className = "w-full py-2 rounded bg-rose-600 font-bold text-white text-xs uppercase tracking-wider shadow-[0_0_10px_rgba(225,29,72,0.6)]";
            status.innerText = "Listening... Say 'Hey Lyra load COPD'";
            lyraSpeak("Lyra activated. Ready for synchronization.", langCode);
        } else {
            lyraActive = false;
            recognition.stop();
            btn.innerText = TRANSLATIONS[langCode]['lyra_btn'];
            btn.className = "w-full py-2 rounded bg-purple-600 font-bold text-white text-xs uppercase tracking-wider";
            status.innerText = TRANSLATIONS[langCode]['lyra_status'];
        }
    }

    function processLyraCommand(text, lang) {
        let matched = null;
        if (text.includes('healthy') || text.includes('saludable') || text.includes('sain') || text.includes('normal')) matched = 'healthy';
        else if (text.includes('mild') && text.includes('ards')) matched = 'mild_ards';
        else if (text.includes('mod') && text.includes('ards')) matched = 'ards_mod';
        else if (text.includes('ards') || text.includes('sdra')) matched = 'ards';
        else if (text.includes('copd') || text.includes('cops') || text.includes('c.o.p.d') || text.includes('epoc') || text.includes('bpco')) matched = 'copd';
        else if (text.includes('asthma') || text.includes('asma') || text.includes('asthme')) matched = 'asthma';
        else if (text.includes('fibrosis') || text.includes('fibrose')) matched = 'fibrosis';
        else if (text.includes('embol') || text.includes('pe') || text.includes('p.e')) matched = 'pe';
        else if (text.includes('pneumonia') || text.includes('neumonia') || text.includes('pneumonie')) matched = 'pneumonia';
        else if (text.includes('neuro')) matched = 'neuro';
        else if (text.includes('obesity') || text.includes('obesidad') || text.includes('obesite')) matched = 'obesity';
        else if (text.includes('pneumothorax') || text.includes('neumotorax')) matched = 'pneumothorax';
        else if (text.includes('edema') || text.includes('oedeme')) matched = 'edema';
        else if (text.includes('cystic') || text.includes('quistica')) matched = 'cf';
        else if (text.includes('kypho') || text.includes('cifosis')) matched = 'kypho';
        else if (text.includes('bronch') || text.includes('bronquiectasias')) matched = 'bronch';
        else if (text.includes('atelectas')) matched = 'atelectasis';
        else if (text.includes('flail') || text.includes('trauma')) matched = 'flail';
        else if (text.includes('hypertension') || text.includes('hipertension')) matched = 'p_htn';
        else if (text.includes('carbon') || text.includes('monoxide') || text.includes('monoxido')) matched = 'co_poison';

        if (matched) {
            let msg = "Synchronizing matrix for " + matched;
            if (lang === 'es') msg = "Sincronizando matriz para " + matched;
            if (lang === 'fr') msg = "Synchronisation de la matrice pour " + matched;
            
            lyraSpeak(msg, lang);
            document.getElementById('lyra-status').innerText = msg;
            setTimeout(() => { loadPreset(matched); }, 2000);
        } else {
            let msg = "Pathology parameter not recognized. Please repeat.";
            if (lang === 'es') msg = "Parámetro no reconocido. Repita.";
            if (lang === 'fr') msg = "Paramètre non reconnu. Répétez.";
            lyraSpeak(msg, lang);
        }
    }

    function lyraSpeak(text, lang) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            if(lang === 'es') u.lang = 'es-ES';
            else if(lang === 'fr') u.lang = 'fr-FR';
            else u.lang = 'en-US';
            u.pitch = 1.1;
            window.speechSynthesis.speak(u);
        }
    }

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
</script>
"""

LOGIN_HTML = GLOBAL_CSS_JS + BACKGROUND_SVG + """
<body class="flex items-center justify-center min-h-screen">
    <div class="glass-panel p-10 rounded-3xl w-full max-w-md text-center shadow-2xl border-t border-cyan-500/30">
        <h1 class="text-5xl font-black text-white mb-2" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
        <form action="/login" method="POST" class="space-y-4 text-left mt-8">
            <div><label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Architect ID</label><input type="text" name="username" class="w-full glass-input px-4 py-3 rounded-lg text-sm" required></div>
            <div><label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Passkey</label><input type="password" name="password" class="w-full glass-input px-4 py-3 rounded-lg text-sm" required></div>
            <button type="submit" class="w-full mt-4 py-3 rounded-lg bg-cyan-600 font-bold text-white uppercase text-xs tracking-wider">Initialize</button>
        </form>
    </div>
</body>
"""

DASHBOARD_HTML = GLOBAL_CSS_JS + BACKGROUND_SVG + """
<body class="min-h-screen flex bg-slate-950/80">
    
    <!-- SIDEBAR: Clock, Lang, Sync Settings -->
    <aside class="w-[340px] shrink-0 glass-panel border-r border-white/5 flex flex-col justify-between sticky top-0 h-screen z-40 p-6">
        <div class="space-y-6 overflow-y-auto pr-2">
            <div>
                <h1 class="text-3xl font-black text-white tracking-tighter" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
                <div class="flex items-center justify-between mt-4">
                    <select id="lang-selector" onchange="changeLanguage(this.value)" class="bg-black/50 border border-slate-700 text-slate-300 text-[10px] font-bold uppercase rounded-lg px-2 py-1.5 cursor-pointer">
                        <option value="en">EN</option><option value="es">ES</option><option value="fr">FR</option>
                    </select>
                    <div class="flex gap-2">
                        <!-- SETTINGS AND LOGOUT BUTTONS -->
                        <button onclick="document.getElementById('settings-modal').classList.remove('hidden')" class="text-[9px] font-bold text-slate-300 uppercase border border-slate-700 bg-black/50 px-2 py-1.5 rounded transition hover:bg-slate-800" data-i18n="settings">Settings</button>
                        <a href="/logout" class="text-[9px] font-bold text-rose-400 uppercase border border-rose-900/50 bg-rose-950/30 px-2 py-1.5 rounded transition hover:bg-rose-900" data-i18n="logout">Logout</a>
                    </div>
                </div>
            </div>

            <!-- LIVE CLOCK -->
            <div class="bg-black/40 border border-white/5 p-4 rounded-xl text-center">
                <div id="clock-time" class="text-cyan-400 font-mono font-bold text-2xl"></div>
                <div id="clock-day" class="text-slate-300 text-xs font-bold uppercase tracking-widest mt-1"></div>
                <div id="clock-date" class="text-slate-500 text-[10px] font-mono mt-0.5"></div>
            </div>

            <!-- LYRA VOICE TOGGLE -->
            <div class="bg-purple-950/20 border border-purple-500/30 p-4 rounded-xl text-center shadow-[0_0_15px_rgba(147,51,234,0.1)]">
                <button id="lyra-btn" onclick="toggleLyra()" class="w-full py-2 rounded bg-purple-600 font-bold text-white text-xs uppercase tracking-wider transition-all" data-i18n="lyra_btn">Wake Lyra</button>
                <div id="lyra-status" class="text-[9px] text-purple-300 font-mono mt-2" data-i18n="lyra_status">Lyra Sleeping</div>
            </div>

            <!-- 20 PATHOLOGIES DROPDOWN -->
            <div>
                <label class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest block mb-2" data-i18n="db_title">Pathology Matrix</label>
                <select id="preset-dropdown" onchange="if(this.value) loadPreset(this.value);" class="w-full glass-input px-3 py-2 rounded-lg text-xs font-semibold">
                    <option value="" disabled {% if not current_preset %}selected{% endif %} data-i18n="select_preset">-- Select Pathology --</option>
                    <option value="healthy" {% if current_preset == 'healthy' %}selected{% endif %}>Healthy Baseline</option>
                    <option value="mild_ards" {% if current_preset == 'mild_ards' %}selected{% endif %}>Mild ARDS</option>
                    <option value="ards_mod" {% if current_preset == 'ards_mod' %}selected{% endif %}>Moderate ARDS</option>
                    <option value="ards" {% if current_preset == 'ards' %}selected{% endif %}>Severe ARDS</option>
                    <option value="copd" {% if current_preset == 'copd' %}selected{% endif %}>End-Stage COPD</option>
                    <option value="asthma" {% if current_preset == 'asthma' %}selected{% endif %}>Status Asthmaticus</option>
                    <option value="fibrosis" {% if current_preset == 'fibrosis' %}selected{% endif %}>Pulmonary Fibrosis</option>
                    <option value="pe" {% if current_preset == 'pe' %}selected{% endif %}>Massive Pulm Embolism</option>
                    <option value="pneumonia" {% if current_preset == 'pneumonia' %}selected{% endif %}>Severe Pneumonia</option>
                    <option value="neuro" {% if current_preset == 'neuro' %}selected{% endif %}>Neuromuscular Failure</option>
                    <option value="obesity" {% if current_preset == 'obesity' %}selected{% endif %}>Obesity Hypoventilation</option>
                    <option value="pneumothorax" {% if current_preset == 'pneumothorax' %}selected{% endif %}>Tension Pneumothorax</option>
                    <option value="edema" {% if current_preset == 'edema' %}selected{% endif %}>Cardiogenic Edema</option>
                    <option value="cf" {% if current_preset == 'cf' %}selected{% endif %}>Cystic Fibrosis</option>
                    <option value="kypho" {% if current_preset == 'kypho' %}selected{% endif %}>Kyphoscoliosis</option>
                    <option value="bronch" {% if current_preset == 'bronch' %}selected{% endif %}>Bronchiectasis</option>
                    <option value="atelectasis" {% if current_preset == 'atelectasis' %}selected{% endif %}>Lobar Atelectasis</option>
                    <option value="flail" {% if current_preset == 'flail' %}selected{% endif %}>Flail Chest Trauma</option>
                    <option value="p_htn" {% if current_preset == 'p_htn' %}selected{% endif %}>Pulmonary HTN</option>
                    <option value="co_poison" {% if current_preset == 'co_poison' %}selected{% endif %}>Carbon Monoxide Poisoning</option>
                    <option value="custom" {% if current_preset == 'custom' %}selected{% endif %} hidden>Custom Override</option>
                </select>
            </div>

            <!-- MANUAL INPUTS & COPY BTN -->
            <form id="calc-form" method="POST" action="/dashboard" class="border-t border-white/10 pt-4">
                <input type="hidden" name="preset_id" id="preset_id" value="{{ current_preset }}">
                <div class="flex justify-between items-center mb-2">
                    <label class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest block" data-i18n="override">Manual Override</label>
                    <button type="button" id="copy-btn" onclick="copyConfiguration()" class="bg-slate-800 text-cyan-300 text-[8px] uppercase font-bold px-2 py-1 rounded transition-colors" data-i18n="copy_btn">Copy Config</button>
                </div>
                <div class="grid grid-cols-2 gap-2 mb-4">
                    <div><label class="text-[8px] text-slate-400 uppercase font-bold">Vt</label><input type="number" name="vt_input" id="vt_input" value="{{ inputs.vt_input|default(500) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono" oninput="document.getElementById('preset-dropdown').value='custom'; document.getElementById('preset_id').value='custom';"></div>
                    <div><label class="text-[8px] text-slate-400 uppercase font-bold">Rate</label><input type="number" name="rr" id="rr" value="{{ inputs.rr|default(14) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                    <div><label class="text-[8px] text-slate-400 uppercase font-bold">PIP</label><input type="number" name="pip" id="pip" value="{{ inputs.pip|default(20) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                    <div><label class="text-[8px] text-slate-400 uppercase font-bold">Pplat</label><input type="number" name="pplat" id="pplat" value="{{ inputs.pplat|default(14) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                    <div><label class="text-[8px] text-slate-400 uppercase font-bold">PEEP</label><input type="number" name="peep" id="peep" value="{{ inputs.peep|default(5) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                    <div><label class="text-[8px] text-slate-400 uppercase font-bold">FiO2</label><input type="number" name="fio2" id="fio2" value="{{ inputs.fio2|default(30) }}" class="w-full glass-input px-2 py-1 rounded text-xs font-mono"></div>
                    <input type="hidden" name="peak_flow" id="peak_flow" value="{{ inputs.peak_flow|default(60) }}">
                    <input type="hidden" name="ie_ratio" id="ie_ratio" value="{{ inputs.ie_ratio|default(2.0) }}">
                    <input type="hidden" name="cao2" id="cao2" value="{{ inputs.cao2|default(19.8) }}">
                    <input type="hidden" name="cvo2" id="cvo2" value="{{ inputs.cvo2|default(14.8) }}">
                    <input type="hidden" name="cco2" id="cco2" value="{{ inputs.cco2|default(20.4) }}">
                    <input type="hidden" name="peco2" id="peco2" value="{{ inputs.peco2|default(28) }}">
                    <input type="hidden" name="vco2" id="vco2" value="{{ inputs.vco2|default(200) }}">
                    <input type="hidden" name="hco3_input" id="hco3_input" value="{{ inputs.hco3_input|default(24) }}">
                </div>
                <button type="submit" class="w-full py-2 rounded bg-cyan-600 text-white font-bold text-xs uppercase" data-i18n="btn_scan">Synchronize Data</button>
            </form>
        </div>

        <div class="border-t border-slate-800/80 pt-4 text-center mt-4">
            <p class="text-[10px] text-slate-500 font-mono tracking-wide">&copy; 2026 Shreesh Santoshkumar Rolli</p>
        </div>
    </aside>

    <!-- MAIN DASHBOARD -->
    <main class="flex-1 p-8 overflow-y-auto w-full relative z-10">
        {% if not sim_data %}
        <div class="glass-panel rounded-3xl h-[600px] flex flex-col items-center justify-center text-center p-8 border-dashed border-white/10 shadow-2xl">
            <h2 class="text-3xl font-black text-white uppercase tracking-tight mb-2" data-i18n="standby_title">System Standby</h2>
            <p class="text-sm text-slate-400 font-mono" data-i18n="standby_desc">Select a pathology profile or activate Lyra.</p>
        </div>
        {% else %}
        
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
            <div class="glass-panel p-8 rounded-2xl border-l-4 border-l-cyan-400 bg-gradient-to-br from-slate-900/90 to-black">
                <h3 class="text-[10px] font-bold uppercase tracking-widest text-cyan-400 mb-1" data-i18n="primary_diag">Primary Diagnosis</h3>
                <div class="text-3xl font-black text-white uppercase mb-4">{{ sim_data.ai_condition }}</div>
                
                <h4 class="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1" data-i18n="physio">Physiology</h4>
                <p class="text-sm text-slate-300 bg-black/40 p-4 rounded-lg border border-white/5 mb-4">{{ sim_data.ai_description }}</p>
                
                <h4 class="text-[9px] font-bold text-emerald-500 uppercase tracking-widest mb-1" data-i18n="action_plan">Action Plan</h4>
                <ul class="space-y-2">
                    {% for sol in sim_data.ai_solutions %}
                    <li class="flex items-start gap-2 bg-emerald-950/20 p-2.5 rounded-lg border border-emerald-900/30 text-xs text-slate-200">
                        <span class="text-emerald-500 font-bold mt-0.5">⯈</span> <span>{{ sol }}</span>
                    </li>
                    {% endfor %}
                </ul>
            </div>

            <div class="glass-panel p-8 rounded-2xl border-t-4 border-t-purple-500 flex flex-col justify-center">
                <h3 class="text-[10px] font-bold uppercase tracking-widest text-purple-400 mb-6 text-center" data-i18n="abg">Arterial Blood Gas</h3>
                <div class="grid grid-cols-3 gap-2 bg-black/40 p-6 rounded-2xl border border-white/5 text-center mb-6">
                    <div><div class="text-[10px] text-slate-500 font-bold uppercase mb-2">pH</div><div class="text-3xl font-black font-mono text-emerald-400">{{ sim_data.ph }}</div></div>
                    <div class="border-l border-white/10"><div class="text-[10px] text-slate-500 font-bold uppercase mb-2">PaCO2</div><div class="text-3xl font-black font-mono text-amber-400">{{ sim_data.paco2 }}</div></div>
                    <div class="border-l border-white/10"><div class="text-[10px] text-slate-500 font-bold uppercase mb-2">HCO3</div><div class="text-3xl font-black font-mono text-purple-400">{{ sim_data.hco3 }}</div></div>
                </div>
                <div class="text-sm font-bold text-white uppercase tracking-wider bg-purple-950/50 block text-center py-3 rounded-lg border border-purple-800">{{ sim_data.acid_base_status }}</div>
            </div>
        </div>

        <div class="glass-panel p-6 rounded-2xl mb-6">
            <h3 class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-4 border-b border-white/10 pb-2" data-i18n="mech_exp">Mechanics Explained</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5"><span class="text-[10px] text-cyan-400 font-bold uppercase block mb-2" data-i18n="comp">Compliance</span><div class="text-3xl font-black text-white font-mono">{{ sim_data.compliance }}</div></div>
                <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5"><span class="text-[10px] text-rose-400 font-bold uppercase block mb-2" data-i18n="res">Resistance</span><div class="text-3xl font-black text-white font-mono">{{ sim_data.resistance }}</div></div>
                <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5"><span class="text-[10px] text-amber-400 font-bold uppercase block mb-2" data-i18n="dead">Dead Space</span><div class="text-3xl font-black text-white font-mono">{{ sim_data.vd_vt }}%</div></div>
                <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5"><span class="text-[10px] text-emerald-400 font-bold uppercase block mb-2" data-i18n="shunt">Shunt</span><div class="text-3xl font-black text-white font-mono">{{ sim_data.shunt }}%</div></div>
            </div>
        </div>

        <!-- LIVE GRAPHS WITH TIMESTAMP -->
        <div class="glass-panel p-6 rounded-2xl h-[400px] flex flex-col relative">
            <div id="graph-timestamp" class="absolute top-6 right-6 text-xs text-cyan-400/80 font-mono tracking-wider z-20"></div>
            <div class="flex justify-between items-center mb-4 border-b border-white/10 pb-2">
                <h3 class="text-[10px] font-bold uppercase tracking-widest text-slate-400" data-i18n="graphs">Waveform Analytics</h3>
                <div class="text-[10px] text-slate-300 flex gap-4 font-mono bg-black/50 px-3 py-1.5 rounded-lg border border-white/5 mr-40">
                    <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded bg-[#22d3ee]"></span><span class="font-bold">Paw</span></div>
                    <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded bg-[#10b981]"></span><span class="font-bold">Vol</span></div>
                    <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded bg-[#f43f5e]"></span><span class="font-bold">Flow</span></div>
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
                        { label: 'Pressure (cmH2O)', data: waveData.p, borderColor: '#22d3ee', borderWidth: 2, pointRadius: 0, fill: false },
                        { label: 'Volume (mL)', data: waveData.v, borderColor: '#10b981', borderWidth: 2, pointRadius: 0, fill: false },
                        { label: 'Flow (L/m)', data: waveData.f, borderColor: '#f43f5e', borderWidth: 2, pointRadius: 0, fill: false }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { 
                        x: { grid: { color: 'rgba(255,255,255,0.05)' } }, 
                        y: { grid: { color: 'rgba(255,255,255,0.05)' } } 
                    }
                }
            });
        </script>
        {% endif %}
    </main>

    <!-- UPDATE CREDENTIALS MODAL -->
    <div id="settings-modal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div class="glass-panel p-8 rounded-2xl w-[400px] border border-cyan-500/30 shadow-2xl relative">
            <button onclick="document.getElementById('settings-modal').classList.add('hidden')" class="absolute top-4 right-4 text-slate-400 hover:text-white transition">✕</button>
            <h2 class="text-xl font-black text-white uppercase tracking-widest mb-6" data-i18n="update_title">Update Credentials</h2>
            <form action="/update_credentials" method="POST" class="space-y-4">
                <div><label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">New Architect ID</label><input type="text" name="new_username" class="w-full glass-input px-3 py-2 rounded text-sm" required></div>
                <div><label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">New Passkey</label><input type="password" name="new_password" class="w-full glass-input px-3 py-2 rounded text-sm" required></div>
                <button type="submit" class="w-full mt-4 py-2 rounded bg-cyan-600 font-bold text-white uppercase text-xs tracking-wider transition hover:bg-cyan-500">Save Changes</button>
            </form>
        </div>
    </div>

</body>
"""

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

@app.route('/update_credentials', methods=['POST'])
def update_credentials():
    if 'user' not in session: 
        return redirect(url_for('home'))
    
    new_user = request.form.get('new_username')
    new_pass = request.form.get('new_password')
    
    if new_user and new_pass:
        hashed_pw = generate_password_hash(new_pass)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        try:
            # Update the currently logged-in user's credentials
            c.execute("UPDATE users SET username=?, password=? WHERE username=?", (new_user, hashed_pw, session['user']))
            conn.commit()
            session['user'] = new_user  # Keep them logged in with the new username
        except sqlite3.IntegrityError:
            # If the username already exists, just fail silently for now or flash an error
            pass
        finally:
            conn.close()
            
    return redirect(url_for('dashboard'))

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
            
    return render_template_string(DASHBOARD_HTML, sim_data=sim_data, inputs=inputs, current_preset=preset)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
