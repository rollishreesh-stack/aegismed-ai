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
# 2. ADVANCED CLINICAL MATH & AI ENGINE
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

        # Hemodynamics & Mechanics
        driving_pressure = max(0.1, pplat - peep)
        compliance = vt / driving_pressure
        flow_lsec = flow_lmin / 60.0
        resistance = max(0.1, (pip - pplat) / flow_lsec)
        
        # Ventilation & Dead Space
        min_vent_est = (vt * rr) / 1000.0
        paco2_derived = max(1.0, (0.863 * vco2) / max(0.1, min_vent_est * 0.75))
        if peco2 >= paco2_derived: 
            peco2 = max(0.1, paco2_derived - 4.0)
            
        vd_vt_ratio = max(0.01, min(0.95, (paco2_derived - peco2) / paco2_derived))
        
        # Shunt Fraction
        shunt_denominator = max(0.1, cco2 - cvo2)
        shunt_ratio = (cco2 - cao2) / shunt_denominator
        shunt_pct = round(max(0.01, min(0.95, shunt_ratio)) * 100, 1)

        alv_vent = max(0.1, ((vt * (1 - vd_vt_ratio)) * rr) / 1000.0)
        paco2 = round((0.863 * vco2) / alv_vent, 1)
        
        # Acid-Base
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
                "description": "Catastrophic loss of lung compliance combined with acute hypercapnia. Suggests complete unilateral lung collapse, pleural air accumulation, and mediastinal shift impairing venous return to the heart.", 
                "solutions": ["IMMEDIATE: Perform needle thoracostomy at 2nd intercostal space.", "Prepare for urgent chest tube insertion.", "Disconnect from positive pressure ventilator briefly if hemodynamic collapse is imminent.", "Obtain stat portable Chest X-Ray post-decompression."]
            }
        elif resistance > 25 and paco2 > 45:
            return {
                "condition": "STATUS ASTHMATICUS", 
                "description": "Critically elevated airway resistance indicating severe, refractory bronchospasm, mucosal edema, and mucus plugging. High risk of dynamic hyperinflation (Auto-PEEP) leading to barotrauma.", 
                "solutions": ["Administer continuous nebulized Albuterol and Ipratropium.", "Administer systemic IV corticosteroids (Methylprednisolone).", "Decrease respiratory rate (8-10 breaths/min) to allow complete exhalation.", "Increase Inspiratory:Expiratory (I:E) ratio to 1:4 or 1:5."]
            }
        elif vd_vt_ratio > 0.55 and shunt_pct < 15:
            return {
                "condition": "MASSIVE PULMONARY EMBOLISM", 
                "description": "Severe dead-space (Vd/Vt) ventilation detected. The alveoli are perfectly ventilated, but blood flow is blocked. Indicates a massive obstruction in the pulmonary arterial bed.", 
                "solutions": ["Initiate immediate systemic anticoagulation.", "Consider systemic thrombolytics (tPA) or catheter-directed embolectomy if hemodynamically unstable.", "Provide vasopressor support for right ventricular failure.", "Avoid excessive PEEP."]
            }
        elif compliance < 30 and shunt_pct > 25:
            return {
                "condition": "SEVERE ARDS (ACUTE RESPIRATORY DISTRESS)", 
                "description": "Profound, refractory hypoxemia secondary to massive intrapulmonary shunting and severely stiffened lungs. Indicates diffuse alveolar damage and protein-rich pulmonary edema.", 
                "solutions": ["Implement strict lung-protective ventilation (Tidal Volume 4-6 mL/kg Ideal Body Weight).", "Optimize PEEP via ARDSNet high PEEP/FiO2 table.", "Initiate early prone positioning for at least 16 hours per day.", "Consult for V-V ECMO if hypoxemia remains refractory."]
            }
        elif compliance > 60 and resistance > 15:
            return {
                "condition": "END-STAGE COPD / EMPHYSEMA", 
                "description": "Abnormally high static lung compliance with elevated airway resistance. Indicates severe destruction of alveolar septa, loss of natural elastic recoil, and chronic airflow limitation.", 
                "solutions": ["Accept permissive hypercapnia (Target pH > 7.20) to avoid dynamic hyperinflation.", "Apply extrinsic PEEP to match approx 80% of intrinsic Auto-PEEP.", "Administer scheduled bronchodilators.", "Treat underlying exacerbation triggers."]
            }
        elif compliance < 40 and shunt_pct > 15 and resistance < 15:
            return {
                "condition": "CARDIOGENIC PULMONARY EDEMA", 
                "description": "Reduced lung compliance and elevated shunt fraction indicative of hydrostatic fluid accumulation in the alveolar spaces secondary to acute left ventricular failure.", 
                "solutions": ["Administer IV loop diuretics (e.g., Furosemide) to actively diurese.", "Administer vasodilators (e.g., Nitroglycerin infusion) if blood pressure is adequate.", "Apply sufficient PEEP to mechanically push fluid out of alveoli.", "Perform urgent Echocardiogram."]
            }
        elif compliance < 35 and shunt_pct < 15 and vd_vt_ratio < 0.40:
            return {
                "condition": "ADVANCED PULMONARY FIBROSIS", 
                "description": "Severely restricted lung volumes due to thick parenchymal scarring. Compliance is critically low, rendering the lungs 'stiff'.", 
                "solutions": ["Utilize ultra-low tidal volume ventilation to prevent severe volutrauma.", "Titrate PEEP very carefully; high PEEP may cause overdistension of the remaining healthy alveoli.", "Investigate for acute infectious exacerbation."]
            }
        elif compliance > 40 and resistance < 15 and paco2 > 60:
            return {
                "condition": "NEUROMUSCULAR PUMP FAILURE", 
                "description": "Lung mechanics are completely normal, but ventilation is grossly inadequate leading to severe hypercapnia. Suggests critical diaphragm weakness.", 
                "solutions": ["Provide full mechanical ventilatory support.", "Assess for reversible neurologic causes (e.g., Guillain-Barré, Myasthenia Gravis, spinal cord injury).", "Perform regular, aggressive secretion clearance.", "Monitor Negative Inspiratory Force (NIF)."]
            }
        elif resistance > 15 and shunt_pct > 15 and paco2 > 45:
            return {
                "condition": "CYSTIC FIBROSIS EXACERBATION", 
                "description": "A complex mixed obstructive and shunting defect. Thick, inspissated, purulent secretions are causing high airway resistance and localized areas of lung collapse.", 
                "solutions": ["Administer aggressive inhaled mucolytics (e.g., Dornase alfa).", "Perform intense chest physiotherapy and postural drainage.", "Initiate targeted, broad-spectrum IV antibiotics.", "Use moderate levels of PEEP to stent airways open."]
            }
        elif compliance < 45 and paco2 > 50 and vd_vt_ratio > 0.40:
            return {
                "condition": "OBESITY HYPOVENTILATION SYNDROME", 
                "description": "Decreased overall respiratory system compliance due to massive adiposity on the chest wall, leading to chronic CO2 retention and basilar lung collapse.", 
                "solutions": ["Utilize significantly higher PEEP levels to overcome heavy chest wall weight.", "Position the patient in a reverse Trendelenburg or fully seated upright position.", "Target Ideal Body Weight (IBW) for tidal volume calculations.", "Monitor closely for Cor Pulmonale."]
            }
        elif shunt_pct > 15 and resistance < 12 and compliance > 35:
            return {
                "condition": "SEVERE LOBAR PNEUMONIA", 
                "description": "A localized alveolar filling process (pus and inflammation) causing significant right-to-left intrapulmonary shunting, without diffuse stiffening.", 
                "solutions": ["Administer broad-spectrum empiric IV antibiotics immediately.", "Target oxygen therapy and moderate PEEP to improve saturation.", "Consider positioning the patient with the 'good lung down' to optimize V/Q matching.", "Obtain respiratory sputum cultures."]
            }
        elif compliance < 40 and paco2 < 35:
            return {
                "condition": "EARLY / MILD ARDS",
                "description": "Decreasing lung compliance and tachypnea causing a respiratory alkalosis (low CO2) early in the disease process. Inflammatory fluid is just beginning to leak into alveoli.",
                "solutions": ["Monitor closely for progression to severe ARDS.", "Apply moderate PEEP (8-10 cmH2O) to stabilize alveoli early.", "Restrict IV fluids to keep the patient 'even' or slightly 'dry'.", "Aggressively treat the underlying cause (e.g., sepsis)."]
            }
        elif compliance < 30 and vd_vt_ratio > 0.45:
            return {
                "condition": "LOBAR ATELECTASIS",
                "description": "Loss of lung volume due to a collapsed lobe, resulting in decreased compliance and increased dead space. Often caused by a mucus plug in a mainstem bronchus.",
                "solutions": ["Perform therapeutic bronchoscopy to visually identify and clear mucus plugs.", "Institute aggressive chest physiotherapy and suctioning.", "Perform recruitment maneuvers to pop open collapsed alveoli.", "Ensure adequate humidification of inspired gases."]
            }
        elif paco2 < 30 and pao2 > 100:
            return {
                "condition": "CARBON MONOXIDE POISONING",
                "description": "Patient is hyperventilating with excellent oxygenation numbers, but standard SpO2 probes cannot differentiate between Oxyhemoglobin and Carboxyhemoglobin.",
                "solutions": ["Maintain 100% FiO2 via a non-rebreather mask or mechanical ventilator to decrease the half-life of Carbon Monoxide.", "Obtain an arterial blood gas with CO-oximetry to measure exact Carboxyhemoglobin levels.", "Consider hyperbaric oxygen chamber facility transfer."]
            }
        elif compliance < 35 and resistance < 15 and vd_vt_ratio > 0.40:
            return {
                "condition": "PULMONARY HYPERTENSION / COR PULMONALE",
                "description": "Right heart failure causing poor perfusion to the lungs. Reflected by high dead space (ventilation without perfusion) and stiffened pulmonary vasculature.",
                "solutions": ["Administer inhaled pulmonary vasodilators (e.g., Nitric Oxide or Epoprostenol).", "Avoid hypoxia and hypercapnia, both of which cause pulmonary vasoconstriction.", "Optimize right ventricular preload with careful fluid management.", "Provide inotropic support (e.g., Milrinone)."]
            }
        elif compliance < 30 and resistance < 15 and paco2 > 45:
            return {
                "condition": "FLAIL CHEST / BLUNT THORACIC TRAUMA",
                "description": "Paradoxical chest wall movement due to multiple rib fractures, leading to severely impaired compliance, pain-induced hypoventilation, and underlying pulmonary contusion.",
                "solutions": ["Provide positive pressure ventilation to mechanically stabilize the chest wall ('pneumatic splinting').", "Ensure aggressive pain control (e.g., epidural analgesia).", "Avoid fluid overload which will rapidly worsen the underlying pulmonary contusion.", "Consult thoracic surgery for surgical rib fixation."]
            }
        elif compliance < 25 and paco2 > 55:
            return {
                "condition": "SEVERE SEPSIS-INDUCED ARDS",
                "description": "Extreme systemic inflammation causing capillary leak, rock-stiff lungs, and mixed respiratory/metabolic failure.",
                "solutions": ["Source control of infection immediately.", "Broad spectrum antibiotics.", "Lung protective ventilation (Vt 4cc/kg).", "Consider ECMO if conventional therapy fails."]
            }
        elif resistance > 20 and paco2 > 60:
            return {
                "condition": "ACUTE BRONCHIECTASIS EXACERBATION",
                "description": "Chronically dilated, scarred airways filled with pus causing massive resistance and hypercapnia.",
                "solutions": ["Aggressive pulmonary toilet.", "Targeted IV antibiotics.", "Bronchodilators and low respiratory rates to prevent auto-PEEP."]
            }
        elif compliance < 30 and paco2 > 50 and ph < 7.2:
            return {
                "condition": "SEVERE KYPHOSCOLIOSIS WITH RESP FAILURE",
                "description": "Chest wall deformity severely restricting lung expansion, leading to chronic hypercapnia that has acutely decompensated.",
                "solutions": ["Non-invasive positive pressure ventilation (BiPAP) if airway is safe.", "Mechanical ventilation with high PEEP to overcome chest wall resistance.", "Treat acute triggers (usually pneumonia or viral illness)."]
            }
        else:
            return {
                "condition": "STABLE PULMONARY HOMEOSTASIS", 
                "description": "Ventilatory mechanics, resistance, compliance, and gas exchange parameters are currently registering within normal, optimal clinical limits. No acute pathological deviations detected.", 
                "solutions": ["Maintain current ventilatory support and oxygenation settings.", "Monitor patient for readiness to wean.", "Perform daily Spontaneous Breathing Trials (SBTs).", "Ensure adequate nutritional support and early physical mobility."]
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
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Outfit', sans-serif; background-color: #020617; color: #f8fafc; overflow-x: hidden; min-height: 100vh; display: flex; flex-direction: column; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    
    @keyframes holographicBreathe {
        0% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.3; filter: drop-shadow(0 0 20px rgba(6,182,212,0.4)); }
        50% { transform: translate(-50%, -50%) scale(1.03); opacity: 0.7; filter: drop-shadow(0 0 50px rgba(6,182,212,0.8)); }
        100% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.3; filter: drop-shadow(0 0 20px rgba(6,182,212,0.4)); }
    }
    .living-lung { position: fixed; top: 50%; left: 50%; width: 100vw; max-width: 900px; z-index: 0; pointer-events: none; animation: holographicBreathe 5s ease-in-out infinite; }
    
    .glass-panel { 
        background: rgba(15, 23, 42, 0.45); 
        backdrop-filter: blur(16px); 
        -webkit-backdrop-filter: blur(16px); 
        border: 1px solid rgba(255, 255, 255, 0.08); 
        position: relative; z-index: 10;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); 
    }
    
    .glass-input { background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.1); color: #fff; transition: all 0.3s ease; }
    .glass-input:focus { outline: none; border-color: #22d3ee; box-shadow: 0 0 15px rgba(34, 211, 238, 0.3); background: rgba(0, 0, 0, 0.8); }

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
        if(clockEl) clockEl.innerHTML = `<span class="text-cyan-400 font-bold text-sm tracking-wider">${timeString}</span> <span class="text-slate-400 text-[11px] uppercase ml-3 tracking-widest border-l border-slate-700 pl-3">${dateString}</span>`;
    }
    setInterval(updateClock, 1000);
    window.onload = updateClock;
