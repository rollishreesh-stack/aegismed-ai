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
    .glass-panel { background: rgba(15, 23, 42, 0.45); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); position: relative; z-index: 10; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }
    .glass-input { background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.1); color: #fff; transition: all 0.3s ease; }
    .glass-input:focus { border-color: #22d3ee; box-shadow: 0 0 15px rgba(34, 211, 238, 0.3); }
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
</script>

<!-- INTERNAL INTERNATIONALIZATION GLOBAL CORE -->
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
        lyra_welcome: "Hello, I am Lyra. Tell me to load presets or adjust parameters. I will speak to you natively!",
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
        modify_creds: "Modificar credenciales",
        global_db: "Base de Datos de Patologías",
        preset_desc: "Seleccione una condición para completar los datos hemodinámicos clínicos.",
        select_preset: "-- Seleccione una Patología Clínica --",
        manual_override: "Anulación de Telemetría Manual",
        vent_mechanics: "Mecánica de Ventilación",
        gas_exchange: "Intercambio de Gases",
        btn_scan: "Iniciar escaneo",
        standby_title: "Sistema en Espera",
        standby_desc: "Seleccione un perfil de patología o dé una orden a Lyra.",
        primary_diag: "Diagnóstico Principal de IA",
        physio_breakdown: "Desglose Fisiológico",
        action_plan: "Plan de Acción Clínico",
        abg_analysis: "Análisis de Gases en Sangre",
        blood_ph: "pH en sangre",
        paco2_lbl: "PaCO2",
        hco3_lbl: "HCO3",
        mech_explained: "Mecánica Pulmonar Explicada",
        lung_compliance: "Distensibilidad Pulmonar",
        airway_resistance: "Resistencia de Vías Aéreas",
        dead_space: "Vd/Vt (Espacio Muerto)",
        shunt_fraction: "Fracción de Shunt",
        waveform_analytics: "Análisis de Ondas",
        lyra_title: "ASISTENTE CLINICA VIRTUAL LYRA",
        lyra_placeholder: "Pídele a Lyra que cargue parámetros...",
        lyra_send: "Enviar",
        lyra_welcome: "Hola, soy Lyra. ¡Pídeme que cargue ajustes o modifique parámetros y hablaré contigo directamente!",
        lyra_loaded_preset: "Entendido. Cargando la matriz de simulación para: ",
        lyra_updated_params: "Matriz modificada. Actualizando parámetros: ",
        lyra_not_found: "Comando no reconocido. Intenta con 'cargar SDRA' o 'fijar PEEP en 10'."
    },
    fr: {
        brand: "AERO<span class='text-cyan-400'>LUNG</span>",
        settings: "Paramètres",
        logout: "Déconnexion",
        return_dash: "Retour au Tableau de Bord",
        account_settings: "Paramètres du Compte",
        modify_creds: "Modifier les identifiants",
        global_db: "Base de Données Pathologiques",
        preset_desc: "Sélectionnez une condition pour remplir l'hémodynamique clinique.",
        select_preset: "-- Sélectionner une Pathologie --",
        manual_override: "Contrôle Manuel de la Télémétrie",
        vent_mechanics: "Mécanique de Ventilation",
        gas_exchange: "Échange Gazeux & Labos Sanguins",
        btn_scan: "Initialiser l'analyse",
        standby_title: "Système en Veille",
        standby_desc: "Sélectionnez une pathologie ou commandez Lyra.",
        primary_diag: "Diagnostic Principal par IA",
        physio_breakdown: "Analyse Physiologique",
        action_plan: "Plan d'Action Clinique Requis",
        abg_analysis: "Analyse des Gaz du Sang",
        blood_ph: "pH Sanguin",
        paco2_lbl: "PaCO2",
        hco3_lbl: "HCO3",
        mech_explained: "Mécanique Pulmonaire Expliquée",
        lung_compliance: "Compliance Pulmonaire",
        airway_resistance: "Résistance des Voies Aériennes",
        dead_space: "Vd/Vt (Espace Mort)",
        shunt_fraction: "Fraction de Shunt",
        waveform_analytics: "Analyse des Ondas",
        lyra_title: "ASSISTANTE CLINIQUE VIRTUELLE LYRA",
        lyra_placeholder: "Demandez à Lyra de charger des paramètres...",
        lyra_send: "Envoyer",
        lyra_welcome: "Bonjour, je suis Lyra. Demandez-moi de charger des préréglages ou d'ajuster les paramètres, je vous répondrai à haute voix !",
        lyra_loaded_preset: "Bien reçu. Chargement de la matrice de simulation pour : ",
        lyra_updated_params: "Matrice modifiée. Mise à jour des paramètres : ",
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
        "STABLE PULMONARY HOMEOSTASIS": "HOMEOSTASIS PULMONAR ESTABLE",
        "Respiratory Acidosis": "Acidosis Respiratoria",
        "Metabolic Acidosis": "Acidosis Metabolic",
        "Respiratory Alkalosis": "Alcalosis Respiratoria",
        "Metabolic Alkalosis": "Alcalosis Metabólica",
        "Normal Acid-Base Equilibrium": "Equilibrio Ácido-Base Normal"
    },
    fr: {
        "TENSION PNEUMOTHORAX": "PNEUMOTHORAX SOUS TENSION",
        "STATUS ASTHMATICUS": "CHOC ASTHMATIQUE",
        "MASSIVE PULMONARY EMBOLISM": "EMBOLIE PULMONAIRE MASSIVE",
        "SEVERE ARDS (ACUTE RESPIRATORY DISTRESS)": "SDRA SÉVÈRE (SYNDROME DE DÉTRESSE RESPIRATOIRE AIGUË)",
        "END-STAGE COPD / EMPHYSEMA": "BPCO TERMINALE / EMPHYSÈME",
        "CARDIOGENIC PULMONARY EDEMA": "ŒDÈME PULMONAIRE CARDIOGÉNIQUE",
        "STABLE PULMONARY HOMEOSTASIS": "HOMÉOSTASIE PULMONAIRE STABLE",
        "Respiratory Acidosis": "Acidose Respiratoire",
        "Metabolic Acidosis": "Acidose Métabolique",
        "Respiratory Alkalosis": "Alcalose Respiratoire",
        "Metabolic Alkalosis": "Alcalose Métabolique",
        "Normal Acid-Base Equilibrium": "Équilibre Acido-Basique Normal"
    }
};

