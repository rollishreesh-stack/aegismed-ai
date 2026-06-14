import os
import time
import random
import json
import sqlite3
import threading
from datetime import datetime
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, Response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_premium_matrix_2026")
DB_NAME = "aerolung_telemetry.db"

# ==========================================
# 1. DATABASE INITIALIZATION (FIXED)
# ==========================================
# By running this outside of the __main__ block, we guarantee the database 
# is created regardless of how your web server (Gunicorn/Flask) runs the app.
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY, timestamp TEXT, event TEXT, severity TEXT)''')
    
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed_pw = generate_password_hash('admin2026')
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  ('admin', hashed_pw, 'Chief Architect'))
    
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. LIVE PATIENT SIMULATION ENGINE
# ==========================================
class QuantumPatientState:
    def __init__(self):
        self.hr = 95.0     
        self.spo2 = 88.0   
        self.rr = 24.0     
        self.sys_bp = 100.0 
        
        self.target_hr = 75.0
        self.target_spo2 = 98.0
        self.target_rr = 14.0
        self.target_sys_bp = 120.0
        
        self.volatility = 1.0 
        self.lock = threading.Lock()

    def apply_intervention(self, med_type):
        with self.lock:
            if med_type == "oxygen":
                self.target_spo2 = min(100.0, self.target_spo2 + 8.0)
                self.target_rr = max(12.0, self.target_rr - 4.0)
                return "Administered 100% FiO2. Alveolar recruitment initiated."
            elif med_type == "epinephrine":
                self.target_hr = min(180.0, self.target_hr + 30.0)
                self.target_sys_bp = min(180.0, self.target_sys_bp + 40.0)
                return "Administered 1mg Epinephrine. Sympathetic nervous system stimulated."
            elif med_type == "bronchodilator":
                self.target_spo2 = min(100.0, self.target_spo2 + 4.0)
                self.target_rr = max(12.0, self.target_rr - 6.0)
                self.volatility = max(0.2, self.volatility - 0.3)
                return "Administered Albuterol. Airway resistance decreased."
            elif med_type == "sedative":
                self.target_hr = max(50.0, self.target_hr - 15.0)
                self.target_rr = max(8.0, self.target_rr - 5.0)
                self.target_sys_bp = max(80.0, self.target_sys_bp - 15.0)
                return "Administered Propofol. Metabolic demand reduced."
        return "Unknown intervention."

    def tick(self):
        with self.lock:
            self.hr += (self.target_hr - self.hr) * 0.05 + (random.uniform(-1, 1) * self.volatility)
            self.spo2 += (self.target_spo2 - self.spo2) * 0.05 + (random.uniform(-0.5, 0.5) * self.volatility)
            self.rr += (self.target_rr - self.rr) * 0.05 + (random.uniform(-0.5, 0.5) * self.volatility)
            self.sys_bp += (self.target_sys_bp - self.sys_bp) * 0.05 + (random.uniform(-1, 1) * self.volatility)
            
            self.spo2 = max(0.0, min(100.0, self.spo2))
            self.hr = max(0.0, self.hr)
            self.rr = max(0.0, self.rr)

            return {
                "hr": round(self.hr, 1),
                "spo2": round(self.spo2, 1),
                "rr": round(self.rr, 1),
                "bp": round(self.sys_bp, 1),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }

GLOBAL_PATIENT = QuantumPatientState()

# ==========================================
# 3. PREMIUM UI & ASSETS
# ==========================================

GLOBAL_CSS = """
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Inter', sans-serif; background-color: #020617; color: #f8fafc; margin: 0; height: 100vh; overflow: hidden; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    
    /* Clean, premium glassmorphism without neon outlines */
    .premium-panel { 
        background: rgba(15, 23, 42, 0.6); 
        backdrop-filter: blur(16px); 
        border: 1px solid rgba(255, 255, 255, 0.05); 
        border-radius: 16px;
        box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.5); 
    }
    
    .clean-input {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        transition: all 0.3s ease;
    }
    .clean-input:focus { outline: none; border-color: #38bdf8; background: rgba(0, 0, 0, 0.5); }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }

    /* Custom Particle Canvas */
    #particle-lung { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; opacity: 0.8; }
</style>
"""

PARTICLE_ENGINE_JS = """
<script>
    const canvas = document.getElementById('particle-lung');
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    let particles = [];
    let current_rr = 15.0; 

    class LungNode {
        constructor(x, y, isRightLobe) {
            this.baseX = x;
            this.baseY = y;
            this.x = x;
            this.y = y;
            this.size = Math.random() * 1.5 + 0.5;
            // Clean, sophisticated blue/white particles
            this.color = Math.random() > 0.5 ? 'rgba(56, 189, 248, 0.6)' : 'rgba(255, 255, 255, 0.4)';
            this.isRight = isRightLobe;
            this.expandFactorX = (Math.random() * 12 + 3) * (this.isRight ? 1 : -1);
            this.expandFactorY = Math.random() * 15 + 3;
            this.phase = Math.random() * Math.PI;
        }
        update(time) {
            let breathCycle = Math.sin(time * (current_rr / 60) * Math.PI * 2);
            this.x = this.baseX + (breathCycle * this.expandFactorX);
            this.y = this.baseY + (breathCycle * this.expandFactorY);
        }
        draw() {
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function initLung() {
        particles = [];
        let cx = canvas.width / 2;
        let cy = canvas.height / 2;
        
        for(let i=0; i<80; i++) {
            particles.push(new LungNode(cx + (Math.random()*20-10), cy - 130 + (Math.random()*80), true));
        }
        for(let i=0; i<500; i++) {
            let r = Math.random() * 70;
            let angle = Math.random() * Math.PI * 2;
            let px = cx + 60 + r * Math.cos(angle);
            let py = cy + 40 + (r * 1.4) * Math.sin(angle);
            particles.push(new LungNode(px, py, true));
        }
        for(let i=0; i<500; i++) {
            let r = Math.random() * 70;
            let angle = Math.random() * Math.PI * 2;
            let px = cx - 60 + r * Math.cos(angle);
            let py = cy + 40 + (r * 1.4) * Math.sin(angle);
            particles.push(new LungNode(px, py, false));
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        let time = Date.now() / 1000;
        particles.forEach(p => { p.update(time); p.draw(); });
        
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        for(let i=0; i<particles.length; i+=12) {
            for(let j=i+1; j<particles.length; j+=12) {
                let dx = particles[i].x - particles[j].x;
                let dy = particles[i].y - particles[j].y;
                if(dx*dx + dy*dy < 1200) {
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                }
            }
        }
        ctx.stroke();
        requestAnimationFrame(animate);
    }

    window.addEventListener('resize', () => {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
        initLung();
    });

    initLung();
    animate();
</script>
"""

# ==========================================
# 4. HTML TEMPLATES
# ==========================================

LOGIN_HTML = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>AeroLung | Authentication</title>{GLOBAL_CSS}</head>
<body class="flex items-center justify-center relative">
    <div class="absolute inset-0 z-0 pointer-events-none"><canvas id="particle-lung" class="w-full h-full"></canvas></div>
    
    <div class="premium-panel p-10 w-full max-w-md z-10 text-center relative overflow-hidden">
        <h1 class="text-4xl font-black text-white tracking-tight mb-1">AERO<span class="text-sky-400">LUNG</span></h1>
        <p class="text-xs text-slate-400 font-medium uppercase tracking-[0.2em] mb-8">Clinical Telemetry System</p>
        
        {{% if get_flashed_messages() %}}
            <div class="mb-6 p-3 text-xs text-rose-400 bg-rose-950/30 border border-rose-900/50 rounded-lg">
                {{% for msg in get_flashed_messages() %}} {{ msg }} {{% endfor %}}
            </div>
        {{% endif %}}

        <form action="/login" method="POST" class="space-y-5 text-left">
            <div>
                <label class="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">User ID</label>
                <input type="text" name="username" class="w-full clean-input rounded-xl px-4 py-3 text-sm font-mono" placeholder="Enter ID" required>
            </div>
            <div>
                <label class="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Password</label>
                <input type="password" name="password" class="w-full clean-input rounded-xl px-4 py-3 text-sm font-mono" placeholder="••••••••" required>
            </div>
            <button type="submit" class="w-full mt-6 py-3.5 bg-sky-500 hover:bg-sky-400 text-white rounded-xl font-bold uppercase tracking-wider transition-colors shadow-lg shadow-sky-500/20">
                Authenticate
            </button>
        </form>
        
        <div class="mt-8 text-[10px] text-slate-500 font-medium tracking-wide">
            &copy; 2026 Shreesh Santoshkumar Rolli
        </div>
    </div>
    {PARTICLE_ENGINE_JS}
</body></html>
"""

DASHBOARD_HTML = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>AeroLung | Master Dashboard</title>{GLOBAL_CSS}</head>
<body class="flex flex-col relative">
    <div class="absolute inset-0 bg-gradient-to-b from-slate-900 to-slate-950 z-[-2]"></div>
    <div class="absolute inset-0 z-[-1] pointer-events-none"><canvas id="particle-lung" class="w-full h-full"></canvas></div>

    <header class="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 flex justify-between items-center px-8 py-4 z-10">
        <div class="flex items-center gap-4">
            <div class="text-2xl font-black text-white tracking-tight">AERO<span class="text-sky-400">LUNG</span></div>
            <div class="border-l border-slate-700 pl-4">
                <div class="text-xs text-slate-300 font-medium">Dr. {{ session.user }}</div>
                <div class="text-[10px] text-emerald-400 font-mono tracking-widest uppercase">Live Telemetry Active</div>
            </div>
        </div>
        <div class="flex items-center gap-6">
            <div id="clock" class="text-sm font-mono text-slate-300"></div>
            <a href="/logout" class="text-xs font-semibold bg-slate-800 hover:bg-rose-900 hover:text-rose-100 text-slate-300 px-4 py-2 rounded-lg transition-colors border border-slate-700 hover:border-rose-800">Sign Out</a>
        </div>
    </header>

    <main class="flex-1 grid grid-cols-12 gap-6 p-6 z-10 overflow-hidden h-full max-w-[1800px] mx-auto w-full">
        
        <div class="col-span-12 lg:col-span-3 flex flex-col gap-4 h-full">
            <div class="premium-panel p-5 flex-1 flex flex-col relative group">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Heart Rate</span>
                    <span class="text-sky-400 font-mono text-xs">BPM</span>
                </div>
                <div class="text-5xl font-light text-white mb-2 tracking-tighter" id="val-hr">--</div>
                <div class="flex-1 relative"><canvas id="chart-hr"></canvas></div>
            </div>
            
            <div class="premium-panel p-5 flex-1 flex flex-col relative group">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-[11px] font-bold text-slate-400 uppercase tracking-widest">SpO2 Oxygen</span>
                    <span class="text-emerald-400 font-mono text-xs">%</span>
                </div>
                <div class="text-5xl font-light text-white mb-2 tracking-tighter" id="val-spo2">--</div>
                <div class="flex-1 relative"><canvas id="chart-spo2"></canvas></div>
            </div>
            
            <div class="premium-panel p-5 flex-1 flex flex-col relative group">
                <div class="flex justify-between items-start mb-2">
                    <span class="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Resp Rate</span>
                    <span class="text-amber-400 font-mono text-xs">/MIN</span>
                </div>
                <div class="text-5xl font-light text-white mb-2 tracking-tighter" id="val-rr">--</div>
                <div class="flex-1 relative"><canvas id="chart-rr"></canvas></div>
            </div>
        </div>

        <div class="col-span-12 lg:col-span-6 flex flex-col justify-end items-center pb-8">
            <div class="premium-panel w-full max-w-lg p-8 text-center bg-slate-900/80">
                <div class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-3">Diagnostic Status</div>
                <div id="ai-status" class="text-2xl font-bold text-white tracking-tight">Synchronizing...</div>
            </div>
        </div>

        <div class="col-span-12 lg:col-span-3 flex flex-col gap-4 h-full">
            <div class="premium-panel p-5">
                <h3 class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-4">Interventions</h3>
                <div class="grid grid-cols-1 gap-2">
                    <button onclick="inject('oxygen')" class="bg-slate-800/50 hover:bg-sky-900/40 border border-slate-700 hover:border-sky-500/50 text-slate-300 py-3 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex justify-between px-4">
                        <span>Oxygen Therapy</span> <span class="text-sky-400">100% FiO2</span>
                    </button>
                    <button onclick="inject('bronchodilator')" class="bg-slate-800/50 hover:bg-emerald-900/40 border border-slate-700 hover:border-emerald-500/50 text-slate-300 py-3 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex justify-between px-4">
                        <span>Albuterol</span> <span class="text-emerald-400">Administer</span>
                    </button>
                    <button onclick="inject('epinephrine')" class="bg-slate-800/50 hover:bg-rose-900/40 border border-slate-700 hover:border-rose-500/50 text-slate-300 py-3 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex justify-between px-4">
                        <span>Epinephrine</span> <span class="text-rose-400">1mg IV</span>
                    </button>
                    <button onclick="inject('sedative')" class="bg-slate-800/50 hover:bg-purple-900/40 border border-slate-700 hover:border-purple-500/50 text-slate-300 py-3 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex justify-between px-4">
                        <span>Propofol</span> <span class="text-purple-400">Sedate</span>
                    </button>
                </div>
            </div>

            <div class="premium-panel p-5 flex-1 flex flex-col">
                <h3 class="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-4">System Event Log</h3>
                <div id="terminal-output" class="flex-1 overflow-y-auto font-mono text-[11px] text-slate-400 space-y-2 flex flex-col justify-end pb-2">
                </div>
            </div>
        </div>
    </main>

    {PARTICLE_ENGINE_JS}

    <script>
        setInterval(() => document.getElementById('clock').innerText = new Date().toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit', second:'2-digit'}}), 1000);

        Chart.defaults.color = '#64748b';
        Chart.defaults.font.family = "'JetBrains Mono', monospace";
        const chartOptions = {{
            responsive: true, maintainAspectRatio: false, animation: false,
            plugins: {{ legend: {{ display: false }} }},
            elements: {{ point: {{ radius: 0 }}, line: {{ tension: 0.4, borderWidth: 2 }} }},
            scales: {{ x: {{ display: false }}, y: {{ grid: {{ color: 'rgba(255,255,255,0.05)', borderDash: [4, 4] }} }} }}
        }};

        function createChart(ctxId, color) {{
            return new Chart(document.getElementById(ctxId), {{
                type: 'line',
                data: {{ labels: Array(40).fill(''), datasets: [{{ data: Array(40).fill(null), borderColor: color, fill: true, backgroundColor: color+'15' }}] }},
                options: chartOptions
            }});
        }}

        const chartHR = createChart('chart-hr', '#38bdf8');   // Sky blue
        const chartSpO2 = createChart('chart-spo2', '#34d399'); // Emerald
        const chartRR = createChart('chart-rr', '#fbbf24');    // Amber

        function logToTerminal(msg) {{
            const term = document.getElementById('terminal-output');
            const p = document.createElement('div');
            p.innerHTML = `<span class="text-slate-500">[${{new Date().toLocaleTimeString()}}]</span> ${{msg}}`;
            term.appendChild(p);
            if(term.children.length > 12) term.removeChild(term.firstChild);
        }}

        const evtSource = new EventSource("/api/stream");
        
        evtSource.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            
            document.getElementById('val-hr').innerText = Math.round(data.hr);
            document.getElementById('val-spo2').innerText = Math.round(data.spo2);
            document.getElementById('val-rr').innerText = Math.round(data.rr);
            
            current_rr = data.rr;

            let status = "Stable Homeostasis";
            let colorClass = "text-emerald-400";
            
            if (data.spo2 < 90 || data.hr > 130 || data.rr > 30) {{ 
                status = "Critical Instability"; 
                colorClass = "text-rose-400"; 
            }}
            else if (data.spo2 < 95 || data.hr > 100) {{ 
                status = "Compensatory Distress"; 
                colorClass = "text-amber-400"; 
            }}
            
            const statusEl = document.getElementById('ai-status');
            statusEl.className = `text-2xl font-bold tracking-tight ${{colorClass}}`;
            statusEl.innerText = status;

            function pushData(chart, val) {{
                let d = chart.data.datasets[0].data;
                d.push(val);
                d.shift();
                chart.update();
            }}
            pushData(chartHR, data.hr);
            pushData(chartSpO2, data.spo2);
            pushData(chartRR, data.rr);
        }};

        async function inject(med) {{
            logToTerminal(`Administering protocol: <span class="text-sky-300">${{med}}</span>`);
            const formData = new FormData();
            formData.append('med_type', med);
            try {{
                const res = await fetch('/api/intervene', {{ method: 'POST', body: formData }});
                const json = await res.json();
                logToTerminal(`<span class="text-emerald-400">Success:</span> ${{json.message}}`);
            }} catch(e) {{
                logToTerminal(`<span class="text-rose-400">Error:</span> Uplink failed.`);
            }}
        }}

        logToTerminal("System initialized. Awaiting biological telemetry.");
    </script>
</body></html>
"""

# ==========================================
# 5. ROUTES
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
    
    flash("Authentication failed. Invalid credentials.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/stream')
def stream():
    if 'user' not in session: return "Unauthorized", 401

    def generate_telemetry():
        while True:
            data = GLOBAL_PATIENT.tick() 
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1) 

    return Response(generate_telemetry(), mimetype='text/event-stream')

@app.route('/api/intervene', methods=['POST'])
def intervene():
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    med_type = request.form.get('med_type')
    message = GLOBAL_PATIENT.apply_intervention(med_type)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO logs (timestamp, event, severity) VALUES (?, ?, ?)", 
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"{session['user']} deployed {med_type}", "ACTION"))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": message})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True, threaded=True)