</script>

<script>
const TRANSLATIONS = {
    en: {
        brand: "AERO<span class='text-cyan-400'>LUNG</span>",
        settings: "Settings",
        logout: "Logout",
        return_dash: "Return to Dashboard",
        account_settings: "Account Settings",
        modify_creds: "Modify Access Credentials",
        global_db: "Global Pathology Database",
        preset_desc: "Select a condition from the dropdown to auto-populate clinical hemodynamics.",
        select_preset: "-- Select a Clinical Pathology --",
        manual_override: "Manual Telemetry Override",
        vent_mechanics: "Ventilation Mechanics",
        gas_exchange: "Gas Exchange & Blood Labs",
        btn_scan: "Initialize Matrix Scan",
        standby_title: "System Standby",
        standby_desc: "Select a pathology profile from the left dropdown matrix or command Lyra.",
        primary_diag: "Primary AI Diagnosis",
        physio_breakdown: "Physiological Breakdown",
        action_plan: "Required Clinical Action Plan",
        abg_analysis: "Arterial Blood Gas Analysis",
        blood_ph: "Blood pH",
        paco2_lbl: "PaCO2",
        hco3_lbl: "HCO3",
        mech_explained: "Pulmonary Mechanics Explained",
        lung_compliance: "Lung Compliance",
        airway_resistance: "Airway Resistance",
        dead_space: "Vd/Vt (Dead Space)",
        shunt_fraction: "Shunt Fraction",
        waveform_analytics: "Ventilator Waveform Analytics",
        lyra_title: "LYRA VIRTUAL CLINICAL ASSISTANT",
        lyra_placeholder: "Ask Lyra to load parameters or conditions...",
        lyra_send: "Send",
        lyra_welcome: "Hello, I am Lyra, your clinical simulation assistant. Tell me to load presets or adjust telemetry parameters in English, Spanish, or French!",
        lyra_loaded_preset: "Understood. Loading the simulation matrix for: ",
        lyra_updated_params: "Telemetry matrix modified. Updating parameters: ",
        lyra_not_found: "Command not recognized. Try 'load ARDS' or 'set PEEP to 10'."
    },
    es: {
        brand: "AERO<span class='text-cyan-400'>LUNG</span>",
        settings: "Configuración",
        logout: "Cerrar sesión",
        return_dash: "Volver al Panel",
        account_settings: "Configuración de la Cuenta",
        modify_creds: "Modificar credenciales de acceso",
        global_db: "Base de Datos de Patologías Globales",
        preset_desc: "Seleccione una condición del menú desplegable para completar automáticamente la hemodinámica clínica.",
        select_preset: "-- Seleccione una Patología Clínica --",
        manual_override: "Anulación de Telemetría Manual",
        vent_mechanics: "Mecánica de Ventilación",
        gas_exchange: "Intercambio de Gases y Laboratorios de Sangre",
        btn_scan: "Iniciar escaneo de matriz",
        standby_title: "Sistema en Espera",
        standby_desc: "Seleccione un perfil de patología de la matriz desplegable izquierda o dé una orden a Lyra.",
        primary_diag: "Diagnóstico Principal de IA",
        physio_breakdown: "Desglose Fisiológico",
        action_plan: "Plan de Acción Clínico Requerido",
        abg_analysis: "Análisis de Gases en Sangre Arterial",
        blood_ph: "pH en sangre",
        paco2_lbl: "PaCO2",
        hco3_lbl: "HCO3",
        mech_explained: "Mecánica Pulmonar Explicada",
        lung_compliance: "Distensibilidad Pulmonar",
        airway_resistance: "Resistencia de Vías Aéreas",
        dead_space: "Vd/Vt (Espacio Muerto)",
        shunt_fraction: "Fracción de Shunt",
        waveform_analytics: "Análisis de Ondas del Ventilador",
        lyra_title: "ASISTENTE CLÍNICA VIRTUAL LYRA",
        lyra_placeholder: "Pídale a Lyra que cargue parámetros o condiciones...",
        lyra_send: "Enviar",
        lyra_welcome: "Hola, soy Lyra, su asistente de simulación clínica. ¡Pídame que cargue ajustes preestablecidos o modifique parámetros de telemetría en inglés, español o francés!",
        lyra_loaded_preset: "Entendido. Cargando la matriz de simulación para: ",
        lyra_updated_params: "Matriz de telemetría modificada. Actualizando parámetros: ",
        lyra_not_found: "Comando no reconocido. Intente con 'cargar SDRA' o 'fijar PEEP en 10'."
    },
    fr: {
        brand: "AERO<span class='text-cyan-400'>LUNG</span>",
        settings: "Paramètres",
        logout: "Déconnexion",
        return_dash: "Retour au Tableau de Bord",
        account_settings: "Paramètres du Compte",
        modify_creds: "Modifier les identifiants d'accès",
        global_db: "Base de Données Pathologiques Globale",
        preset_desc: "Sélectionnez une condition dans le menu déroulant pour remplir automatiquement l'hémodynamique clinique.",
        select_preset: "-- Sélectionner une Pathologie Clinique --",
        manual_override: "Contrôle Manuel de la Télémétrie",
        vent_mechanics: "Mécanique de Ventilation",
        gas_exchange: "Échange Gazeux & Labos Sanguins",
        btn_scan: "Initialiser l'analyse de la matrice",
        standby_title: "Système en Veille",
        standby_desc: "Sélectionnez un profil de pathologie dans la matrice déroulante de gauche ou commandez Lyra.",
        primary_diag: "Diagnostic Principal par IA",
        physio_breakdown: "Analyse Physiologique",
        action_plan: "Plan d'Action Clinique Requis",
        abg_analysis: "Analyse des Gaz du Sang Artériel",
        blood_ph: "pH Sanguin",
        paco2_lbl: "PaCO2",
        hco3_lbl: "HCO3",
        mech_explained: "Mécanique Pulmonaire Expliquée",
        lung_compliance: "Compliance Pulmonaire",
        airway_resistance: "Résistance des Voies Aériennes",
        dead_space: "Vd/Vt (Espace Mort)",
        shunt_fraction: "Fraction de Shunt",
        waveform_analytics: "Analyse des Ondes du Ventilateur",
        lyra_title: "ASSISTANTE CLINIQUE VIRTUELLE LYRA",
        lyra_placeholder: "Demandez à Lyra de charger des paramètres ou des conditions...",
        lyra_send: "Envoyer",
        lyra_welcome: "Bonjour, je suis Lyra, votre assistante de simulation clinique. Demandez-moi de charger des préréglages ou d'ajuster les paramètres en anglais, espagnol ou français !",
        lyra_loaded_preset: "Bien reçu. Chargement de la matrice de simulation pour : ",
        lyra_updated_params: "Matrice de télémétrie modifiée. Mise à jour des paramètres : ",
        lyra_not_found: "Commande non reconnue. Essayez 'charger SDRA' ou 'régler PEEP à 10'."
    }
};

