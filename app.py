from flask import Flask, request, redirect, url_for, session, flash, render_template_string, jsonify
import os
import math
import time
from datetime import datetime

# ==========================================
# 1. SERVER CONFIGURATION & IN-MEMORY DB
# ==========================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "shreesh_premium_lung_matrix_2026")

# In a real app, this would be a SQL database. 
# For this advanced script, we use an in-memory dictionary that updates live.
SYSTEM_USERS = {
    "admin": {
        "password": "password123",
        "clearance": "Supreme Architect"
    }
}

# ==========================================
# 2. THE AI DIAGNOSTIC ENGINE (BACKEND)
# ==========================================
class AILungEngine:
    @staticmethod
    def analyze_vitals(spo2, resp_rate, heart_rate, cough_severity, sob_level):
        """
        Analyzes the inputs to generate a simulated AI response explaining the physiology
        and offering precise clinical solutions.
        """
        # Convert inputs safely
        try: spo2 = float(spo2)
        except: spo2 = 98.0
        try: rr = float(resp_rate)
        except: rr = 14.0
        try: hr = float(heart_rate)
        except: hr = 75.0
        try: cough = int(cough_severity)
        except: cough = 0
        try: sob = int(sob_level)
        except: sob = 0

        # Calculate severity indices
        hypoxia_index = max(0, 95 - spo2) * 2.5
        tachypnea_index = max(0, rr - 20) * 1.5
        distress_score = hypoxia_index + tachypnea_index + (cough * 2) + (sob * 3)

        # Base outputs
        status = "NORMAL HOMEOSTASIS"
        color = "text-emerald-400"
        explanation = "The pulmonary system is operating within optimal parameters. Alveolar gas exchange is efficient, maintaining excellent blood oxygenation without excess cardiopulmonary strain."
        solutions = [
            "Maintain current cardiovascular exercise routine.",
            "Continue standard atmospheric breathing.",
            "No pharmacological intervention required."
        ]
        vital_breakdown = f"SpO2 ({spo2}%) is excellent. Respiratory rate ({rr} bpm) indicates low work of breathing."

        # Logic Tree for AI Assessment
        if distress_score > 30 or spo2 < 88:
            status = "CRITICAL HYPOXIC RESPIRATORY FAILURE"
            color = "text-rose-500"
            explanation = "SEVERE ALERT: The pulmonary parenchyma is failing to adequately oxygenate the arterial blood. This level of hypoxia indicates significant alveolar shunting, dead-space ventilation, or massive airflow obstruction. The myocardium is likely under immense stress to compensate."
            solutions = [
                "IMMEDIATE INTERVENTION REQUIRED: Apply high-flow supplemental oxygen.",
                "Prepare for potential intubation and mechanical ventilatory support.",
                "Draw immediate Arterial Blood Gas (ABG) for pH/PaCO2 analysis.",
                "Administer rapid-acting bronchodilators and IV corticosteroids."
            ]
            vital_breakdown = f"SpO2 critically low at {spo2}%. Tachypnea ({rr} bpm) and tachycardia ({hr} bpm) signify impending respiratory muscle fatigue."
        elif distress_score > 15 or spo2 < 94:
            status = "MODERATE RESPIRATORY DISTRESS / IMPAIRED EXCHANGE"
            color = "text-amber-400"
            explanation = "The system detects a moderate impairment in gas exchange. The subjective feeling of shortness of breath correlates with the decreased oxygen saturation. There is likely an inflammatory process, fluid accumulation, or bronchospasm occurring within the terminal bronchioles."
            solutions = [
                "Apply low-flow oxygen via nasal cannula (2-4 L/min) to target SpO2 > 94%.",
                "Conduct a thorough auscultation of lung fields to check for wheezing or rales.",
                "Consider spirometry testing to rule out obstructive pathology.",
                "Monitor closely; elevate the patient's upper body to reduce diaphragmatic pressure."
            ]
            vital_breakdown = f"SpO2 is suboptimal ({spo2}%). Work of breathing is elevated with a respiratory rate of {rr} bpm."
        elif cough > 6 or sob > 6:
            status = "ACUTE AIRWAY REACTIVITY / INFLAMMATION"
            color = "text-blue-400"
            explanation = "While systemic oxygenation remains relatively stable, the high severity of coughing and shortness of breath indicates severe hypersensitivity or inflammation of the airway mucosa. This is characteristic of reactive airway disease or an acute viral bronchitis."
            solutions = [
                "Administer inhaled Beta-2 agonists (e.g., Albuterol) to induce bronchodilation.",
                "Prescribe an inhaled corticosteroid to suppress localized airway inflammation.",
                "Ensure adequate hydration to thin pulmonary secretions.",
                "Identify and remove potential environmental triggers (dust, allergens, smoke)."
            ]
            vital_breakdown = f"Oxygenation is maintained ({spo2}%), but symptom indices (Cough: {cough}/10, SOB: {sob}/10) require intervention."

        # Simulate processing delay for UI effect
        time.sleep(1.2)
        
        return {
            "status": status,
            "color": color,
            "explanation": explanation,
            "vital_breakdown": vital_breakdown,
            "solutions": solutions,
            "score": round(distress_score, 1)
        }