const CLINICAL_TEXTS = {
    es: {
        "SEVERE ARDS (ACUTE RESPIRATORY DISTRESS)": {
            desc: "Hipoxemia profunda y refractaria secundaria a un cortocircuito (shunt) intrapulmonar masivo y pulmones gravemente rígidos. Indica daño alveolar difuso y edema pulmonar rico en proteínas.",
            sols: ["Implementar ventilación protectora pulmonar estricta (Volumen Tidal 4-6 mL/kg).", "Optimizar PEEP a través de la tabla de PEEP alto de ARDSNet.", "Iniciar posición prona temprana durante al menos 16 horas al día."]
        },
        "TENSION PNEUMOTHORAX": {
            desc: "Pérdida catastrófica de distensibilidad pulmonar combinada con hipercapnia aguda. Sugiere colapso pulmonar unilateral completo por acumulación de aire en el espacio pleural.",
            sols: ["INMEDIATO: Realizar toracostomía con aguja en el segundo espacio intercostal.", "Preparar inserción urgente de tubo de tórax."]
        },
        "STATUS ASTHMATICUS": {
            desc: "Resistencia críticamente elevada en las vías respiratorias que indica broncoespasmo severo y refractario. Alto riesgo de atrapamiento de aire (Auto-PEEP).",
            sols: ["Administrar Albuterol e Ipratropio nebulizados continuos.", "Disminuir la frecuencia respiratoria para permitir la exhalación completa."]
        },
        "MASSIVE PULMONARY EMBOLISM": {
            desc: "Ventilación de espacio muerto severa (Vd/Vt). Los alvéolos están ventilados pero el flujo sanguíneo está bloqueado por una obstrucción arterial.",
            sols: ["Iniciar anticoagulación sistémica inmediata.", "Considerar trombolíticos si el paciente está inestable."]
        },
        "END-STAGE COPD / EMPHYSEMA": {
            desc: "Distensibilidad estática anormalmente alta con pérdida del retroceso elástico natural y atrapamiento crónico de aire.",
            sols: ["Aceptar hipercapnia permisiva (pH > 7.20) para evitar hiperinsuflación.", "Aplicar PEEP extrínseca a juego con la auto-PEEP."]
        },
        "CARDIOGENIC PULMONARY EDEMA": {
            desc: "Reducción de la distensibilidad pulmonar debido a acumulación de líquido hidrostático secundario a falla ventricular izquierda.",
            sols: ["Administrar diuréticos de asa intravenosos (Furosemida).", "Aplicar PEEP suficiente para desplazar mecánicamente el líquido alvéolar."]
        },
        "STABLE PULMONARY HOMEOSTASIS": {
            desc: "La mecánica ventilatoria, resistencia, distensibilidad y parámetros de intercambio de gases se registran estables y normales.",
            sols: ["Mantener el soporte ventilatorio actual.", "Monitorear la preparación del paciente para el destete."]
        }
    },
    fr: {
        "SEVERE ARDS (ACUTE RESPIRATORY DISTRESS)": {
            desc: "Hypoxémie profonde et réfractaire secondaire à un shunt intrapulmonaire massif et à des poumons sévèrement rigides.",
            sols: ["Mettre en œuvre une ventilation protectrice pulmonaire stricte (Volume Courant 4-6 mL/kg).", "Optimiser la PEEP via le tableau ARDSNet.", "Initier le décubitus ventral précoce (16h/jour)."]
        },
        "TENSION PNEUMOTHORAX": {
            desc: "Perte catastrophique de compliance pulmonaire combinée à une hypercapnie aiguë. Suggère un affaissement pulmonaire unilatéral complet.",
            sols: ["IMMÉDIAT : Effectuer une thoracostomie à l'aiguille au 2ème espace intercostal.", "Préparer l'insertion d'un drain thoracique d'urgence."]
        },
        "STATUS ASTHMATICUS": {
            desc: "Résistance des voies respiratoires extrêmement élevée indiquant un bronchospasme sévère et réfractaire.",
            sols: ["Administrer des nébulisations continues d'Albutérol et d'Ipratropium.", "Diminuer la fréquence respiratoire pour permettre une expiration complète."]
        },
        "MASSIVE PULMONARY EMBOLISM": {
            desc: "Ventilation sévère de l'espace mort (Vd/Vt). Les alvéoles sont ventilées mais le flux sanguin est bloqué.",
            sols: ["Initier une anticoagulation systémique immédiate.", "Envisager des thrombolytiques systémiques en cas d'instabilité."]
        },
        "END-STAGE COPD / EMPHYSEMA": {
            desc: "Compliance pulmonaire statique anormalement élevée avec perte de recul élastique naturel.",
            sols: ["Accepter l'hypercapnie permissive (pH cible > 7.20).", "Appliquer une PEEP extrinsèque pour correspondre à l'auto-PEEP."]
        },
        "CARDIOGENIC PULMONARY EDEMA": {
            desc: "Diminution de la compliance pulmonaire due à une accumulation de liquide hydrostatique secondaire à une insuffisance ventriculaire gauche.",
            sols: ["Administrer des diurétiques de l'anse IV (Furosémide).", "Appliquer une PEEP suffisante pour repousser le liquide hors des alvéoles."]
        },
        "STABLE PULMONARY HOMEOSTASIS": {
            desc: "La mécanique ventilatoire, la résistance, la compliance et les paramètres d'échange gazeux sont normaux.",
            sols: ["Maintenir le support ventilatoire actuel.", "Surveiller la préparation du patient au sevrage."]
        }
    }
};