const DYNAMIC_MAPPING = {
    es: {
        "TENSION PNEUMOTHORAX": "NEUMOTÓRAX A TENSIÓN",
        "STATUS ASTHMATICUS": "ESTADO ASMÁTICO",
        "MASSIVE PULMONARY EMBOLISM": "EMBOLIA PULMONAR MASIVA",
        "SEVERE ARDS (ACUTE RESPIRATORY DISTRESS)": "SDRA SEVERO (SÍNDROME DE DIFICULTAD RESPIRATORIA AGUDA)",
        "END-STAGE COPD / EMPHYSEMA": "EPOC EN ETAPA TERMINAL / ENFISEMA",
        "CARDIOGENIC PULMONARY EDEMA": "EDEMA PULMONAR CARDIOGÉNICO",
        "ADVANCED PULMONARY FIBROSIS": "FIBROSIS PULMONAR AVANZADA",
        "NEUROMUSCULAR PUMP FAILURE": "FALLA DE LA BOMBA NEUROMUSCULAR",
        "CYSTIC FIBROSIS EXACERBATION": "EXACERBACIÓN DE FIBROSIS QUÍSTICA",
        "OBESITY HYPOVENTILATION SYNDROME": "SÍNDROME DE HIPOVENTILACIÓN POR OBESIDAD",
        "SEVERE LOBAR PNEUMONIA": "NEUMONÍA LOBAR SEVERA",
        "EARLY / MILD ARDS": "SDRA TEMPRANO / LEVE",
        "LOBAR ATELECTASIS": "ATELECTASIA LOBAR",
        "CARBON MONOXIDE POISONING": "INTOXICACIÓN POR MONÓXIDO DE CARBONO",
        "PULMONARY HYPERTENSION / COR PULMONALE": "HIPERTENSIÓN PULMONAR / COR PULMONALE",
        "FLAIL CHEST / BLUNT THORACIC TRAUMA": "TÓRAX INESTABLE / TRAUMA TORÁCICO CERRADO",
        "SEVERE SEPSIS-INDUCED ARDS": "SDRA INDUCIDO POR SEPSIS SEVERA",
        "ACUTE BRONCHIECTASIS EXACERBATION": "EXACERBACIÓN AGUDA DE BRONQUIECTASIAS",
        "SEVERE KYPHOSCOLIOSIS WITH RESP FAILURE": "CIFOSCOLIOSIS SEVERA CON INSUFICIENCIA RESPIRATORIA",
        "STABLE PULMONARY HOMEOSTASIS": "HOMEOSTASIS PULMONAR ESTABLE",
        "Respiratory Acidosis": "Acidosis Respiratoria",
        "Metabolic Acidosis": "Acidosis Metabólica",
        "Respiratory Alkalosis": "Alcalosis Respiratoria",
        "Metabolic Alkalosis": "Alcalosis Metabólica",
        "Normal Acid-Base Equilibrium": "Equilibrio Ácido-Base Normal"
    },
    fr: {
        "TENSION PNEUMOTHORAX": "PNEUMOTHORAX SOUS TENSION",
        "STATUS ASTHMATICUS": "CHOC ASTHMATIQUE",
        "MASSIVE PULMONARY EMBOLISM": "EMBOLIE PULMONAIRE MASSIVE",
        "SEVERE ARDS (ACUTE RESPIRATORY DISTRESS)": "SDRA SÉVÈRE (SYNDROME DE DÉTRESSE RESPIRATOIRE AIGUË)",
        "END-STAGE COPD / EMPHYSEMA": "BPCO POST-TARDIVE / EMPHYSÈME",
        "CARDIOGENIC PULMONARY EDEMA": "ŒDÈME PULMONAIRE CARDIOGÉNIQUE",
        "ADVANCED PULMONARY FIBROSIS": "FIBROSE PULMONAIRE AVANZÉE",
        "NEUROMUSCULAR PUMP FAILURE": "INSUFFISANCE DE LA POMPE NEUROMUSCULAIRE",
        "CYSTIC FIBROSIS EXACERBATION": "EXACERBATION DE LA MUCOVISCIDOSE",
        "OBESITY HYPOVENTILATION SYNDROME": "SYNDROME D'HYPOVENTILATION OBÉSITÉ",
        "SEVERE LOBAR PNEUMONIA": "PNEUMONIE LOBAIRE SÉVÈRE",
        "EARLY / MILD ARDS": "SDRA PRÉCOCE / LÉGER",
        "LOBAR ATELECTASIS": "ATÉLECTASIE LOBAIRE",
        "CARBON MONOXIDE POISONING": "INTOXICATION AU MONOXYDE DE CARBONE",
        "PULMONARY HYPERTENSION / COR PULMONALE": "HYPERTENSION PULMONAIRE / CŒUR PULMONAIRE CHRONIQUE",
        "FLAIL CHEST / BLUNT THORACIC TRAUMA": "VOLET COSTAL / TRAUMATISME THORACIQUE FERMÉ",
        "SEVERE SEPSIS-INDUCED ARDS": "SDRA INDUIT PAR UN SEPSIS SÉVÈRE",
        "ACUTE BRONCHIECTASIS EXACERBATION": "EXACERBATION AIGUË DE BRONCHECTASIE",
        "SEVERE KYPHOSCOLIOSIS WITH RESP FAILURE": "CYPHOSCOLIOSE SÉVÈRE AVEC INSUFFISANCE RESPIRATOIRE",
        "STABLE PULMONARY HOMEOSTASIS": "HOMÉOSTASIE PULMONAIRE STABLE",
        "Respiratory Acidosis": "Acidose Respiratoire",
        "Metabolic Acidosis": "Acidose Métabolique",
        "Respiratory Alkalosis": "Alcalose Respiratoire",
        "Metabolic Alkalosis": "Alcalose Métabolique",
        "Normal Acid-Base Equilibrium": "Équilibre Acido-Basique Normal"
    }
};