# ==========================================
# 3. GLOBAL UI ASSETS (CSS, SVG BACKGROUND)
# ==========================================

# The animated, breathing background lung
BACKGROUND_SVG = """
<svg class="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[120vw] md:w-[80vw] z-[-1] pointer-events-none opacity-20" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" style="animation: breatheBackground 6s ease-in-out infinite;">
    <defs>
        <radialGradient id="lungGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.3"/>
            <stop offset="60%" stop-color="#0891b2" stop-opacity="0.1"/>
            <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
        </radialGradient>
        <filter id="neonBlur"><feGaussianBlur stdDeviation="8" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>
    <rect width="400" height="400" fill="url(#lungGlow)" />
    <g filter="url(#neonBlur)" stroke="#06b6d4" stroke-width="1.5" fill="none">
        <path d="M190 40 v60 M210 40 v60" stroke-width="2"/>
        <path d="M190 100 C 80 80, 20 200, 50 300 C 80 340, 160 340, 190 280 Z" fill="rgba(6, 182, 212, 0.05)"/>
        <path d="M210 100 C 320 80, 380 200, 350 300 C 320 340, 240 340, 210 280 Z" fill="rgba(6, 182, 212, 0.05)"/>
        <path d="M190 120 L140 160 M165 140 L130 130 M140 160 L100 180 M140 160 L120 210 M120 210 L80 230"/>
        <path d="M210 120 L260 160 M235 140 L270 130 M260 160 L300 180 M260 160 L280 210 M280 210 L320 230"/>
    </g>
</svg>
<style>
    @keyframes breatheBackground {
        0% { transform: translate(-50%, -50%) scale(0.98); opacity: 0.15; }
        50% { transform: translate(-50%, -50%) scale(1.02); opacity: 0.3; }
        100% { transform: translate(-50%, -50%) scale(0.98); opacity: 0.15; }
    }
</style>
"""

GLOBAL_STYLES = """
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Outfit', sans-serif; background-color: #030712; color: #f3f4f6; margin: 0; min-height: 100vh; display: flex; flex-direction: column; overflow-x: hidden; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    
    /* Glassmorphism Classes */
    .glass-panel { background: rgba(17, 24, 39, 0.65); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }
    .glass-input { background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); color: #fff; transition: all 0.3s ease; }
    .glass-input:focus { outline: none; border-color: #06b6d4; box-shadow: 0 0 15px rgba(6, 182, 212, 0.3); background: rgba(0, 0, 0, 0.7); }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #030712; }
    ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #06b6d4; }

    /* Scan Line Animation */
    .scan-container { position: relative; overflow: hidden; }
    .scan-line { position: absolute; top: 0; left: 0; width: 100%; height: 2px; background: #06b6d4; box-shadow: 0 0 15px 3px #06b6d4; opacity: 0; transform: translateY(-100%); }
    .scanning .scan-line { animation: scanDown 1.5s linear infinite; opacity: 1; }
    @keyframes scanDown { 0% { transform: translateY(0); } 100% { transform: translateY(400px); } }

    /* Typing cursor */
    .cursor-blink { animation: blink 1s step-end infinite; }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
</style>
<script>
    // Global Clock Function
    function updateClock() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' });
        const dateStr = now.toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
        const clockElem = document.getElementById('global-clock');
        if(clockElem) clockElem.innerHTML = `<span class="text-cyan-400 font-bold">${timeStr}</span> <span class="text-gray-500 text-xs ml-2">${dateStr}</span>`;
    }
    setInterval(updateClock, 1000);
    window.onload = updateClock;
</script>
"""

