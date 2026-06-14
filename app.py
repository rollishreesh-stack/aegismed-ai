import os
import math
import json
import sqlite3
import traceback
from flask import Flask, request, redirect, url_for, session, flash, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_absolute_sync_2026")
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
# 2. PATHOLOGY DATABASE WITH DEEP CLINICAL DETAIL
# ==========================================

DISEASE_PROFILES = {
    "healthy": {
        "condition": "Stable Pulmonary Homeostasis",
        "description": "The patient demonstrates stable pulmonary homeostasis with intact ventilatory mechanics, optimal airway caliber, and unimpeded alveolar-capillary gas exchange. Thoracic cage compliance and lung parenchymal elasticity are within normal physiological bounds. There is no evidence of intrapulmonary shunting, airflow obstruction, or diffusion defects. The work of breathing is minimal, and the neuromuscular pump is fully functional, maintaining an ideal acid-base equilibrium.",
        "solutions": [
            "Maintain current baseline respiratory support and ambient room air settings.",
            "Continuously monitor spontaneous breathing trials (SBT) if mechanical ventilation is active.",
            "Assess readiness for immediate extubation or weaning protocols based on clinical criteria.",
            "Perform routine pulmonary hygiene and check vital sign trends every 4 hours."
        ]
    },
    "ards": {
        "condition": "Severe Acute Respiratory Distress Syndrome",
        "description": "The clinical picture is highly indicative of severe acute respiratory distress syndrome (ARDS), characterized by diffuse alveolar damage, profound inflammatory exudate accumulation, and surfactant inactivation. This results in critically low static lung compliance and massive intrapulmonary right-to-left shunting. Refractory hypoxemia is driven by alveolar flooding and atelectasis, rendering large lung zones completely unventilated yet perfused, vastly increasing the alveolar-arterial oxygen gradient.",
        "solutions": [
            "Implement ultra-protective lung ventilation targeting a tidal volume of 4-6 mL/kg of Predicted Body Weight (PBW).",
            "Maintain plateau pressures strictly below 30 cmH2O and driving pressure below 15 cmH2O to prevent barotrauma.",
            "Titrate high positive end-expiratory pressure (PEEP) utilizing the ARDSNet high-PEEP table to recruit collapsed alveoli.",
            "Initiate early prone positioning for 16-24 hours per day to optimize ventilation-perfusion (V/Q) matching.",
            "Consider continuous neuromuscular blockade (paralysis) to eliminate patient-ventilator dyssynchrony.",
            "Institute a strict, conservative fluid management strategy to minimize secondary pulmonary hydrostatic edema."
        ]
    },
    "copd": {
        "condition": "End-Stage COPD / Emphysema Exacerbation",
        "description": "The presentation reflects severe airflow obstruction and parenchymal destruction consistent with an acute exacerbation of end-stage chronic obstructive pulmonary disease (COPD) and emphysema. Loss of elastic recoil and terminal airway collapse during expiration cause critical dynamic hyperinflation and air trapping. This manifests as highly elevated airway resistance and the generation of intrinsic positive end-expiratory pressure (Auto-PEEP), which severely increases the mechanical work required to trigger a breath and leads to chronic respiratory acidosis with metabolic compensation.",
        "solutions": [
            "Administer continuous or frequent scheduled nebulized short-acting beta-agonists (Albuterol) and anticholinergics (Ipratropium).",
            "Initiate systemic intravenous corticosteroids (e.g., Methylprednisolone 40-60mg) to reduce bronchial mucosal inflammation.",
            "Apply external PEEP cautiously, titrating to approximately 70-80% of measured Auto-PEEP to reduce the work of triggering.",
            "Prolong the expiratory time by reducing the respiratory rate and increasing the peak inspiratory flow rate.",
            "Target a permissive hypercapnia strategy, accepting an elevated PaCO2 as long as arterial pH remains above 7.20.",
            "Maintain a strict oxygenation target (SpO2 88-92%) to safeguard the patient's hypoxic respiratory drive."
        ]
    },
    "asthma": {
        "condition": "Status Asthmaticus",
        "description": "This presentation represents status asthmaticus—an acute, life-threatening bronchospastic crisis refractory to initial conventional therapy. Severe smooth muscle constriction, bronchial wall edema, and tenacious mucus plugging create extreme airway resistance. Expiratory airflow is critically choked, precipitating rapid dynamic hyperinflation and severe air trapping. The mechanical burden threatens respiratory muscle fatigue, progressing from an initial respiratory alkalosis to a catastrophic, uncompensated respiratory and metabolic acidosis.",
        "solutions": [
            "Initiate continuous nebulized Albuterol combined with scheduled hourly Ipratropium bromide.",
            "Administer immediate systemic high-dose corticosteroids intravenously (e.g., Methylprednisolone 60-125mg).",
            "Provide intravenous Magnesium Sulfate (2g infused over 20 minutes) to induce rapid bronchial smooth muscle relaxation.",
            "Optimize ventilator settings to allow a prolonged expiratory phase (low respiratory rate, high inspiratory flow, I:E ratio 1:4 or greater).",
            "Monitor closely for auto-PEEP, barotrauma, and hemodynamic collapse due to increased intrathoracic pressure.",
            "Prepare for continuous intravenous bronchodilator infusions or inhaled volatile anesthetics if the condition remains refractory."
        ]
    },
    "fibrosis": {
        "condition": "Advanced Pulmonary Fibrosis Exacerbation",
        "description": "The clinical markers indicate advanced idiopathic pulmonary fibrosis, a chronic fibrosing interstitial pneumonia causing architectural distortion and dense parenchymal scarring. Lung tissue is profoundly stiff and non-compliant, severely restricting lung volumes. The alveolar-capillary membrane is significantly thickened, drastically impairing diffusion capacity and causing exertional hypoxemia. Gas exchange is limited by restrictive mechanics, where even small tidal volumes generate high plateau pressures.",
        "solutions": [
            "Utilize low tidal volume ventilation strategies carefully adjusted for a severe restrictive defect.",
            "Maintain plateau pressures strictly below 30 cmH2O to prevent barotrauma to fragile, scarred parenchymal tissues.",
            "Titrate PEEP with extreme caution, as high pressures may cause alveolar overdistension without recruiting fibrotic tissue.",
            "Provide high-flow supplemental oxygen therapy to compensate for severe alveolar-capillary diffusion barriers.",
            "Evaluate the patient for an acute exacerbation of interstitial lung disease (AE-ILD) and consider pulse-dose methylprednisolone.",
            "Maintain an optimized fluid balance to avoid any superimposed hydrostatic pulmonary edema."
        ]
    },
    "pe": {
        "condition": "Massive Pulmonary Embolism",
        "description": "The presentation represents a catastrophic, massive pulmonary embolism causing acute mechanical obstruction of the pulmonary arterial bed. This creates an extreme alveolar dead-space (Vd/Vt) anomaly where substantial portions of the lung are well-ventilated but completely unperfused. The sudden increase in pulmonary vascular resistance triggers acute right ventricular (RV) afterload strain, leading to RV dilation, systemic hypotension, severe ventilation-perfusion mismatch, and critical tissue hypoxia.",
        "solutions": [
            "Initiate immediate systemic anticoagulation with an intravenous Unfractionated Heparin bolus followed by a continuous infusion.",
            "Evaluate candidacy for systemic thrombolytic therapy (e.g., alteplase) or catheter-directed embolectomy if hemodynamically unstable.",
            "Provide cautious vasopressor support (Norepinephrine or Epinephrine) to maintain systemic blood pressure and RV perfusion.",
            "Avoid aggressive fluid resuscitation, as volume overloading the failing right ventricle can worsen septal shift and decrease cardiac output.",
            "Deliver 100% supplemental high-flow oxygen to promote pulmonary vasodilation and minimize hypoxic vasoconstriction.",
            "Avoid positive pressure ventilation if possible; if required, keep airway pressures extremely low to protect RV afterload."
        ]
    },
    "pneumonia": {
        "condition": "Severe Lobar Pneumonia",
        "description": "The patient exhibits severe lobar pneumonia, characterized by acute inflammatory consolidation of the alveolar spaces with purulent exudate, red blood cells, and fibrin. This localized alveolar filling prevents ventilation of the affected segments while perfusion persists, creating a severe localized right-to-left intrapulmonary shunt. The resulting ventilation-perfusion mismatch causes marked hypoxemia and increases the work of breathing, coupled with systemic signs of infection and tissue inflammation.",
        "solutions": [
            "Initiate empiric broad-spectrum intravenous antibiotic therapy within 1 hour of presentation (e.g., Beta-lactam plus Macrolide or Fluoroquinolar).",
            "Implement aggressive pulmonary hygiene, including frequent suctioning, chest physiotherapy, and therapeutic mobilization.",
            "Utilize moderate PEEP (8-12 cmH2O) to recruit atelectatic alveoli adjacent to the consolidation zone.",
            "Position the patient 'good lung down' to optimize gravity-dependent blood flow to better-ventilated lung regions.",
            "Provide targeted fluid resuscitation guided by hemodynamic monitoring to address sepsis without worsening alveolar flooding.",
            "Monitor serial inflammatory markers, lactic acid, and chest radiographs to evaluate treatment efficacy."
        ]
    },
    "neuro": {
        "condition": "Neuromuscular Pump Failure",
        "description": "The data demonstrates acute neuromuscular pump failure, where the intrinsic mechanics of the lung parenchyma and airways are normal, but the mechanical apparatus of ventilation is failing. Impaired neural drive or diaphragmatic weakness leads to a critical drop in minute ventilation. This failure to clear metabolic carbon dioxide results in progressive hypercapnic respiratory failure, respiratory acidosis, and secondary micro-atelectasis due to a chronic lack of deep sigh breaths.",
        "solutions": [
            "Provide immediate full mechanical ventilatory support (Volume Control or Pressure Support) to assume the work of breathing.",
            "Perform serial measurements of Negative Inspiratory Force (NIF), Vital Capacity (VC), and Maximal Inspiratory Pressure (MIP).",
            "Investigate and treat the underlying etiology (e.g., Guillain-Barré flare, Myasthenia Gravis crisis, ALS progression, or toxin exposure).",
            "Initiate aggressive pulmonary toilet and assisted cough techniques to clear secretions and prevent secondary hypostatic pneumonia.",
            "Maintain strict aspiration precautions and evaluate swallowing function before any oral intake.",
            "Avoid respiratory depressant medications (e.g., sedatives, narcotics) unless the airway is fully secured."
        ]
    },
    "obesity": {
        "condition": "Obesity Hypoventilation Syndrome (OHS)",
        "description": "The physiological parameters match Obesity Hypoventilation Syndrome (Pickwickian syndrome). Extreme adiposity on the chest wall and abdomen acts as a severe restrictive load, drastically reducing chest wall compliance. This extrinsic load increases intra-abdominal pressure, elevates the diaphragm, and causes widespread basal micro-atelectasis. The increased respiratory workload leads to chronic nocturnal hypoventilation, blunted central respiratory drive, diurnal hypercapnia, and secondary polycythemia.",
        "solutions": [
            "Utilize high baseline PEEP (12-16 cmH2O) to counteract extrinsic chest wall weight and recruit collapsed basal alveoli.",
            "Position the patient in a reverse Trendelenburg or semi-fowler's position to relieve diaphragmatic pressure from abdominal mass.",
            "Calculate all ventilator tidal volumes strictly based on Ideal Body Weight (IBW) rather than actual body weight.",
            "Transition to Non-Invasive Positive Pressure Ventilation (BiPAP) with high expiratory pressures during periods of stability.",
            "Monitor for signs of pulmonary hypertension and right ventricular failure (cor pulmonale) secondary to chronic hypoxia.",
            "Implement a controlled, long-term multidisciplinary weight management and nutritional support plan."
        ]
    },
    "pneumothorax": {
        "condition": "Tension Pneumothorax",
        "description": "This is a catastrophic, acute clinical emergency representing a tension pneumothorax. A one-way valve leak in the visceral or parietal pleura allows air to enter the pleural space during inspiration but prevents its escape during expiration. The progressive accumulation of trapped air creates positive intrapleural pressure, completely collapsing the ipsilateral lung, shifting the mediastinum, compressing the vena cava, and causing immediate hemodynamic shock and severe hypoxemia.",
        "solutions": [
            "PERFORM IMMEDIATE needle decompression using a large-bore angiocatheter in the 2nd intercostal space at the midclavicular line.",
            "Prepare immediately for the insertion of a formal tube thoracostomy (chest tube) connected to a water-seal suction system.",
            "Disconnect the patient briefly from positive pressure ventilation if hemodynamic collapse is imminent to reduce intrathoracic pressure.",
            "Administer 100% supplemental oxygen to accelerate the reabsorption of intrapleural nitrogen.",
            "Obtain a stat post-procedure portable chest X-ray to confirm lung re-expansion and correct tube placement.",
            "Monitor chest tube drainage output and check the system for persistent air leaks or fluid blockages."
        ]
    },
    "edema": {
        "condition": "Acute Cardiogenic Pulmonary Edema",
        "description": "The presentation is classic for acute cardiogenic pulmonary edema, driven by a rapid rise in left ventricular end-diastolic pressure (LVEDP) and secondary pulmonary venous hypertension. This elevates capillary hydrostatic pressure above plasma oncotic pressure, forcing fluid across the alveolar-capillary barrier into the interstitium and alveoli. The result is rapid alveolar flooding, lost compliance, severe V/Q mismatch, and an exhausting workload of breathing.",
        "solutions": [
            "Apply immediate Non-Invasive Positive Pressure Ventilation (CPAP or BiPAP) to increase alveolar pressure and drive fluid back into the vasculature.",
            "Administer rapid-acting intravenous loop diuretics (e.g., Furosemide) to reduce circulating intravascular volume.",
            "Initiate intravenous Nitroglycerin titration to decrease preload and afterload, reducing the workload on the failing left ventricle.",
            "Provide supplemental oxygen to maintain adequate tissue oxygenation while active diuresis takes effect.",
            "Obtain an urgent 12-lead ECG, troponins, and an echocardiogram to evaluate for acute myocardial infarction or structural dysfunction.",
            "Monitor urine output, serum electrolytes, and renal function closely during aggressive fluid clearance."
        ]
    },
    "anaphylaxis": {
        "condition": "Acute Severe Laryngospasm / Anaphylaxis",
        "description": "This critical state represents an upper airway emergency secondary to anaphylaxis or profound laryngospasm. IgE-mediated mast cell degranulation has triggered massive angioedema of the epiglottis, vocal cords, and subglottic tissues. This creates near-total upper airway occlusion, resulting in high airway resistance, extreme inspiratory stridor, profound patient panic, and rapid, life-threatening asphyxiation.",
        "solutions": [
            "Administer Intramuscular Epinephrine (0.3 - 0.5 mg, 1:1000) immediately in the anterolateral thigh; repeat every 5-15 minutes if necessary.",
            "Establish an advanced airway via direct laryngoscopy or video-assisted intubation using a smaller-diameter endotracheal tube.",
            "Prepare for an emergency surgical airway (cricothyroidotomy) if upper airway edema prevents endotracheal tube passage.",
            "Administer adjunctive intravenous medications: Corticosteroids (Methylprednisolone), H1-antagonists (Diphenhydramine), and H2-antagonists.",
            "Infuse rapid intravenous crystalloid fluid boluses to counteract widespread vasodilation and distributive shock.",
            "Maintain continuous monitoring of oxygenation, heart rate, and blood pressure in a high-acuity care unit."
        ]
    },
    "copd_overlap": {
        "condition": "COPD-Asthma Overlap Syndrome (ACOS)",
        "description": "The data confirms COPD-Asthma Overlap Syndrome (ACOS), a complex obstructive condition featuring fixed expiratory airflow limitation alongside marked airway hyperresponsiveness. The pathophysiology combines parenchymal emphysema with active, variable eosinophilic/neutrophilic airway inflammation. This results in highly unpredictable airway resistance fluctuations, persistent air trapping, and frequent acute respiratory failures.",
        "solutions": [
            "Prescribe a combined long-term maintenance regimen consisting of an Inhaled Corticosteroid (ICS) and a Long-Acting Beta-Agonist (LABA).",
            "Utilize short-acting bronchodilator rescue therapy (Albuterol/Ipratropium) for acute changes in respiratory status.",
            "Tailor positive pressure ventilation settings to accommodate both high resistance and the need for prolonged expiration.",
            "Obtain peripheral blood eosinophil counts and serum IgE levels to guide potential biological targeted therapies.",
            "Incorporate a regular, comprehensive pulmonary rehabilitation program once the acute exacerbation is fully resolved.",
            "Educate the patient extensively on trigger avoidance, correct inhaler technique, and an early-intervention action plan."
        ]
    },
    "sars_cov_2": {
        "condition": "Severe COVID-19 Pneumonitis",
        "description": "The clinical picture demonstrates severe COVID-19 pneumonitis, characterized by extensive alveolar epithelial cell injury, intense local hyper-inflammation (cytokine release), and widespread pulmonary microvascular thrombosis. This creates an atypical lung injury pattern featuring severe hypoxemia alongside initially preserved lung compliance, which later transitions into standard, low-compliance ARDS due to progressive fibroproliferative remodeling.",
        "solutions": [
            "Administer systemic corticosteroids (e.g., Dexamethasone 6mg daily) to mitigate the systemic inflammatory cascade.",
            "Initiate early therapeutic or prophylactic-dose low-molecular-weight heparin to address the high risk of microvascular thrombosis.",
            "Utilize High-Flow Nasal Cannula (HFNC) or non-invasive ventilation with an early, closely-monitored awake prone positioning protocol.",
            "Monitor the ROX index closely; execute a timely, non-delayed endotracheal intubation if the patient shows signs of self-induced lung injury (P-SILI).",
            "Consider targeted immunomodulatory agents (e.g., Tocilizumab or Baricitinib) if inflammatory markers are rapidly escalating.",
            "Implement a fluid-restrictive strategy to prevent worsening alveolar edema while ensuring adequate organ perfusion."
        ]
    },
    "trali": {
        "condition": "Transfusion-Related Acute Lung Injury (TRALI)",
        "description": "The presentation represents Transfusion-Related Acute Lung Injury (TRALI), an acute immune-mediated reaction triggered by the sequestration and activation of recipient neutrophils within the pulmonary microvasculature. This activation causes extensive endothelial damage and profound capillary leaking, resulting in non-cardiogenic pulmonary edema, diffuse alveolar flooding, and severe acute hypoxemia occurring within 6 hours of blood product administration.",
        "solutions": [
            "Stop the transfusion of all blood products immediately and notify the blood bank to quarantine donor units.",
            "Provide immediate supportive respiratory care utilizing a lung-protective mechanical ventilation strategy.",
            "Avoid empirical diuretic therapy unless concurrent volume overload is definitively proven, as TRALI patients are often intravascularly volume-depleted.",
            "Support systemic blood pressure with cautious crystalloid fluid administration or vasopressors if distributive shock is present.",
            "Monitor arterial blood gases and chest radiographs serially to track resolution, which typically occurs within 48-96 hours.",
            "Report the case formally to the hemovigilance system to ensure donor screening for leukocyte antibodies."
        ]
    },
    "aco": {
        "condition": "Acute Circulatory Collapse / Obstructive Shock",
        "description": "The patient's values point to acute circulatory collapse presenting as obstructive shock. Severe restriction to cardiac filling or outflow creates global tissue hypoperfusion, critical oxygen delivery ($DO_2$) deficits, and severe systemic metabolic lactic acidosis. The respiratory system attempts to compensate through an exhausting hyperventilatory response, leading to rapid respiratory muscle fatigue and multi-organ dysfunction syndrome.",
        "solutions": [
            "Identify and rapidly reverse the definitive source of mechanical obstruction (e.g., cardiac tamponade, tension pneumothorax, pulmonary embolus).",
            "Initiate an empirical vasopressor infusion (Norepinephrine) to maintain critical coronary and cerebral perfusion pressures.",
            "Perform an urgent bedside point-of-care ultrasound (POCUS) to evaluate right/left ventricular function and pericardial space.",
            "Maximize supplemental oxygen delivery to optimize arterial oxygen saturation and support tissue cellular metabolism.",
            "Minimize positive pressure ventilation settings, as high intrathoracic pressures further impair venous return and worsen cardiovascular collapse.",
            "Establish large-bore intravenous access or central venous access for rapid resuscitation and reliable drug delivery."
        ]
    },
    "emphysema": {
        "condition": "Advanced Centrilobular Emphysema",
        "description": "The presentation confirms advanced centrilobular emphysema, characterized by the irreversible destruction of alveolar walls and permanent enlargement of airspaces distal to the terminal bronchioles. This structural collapse destroys the pulmonary capillary bed and eliminates elastic recoil, causing severe expiratory flow limitation, permanent air trapping, a markedly increased residual volume, and chronic ventilation-perfusion mismatching.",
        "solutions": [
            "Optimize regular maintenance therapy utilizing long-acting anticholinergics (LAMA) and long-acting beta-agonists (LABA).",
            "Provide long-term home oxygen therapy (LTOT) if the baseline PaO2 is less than 55 mmHg or SpO2 is less than 88%.",
            "Implement a structured pulmonary rehabilitation program to improve exercise tolerance and peripheral muscle efficiency.",
            "Perform regular screens for secondary pulmonary hypertension and right-sided heart failure via echocardiography.",
            "Evaluate candidacy for advanced lung volume reduction interventions (e.g., endobronchial valves or surgical LVRS).",
            "Ensure up-to-date immunizations against pneumococcus, influenza, and respiratory viruses to minimize life-threatening exacerbations."
        ]
    },
    "interstitial": {
        "condition": "Nonspecific Interstitial Pneumonia (NSIP)",
        "description": "The clinical markers indicate Nonspecific Interstitial Pneumonia (NSIP), an interstitial lung disease featuring uniform alveolar wall thickening and variable degrees of cellular inflammation or dense collagen fibrosis. This creates a severe restrictive ventilatory pattern with reduced total lung capacity, increased lung stiffness, and a significant reduction in gas diffusion across the fibrotic alveolar-capillary barrier.",
        "solutions": [
            "Initiate systemic immunosuppressive therapy with oral or intravenous corticosteroids (e.g., Prednisone) as the primary treatment.",
            "Consider adjunctive steroid-sparing immunosuppressive agents (e.g., Mycophenolate Mofetil or Azathioprine) for long-term maintenance.",
            "Monitor pulmonary function tests (PFTs) and high-resolution chest CT scans every 3-6 months to assess response to therapy.",
            "Provide continuous high-flow supplemental oxygen as required to correct chronic hypoxemia and reduce pulmonary vascular pressure.",
            "Incorporate anti-fibrotic agents (e.g., Nintedanib) if a progressive, fibrosing phenotype becomes evident over time.",
            "Screen for secondary connective tissue diseases, as NSIP is frequently an early manifestation of autoimmune pathology."
        ]
    },
    "cyber_trauma": {
        "condition": "Blast Injury / Pulmonary Contusion",
        "description": "This critical presentation indicates a severe blast injury with secondary pulmonary contusion. High-energy shockwaves passing through lung tissue have caused parenchymal laceration, alveolar tear, and extensive intra-alveolar hemorrhage. The resulting localized non-cardiogenic pulmonary edema, severe ventilation-perfusion mismatching, and localized surfactant wash-out cause progressive lung consolidation and severe hypoxemia.",
        "solutions": [
            "Implement a strict lung-protective ventilation protocol to minimize further mechanical trauma to damaged alveolar structures.",
            "Maintain targeted volume-restrictive fluid management to prevent exacerbating capillary leaks within the contused tissue.",
            "Provide aggressive airway clearance to remove blood, cellular debris, and secretions from the tracheobronchial tree.",
            "Utilize localized PEEP titration to splint open damaged, atelectatic alveoli without over-distending healthy lung tissue.",
            "Administer adequate, multi-modal analgesia (e.g., regional epidural or nerve blocks) to control pain and optimize chest wall movement.",
            "Monitor continuously for delayed complications, including secondary bacterial pneumonia, ARDS progression, or delayed pulmonary hemorrhage."
        ]
    },
    "unknown": {
        "condition": "Undifferentiated Acute Respiratory Failure",
        "description": "The clinical presentation represents an undifferentiated acute respiratory failure where physiological data indicates severe respiratory distress and impaired gas exchange without a clear initial etiology. The abnormal compliance, high airway resistance, and severe ventilation-perfusion mismatch demand broad supportive interventions while an exhaustive diagnostic workup is completed to isolate the primary cause.",
        "solutions": [
            "Stabilize gas exchange immediately using non-invasive positive pressure support or safe, lung-protective mechanical ventilation.",
            "Perform an urgent diagnostic workup, including a comprehensive metabolic panel, complete blood count, chest imaging, and blood cultures.",
            "Utilize bedside point-of-care ultrasound (POCUS) to systematically evaluate heart, lung, and deep venous structures.",
            "Maintain stable hemodynamics through cautious fluid management and targeted vasoactive support based on perfusion markers.",
            "Review the patient's entire medical history, current medications, toxic exposures, and recent clinical events.",
            "Re-evaluate and refine treatment strategies hourly as new diagnostic data and clinical responses become available."
        ]
    }
}