const CHART_LABELS = {
    en: ["Pressure (cmH2O)", "Volume (mL)", "Flow (L/m)"],
    es: ["Presión (cmH2O)", "Volumen (mL)", "Flujo (L/m)"],
    fr: ["Pression (cmH2O)", "Volume (mL)", "Débit (L/m)"]
};

function changeLanguage(lang) {
    localStorage.setItem('selectedLang', lang);
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) {
            if (el.tagName === 'INPUT') {
                el.setAttribute('placeholder', TRANSLATIONS[lang][key]);
            } else {
                el.innerHTML = TRANSLATIONS[lang][key];
            }
        }
    });

    document.querySelectorAll('[data-i18n-label]').forEach(el => {
        const key = el.getAttribute('data-i18n-label');
        if (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) {
            el.setAttribute('label', TRANSLATIONS[lang][key]);
        }
    });
    
    const dropdown = document.getElementById('preset-dropdown');
    if (dropdown && TRANSLATIONS[lang]['select_preset']) {
        dropdown.options[0].text = TRANSLATIONS[lang]['select_preset'];
    }
    
    const condEl = document.getElementById('ai-condition-text');
    if (condEl) {
        const raw = condEl.getAttribute('data-raw');
        condEl.innerText = (DYNAMIC_MAPPING[lang] && DYNAMIC_MAPPING[lang][raw]) ? DYNAMIC_MAPPING[lang][raw] : raw;
    }
    
    const statusEl = document.getElementById('abg-status-text');
    if (statusEl) {
        const raw = statusEl.getAttribute('data-raw');
        statusEl.innerText = (DYNAMIC_MAPPING[lang] && DYNAMIC_MAPPING[lang][raw]) ? DYNAMIC_MAPPING[lang][raw] : raw;
    }

    if (window.myMatrixChart) {
        const labels = CHART_LABELS[lang] || CHART_LABELS['en'];
        window.myMatrixChart.data.datasets[0].label = labels[0];
        window.myMatrixChart.data.datasets[1].label = labels[1];
        window.myMatrixChart.data.datasets[2].label = labels[2];
        window.myMatrixChart.update();
    }

    if (typeof translateClinicalDetails === 'function') {
        translateClinicalDetails(lang);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    const savedLang = localStorage.getItem('selectedLang') || 'en';
    const selector = document.getElementById('lang-selector');
    if (selector) selector.value = savedLang;
    changeLanguage(savedLang);
});
</script>
"""

COPYRIGHT_FOOTER = """
<footer class="mt-auto py-5 text-center relative z-20 border-t border-slate-800 bg-slate-950/90">
    <div class="text-[11px] text-slate-500 font-medium tracking-wide">
        &copy; 2026 Shreesh Santoshkumar Rolli &nbsp;|&nbsp; AeroLung Medical System
    </div>