// LYRA NATIVE CLIENT VOICE SPEAKER SYNCHRONIZER
function lyraSpeak(text, lang) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel(); // Abort tracking voice queue
        const utterance = new SpeechSynthesisUtterance(text);
        if (lang === 'es') utterance.lang = 'es-ES';
        else if (lang === 'fr') utterance.lang = 'fr-FR';
        else utterance.lang = 'en-US';
        utterance.pitch = 1.1;
        utterance.rate = 1.0;
        window.speechSynthesis.speak(utterance);
    }
}

function changeLanguage(lang) {
    localStorage.setItem('selectedLang', lang);
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) {
            if (el.tagName === 'INPUT') el.setAttribute('placeholder', TRANSLATIONS[lang][key]);
            else el.innerHTML = TRANSLATIONS[lang][key];
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
        
        // Dynamic execution of description & solutions translation sync
        const descBox = document.getElementById('ai-description-text');
        const solutionsBox = document.getElementById('ai-solutions-list');
        if (descBox && solutionsBox) {
            if (lang !== 'en' && CLINICAL_TEXTS[lang] && CLINICAL_TEXTS[lang][raw]) {
                descBox.innerText = CLINICAL_TEXTS[lang][raw].desc;
                let html = '';
                CLINICAL_TEXTS[lang][raw].sols.forEach(s => {
                    html += `<li class="flex items-start gap-3 bg-emerald-950/20 p-3 rounded-lg border border-emerald-900/30 text-xs text-slate-200"><span class="text-emerald-500 font-bold mt-0.5">⯈</span> <span>${s}</span></li>`;
                });
                solutionsBox.innerHTML = html;
            } else {
                // Revert to standard fallback parameters template render
                descBox.innerText = descBox.getAttribute('data-orig');
                solutionsBox.innerHTML = solutionsBox.getAttribute('data-orig');
            }
        }
    }
    
    const statusEl = document.getElementById('abg-status-text');
    if (statusEl) {
        const raw = statusEl.getAttribute('data-raw');
        statusEl.innerText = (DYNAMIC_MAPPING[lang] && DYNAMIC_MAPPING[lang][raw]) ? DYNAMIC_MAPPING[lang][raw] : raw;
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
    <div class="glass-panel rounded-3xl p-10 w-full max-w-md text-center shadow-[0_0_40px_rgba(6,182,212,0.15)]">
        <h1 class="text-5xl font-black tracking-tighter text-white mb-2" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
        <p class="text-xs font-mono text-cyan-500/80 uppercase tracking-[0.3em] mb-10">Systematic Authentication</p>
        <form action="/login" method="POST" class="space-y-5 text-left">
            <div><label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1">Architect ID</label><input type="text" name="username" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm" placeholder="Enter ID..." required></div>
            <div><label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 ml-1">Secure Passkey</label><input type="password" name="password" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm" placeholder="••••••••" required></div>
            <button type="submit" class="w-full mt-4 py-4 rounded-xl bg-cyan-600 text-white font-bold text-sm uppercase tracking-[0.2em]">Initialize Secure Uplink</button>
        </form>
    </div>
    {{ COPYRIGHT_FOOTER | safe }}
</body>
"""

SETTINGS_HTML = GLOBAL_CSS + BACKGROUND_SVG + """
<body class="flex items-center justify-center relative flex-col min-h-screen">
    <nav class="glass-panel w-full bg-slate-950/90 py-4 px-6 flex justify-between absolute top-0 z-50">
        <h1 class="text-2xl font-black tracking-tighter text-white" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
        <a href="/dashboard" class="px-4 py-2 rounded-lg bg-slate-800 text-white text-xs font-bold uppercase" data-i18n="return_dash">Return to Dashboard</a>
    </nav>
    <div class="glass-panel rounded-3xl p-10 w-full max-w-lg mt-20">
        <h2 class="text-3xl font-black text-white mb-2 uppercase" data-i18n="account_settings">Account Settings</h2>
        <form action="/settings" method="POST" class="space-y-5 text-left">
            <div><label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2">New ID</label><input type="text" name="new_username" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm"></div>
            <div><label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2">New Passkey</label><input type="password" name="new_password" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm"></div>
            <button type="submit" class="w-full py-4 rounded-xl bg-cyan-600 text-white font-bold text-sm uppercase">Commit Changes</button>
        </form>
    </div>
    {{ COPYRIGHT_FOOTER | safe }}
</body>
"""

DASHBOARD_HTML = GLOBAL_CSS + BACKGROUND_SVG + """
<body class="min-h-screen flex flex-col relative">
    <nav class="glass-panel sticky top-0 z-50 border-b border-slate-800 bg-slate-950/90 shadow-2xl">
        <div class="max-w-[1800px] mx-auto px-6 py-4 flex justify-between items-center">
            <h1 class="text-3xl font-black tracking-tighter text-white" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
            <div class="flex items-center gap-4">
                <select id="lang-selector" onchange="changeLanguage(this.value)" class="bg-slate-900/80 border border-slate-700/50 rounded-lg px-3 py-1.5 text-xs text-white font-mono font-bold cursor-pointer">
                    <option value="en">EN</option>
                    <option value="es">ES</option>
                    <option value="fr">FR</option>
                </select>
                <a href="/settings" class="px-4 py-2 rounded-lg bg-slate-800/80 text-slate-200 text-[10px] font-bold uppercase" data-i18n="settings">Settings</a>
                <a href="/logout" class="px-4 py-2 rounded-lg bg-rose-900/40 text-rose-300 text-[10px] font-bold uppercase" data-i18n="logout">Logout</a>
            </div>
        </div>
    </nav>

    <main class="flex-1 max-w-[1800px] mx-auto w-full p-6 flex flex-col lg:flex-row gap-8 relative z-10 h-full">
        <div class="w-full lg:w-[450px] flex flex-col gap-6 shrink-0">
            <div class="glass-panel rounded-2xl p-5 border-t-2 border-t-cyan-500">
                <h2 class="text-[11px] font-bold uppercase tracking-widest text-cyan-400 mb-2" data-i18n="global_db">Global Pathology Database</h2>
                <select id="preset-dropdown" onchange="if(this.value) loadPreset(this.value);" class="w-full glass-input px-3 py-3 rounded-lg text-sm text-slate-200">
                    <option value="" disabled selected data-i18n="select_preset">-- Select a Clinical Pathology --</option>
                    <option value="healthy">Healthy Baseline</option>
                    <option value="ards">Severe ARDS</option>
                    <option value="copd">End-Stage COPD</option>
                    <option value="asthma">Status Asthmaticus</option>
                    <option value="pneumothorax">Tension Pneumothorax</option>
                    <option value="pe">Massive Pulm Embolism</option>
                    <option value="edema">Cardiogenic Edema</option>
                </select>
            </div>

            <div class="glass-panel rounded-2xl p-5">
                <form id="calc-form" method="POST" action="/dashboard">
                    <h3 class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest border-b border-white/10 pb-2 mb-4" data-i18n="manual_override">Manual Telemetry Override</h3>
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <div><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">Vt (mL)</label><input type="number" name="vt_input" id="vt_input" value="{{ inputs.vt_input|default(500) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                        <div><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">Rate (RR)</label><input type="number" name="rr" id="rr" value="{{ inputs.rr|default(14) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                        <div><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">PIP</label><input type="number" name="pip" id="pip" value="{{ inputs.pip|default(20) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                        <div><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">Pplat</label><input type="number" name="pplat" id="pplat" value="{{ inputs.pplat|default(14) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                        <div><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">PEEP</label><input type="number" name="peep" id="peep" value="{{ inputs.peep|default(5) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                        <div><label class="text-[9px] font-bold text-slate-500 uppercase block mb-1">FiO2 %</label><input type="number" name="fio2" id="fio2" value="{{ inputs.fio2|default(30) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                        <input type="hidden" name="peak_flow" id="peak_flow" value="{{ inputs.peak_flow|default(60) }}">
                        <input type="hidden" name="ie_ratio" id="ie_ratio" value="{{ inputs.ie_ratio|default(2.0) }}">
                        <input type="hidden" name="cao2" id="cao2" value="{{ inputs.cao2|default(19.8) }}">
                        <input type="hidden" name="cvo2" id="cvo2" value="{{ inputs.cvo2|default(14.8) }}">
                        <input type="hidden" name="cco2" id="cco2" value="{{ inputs.cco2|default(20.4) }}">
                        <input type="hidden" name="peco2" id="peco2" value="{{ inputs.peco2|default(28) }}">
                        <input type="hidden" name="vco2" id="vco2" value="{{ inputs.vco2|default(200) }}">
                        <input type="hidden" name="hco3_input" id="hco3_input" value="{{ inputs.hco3_input|default(24) }}">
                    </div>
                    <button type="submit" class="w-full py-3 rounded-xl bg-cyan-600 text-white font-bold text-xs uppercase" data-i18n="btn_scan">Initialize Matrix Scan</button>
                </form>
            </div>

            <!-- LYRA TALKING AUDIO ASSISTANT PANEL -->
            <div class="glass-panel rounded-2xl flex flex-col border-t-2 border-t-amber-500">
                <div class="p-4 border-b border-white/10 bg-slate-950/40 rounded-t-2xl">
                    <h3 class="text-[11px] font-black text-amber-400 uppercase tracking-widest" data-i18n="lyra_title">LYRA VIRTUAL CLINICAL ASSISTANT</h3>
                </div>
                <div id="lyra-chat-box" class="p-4 h-48 overflow-y-auto space-y-3 text-xs font-mono bg-black/30"></div>
                <div class="p-3 border-t border-white/10 flex gap-2">
                    <input type="text" id="lyra-input" class="flex-1 glass-input px-3 py-2 rounded-lg text-xs font-mono" placeholder="Ask Lyra to load parameters..." data-i18n="lyra_placeholder" onkeydown="if(event.key === 'Enter') sendLyraMessage();">
                    <button onclick="sendLyraMessage()" class="px-4 py-2 bg-amber-600 text-white rounded-lg font-bold text-xs uppercase" data-i18n="lyra_send">Send</button>
                </div>
            </div>
        </div>

        <div class="flex-1 flex flex-col gap-6 w-full min-w-0">
            {% if not sim_data %}
            <div class="glass-panel rounded-3xl flex-1 flex flex-col items-center justify-center min-h-[500px]">
                <h3 class="text-2xl font-black text-white mb-2 uppercase" data-i18n="standby_title">System Standby</h3>
                <p class="text-sm text-slate-400 font-mono" data-i18n="standby_desc">Select a pathology profile from the left dropdown matrix.</p>
            </div>
            {% else %}
            <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <div class="glass-panel p-8 rounded-2xl border-l-4 border-l-cyan-400">
                    <h3 class="text-[11px] text-cyan-400 font-black uppercase tracking-widest mb-2" data-i18n="primary_diag">Primary AI Diagnosis</h3>
                    <div id="ai-condition-text" data-raw="{{ sim_data.ai_condition }}" class="text-3xl font-black text-white mb-5 uppercase">{{ sim_data.ai_condition }}</div>
                    
                    <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 border-b border-white/10 pb-1" data-i18n="physio_breakdown">Physiological Breakdown</div>
                    <div class="text-sm text-slate-300 bg-black/40 p-4 rounded-lg border mb-5" id="ai-description-text" data-orig="{{ sim_data.ai_description }}">
                        {{ sim_data.ai_description }}
                    </div>

                    <div class="text-[10px] font-bold text-emerald-400 uppercase tracking-widest mb-2 border-b border-white/10 pb-1" data-i18n="action_plan">Required Clinical Action Plan</div>
                    <ul class="space-y-2" id="ai-solutions-list" data-orig="{% for solution in sim_data.ai_solutions %}<li class='flex items-start gap-3 bg-emerald-950/20 p-3 rounded-lg border text-xs text-slate-200'><span class='text-emerald-500 font-bold'>⯈</span> <span>{{ solution }}</span></li>{% endfor %}">
                        {% for solution in sim_data.ai_solutions %}
                        <li class="flex items-start gap-3 bg-emerald-950/20 p-3 rounded-lg border border-emerald-900/30 text-xs text-slate-200">
                            <span class="text-emerald-500 font-bold mt-0.5">⯈</span> <span>{{ solution }}</span>
                        </li>
                        {% endfor %}
                    </ul>
                </div>

                <div class="glass-panel p-8 rounded-2xl flex flex-col justify-center">
                    <h3 class="text-[11px] text-purple-400 font-black uppercase tracking-widest mb-6 text-center" data-i18n="abg_analysis">Arterial Blood Gas Analysis</h3>
                    <div class="grid grid-cols-3 gap-2 mb-6 bg-black/40 p-6 rounded-2xl text-center">
                        <div><span class="text-[10px] text-slate-500 font-bold block mb-2" data-i18n="blood_ph">Blood pH</span><span class="text-3xl font-black font-mono text-emerald-400">{{ sim_data.ph }}</span></div>
                        <div><span class="text-[10px] text-slate-500 font-bold block mb-2" data-i18n="paco2_lbl">PaCO2</span><span class="text-3xl font-black font-mono text-amber-400">{{ sim_data.paco2 }}</span></div>
                        <div><span class="text-[10px] text-slate-500 font-bold block mb-2" data-i18n="hco3_lbl">HCO3</span><span class="text-3xl font-black font-mono text-purple-400">{{ sim_data.hco3 }}</span></div>
                    </div>
                    <div id="abg-status-text" data-raw="{{ sim_data.acid_base_status }}" class="text-sm font-bold text-white text-center py-3 rounded-lg border border-purple-800 uppercase">{{ sim_data.acid_base_status }}</div>
                </div>
            </div>

            <div class="glass-panel p-6 rounded-2xl">
                <h3 class="text-[11px] text-slate-400 font-black uppercase tracking-widest mb-4 border-b border-white/10 pb-2" data-i18n="mech_explained">Pulmonary Mechanics Explained</h3>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5">
                        <span class="text-[10px] text-cyan-400 font-bold block mb-2" data-i18n="lung_compliance">Lung Compliance</span>
                        <div class="text-3xl font-black text-white font-mono">{{ sim_data.compliance }}</div>
                    </div>
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5">
                        <span class="text-[10px] text-rose-400 font-bold block mb-2" data-i18n="airway_resistance">Airway Resistance</span>
                        <div class="text-3xl font-black text-white font-mono">{{ sim_data.resistance }}</div>
                    </div>
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5">
                        <span class="text-[10px] text-amber-400 font-bold block mb-2" data-i18n="dead_space">Vd/Vt (Dead Space)</span>
                        <div class="text-3xl font-black text-white font-mono">{{ sim_data.dead_space }}%</div>
                    </div>
                    <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5">
                        <span class="text-[10px] text-emerald-400 font-bold block mb-2" data-i18n="shunt_fraction">Shunt Fraction</span>
                        <div class="text-3xl font-black text-white font-mono">{{ sim_data.shunt }}%</div>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </main>
    {{ COPYRIGHT_FOOTER | safe }}

    <script>
        const PRESETS = {
            healthy:      {vt: 500, rr: 14, pip: 20, pplat: 14, peep: 5,  fio2: 30},
            ards:         {vt: 350, rr: 28, pip: 38, pplat: 32, peep: 14, fio2: 80},
            copd:         {vt: 520, rr: 10, pip: 32, pplat: 16, peep: 5,  fio2: 35},
            asthma:       {vt: 450, rr: 12, pip: 45, pplat: 17, peep: 5,  fio2: 40},
            pneumothorax: {vt: 300, rr: 30, pip: 45, pplat: 40, peep: 5,  fio2: 90},
            pe:           {vt: 500, rr: 28, pip: 22, pplat: 15, peep: 5,  fio2: 50},
            edema:        {vt: 400, rr: 24, pip: 30, pplat: 25, peep: 12, fio2: 50}
        };

        function loadPreset(type) {
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

        function initLyra() {
            const box = document.getElementById('lyra-chat-box');
            if(!box) return;
            const currentLang = localStorage.getItem('selectedLang') || 'en';
            box.innerHTML = `<div class="text-amber-400 mb-0.5">🤖 Lyra:</div><div class="text-slate-300 mb-2">${TRANSLATIONS[currentLang]['lyra_welcome']}</div>`;
            lyraSpeak(TRANSLATIONS[currentLang]['lyra_welcome'], currentLang);
        }

        function sendLyraMessage() {
            const input = document.getElementById('lyra-input');
            if (!input || !input.value.trim()) return;
            const text = input.value.trim();
            input.value = '';
            
            const box = document.getElementById('lyra-chat-box');
            box.innerHTML += `<div class="text-cyan-400 mt-2 mb-0.5">👤 You:</div><div class="text-slate-200 mb-2">${text}</div>`;
            box.scrollTop = box.scrollHeight;
            
            setTimeout(() => { processLyraCommand(text); }, 300);
        }

        function processLyraCommand(msg) {
            const box = document.getElementById('lyra-chat-box');
            const currentLang = localStorage.getItem('selectedLang') || 'en';
            const norm = msg.toLowerCase();
            
            let matched = null;
            if (norm.includes('healthy') || norm.includes('saludable') || norm.includes('sain')) matched = 'healthy';
            else if (norm.includes('ards') || norm.includes('sdra')) matched = 'ards';
            else if (norm.includes('copd') || norm.includes('epoc') || norm.includes('bpco')) matched = 'copd';
            else if (norm.includes('asthma') || norm.includes('asma') || norm.includes('asthme')) matched = 'asthma';
            else if (norm.includes('pneumothorax') || norm.includes('neumotorax')) matched = 'pneumothorax';
            else if (norm.includes('embolia') || norm.includes('embolism') || norm.includes('pe')) matched = 'pe';
            else if (norm.includes('edema') || norm.includes('oedeme')) matched = 'edema';

            if (matched) {
                const responseText = TRANSLATIONS[currentLang]['lyra_loaded_preset'] + matched.toUpperCase();
                box.innerHTML += `<div class="text-amber-400 mb-0.5">🤖 Lyra:</div><div class="text-emerald-400 mb-2">${responseText}</div>`;
                box.scrollTop = box.scrollHeight;
                lyraSpeak(responseText, currentLang);
                setTimeout(() => { loadPreset(matched); }, 1200);
                return;
            }

            // Cross-lingual exact bindings mapping
            let binds = [];
            const expressions = {
                vt_input: /(?:vt|volume|volumen)\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                rr: /(?:rr|rate|frecuencia|fréquence)\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                pip: /pip\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                peep: /peep\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                pplat: /pplat\s*(?:to|en|à|a|=)?\s*(\d+)/i,
                fio2: /fio2\s*(?:to|en|à|a|=)?\s*(\d+)/i
            };

            for (const [key, regex] of Object.entries(expressions)) {
                const match = norm.match(regex);
                if (match && match[1]) {
                    document.getElementById(key).value = match[1];
                    binds.push(`${key.toUpperCase()} = ${match[1]}`);
                }
            }

            if (binds.length > 0) {
                const responseText = TRANSLATIONS[currentLang]['lyra_updated_params'] + binds.join(', ');
                box.innerHTML += `<div class="text-amber-400 mb-0.5">🤖 Lyra:</div><div class="text-emerald-400 mb-2">${responseText}</div>`;
                box.scrollTop = box.scrollHeight;
                lyraSpeak(responseText, currentLang);
                setTimeout(() => { document.getElementById('calc-form').submit(); }, 1200);
                return;
            }

            box.innerHTML += `<div class="text-amber-400 mb-0.5">🤖 Lyra:</div><div class="text-slate-300 mb-2">${TRANSLATIONS[currentLang]['lyra_not_found']}</div>`;
            lyraSpeak(TRANSLATIONS[currentLang]['lyra_not_found'], currentLang);
            box.scrollTop = box.scrollHeight;
        }

        setTimeout(initLyra, 400);
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
    flash("ACCESS DENIED.")
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