COPYRIGHT_FOOTER = """
<footer class="mt-auto py-6 text-center relative z-10 border-t border-white/5 bg-black/40 backdrop-blur-md">
    <div class="flex items-center justify-center gap-2 text-xs font-mono tracking-widest text-gray-500 uppercase">
        <span>&copy; 2026</span>
        <span class="w-1 h-1 rounded-full bg-cyan-500 animate-pulse"></span>
        <span class="text-gray-300 font-bold">Shreesh Santoshkumar Rolli</span>
        <span class="w-1 h-1 rounded-full bg-cyan-500 animate-pulse"></span>
        <span>Premium Architecture</span>
    </div>
</footer>
"""

# ==========================================
# 4. HTML TEMPLATES (VIEWS)
# ==========================================

LOGIN_HTML = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>AeroLung | Neural Gateway</title>{GLOBAL_STYLES}</head>
<body>
    {BACKGROUND_SVG}
    <div class="flex-1 flex items-center justify-center p-4 relative z-10">
        <div class="glass-panel rounded-2xl p-10 w-full max-w-md">
            <div class="text-center mb-10">
                <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-cyan-950 border border-cyan-800 shadow-[0_0_30px_rgba(6,182,212,0.3)] mb-4">
                    <svg class="w-8 h-8 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"/></svg>
                </div>
                <h1 class="text-4xl font-extrabold tracking-tight text-white mb-1">AERO<span class="text-cyan-400">LUNG</span></h1>
                <p class="text-xs font-mono text-cyan-600/80 uppercase tracking-[0.3em]">AI Pulmonary Matrix</p>
            </div>
            
            {{% if get_flashed_messages() %}}
                <div class="mb-6 p-3 rounded bg-red-950/50 border border-red-500/50 text-red-400 text-xs text-center font-mono uppercase tracking-wide">
                    {{% for msg in get_flashed_messages() %}} {{ msg }} {{% endfor %}}
                </div>
            {{% endif %}}

            <form action="/login" method="POST" class="space-y-6">
                <div>
                    <label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2 ml-1">Architect ID</label>
                    <input type="text" name="username" class="w-full glass-input px-4 py-3 rounded-xl font-mono text-sm" placeholder="Enter ID..." required>
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2 ml-1">Secure Passkey</label>
                    <input type="password" name="password" class="w-full glass-input px-4 py-3 rounded-xl font-mono text-sm" placeholder="••••••••" required>
                </div>
                <button type="submit" class="w-full py-4 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-bold text-sm uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:shadow-[0_0_40px_rgba(6,182,212,0.6)] transition-all transform hover:-translate-y-0.5">
                    Establish Uplink
                </button>
            </form>
        </div>
    </div>
    {COPYRIGHT_FOOTER}