</footer>
"""

LOGIN_HTML = GLOBAL_CSS + BACKGROUND_SVG + """
<body class="flex items-center justify-center relative min-h-screen">
    <div class="absolute top-4 right-6 z-50">
        <select id="lang-selector" onchange="changeLanguage(this.value)" class="bg-slate-900/80 border border-slate-700/50 rounded-lg px-3 py-1.5 text-xs text-white font-mono font-bold cursor-pointer">
            <option value="en">EN</option>
            <option value="es">ES</option>
            <option value="fr">FR</option>
        </select>
    </div>
    <div class="glass-panel rounded-3xl p-10 w-full max-w-md text-center border-t border-white/10 shadow-[0_0_40px_rgba(6,182,212,0.15)]">
        <h1 class="text-5xl font-black tracking-tighter text-white mb-2" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
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
                Initialize Secure Uplink
            </button>
        </form>
    </div>
    {{ COPYRIGHT_FOOTER | safe }}
</body>
"""

SETTINGS_HTML = GLOBAL_CSS + BACKGROUND_SVG + """
<body class="flex items-center justify-center relative flex-col min-h-screen">
    <nav class="glass-panel w-full border-b-0 border-white/5 rounded-none bg-slate-950/90 py-4 px-6 flex justify-between absolute top-0 z-50">
        <h1 class="text-2xl font-black tracking-tighter text-white" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
        <div class="flex items-center gap-4">
            <select id="lang-selector" onchange="changeLanguage(this.value)" class="bg-slate-900/80 border border-slate-700/50 rounded-lg px-3 py-1.5 text-xs text-white font-mono font-bold cursor-pointer">
                <option value="en">EN</option>
                <option value="es">ES</option>
                <option value="fr">FR</option>
            </select>
            <a href="/dashboard" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold uppercase tracking-wider transition-colors border border-slate-600" data-i18n="return_dash">Return to Dashboard</a>
        </div>
    </nav>

    <div class="glass-panel rounded-3xl p-10 w-full max-w-lg text-center border-t border-white/10 mt-20 shadow-[0_0_40px_rgba(6,182,212,0.15)]">
        <h2 class="text-3xl font-black tracking-tighter text-white mb-2 uppercase" data-i18n="account_settings">Account Settings</h2>
        <p class="text-xs font-mono text-cyan-500/80 uppercase tracking-[0.2em] mb-8" data-i18n="modify_creds">Modify Access Credentials</p>
        
        {% if get_flashed_messages() %}
            <div class="mb-6 p-3 text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-900/50 rounded uppercase tracking-wide">
                {% for msg in get_flashed_messages() %} {{ msg }} {% endfor %}
            </div>
        {% endif %}

        <form action="/settings" method="POST" class="space-y-5 text-left">
            <div>
                <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 ml-1">Current ID (Display Only)</label>
                <input type="text" value="{{ session.user }}" disabled class="w-full bg-slate-900/50 text-slate-500 border border-white/5 px-5 py-4 rounded-xl font-mono text-sm cursor-not-allowed">
            </div>
            <div>
                <label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2 ml-1">New ID (Optional)</label>
                <input type="text" name="new_username" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm" placeholder="Enter new ID">
            </div>
            <div>
                <label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2 ml-1">New Passkey (Optional)</label>
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
            <h1 class="text-3xl font-black tracking-tighter text-white" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
            
            <div id="live-clock" class="hidden lg:block bg-black/50 border border-slate-800 px-5 py-2.5 rounded-xl shadow-inner"></div>

            <div class="flex items-center gap-4">
                <select id="lang-selector" onchange="changeLanguage(this.value)" class="bg-slate-900/80 border border-slate-700/50 rounded-lg px-3 py-1.5 text-xs text-white font-mono font-bold cursor-pointer">
                    <option value="en">EN</option>
                    <option value="es">ES</option>
                    <option value="fr">FR</option>
                </select>
                <div class="text-[10px] font-mono text-slate-400 uppercase tracking-widest border-r border-slate-700 pr-4 hidden md:block">
                    Session: <span class="text-cyan-400 font-bold">{{ session.user }}</span>
                </div>
                <a href="/settings" class="px-4 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-600/50 text-[10px] font-bold uppercase tracking-wider transition-colors" data-i18n="settings">Settings</a>
                <a href="/logout" class="px-4 py-2 rounded-lg bg-rose-900/40 hover:bg-rose-800/60 text-rose-300 border border-rose-800/50 text-[10px] font-bold uppercase tracking-wider transition-colors" data-i18n="logout">Logout</a>
            </div>
        </div>
    </nav>

    <main class="flex-1 max-w-[1800px] mx-auto w-full p-6 flex flex-col lg:flex-row gap-8 relative z-10 h-full">
        
        <div class="w-full lg:w-[450px] xl:w-[500px] flex flex-col gap-6 shrink-0">
            
            <div class="glass-panel rounded-2xl p-5 border-t-2 border-t-cyan-500">
                <h2 class="text-[11px] font-bold uppercase tracking-widest text-cyan-400 mb-2" data-i18n="global_db">Global Pathology Database</h2>
                <p class="text-[10px] text-slate-400 mb-4" data-i18n="preset_desc">Select a condition from the dropdown to auto-populate clinical hemodynamics.</p>
                
                <select id="preset-dropdown" onchange="if(this.value) loadPreset(this.value);" class="w-full glass-input px-3 py-3 rounded-lg text-sm font-semibold text-slate-200 cursor-pointer">
                    <option value="" disabled selected data-i18n="select_preset">-- Select a Clinical Pathology --</option>
                    <optgroup label="Baseline & Obstructive" data-i18n-label="bg_obstructive">
                        <option value="healthy">Healthy Baseline</option>
                        <option value="copd">End-Stage COPD</option>
                        <option value="asthma">Status Asthmaticus</option>
                        <option value="cf">Cystic Fibrosis</option>
                        <option value="bronch">Bronchiectasis</option>
                    </optgroup>
                    <optgroup label="Restrictive & ARDS" data-i18n-label="bg_restrictive">
                        <option value="mild_ards">Mild ARDS</option>
                        <option value="ards_mod">Moderate ARDS</option>
                        <option value="ards">Severe ARDS</option>
                        <option value="fibrosis">Pulmonary Fibrosis</option>
                        <option value="atelectasis">Lobar Atelectasis</option>
                    </optgroup>
                    <optgroup label="Vascular & Fluid" data-i18n-label="bg_vascular">
                        <option value="pe">Massive Pulm Embolism</option>
                        <option value="p_htn">Pulmonary HTN / Cor Pulmonale</option>
                        <option value="edema">Cardiogenic Edema</option>
                        <option value="pneumonia">Severe Pneumonia</option>
                    </optgroup>
                    <optgroup label="Chest Wall & Toxic" data-i18n-label="bg_chestwall">
                        <option value="neuro">Neuromuscular Failure</option>
                        <option value="obesity">Obesity Hypoventilation</option>
                        <option value="pneumothorax">Tension Pneumothorax</option>
                        <option value="kypho">Kyphoscoliosis</option>
                        <option value="flail">Flail Chest Trauma</option>
                        <option value="co_poison">Carbon Monoxide Poisoning</option>
                    </optgroup>
                </select>
            </div>

            <div class="glass-panel rounded-2xl flex flex-col shadow-2xl">
                <form id="calc-form" method="POST" action="/dashboard" class="p-5">
                    <h3 class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest border-b border-white/10 pb-2 mb-4" data-i18n="manual_override">Manual Telemetry Override</h3>
                    
                    <div class="text-[9px] text-slate-400 uppercase tracking-widest mb-2 font-bold" data-i18n="vent_mechanics">Ventilation Mechanics</div>
                    <div class="grid grid-cols-4 gap-3 mb-4 bg-black/40 p-4 rounded-xl border border-white/5">
                        <div title="Tidal Volume in mL"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">Vt (mL)</label><input type="number" name="vt_input" id="vt_input" value="{{ inputs.vt_input|default(500) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                        <div title="Respiratory Rate"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">Rate</label><input type="number" name="rr" id="rr" value="{{ inputs.rr|default(14) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                        <div title="Peak Inspiratory Pressure"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">PIP</label><input type="number" name="pip" id="pip" value="{{ inputs.pip|default(20) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-rose-300"></div>
                        <div title="Plateau Pressure"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">Pplat</label><input type="number" name="pplat" id="pplat" value="{{ inputs.pplat|default(14) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-rose-300"></div>
                        <div title="Positive End-Expiratory Pressure"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">PEEP</label><input type="number" name="peep" id="peep" value="{{ inputs.peep|default(5) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-cyan-300"></div>
                        <div title="Peak Flow in L/min"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">Flow</label><input type="number" name="peak_flow" id="peak_flow" value="{{ inputs.peak_flow|default(60) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                        <div title="Fraction of Inspired Oxygen"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">FiO2 %</label><input type="number" name="fio2" id="fio2" value="{{ inputs.fio2|default(30) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                        <div title="Inspiratory:Expiratory Ratio"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">I:E</label><input type="number" step="0.1" name="ie_ratio" id="ie_ratio" value="{{ inputs.ie_ratio|default(2.0) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                    </div>
                    
                    <div class="text-[9px] text-slate-400 uppercase tracking-widest mb-2 font-bold mt-4" data-i18n="gas_exchange">Gas Exchange & Blood Labs</div>
                    <div class="grid grid-cols-3 gap-3 mb-6 bg-black/40 p-4 rounded-xl border border-white/5">
                        <div title="Arterial Oxygen Content"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">CaO2</label><input type="number" step="0.1" name="cao2" id="cao2" value="{{ inputs.cao2|default(19.8) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-emerald-300"></div>
                        <div title="Venous Oxygen Content"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">CvO2</label><input type="number" step="0.1" name="cvo2" id="cvo2" value="{{ inputs.cvo2|default(14.8) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-emerald-300"></div>
                        <div title="Capillary Oxygen Content"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">CcO2</label><input type="number" step="0.1" name="cco2" id="cco2" value="{{ inputs.cco2|default(20.4) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-emerald-300"></div>
                        <div title="Exhaled CO2"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1 mt-2">PECO2</label><input type="number" name="peco2" id="peco2" value="{{ inputs.peco2|default(28) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-amber-300"></div>
                        <div title="CO2 Production"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1 mt-2">VCO2</label><input type="number" name="vco2" id="vco2" value="{{ inputs.vco2|default(200) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-amber-300"></div>
                        <div title="Systemic Bicarbonate"><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1 mt-2">HCO3</label><input type="number" name="hco3_input" id="hco3_input" value="{{ inputs.hco3_input|default(24) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-purple-300"></div>
                    </div>

                    <button type="submit" class="w-full py-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-black text-xs uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(34,211,238,0.4)] transition-all" data-i18n="btn_scan">
                        Initialize Matrix Scan
                    </button>
                </form>
            </div>

            <div class="glass-panel rounded-2xl flex flex-col shadow-2xl border-t-2 border-t-amber-500">
                <div class="p-4 border-b border-white/10 flex justify-between items-center bg-slate-950/40 rounded-t-2xl">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse"></span>
                        <h3 class="text-[11px] font-black text-amber-400 uppercase tracking-widest" data-i18n="lyra_title">LYRA VIRTUAL CLINICAL ASSISTANT</h3>
                    </div>
                </div>
                <div id="lyra-chat-box" class="p-4 h-48 overflow-y-auto space-y-3 text-xs font-mono bg-black/30 shadow-inner"></div>
                <div class="p-3 border-t border-white/10 bg-slate-950/60 rounded-b-2xl flex gap-2">
                    <input type="text" id="lyra-input" class="flex-1 glass-input px-3 py-2 rounded-lg text-xs font-mono" placeholder="Ask Lyra to load parameters or conditions..." data-i18n="lyra_placeholder" onkeydown="if(event.key === 'Enter') sendLyraMessage();">
                    <button onclick="sendLyraMessage()" class="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg font-bold text-xs uppercase tracking-wider transition-all" data-i18n="lyra_send">Send</button>
                </div>
            </div>

        </div>

        <div class="flex-1 flex flex-col gap-6 w-full min-w-0">
            {% if not sim_data %}
            <div class="glass-panel rounded-3xl flex-1 flex flex-col items-center justify-center min-h-[600px] border-dashed border-slate-600/50">
                <div class="w-24 h-24 border-4 border-slate-700 border-t-cyan-400 rounded-full animate-spin mb-6 shadow-[0_0_30px_rgba(34,211,238,0.4)]"></div>
                <h3 class="text-2xl font-black text-white mb-2 uppercase tracking-widest" data-i18n="standby_title">System Standby</h3>
                <p class="text-sm text-slate-400 font-mono" data-i18n="standby_desc">Select a pathology profile from the left dropdown matrix.</p>
            </div>
            {% else %}
            
            <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <div class="glass-panel p-8 rounded-2xl border-l-4 border-l-cyan-400 bg-gradient-to-br from-slate-900/95 to-black">
                    <h3 class="text-[11px] text-cyan-400 font-black uppercase tracking-[0.2em] mb-2" data-i18n="primary_diag">Primary AI Diagnosis</h3>
                    <div id="ai-condition-text" data-raw="{{ sim_data.ai_condition }}" class="text-3xl font-black text-white leading-tight tracking-tight mb-5 uppercase drop-shadow-md">{{ sim_data.ai_condition }}</div>
                    
                    <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 border-b border-white/10 pb-1" data-i18n="physio_breakdown">Physiological Breakdown</div>
                    <div class="text-sm text-slate-300 bg-black/40 p-4 rounded-lg border border-white/5 leading-relaxed mb-5 shadow-inner" id="ai-description-text">
                        {{ sim_data.ai_description }}
                    </div>

                    <div class="text-[10px] font-bold text-emerald-400 uppercase tracking-widest mb-2 border-b border-white/10 pb-1" data-i18n="action_plan">Required Clinical Action Plan</div>
                    <ul class="space-y-2" id="ai-solutions-list">
                        {% for solution in sim_data.ai_solutions %}
                        <li class="flex items-start gap-3 bg-emerald-950/20 p-3 rounded-lg border border-emerald-900/30 text-xs text-slate-200">
                            <span class="text-emerald-500 font-bold mt-0.5">⯈</span> <span>{{ solution }}</span>
                        </li>
                        {% endfor %}
                    </ul>
                </div>

                <div class="flex flex-col gap-6">
                    <div class="glass-panel p-8 rounded-2xl border-t-4 border-t-purple-500 flex-1 flex flex-col justify-center">
                        <h3 class="text-[11px] text-purple-400 font-black uppercase tracking-[0.2em] mb-6 text-center" data-i18n="abg_analysis">Arterial Blood Gas Analysis</h3>
                        <div class="grid grid-cols-3 gap-2 mb-6 bg-black/40 p-6 rounded-2xl border border-white/5 text-center shadow-inner">
                            <div>
                                <span class="text-[10px] text-slate-500 font-bold uppercase block mb-2" data-i18n="blood_ph">Blood pH</span>
                                <span class="text-3xl font-black font-mono {% if sim_data.ph < 7.35 %}text-rose-500{% elif sim_data.ph > 7.45 %}text-cyan-400{% else %}text-emerald-400{% endif %}">{{ sim_data.ph }}</span>
                            </div>
                            <div class="border-l border-white/10">
                                <span class="text-[10px] text-slate-500 font-bold uppercase block mb-2" data-i18n="paco2_lbl">PaCO2</span>
                                <span class="text-3xl font-black font-mono text-amber-400">{{ sim_data.paco2 }}</span>
                            </div>
                            <div class="border-l border-white/10">
                                <span class="text-[10px] text-slate-500 font-bold uppercase block mb-2" data-i18n="hco3_lbl">HCO3</span>
                                <span class="text-3xl font-black font-mono text-purple-400">{{ sim_data.hco3 }}</span>
                            </div>
                        </div>
                        <div id="abg-status-text" data-raw="{{ sim_data.acid_base_status }}" class="text-sm font-bold text-white uppercase tracking-wider bg-purple-950/50 block text-center py-3 rounded-lg border border-purple-800">{{ sim_data.acid_base_status }}</div>
                    </div>
                </div>
            </div>

            <div class="glass-panel p-6 rounded-2xl">
                <h3 class="text-[11px] text-slate-400 font-black uppercase tracking-[0.2em] mb-4 border-b border-white/10 pb-2" data-i18n="mech_explained">Pulmonary Mechanics Explained</h3>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5 shadow-inner">
                        <span class="text-[10px] text-cyan-400 font-bold uppercase tracking-widest block mb-2" data-i18n="lung_compliance">Lung Compliance</span>
                        <div class="text-3xl font-black text-white font-mono mb-1">{{ sim_data.compliance }}</div>
                        <div class="text-[9px] text-slate-500 uppercase font-bold mb-3">mL/cmH2O</div>
                    </div>
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5 shadow-inner">
                        <span class="text-[10px] text-rose-400 font-bold uppercase tracking-widest block mb-2" data-i18n="airway_resistance">Airway Resistance</span>
                        <div class="text-3xl font-black text-white font-mono mb-1">{{ sim_data.resistance }}</div>
                        <div class="text-[9px] text-slate-500 uppercase font-bold mb-3">cmH2O/L/s</div>
                    </div>
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5 shadow-inner">
                        <span class="text-[10px] text-amber-400 font-bold uppercase tracking-widest block mb-2" data-i18n="dead_space">Vd/Vt (Dead Space)</span>
                        <div class="text-3xl font-black text-white font-mono mb-1">{{ sim_data.dead_space }}<span class="text-lg text-slate-500">%</span></div>
                        <div class="text-[9px] text-slate-500 uppercase font-bold mb-3">Percentage</div>
                    </div>
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5 shadow-inner">
                        <span class="text-[10px] text-emerald-400 font-bold uppercase tracking-widest block mb-2" data-i18n="shunt_fraction">Shunt Fraction</span>
                        <div class="text-3xl font-black text-white font-mono mb-1">{{ sim_data.shunt }}<span class="text-lg text-slate-500">%</span></div>
                        <div class="text-[9px] text-slate-500 uppercase font-bold mb-3">Percentage</div>
                    </div>
                </div>
            </div>

            <div class="glass-panel p-8 rounded-2xl flex flex-col relative h-[420px] w-full">
                <div class="flex justify-between items-center mb-6 border-b border-white/10 pb-3">
                    <h3 class="text-[11px] text-slate-400 font-black uppercase tracking-[0.2em]" data-i18n="waveform_analytics">Ventilator Waveform Analytics</h3>
                    <div class="text-[10px] text-slate-300 flex gap-6 font-mono bg-black/50 px-4 py-2 rounded-lg border border-white/5">
                        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded bg-[#22d3ee]"></span><span class="font-bold">Paw:</span> Airway Pressure</div>
                        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded bg-[#10b981]"></span><span class="font-bold">Vol:</span> Lung Expansion</div>
                        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded bg-[#f43f5e]"></span><span class="font-bold">Flow:</span> Air Velocity</div>
                    </div>
                </div>
                <div class="flex-1 w-full relative"><canvas id="matrixChart"></canvas></div>
            </div>

            <script>
                const waveData = {{ sim_data.waveform_data | safe }};
                Chart.defaults.color = '#64748b';
                Chart.defaults.font.family = "'JetBrains Mono', monospace";
                
                window.myMatrixChart = new Chart(document.getElementById('matrixChart'), {
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
            if(!data) return;
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

        // --- LYRA CORE CHAT ENGINE FUNCTIONS ---
        function initLyra() {
            const box = document.getElementById('lyra-chat-box');
            if(!box) return;
            const currentLang = localStorage.getItem('selectedLang') || 'en';
            box.innerHTML = `<div class="text-amber-400 mb-0.5">🤖 Lyra:</div><div class="text-slate-300 mb-2">${TRANSLATIONS[currentLang]['lyra_welcome']}</div>`;
        }

        function sendLyraMessage() {
            const input = document.getElementById('lyra-input');
            if (!input || !input.value.trim()) return;
            const text = input.value.trim();
            input.value = '';
            
            const box = document.getElementById('lyra-chat-box');
            box.innerHTML += `<div class="text-cyan-400 mt-2 mb-0.5">👤 You:</div><div class="text-slate-200 mb-2">${text}</div>`;
            box.scrollTop = box.scrollHeight;
            
            setTimeout(() => { processLyraCommand(text); }, 350);
        }

        function processLyraCommand(msg) {
            const box = document.getElementById('lyra-chat-box');
            const currentLang = localStorage.getItem('selectedLang') || 'en';
            const norm = msg.toLowerCase();
            
            let matched = null;
            if (norm.includes('healthy') || norm.includes('saludable') || norm.includes('sain')) matched = 'healthy';
            else if (norm.includes('mild ards') || norm.includes('sdra leve') || norm.includes('sdra léger')) matched = 'mild_ards';
            else if (norm.includes('mod') && norm.includes('ards')) matched = 'ards_mod';
            else if (norm.includes('ards') || norm.includes('sdra')) matched = 'ards';
            else if (norm.includes('copd') || norm.includes('epoc') || norm.includes('bpco')) matched = 'copd';
            else if (norm.includes('asthma') || norm.includes('asma') || norm.includes('asthme')) matched = 'asthma';
            else if (norm.includes('fibrosis') || norm.includes('fibrose')) matched = 'fibrosis';
            else if (norm.includes('embolia') || norm.includes('embolie') || norm.includes('embolism') || norm.includes('pe')) matched = 'pe';
            else if (norm.includes('pneumonia') || norm.includes('neumonia') || norm.includes('pneumonie')) matched = 'pneumonia';
            else if (norm.includes('neuro')) matched = 'neuro';
            else if (norm.includes('obesity') || norm.includes('obesidad') || norm.includes('obesite')) matched = 'obesity';
            else if (norm.includes('pneumothorax') || norm.includes('neumotorax')) matched = 'pneumothorax';
            else if (norm.includes('edema') || norm.includes('oedeme')) matched = 'edema';
            else if (norm.includes('cf') || norm.includes('cystic') || norm.includes('quistica')) matched = 'cf';
            else if (norm.includes('kypho') || norm.includes('cifosis')) matched = 'kypho';
            else if (norm.includes('bronch') || norm.includes('bronquiectasias')) matched = 'bronch';
            else if (norm.includes('atelectasis') || norm.includes('atelectasia')) matched = 'atelectasis';
            else if (norm.includes('flail') || norm.includes('volet')) matched = 'flail';
            else if (norm.includes('htn') || norm.includes('pulmonary hypertension')) matched = 'p_htn';
            else if (norm.includes('carbon') || norm.includes('monoxide') || norm.includes('co_poison')) matched = 'co_poison';

            if (matched) {
                box.innerHTML += `<div class="text-amber-400 mb-0.5">🤖 Lyra:</div><div class="text-emerald-400 mb-2">${TRANSLATIONS[currentLang]['lyra_loaded_preset']} <strong>${matched.toUpperCase()}</strong></div>`;
                box.scrollTop = box.scrollHeight;
                setTimeout(() => { loadPreset(matched); }, 1000);
                return;
            }

            // Bind single or multiple explicit parameter assignments cross-lingual
            let binds = [];
            const expressions = {
                vt_input: /(?:vt|volume|volumen)\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                rr: /(?:rr|rate|frecuencia|fréquence|fr)\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                pip: /pip\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                peep: /peep\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                pplat: /pplat\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                peak_flow: /(?:flow|flujo|débit)\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                fio2: /fio2\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                ie_ratio: /(?:i:e|ie)\s*(?:to|en|à|a|=)?\s*([0-9.]+)/i,
                cao2: /cao2\s*(?:to|en|à|a|=)?\s*([0-9.]+)/i,
                cvo2: /cvo2\s*(?:to|en|à|a|=)?\s*([0-9.]+)/i,
                cco2: /cco2\s*(?:to|en|à|a|=)?\s*([0-9.]+)/i,
                peco2: /peco2\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                vco2: /vco2\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                hco3_input: /(?:hco3|bicarb|bicarbonato|bicarbonate)\s*(?:to|en|à|a|=)?\s*(\d+)/i
            };

            for (const [key, regex] of Object.entries(expressions)) {
                const match = norm.match(regex);
                if (match && match[1]) {
                    const value = match[1];
                    const element = document.getElementById(key);
                    if (element) {
                        element.value = value;
                        binds.push(`${key.replace('_input','')}=${value}`);
                    }
                }
            }

            if (binds.length > 0) {
                box.innerHTML += `<div class="text-amber-400 mb-0.5">🤖 Lyra:</div><div class="text-emerald-400 mb-2">${TRANSLATIONS[currentLang]['lyra_updated_params']} <strong>${binds.join(', ')}</strong></div>`;
                box.scrollTop = box.scrollHeight;
                setTimeout(() => { document.getElementById('calc-form').submit(); }, 1200);
                return;
            }

            box.innerHTML += `<div class="text-amber-400 mb-0.5">🤖 Lyra:</div><div class="text-slate-300 mb-2">${TRANSLATIONS[currentLang]['lyra_not_found']}</div>`;
            box.scrollTop = box.scrollHeight;
        }

        // Translate the diagnostic descriptions dynamically based on the current context language
        function translateClinicalDetails(lang) {
            const descBox = document.getElementById('ai-description-text');
            const solutionsBox = document.getElementById('ai-solutions-list');
            const condTitle = document.getElementById('ai-condition-text');
            if(!descBox || !solutionsBox || !condTitle) return;

            const rawCondition = condTitle.getAttribute('data-raw');
            const medicalRepo = {
                es: {
                    "SEVERE ARDS (ACUTE RESPIRATORY DISTRESS)": {
                        desc: "Hipoxemia profunda y refractaria secundaria a un cortocircuito (shunt) intrapulmonar masivo y pulmones gravemente rígidos. Indica daño alveolar difuso y edema pulmonar rico en proteínas.",
                        sols: ["Implementar ventilación protectora pulmonar estricta (Volumen Tidal 4-6 mL/kg de Peso Corporal Ideal).", "Optimizar PEEP a través de la tabla de PEEP alto/FiO2 de ARDSNet.", "Iniciar posición prona temprana durante al menos 16 horas al día.", "Consultar para ECMO V-V si la hipoxemia sigue siendo refractaria."]
                    },
                    "END-STAGE COPD / EMPHYSEMA": {
                        desc: "Distensibilidad pulmonar estática anormalmente alta con resistencia elevada de las vías respiratorias. Indica destrucción severa de los tabiques alveolares, pérdida del retroceso elástico natural y limitación crónica del flujo aéreo.",
                        sols: ["Aceptar hipercapnia permisiva (pH objetivo > 7.20) para evitar la hiperinsuflación dinámica.", "Aplicar PEEP extrínseca para igualar aproximadamente el 80% de la Auto-PEEP intrínseca.", "Administrar broncodilatadores programados."]
                    }
                },
                fr: {
                    "SEVERE ARDS (ACUTE RESPIRATORY DISTRESS)": {
                        desc: "Hypoxémie profonde et réfractaire secondaire à un shunt intrapulmonaire massif et à des poumons sévèrement rigides. Indique des lésions alvéolaires diffuses et un œdème pulmonaire riche en protéines.",
                        sols: ["Mettre en œuvre une ventilation protectrice pulmonaire stricte (Volume Courant 4-6 mL/kg de Poids Idéal).", "Optimiser la PEEP via le tableau ARDSNet PEEP élevée/FiO2.", "Initier le décubitus ventral précoce pendant au moins 16 heures par jour."]
                    },
                    "END-STAGE COPD / EMPHYSEMA": {
                        desc: "Compliance pulmonaire statique anormalement élevée avec résistance accrue des voies aériennes. Indique une destruction sévère des septas alvéolaires, une perte de recul élastique naturel et une limitation chronique du débit d'air.",
                        sols: ["Accepter l'hypercapnie permissive (pH cible > 7.20) pour éviter l'hyperinflation dynamique.", "Appliquer une PEEP extrinsèque pour correspondre à environ 80% de l'auto-PEEP intrinsèque."]
                    }
                }
            };

            if (medicalRepo[lang] && medicalRepo[lang][rawCondition]) {
                descBox.innerText = medicalRepo[lang][rawCondition].desc;
                let htmlElements = '';
                medicalRepo[lang][rawCondition].sols.forEach(s => {
                    htmlElements += `<li class="flex items-start gap-3 bg-emerald-950/20 p-3 rounded-lg border border-emerald-900/30 text-xs text-slate-200"><span class="text-emerald-500 font-bold mt-0.5">⯈</span> <span>${s}</span></li>`;
                });
                solutionsBox.innerHTML = htmlElements;
            }
        }

        setTimeout(initLyra, 200);
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