# ==========================================
# 3. CORE FLASK FLUID INTERACTION INTERFACE
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            flash('Secure session established.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid architectural credentials.', 'danger')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>AeroLung Sync | Secure Gate</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #0b0f19; color: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif; display: flex; align-items: center; height: 100vh; margin:0; }
            .card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
            .btn-cyber { background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; border: none; font-weight: 600; }
            .btn-cyber:hover { background: linear-gradient(135deg, #2563eb, #7c3aed); color: white; }
            .glow-text { text-shadow: 0 0 10px rgba(59,130,246,0.5); color: #60a5fa; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-4">
                    <div class="card p-4">
                        <div class="text-center mb-4">
                            <h3 class="glow-text font-monospace">AEROLUNG SYNC v2026</h3>
                            <small class="text-muted">Clinical Simulation Architecture</small>
                        </div>
                        {% with messages = get_flashed_messages(with_categories=true) %}
                          {% if messages %}
                            {% for cat, msg in messages %}
                              <div class="alert alert-{{cat}} py-2 small">{{msg}}</div>
                            {% endfor %}
                          {% endif %}
                        {% endwith %}
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label small text-muted font-monospace">SYSTEM USERNAME</label>
                                <input type="text" name="username" class="form-control bg-dark text-light border-secondary" required bg-dark text-light border-secondary">
                            </div>
                            <div class="mb-3">
                                <label class="form-label small text-muted font-monospace">ACCESS KEY</label>
                                <input type="password" name="password" class="form-control bg-dark text-light border-secondary" required bg-dark text-light border-secondary">
                            </div>
                            <button type="submit" class="btn btn-cyber w-100 py-2 font-monospace">AUTHORIZE ACCESS</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Default Patient Matrix Base
    inputs = {
        "rr": 16, "vt": 450, "fio2": 40, "peep": 5, "ie_ratio": 2.0,
        "raw": 8, "compl": 50, "p_musc": 0, "weight": 70
    }
    
    selected_pathology = "healthy"
    
    if request.method == 'POST':
        for key in inputs.keys():
            if key == 'ie_ratio':
                inputs[key] = float(request.form.get(key, inputs[key]))
            else:
                inputs[key] = int(request.form.get(key, inputs[key]))
        selected_pathology = request.form.get("pathology", "healthy")
        
        # Pull profile preset values to synchronize engine sliders seamlessly
        if selected_pathology in DISEASE_PROFILES and selected_pathology != "custom":
            if selected_pathology == "ards":
                inputs["compl"] = 22; inputs["raw"] = 10; inputs["peep"] = 14; inputs["fio2"] = 70
            elif selected_pathology == "copd":
                inputs["raw"] = 28; inputs["compl"] = 85; inputs["ie_ratio"] = 4.0; inputs["peep"] = 4
            elif selected_pathology == "asthma":
                inputs["raw"] = 38; inputs["compl"] = 55; inputs["ie_ratio"] = 4.5; inputs["rr"] = 12
            elif selected_pathology == "fibrosis":
                inputs["compl"] = 16; inputs["raw"] = 7; inputs["vt"] = 320; inputs["rr"] = 24
            elif selected_pathology == "pe":
                inputs["fio2"] = 100; inputs["rr"] = 28; inputs["compl"] = 48
            elif selected_pathology == "pneumonia":
                inputs["compl"] = 30; inputs["raw"] = 12; inputs["fio2"] = 60; inputs["peep"] = 8
            elif selected_pathology == "neuro":
                inputs["p_musc"] = 2; inputs["rr"] = 8; inputs["vt"] = 250
            elif selected_pathology == "obesity":
                inputs["compl"] = 20; inputs["peep"] = 14; inputs["vt"] = 550
            elif selected_pathology == "pneumothorax":
                inputs["compl"] = 12; inputs["raw"] = 16; inputs["rr"] = 30; inputs["fio2"] = 100
            elif selected_pathology == "edema":
                inputs["compl"] = 25; inputs["fio2"] = 80; inputs["peep"] = 12
            elif selected_pathology == "anaphylaxis":
                inputs["raw"] = 45; inputs["rr"] = 26; inputs["fio2"] = 60
            elif selected_pathology == "copd_overlap":
                inputs["raw"] = 32; inputs["compl"] = 70; inputs["ie_ratio"] = 4.0
            elif selected_pathology == "sars_cov_2":
                inputs["compl"] = 35; inputs["fio2"] = 85; inputs["peep"] = 12
            elif selected_pathology == "trali":
                inputs["compl"] = 24; inputs["fio2"] = 90; inputs["peep"] = 10
            elif selected_pathology == "aco":
                inputs["rr"] = 32; inputs["fio2"] = 100; inputs["compl"] = 45
            elif selected_pathology == "emphysema":
                inputs["compl"] = 90; inputs["raw"] = 22; inputs["peep"] = 4
            elif selected_pathology == "interstitial":
                inputs["compl"] = 26; inputs["raw"] = 8; inputs["fio2"] = 50
            elif selected_pathology == "cyber_trauma":
                inputs["compl"] = 28; inputs["raw"] = 14; inputs["fio2"] = 80; inputs["peep"] = 10

    # ==========================================
    # 4. ADVANCED PHYSICAL MATH PHYSICS CALCULATION ENGINE
    # ==========================================
    rr = inputs["rr"]
    vt_l = inputs["vt"] / 1000.0
    fio2 = inputs["fio2"]
    peep = inputs["peep"]
    ie = inputs["ie_ratio"]
    raw = inputs["raw"]
    compl = inputs["compl"]
    p_musc = inputs["p_musc"]
    weight = inputs["weight"]
    
    mv = rr * vt_l
    
    # Airflow Timing Dynamics
    t_total = 60.0 / max(rr, 1)
    t_insp = t_total / (1.0 + ie)
    t_exp = t_total - t_insp
    
    # Flow rate calculation assuming constant or decelerating peak equivalence
    flow_l_sec = vt_l / max(t_insp, 0.1)
    flow_l_min = flow_l_sec * 60.0
    
    # Equation of Motion Calculations
    p_res = flow_l_sec * raw
    p_elas = inputs["vt"] / max(compl, 1)
    p_peak = peep + p_res + p_elas - (p_musc * 0.5)
    p_plat = peep + p_elas
    p_mean = peep + (0.4 * p_elas) + (0.1 * p_res) # Standard modern integral curve approximation
    
    # Metabolic & Arterial Gas Dynamics Fallbacks
    v_deadspace = (2.2 * weight) / 1000.0 # 2.2mL per kg IBW
    v_alveolar_min = max(0.1, (vt_l - v_deadspace) * rr)
    
    # High Fidelity Gas Approximations
    p_co2_base = 40.0
    if selected_pathology in ["copd", "emphysema", "copd_overlap", "obesity"]:
        p_co2_base = 56.0
    elif selected_pathology in ["healthy"]:
        p_co2_base = 40.0
        
    paco2 = p_co2_base * (4.5 / v_alveolar_min)
    paco2 = max(15.0, min(120.0, paco2))
    
    # Henderson-Hasselbalch Approximation for Clinical pH
    hco3 = 24.0
    if selected_pathology in ["copd", "emphysema", "copd_overlap", "obesity"]:
        hco3 = 31.0 # Chronic metabolic compensation
    
    ph = 6.1 + math.log10(hco3 / max(0.03 * paco2, 0.001))
    ph = max(6.80, min(7.70, ph))
    
    # Alveolar Gas Equation Engine
    p_atm = 760.0
    p_h2o = 47.0
    r_quotient = 0.8
    pao2_ideal = (fio2 / 100.0) * (p_atm - p_h2o) - (paco2 / r_quotient)
    
    # Structural Shunt/Diffusion Impairment Scaling Factor
    shunt_factor = 15.0
    if selected_pathology == "ards": shunt_factor = 280.0
    elif selected_pathology == "fibrosis": shunt_factor = 140.0
    elif selected_pathology == "pneumonia": shunt_factor = 110.0
    elif selected_pathology == "pe": shunt_factor = 190.0
    elif selected_pathology == "edema": shunt_factor = 150.0
    elif selected_pathology == "sars_cov_2": shunt_factor = 220.0
    elif selected_pathology == "trali": shunt_factor = 240.0
    elif selected_pathology == "cyber_trauma": shunt_factor = 130.0
    elif selected_pathology == "interstitial": shunt_factor = 95.0
    
    p_ao2 = max(25.0, pao2_ideal - shunt_factor)
    
    # Oxygen Saturation Curve (Severinghaus Equation)
    sat_term = (p_ao2**3 + 150 * p_ao2)
    spo2 = (sat_term / (sat_term + 23450)) * 100.0
    spo2 = max(40.0, min(100.0, spo2))

    # ==========================================
    # 5. DYNAMIC MULTI-MODAL PATHOLOGY GENERATOR (FALLBACK DETECTOR)
    # ==========================================
    # Secure bound parsing logic with detailed dynamic descriptions for customized user-input variables
    if selected_pathology == "custom" or selected_pathology not in DISEASE_PROFILES:
        # Detect true underlying physiological profile via slider telemetry matrix
        if compl < 25 and raw > 20:
            condition_title = "Mixed Severe Obstructive-Restrictive Failure (Custom Matrix)"
            evidence_desc = f"The current architectural telemetry reflects a rare, severe combination of low static compliance ({compl} mL/cmH2O) and markedly high airway resistance ({raw} cmH2O/L/s). The high mechanical load coupled with poor elastic expansion impairs both ventilation delivery and gas exchange, forcing high driving pressures and significant ventilation-perfusion abnormalities."
            treatment_list = [
                "Optimize external PEEP to overcome systemic intrinsic resistance while closely safeguarding plateau pressure boundaries.",
                "Administer aggressive combined bronchodilator therapy and evaluate for underlying interstitial components.",
                "Target low mechanical tidal volumes adjusted precisely for the combined restrictive-obstructive footprint."
            ]
        elif compl < 25:
            condition_title = "Isolated Low-Compliance Parenchymal Pattern (Custom Matrix)"
            evidence_desc = f"The automated assessment isolates a profound loss of static respiratory compliance ({compl} mL/cmH2O). This stiff lung profile significantly elevates the risk of ventilator-induced lung injury (VILI) due to elevated plateau and driving pressures, demonstrating marked alveolar collapse or parenchymal tissue consolidation."
            treatment_list = [
                "Utilize immediate lung-protective mechanical ventilation strategies strictly constrained to 4-6 mL/kg PBW.",
                "Titrate positive end-expiratory pressure to promote alveolar recruitment while maintaining driving pressure < 15 cmH2O.",
                "Evaluate for fluid retention, ARDS evolution, or acute fibrotic exacerbations requiring systemic support."
            ]
        elif raw > 25:
            condition_title = "Severe Airway Airflow Obstruction (Custom Matrix)"
            evidence_desc = f"The real-time telemetry matrix reveals a severe elevation in airway resistance ({raw} cmH2O/L/s). This signature indicates profound narrowing of the conducting airways, precipitating an extensive delay in expiratory airflow and increasing the threat of dynamic hyperinflation, auto-PEEP, and mechanical air trapping."
            treatment_list = [
                "Administer continuous short-acting beta-agonists and anticholinergic agents immediately via inline nebulization.",
                "Maximize expiratory phase durations by executing a low respiratory rate and a fast inspiratory flow profile.",
                "Monitor and measure intrinsic PEEP regularly to adjust applied external PEEP to reduce patient triggering efforts."
            ]
        else:
            condition_title = "Undifferentiated Mild Metabolic/Mechanical Deviance"
            evidence_desc = f"The system observes minor physiological variance. Mechanical resistance ({raw} cmH2O/L/s) and compliance ({compl} mL/cmH2O) are balanced near functional baselines. Monitor for subtle shifts in clinical status or emerging systemic anomalies."
            treatment_list = [
                "Maintain standardized protective ventilation and protocolized respiratory hygiene checks.",
                "Perform sequential arterial blood gas measurements to follow trends in acid-base parameters.",
                "Assess for opportunities to transition safely toward independent spontaneous breathing trials."
            ]
        
        active_profile = {
            "condition": condition_title,
            "description": evidence_desc,
            "solutions": treatment_list
        }
    else:
        active_profile = DISEASE_PROFILES[selected_pathology]

    # Render App
    return render_template_string(HTML_TEMPLATE, 
                                 inputs=inputs, 
                                 selected_pathology=selected_pathology,
                                 active_profile=active_profile,
                                 mv=round(mv, 2),
                                 p_peak=round(p_peak, 1),
                                 p_plat=round(p_plat, 1),
                                 p_mean=round(p_mean, 1),
                                 ph=round(ph, 2),
                                 paco2=round(paco2, 1),
                                 spo2=round(spo2, 1),
                                 flow_l_min=round(flow_l_min, 1))

# ==========================================
# 6. ARCHITECTURAL METRIC FLUID UI DESIGN TEMPLATE
# ==========================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AeroLung Sync | Advanced Simulation Panel</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-main: #060913;
            --bg-card: #0d1326;
            --border-glow: #1e293b;
            --neon-blue: #38bdf8;
            --neon-green: #34d399;
            --neon-amber: #fbbf24;
            --neon-red: #f87171;
        }
        body {
            background-color: var(--bg-main);
            color: #f1f5f9;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        .navbar-cyber {
            background-color: var(--bg-card);
            border-bottom: 2px solid #1e2942;
        }
        .card-cyber {
            background-color: var(--bg-card);
            border: 1px solid var(--border-glow);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            margin-bottom: 20px;
        }
        .header-glow {
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            color: var(--neon-blue);
            text-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
        }
        .metric-box {
            background: rgba(15, 23, 42, 0.6);
            border-left: 4px solid var(--neon-blue);
            padding: 15px;
            border-radius: 4px;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            font-family: 'Courier New', monospace;
        }
        .slider-label {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
        }
        .form-range::-webkit-slider-thumb { background: var(--neon-blue); }
        .form-range::-moz-range-thumb { background: var(--neon-blue); }
        .waveform-container {
            background: #020617;
            border-radius: 8px;
            padding: 10px;
            border: 1px solid #1e294b;
        }
    </style>
</head>
<body>

    <nav class="navbar navbar-dark navbar-cyber px-4 py-3 d-flex justify-content-between">
        <span class="navbar-brand header-glow mb-0 h1"><i class="fa-solid fa-microchip-vascular me-2"></i>AEROLUNG SYNC v2026 Engine</span>
        <div class="d-flex align-items-center gap-3">
            <span class="badge bg-secondary font-monospace"><i class="fa-solid fa-user-shield me-1"></i> {{ session['role'] }}</span>
            <button id="voiceBtn" class="btn btn-outline-info btn-sm font-monospace"><i class="fa-solid fa-microphone me-1"></i> VOICE CONTROL</button>
            <a href="{{ url_for('logout') }}" class="btn btn-outline-danger btn-sm font-monospace"><i class="fa-solid fa-power-off"></i></a>
        </div>
    </nav>

    <div class="container-fluid p-4">
        <form method="POST" id="simulationForm">
            <div class="row">
                
                <!-- LEFT COLUMN: CONTROLS & PATHOLOGIES -->
                <div class="col-xl-4 col-lg-5">
                    <div class="card card-cyber p-3">
                        <h5 class="text-uppercase font-monospace text-info border-bottom border-secondary pb-2 mb-3">
                            <i class="fa-solid fa-virus-pulmonary me-2"></i>Clinical Profiler Matrix
                        </h5>
                        <div class="mb-3">
                            <label class="form-label slider-label fw-bold text-white">SELECT TARGET PATHOLOGY</label>
                            <select name="pathology" class="form-select bg-dark text-white border-secondary" onchange="this.form.submit()">
                                <option value="healthy" {% if selected_pathology == 'healthy' %}selected{% endif %}>Stable Pulmonary Homeostasis</option>
                                <option value="ards" {% if selected_pathology == 'ards' %}selected{% endif %}>Severe ARDS (Diffuse Alveolar Damage)</option>
                                <option value="copd" {% if selected_pathology == 'copd' %}selected{% endif %}>End-Stage COPD Exacerbation</option>
                                <option value="asthma" {% if selected_pathology == 'asthma' %}selected{% endif %}>Status Asthmaticus (Refractory)</option>
                                <option value="fibrosis" {% if selected_pathology == 'fibrosis' %}selected{% endif %}>Advanced Pulmonary Fibrosis</option>
                                <option value="pe" {% if selected_pathology == 'pe' %}selected{% endif %}>Massive Pulmonary Embolism</option>
                                <option value="pneumonia" {% if selected_pathology == 'pneumonia' %}selected{% endif %}>Severe Lobar Pneumonia</option>
                                <option value="neuro" {% if selected_pathology == 'neuro' %}selected{% endif %}>Neuromuscular Pump Failure</option>
                                <option value="obesity" {% if selected_pathology == 'obesity' %}selected{% endif %}>Obesity Hypoventilation Syndrome</option>
                                <option value="pneumothorax" {% if selected_pathology == 'pneumothorax' %}selected{% endif %}>Tension Pneumothorax Emergency</option>
                                <option value="edema" {% if selected_pathology == 'edema' %}selected{% endif %}>Acute Cardiogenic Pulmonary Edema</option>
                                <option value="anaphylaxis" {% if selected_pathology == 'anaphylaxis' %}selected{% endif %}>Acute Laryngospasm / Anaphylaxis</option>
                                <option value="copd_overlap" {% if selected_pathology == 'copd_overlap' %}selected{% endif %}>COPD-Asthma Overlap (ACOS)</option>
                                <option value="sars_cov_2" {% if selected_pathology == 'sars_cov_2' %}selected{% endif %}>Severe COVID-19 Pneumonitis</option>
                                <option value="trali" {% if selected_pathology == 'trali' %}selected{% endif %}>TRALI Reaction (Immune Transfusion Damage)</option>
                                <option value="aco" {% if selected_pathology == 'aco' %}selected{% endif %}>Obstructive Shock / Circulatory Collapse</option>
                                <option value="emphysema" {% if selected_pathology == 'emphysema' %}selected{% endif %}>Advanced Centrilobular Emphysema</option>
                                <option value="interstitial" {% if selected_pathology == 'interstitial' %}selected{% endif %}>Nonspecific Interstitial Pneumonia (NSIP)</option>
                                <option value="cyber_trauma" {% if selected_pathology == 'cyber_trauma' %}selected{% endif %}>Blast Injury / Pulmonary Contusion</option>
                                <option value="unknown" {% if selected_pathology == 'unknown' %}selected{% endif %}>Undifferentiated Acute Respiratory Failure</option>
                                <option value="custom" {% if selected_pathology == 'custom' %}selected{% endif %}>-- UNBOUNDED FREEDOM DYNAMIC MATRIX --</option>
                            </select>
                        </div>
                    </div>

                    <div class="card card-cyber p-3">
                        <h5 class="text-uppercase font-monospace text-info border-bottom border-secondary pb-2 mb-3">
                            <i class="fa-solid fa-sliders me-2"></i>Simulation Inputs
                        </h5>
                        
                        <!-- SLIDER BLOCKS -->
                        <div class="mb-3">
                            <div class="d-flex justify-content-between"><span class="slider-label">Respiratory Rate (RR)</span><span class="text-info font-monospace fw-bold" id="v_rr">{{ inputs.rr }} bpm</span></div>
                            <input type="range" class="form-range" name="rr" min="4" max="50" step="1" value="{{ inputs.rr }}" oninput="document.getElementById('v_rr').innerText=this.value+' bpm'">
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between"><span class="slider-label">Tidal Volume (Vt)</span><span class="text-info font-monospace fw-bold" id="v_vt">{{ inputs.vt }} mL</span></div>
                            <input type="range" class="form-range" name="vt" min="150" max="800" step="10" value="{{ inputs.vt }}" oninput="document.getElementById('v_vt').innerText=this.value+' mL'">
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between"><span class="slider-label">FiO2</span><span class="text-info font-monospace fw-bold" id="v_fio2">{{ inputs.fio2 }}%</span></div>
                            <input type="range" class="form-range" name="fio2" min="21" max="100" step="1" value="{{ inputs.fio2 }}" oninput="document.getElementById('v_fio2').innerText=this.value+'%'">
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between"><span class="slider-label">PEEP</span><span class="text-info font-monospace fw-bold" id="v_peep">{{ inputs.peep }} cmH2O</span></div>
                            <input type="range" class="form-range" name="peep" min="0" max="24" step="1" value="{{ inputs.peep }}" oninput="document.getElementById('v_peep').innerText=this.value+' cmH2O'">
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between"><span class="slider-label">Inspiratory/Expiratory Ratio (I:E)</span><span class="text-info font-monospace fw-bold" id="v_ie">1:{{ inputs.ie_ratio }}</span></div>
                            <input type="range" class="form-range" name="ie_ratio" min="1.0" max="6.0" step="0.5" value="{{ inputs.ie_ratio }}" oninput="document.getElementById('v_ie').innerText='1:'+this.value">
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between"><span class="slider-label">Airway Resistance (Raw)</span><span class="text-warning font-monospace fw-bold" id="v_raw">{{ inputs.raw }} cmH2O/L/s</span></div>
                            <input type="range" class="form-range" name="raw" min="2" max="60" step="1" value="{{ inputs.raw }}" oninput="document.getElementById('v_raw').innerText=this.value+' cmH2O/L/s'">
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between"><span class="slider-label">Static Compliance (Compl)</span><span class="text-warning font-monospace fw-bold" id="v_compl">{{ inputs.compl }} mL/cmH2O</span></div>
                            <input type="range" class="form-range" name="compl" min="5" max="120" step="1" value="{{ inputs.compl }}" oninput="document.getElementById('v_compl').innerText=this.value+' mL/cmH2O'">
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between"><span class="slider-label">Patient Muscular Effort (P_musc)</span><span class="text-warning font-monospace fw-bold" id="v_pmusc">{{ inputs.p_musc }} cmH2O</span></div>
                            <input type="range" class="form-range" name="p_musc" min="0" max="25" step="1" value="{{ inputs.p_musc }}" oninput="document.getElementById('v_pmusc').innerText=this.value+' cmH2O'">
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between"><span class="slider-label">Patient Ideal Weight</span><span class="text-muted font-monospace fw-bold" id="v_weight">{{ inputs.weight }} kg</span></div>
                            <input type="range" class="form-range" name="weight" min="40" max="150" step="1" value="{{ inputs.weight }}" oninput="document.getElementById('v_weight').innerText=this.value+' kg'">
                        </div>
                        
                        <button type="submit" class="btn btn-primary font-monospace w-100 mt-2"><i class="fa-solid fa-sync-alt me-2"></i>RECOMPUTE SYSTEM METRICS</button>
                    </div>
                </div>

                <!-- RIGHT COLUMN: MONITOR & DIAGNOSTIC ANALYTICS -->
                <div class="col-xl-8 col-lg-7">
                    
                    <!-- HIGH-VISIBILITY METRIC TELEMETRY WALL -->
                    <div class="row row-cols-md-4 row-cols-2 g-3 mb-4">
                        <div class="col">
                            <div class="card card-cyber p-3 text-center border-start border-4 border-info">
                                <div class="slider-label">Arterial pH</div>
                                <div class="metric-value {% if ph < 7.35 or ph > 7.45 %}text-danger{% else %}text-success{% endif %}">{{ ph }}</div>
                                <small class="text-muted font-monospace">Target: 7.35 - 7.45</small>
                            </div>
                        </div>
                        <div class="col">
                            <div class="card card-cyber p-3 text-center border-start border-4 border-info">
                                <div class="slider-label">PaCO2 Status</div>
                                <div class="metric-value {% if paco2 > 45 %}text-warning{% else %}text-info{% endif %}">{{ paco2 }} <span style="font-size:1rem">mmHg</span></div>
                                <small class="text-muted font-monospace">Target: 35-45 mmHg</small>
                            </div>
                        </div>
                        <div class="col">
                            <div class="card card-cyber p-3 text-center border-start border-4 border-success">
                                <div class="slider-label">Oxygen Sat (SpO2)</div>
                                <div class="metric-value {% if spo2 < 90 %}text-danger{% else %}text-success{% endif %}">{{趨}} {{ spo2 }}%</div>
                                <small class="text-muted font-monospace">Calculated Output</small>
                            </div>
                        </div>
                        <div class="col">
                            <div class="card card-cyber p-3 text-center border-start border-4 border-danger">
                                <div class="slider-label">Peak Pressure</div>
                                <div class="metric-value {% if p_peak > 35 %}text-danger{% else %}text-warning{% endif %}">{{ p_peak }} <span style="font-size:1rem">cmH2O</span></div>
                                <small class="text-muted font-monospace">Plateau: {{ p_plat }}</small>
                            </div>
                        </div>
                    </div>

                    <!-- CLINICAL REPORT GENERATOR FRAME -->
                    <div class="card card-cyber p-4 border-start border-4 border-primary">
                        <h4 class="font-monospace text-primary mb-2"><i class="fa-solid fa-file-medical-chart me-2"></i>Clinical Evidence Report</h4>
                        <h6 class="text-white font-monospace mb-3">CONSOLIDATED PATHOLOGY: <span class="text-warning fw-bold">{{ active_profile.condition }}</span></h6>
                        
                        <p class="text-light lh-lg" style="font-size: 1.05rem; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 6px; border: 1px dashed #334155;">
                            {{ active_profile.description }}
                        </p>
                        
                        <hr class="border-secondary my-4">
                        
                        <h5 class="font-monospace text-success mb-3"><i class="fa-solid fa-list-check me-2"></i>Customized Action Plan & Treatment Protocol</h5>
                        <ul class="list-group list-group-flush bg-transparent">
                            {% for solution in active_profile.solutions %}
                                <li class="list-group-item bg-transparent text-white border-0 ps-0 d-flex align-items-start gap-2">
                                    <i class="fa-solid fa-square-check text-success mt-1"></i>
                                    <span>{{ solution }}</span>
                                </li>
                            {% endfor %}
                        </ul>
                    </div>

                    <!-- REAL-TIME FLUID SIMULATED VENTILATOR WAVEFORM WAVE -->
                    <div class="card card-cyber p-3">
                        <h6 class="text-uppercase font-monospace text-muted mb-2"><i class="fa-solid fa-wave-square me-2"></i>Simulated Dynamic Flow Curve (Single Respiratory Cycle)</h6>
                        <div class="waveform-container text-center">
                            <svg width="100%" height="160" viewBox="0 0 800 160" style="background:#020617;">
                                <!-- Grid Lines -->
                                <line x1="0" y1="80" x2="800" y2="80" stroke="#1e293b" stroke-dasharray="5,5"/>
                                <!-- Simulated wave path generated dynamically by current input metrics -->
                                <path d="M 50 80 
                                         C 150 {{ 80 - (p_peak * 1.5) }}, 250 {{ 80 - (p_plat * 1.5) }}, 350 {{ 80 - (p_plat * 1.5) }} 
                                         L 350 80 
                                         C 450 {{ 80 + (flow_l_min * 0.5) }}, 600 80, 750 80" 
                                      fill="none" stroke="#38bdf8" stroke-width="3" />
                                <text x="60" y="30" fill="#94a3b8" font-family="monospace" font-size="11">Inspiration</text>
                                <text x="400" y="130" fill="#94a3b8" font-family="monospace" font-size="11">Expiration (Ratio scale: 1:{{ inputs.ie_ratio }})</text>
                            </svg>
                        </div>
                    </div>

                </div>
            </div>
        </form>
    </div>

    <!-- VOICE RECOGNITION INTERACTION ENGINE MODULE -->
    <script>
        const voiceBtn = document.getElementById('voiceBtn');
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            voiceBtn.addEventListener('click', () => {
                recognition.start();
                voiceBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> LISTENING ENGINE...';
                voiceBtn.className = "btn btn-danger btn-sm font-monospace";
            });

            recognition.onresult = (event) => {
                const command = event.results[0][0].transcript.toLowerCase();
                voiceBtn.className = "btn btn-outline-info btn-sm font-monospace";
                voiceBtn.innerHTML = '<i class="fa-solid fa-microphone me-1"></i> VOICE CONTROL';
                
                // Audio interface parsing strings mapping to selector array values
                const pathologySelect = document.querySelector('select[name="pathology"]');
                let matches = false;
                
                if(command.includes('healthy') || command.includes('normal')) { pathologySelect.value = 'healthy'; matches = true; }
                else if(command.includes('ards') || command.includes('distress')) { pathologySelect.value = 'ards'; matches = true; }
                else if(command.includes('copd')) { pathologySelect.value = 'copd'; matches = true; }
                else if(command.includes('asthma')) { pathologySelect.value = 'asthma'; matches = true; }
                else if(command.includes('fibrosis')) { pathologySelect.value = 'fibrosis'; matches = true; }
                else if(command.includes('embolism') || command.includes('pulmonary embolism')) { pathologySelect.value = 'pe'; matches = true; }
                else if(command.includes('pneumonia')) { pathologySelect.value = 'pneumonia'; matches = true; }
                else if(command.includes('neuromuscular') || command.includes('neuro')) { pathologySelect.value = 'neuro'; matches = true; }
                else if(command.includes('obesity')) { pathologySelect.value = 'obesity'; matches = true; }
                else if(command.includes('pneumothorax') || command.includes('tension')) { pathologySelect.value = 'pneumothorax'; matches = true; }
                else if(command.includes('edema') || command.includes('heart fluid')) { pathologySelect.value = 'edema'; matches = true; }
                else if(command.includes('anaphylaxis') || command.includes('allergic')) { pathologySelect.value = 'anaphylaxis'; matches = true; }
                else if(command.includes('overlap') || command.includes('acos')) { pathologySelect.value = 'copd_overlap'; matches = true; }
                else if(command.includes('covid') || command.includes('corona')) { pathologySelect.value = 'sars_cov_2'; matches = true; }
                else if(command.includes('trali') || command.includes('transfusion')) { pathologySelect.value = 'trali'; matches = true; }
                else if(command.includes('shock') || command.includes('circulatory')) { pathologySelect.value = 'aco'; matches = true; }
                else if(command.includes('emphysema')) { pathologySelect.value = 'emphysema'; matches = true; }
                else if(command.includes('interstitial') || command.includes('nsip')) { pathologySelect.value = 'interstitial'; matches = true; }
                else if(command.includes('trauma') || command.includes('blast')) { pathologySelect.value = 'cyber_trauma'; matches = true; }
                else if(command.includes('unknown') || command.includes('failure')) { pathologySelect.value = 'unknown'; matches = true; }
                else if(command.includes('custom') || command.includes('freedom')) { pathologySelect.value = 'custom'; matches = true; }
                
                if(matches) {
                    document.getElementById('simulationForm').submit();
                } else {
                    alert('Command received: "' + command + '". No matching pathology identifier mapped inside engine profiles.');
                }
            };

            recognition.onerror = () => {
                voiceBtn.className = "btn btn-outline-info btn-sm font-monospace";
                voiceBtn.innerHTML = '<i class="fa-solid fa-microphone me-1"></i> VOICE CONTROL';
            };
        } else {
            voiceBtn.style.display = 'none';
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