</body></html>
"""

DASHBOARD_HTML = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>AeroLung | Master Interface</title>{GLOBAL_STYLES}</head>
<body>
    {BACKGROUND_SVG}
    
    <nav class="glass-panel sticky top-0 z-50 border-b-0 border-white/5">
        <div class="max-w-[1600px] mx-auto px-6 py-4 flex justify-between items-center">
            <div class="flex items-center gap-4">
                <div class="w-10 h-10 rounded-lg bg-cyan-950/50 border border-cyan-500/30 flex items-center justify-center">
                    <div class="w-3 h-3 bg-cyan-400 rounded-full animate-ping absolute"></div>
                    <div class="w-3 h-3 bg-cyan-400 rounded-full relative"></div>
                </div>
                <div>
                    <h1 class="text-xl font-extrabold tracking-tight">AERO<span class="text-cyan-400">LUNG</span></h1>
                    <div class="text-[9px] font-mono text-gray-400 uppercase tracking-widest">Active Session: {{ session.user }}</div>
                </div>
            </div>
            
            <div class="flex items-center gap-8">
                <div id="global-clock" class="font-mono text-sm text-right hidden sm:block border-r border-white/10 pr-8"></div>
                <div class="flex gap-4">
                    <a href="/settings" class="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white text-xs font-bold uppercase tracking-wider transition-colors border border-white/10">Settings</a>
                    <a href="/logout" class="px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-bold uppercase tracking-wider transition-colors border border-red-500/20">Disconnect</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="flex-1 max-w-[1600px] mx-auto w-full p-6 relative z-10">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            
            <div class="lg:col-span-4 glass-panel rounded-2xl overflow-hidden flex flex-col shadow-2xl">
                <div class="bg-black/40 p-5 border-b border-white/5">
                    <h2 class="text-sm font-bold uppercase tracking-widest text-cyan-400 flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>
                        Patient Telemetry
                    </h2>
                    <p class="text-[10px] text-gray-500 font-mono mt-1">Enter subjective and objective physiological data.</p>
                </div>
                
                <form id="ai-form" class="p-6 space-y-5">
                    <div>
                        <h3 class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3 border-b border-white/10 pb-1">Objective Vitals</h3>
                        <div class="space-y-4">
                            <div class="flex justify-between items-center">
                                <label class="text-xs font-bold text-gray-300 w-1/2">Blood Oxygen (SpO2 %)</label>
                                <input type="number" id="spo2" value="98" min="50" max="100" class="glass-input w-1/2 px-3 py-2 rounded-lg text-right text-cyan-300 font-mono text-sm">
                            </div>
                            <div class="flex justify-between items-center">
                                <label class="text-xs font-bold text-gray-300 w-1/2">Resp. Rate (Breaths/min)</label>
                                <input type="number" id="rr" value="14" min="5" max="60" class="glass-input w-1/2 px-3 py-2 rounded-lg text-right text-cyan-300 font-mono text-sm">
                            </div>
                            <div class="flex justify-between items-center">
                                <label class="text-xs font-bold text-gray-300 w-1/2">Heart Rate (BPM)</label>
                                <input type="number" id="hr" value="75" min="30" max="220" class="glass-input w-1/2 px-3 py-2 rounded-lg text-right text-cyan-300 font-mono text-sm">
                            </div>
                        </div>
                    </div>

                    <div class="pt-4">
                        <h3 class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3 border-b border-white/10 pb-1">Subjective Symptoms (0-10)</h3>
                        <div class="space-y-4">
                            <div>
                                <div class="flex justify-between text-xs font-bold text-gray-300 mb-2"><span>Cough Severity</span><span id="cough-val" class="font-mono text-amber-400">0</span></div>
                                <input type="range" id="cough" min="0" max="10" value="0" class="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-amber-500" oninput="document.getElementById('cough-val').innerText=this.value">
                            </div>
                            <div>
                                <div class="flex justify-between text-xs font-bold text-gray-300 mb-2"><span>Shortness of Breath</span><span id="sob-val" class="font-mono text-rose-400">0</span></div>
                                <input type="range" id="sob" min="0" max="10" value="0" class="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-rose-500" oninput="document.getElementById('sob-val').innerText=this.value">
                            </div>
                        </div>
                    </div>

                    <button type="submit" class="w-full mt-6 py-4 rounded-xl bg-white hover:bg-gray-200 text-black font-extrabold text-sm uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(255,255,255,0.2)] transition-all">
                        Execute AI Scan
                    </button>
                </form>
            </div>

            <div class="lg:col-span-8 flex flex-col h-full min-h-[600px]">
                <div id="ai-output-container" class="glass-panel rounded-2xl flex-1 flex flex-col relative scan-container">
                    <div class="scan-line"></div>
                    
                    <div id="idle-state" class="flex-1 flex flex-col items-center justify-center text-center p-10 opacity-100 transition-opacity duration-500">
                        <div class="w-24 h-24 border-4 border-dashed border-gray-700 rounded-full animate-[spin_10s_linear_infinite] flex items-center justify-center mb-6">
                            <div class="w-16 h-16 border-4 border-cyan-900 rounded-full flex items-center justify-center">
                                <div class="w-2 h-2 bg-cyan-500 rounded-full"></div>
                            </div>
                        </div>
                        <h3 class="text-xl font-bold text-white mb-2 uppercase tracking-widest">AI Engine Standby</h3>
                        <p class="text-sm text-gray-500 font-mono max-w-md">Input patient telemetry parameters and execute scan to generate neural diagnosis and clinical interventions.</p>
                    </div>

                    <div id="result-state" class="hidden flex-1 flex flex-col p-8 overflow-y-auto">
                        <div class="flex items-center gap-3 mb-8 border-b border-white/10 pb-4">
                            <span class="w-3 h-3 rounded-full bg-red-500 animate-pulse"></span>
                            <h2 class="text-sm font-black uppercase tracking-[0.3em] text-white">Neural Assessment Complete</h2>
                        </div>
                        
                        <div class="space-y-8">
                            <div>
                                <h4 class="text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1">Primary Condition</h4>
                                <div id="res-status" class="text-3xl font-black tracking-tight drop-shadow-md"></div>
                            </div>

                            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div class="bg-black/30 p-5 rounded-xl border border-white/5">
                                    <h4 class="text-[10px] font-mono text-cyan-500 uppercase tracking-widest mb-3 flex items-center gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg> Physiological Explanation</h4>
                                    <p id="res-explanation" class="text-sm text-gray-300 leading-relaxed"></p>
                                </div>
                                <div class="bg-black/30 p-5 rounded-xl border border-white/5">
                                    <h4 class="text-[10px] font-mono text-cyan-500 uppercase tracking-widest mb-3 flex items-center gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg> Telemetry Breakdown</h4>
                                    <p id="res-breakdown" class="text-sm text-gray-300 leading-relaxed font-mono"></p>
                                </div>
                            </div>

                            <div>
                                <h4 class="text-[10px] font-mono text-emerald-400 uppercase tracking-widest mb-3 border-b border-emerald-900/30 pb-2">Recommended Clinical Solutions</h4>
                                <ul id="res-solutions" class="space-y-3"></ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>
    {COPYRIGHT_FOOTER}

    <script>
        document.getElementById('ai-form').addEventListener('submit', async (e) => {{
            e.preventDefault();
            
            const container = document.getElementById('ai-output-container');
            const idle = document.getElementById('idle-state');
            const result = document.getElementById('result-state');
            
            // Start scanning effect
            container.classList.add('scanning');
            idle.style.display = 'none';
            result.style.display = 'none';
            
            // Gather data
            const data = new FormData();
            data.append('spo2', document.getElementById('spo2').value);
            data.append('rr', document.getElementById('rr').value);
            data.append('hr', document.getElementById('hr').value);
            data.append('cough', document.getElementById('cough').value);
            data.append('sob', document.getElementById('sob').value);

            // Fetch AI Response from backend
            try {{
                const res = await fetch('/api/ai_analyze', {{ method: 'POST', body: data }});
                const json = await res.json();
                
                // Stop scanning, show results
                container.classList.remove('scanning');
                result.style.display = 'flex';
                
                // Populate DOM
                const statusEl = document.getElementById('res-status');
                statusEl.className = `text-3xl font-black tracking-tight drop-shadow-md ${{json.color}}`;
                statusEl.innerText = json.status;
                
                document.getElementById('res-breakdown').innerText = json.vital_breakdown;
                
                // Typewriter effect for explanation
                const expEl = document.getElementById('res-explanation');
                expEl.innerHTML = '<span id="type-text"></span><span class="cursor-blink">|</span>';
                typeWriter(json.explanation, document.getElementById('type-text'), 0, 15);
                
                // Render solutions list
                const solList = document.getElementById('res-solutions');
                solList.innerHTML = '';
                json.solutions.forEach(sol => {{
                    const li = document.createElement('li');
                    li.className = "flex items-start gap-3 bg-white/5 p-3 rounded-lg border border-white/5 text-sm font-medium text-gray-200";
                    li.innerHTML = `<svg class="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg> <span>${{sol}}</span>`;
                    solList.appendChild(li);
                }});

            }} catch (err) {{
                console.error(err);
                container.classList.remove('scanning');
                idle.style.display = 'flex';
                alert("Neural Uplink Failed. Please try again.");
            }}
        }});

        function typeWriter(text, element, i, speed) {{
            if (i < text.length) {{
                element.innerHTML += text.charAt(i);
                setTimeout(() => typeWriter(text, element, i + 1, speed), speed);
            }}
        }}
    </script>
</body></html>
"""

SETTINGS_HTML = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>AeroLung | Security Settings</title>{GLOBAL_STYLES}</head>
<body>
    {BACKGROUND_SVG}
    
    <nav class="glass-panel sticky top-0 z-50 border-b-0 border-white/5">
        <div class="max-w-[1600px] mx-auto px-6 py-4 flex justify-between items-center">
            <div class="flex items-center gap-4">
                <div class="w-10 h-10 rounded-lg bg-cyan-950/50 border border-cyan-500/30 flex items-center justify-center">
                    <div class="w-3 h-3 bg-cyan-400 rounded-full"></div>
                </div>
                <h1 class="text-xl font-extrabold tracking-tight">AERO<span class="text-cyan-400">LUNG</span></h1>
            </div>
            <a href="/dashboard" class="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white text-xs font-bold uppercase tracking-wider transition-colors border border-white/10">Return to Matrix</a>
        </div>
    </nav>

    <div class="flex-1 flex items-center justify-center p-6 relative z-10">
        <div class="glass-panel p-10 rounded-2xl w-full max-w-lg shadow-2xl">
            <div class="border-b border-white/10 pb-6 mb-6">
                <h2 class="text-2xl font-black text-white uppercase tracking-widest">Security Override</h2>
                <p class="text-xs text-gray-400 font-mono mt-2">Modify Architect ID and Passkey credentials.</p>
            </div>

            {{% if get_flashed_messages() %}}
                <div class="mb-6 p-4 rounded bg-cyan-950/40 border border-cyan-500/50 text-cyan-300 text-xs font-mono uppercase tracking-wide">
                    {{% for msg in get_flashed_messages() %}} {{ msg }} {{% endfor %}}
                </div>
            {{% endif %}}

            <form action="/settings" method="POST" class="space-y-5">
                <div>
                    <label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2 ml-1">Current Architect ID</label>
                    <input type="text" value="{{ session.user }}" disabled class="w-full bg-black/50 border border-white/5 text-gray-500 px-4 py-3 rounded-xl font-mono text-sm cursor-not-allowed">
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-cyan-500 uppercase tracking-widest mb-2 ml-1">New Architect ID (Optional)</label>
                    <input type="text" name="new_username" class="w-full glass-input px-4 py-3 rounded-xl font-mono text-sm" placeholder="Enter new ID...">
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-cyan-500 uppercase tracking-widest mb-2 ml-1">New Secure Passkey (Optional)</label>
                    <input type="password" name="new_password" class="w-full glass-input px-4 py-3 rounded-xl font-mono text-sm" placeholder="Enter new password...">
                </div>
                <div class="pt-4">
                    <button type="submit" class="w-full py-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-sm uppercase tracking-[0.2em] transition-all">
                        Commit Changes to Database
                    </button>
                </div>
            </form>
        </div>
    </div>
    {COPYRIGHT_FOOTER}
</body></html>
"""


# ==========================================
# 5. FLASK ROUTING LOGIC
# ==========================================

@app.route('/')
def home():
    """Route to login if not authenticated, else dashboard."""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    """Handles authentication checks against the SYSTEM_USERS dictionary."""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username in SYSTEM_USERS and SYSTEM_USERS[username]['password'] == password:
        session['user'] = username
        return redirect(url_for('dashboard'))
    
    flash("ACCESS DENIED: Invalid credentials detected.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    """Clears the session."""
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    """Main interactive AI interface."""
    if 'user' not in session:
        return redirect(url_for('home'))
    return render_template_string(DASHBOARD_HTML)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Allows user to change their ID and Password."""
    if 'user' not in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        current_user = session['user']
        new_username = request.form.get('new_username').strip()
        new_password = request.form.get('new_password').strip()
        
        # We need to update the in-memory database
        user_data = SYSTEM_USERS.pop(current_user) # Remove old entry
        
        if new_username:
            target_username = new_username
        else:
            target_username = current_user
            
        if new_password:
            user_data['password'] = new_password
            
        # Save back to database
        SYSTEM_USERS[target_username] = user_data
        session['user'] = target_username # Update session
        
        flash("SYSTEM UPDATED: Credentials successfully modified in active matrix.")
        return redirect(url_for('settings'))

    return render_template_string(SETTINGS_HTML)

@app.route('/api/ai_analyze', methods=['POST'])
def api_ai_analyze():
    """
    Asynchronous endpoint called by JavaScript to fetch the AI Engine's 
    medical breakdown without reloading the webpage.
    """
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    spo2 = request.form.get('spo2')
    rr = request.form.get('rr')
    hr = request.form.get('hr')
    cough = request.form.get('cough')
    sob = request.form.get('sob')
    
    # Process through our class logic
    result = AILungEngine.analyze_vitals(spo2, rr, hr, cough, sob)
    
    return jsonify(result)

# ==========================================
# 6. APPLICATION ENTRY POINT
# ==========================================
if __name__ == '__main__':
    # Run the server. In production with Gunicorn, this block is bypassed.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
