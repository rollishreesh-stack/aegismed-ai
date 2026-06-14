import os
import time
import math
import json
import random
import sqlite3
import threading
from datetime import datetime
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, Response, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# ==========================================
# 1. SERVER & DATABASE ARCHITECTURE
# ==========================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sdg_quantum_matrix_shreesh_2026")
DB_NAME = "global_telemetry.db"

def init_db():
    """Initializes a real persistent SQLite Database with hashed passwords."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY, timestamp TEXT, event TEXT, severity TEXT)''')
    
    # Create default Admin if not exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed_pw = generate_password_hash('admin2026')
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  ('admin', hashed_pw, 'Global System Architect'))
    
    conn.commit()
    conn.close()

# ==========================================
# 2. LIVE PATIENT SIMULATION ENGINE (STATEFUL)
# ==========================================
class QuantumPatientState:
    """
    Advanced stateful simulator. Vitals drift organically over time.
    Interventions push vitals towards healthy baselines.
    """
    def __init__(self):
        self.hr = 95.0     # Heart Rate
        self.spo2 = 88.0   # Blood Oxygen
        self.rr = 24.0     # Respiratory Rate
        self.sys_bp = 100.0 # Systolic BP
        
        self.target_hr = 75.0
        self.target_spo2 = 98.0
        self.target_rr = 14.0
        self.target_sys_bp = 120.0
        
        self.volatility = 1.0 # How chaotic the vitals are
        self.lock = threading.Lock()

    def apply_intervention(self, med_type):
        """Modifies physiological targets based on chemical inputs."""
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
        """Simulates physiological drift every second."""
        with self.lock:
            # Move current values towards targets smoothly (with organic noise)
            self.hr += (self.target_hr - self.hr) * 0.05 + (random.uniform(-1, 1) * self.volatility)
            self.spo2 += (self.target_spo2 - self.spo2) * 0.05 + (random.uniform(-0.5, 0.5) * self.volatility)
            self.rr += (self.target_rr - self.rr) * 0.05 + (random.uniform(-0.5, 0.5) * self.volatility)
            self.sys_bp += (self.target_sys_bp - self.sys_bp) * 0.05 + (random.uniform(-1, 1) * self.volatility)
            
            # Constrain physics
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

# Global Patient Instance
GLOBAL_PATIENT = QuantumPatientState()

# ==========================================
# 3. ADVANCED FRONTEND ASSETS
# ==========================================

GLOBAL_CSS = """
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
<style>
    :root { --matrix-cyan: #00f3ff; --matrix-green: #00ff88; --matrix-red: #ff003c; --bg-deep: #030508; }
    body { font-family: 'Rajdhani', sans-serif; background-color: var(--bg-deep); color: #fff; margin: 0; height: 100vh; overflow: hidden; }
    .font-tech { font-family: 'Orbitron', sans-serif; }
    
    /* 3D Glass Morphism */
    .cyber-panel { 
        background: rgba(4, 13, 26, 0.6); 
        backdrop-filter: blur(12px); 
        border: 1px solid rgba(0, 243, 255, 0.15); 
        box-shadow: inset 0 0 20px rgba(0, 243, 255, 0.05), 0 10px 30px rgba(0, 0, 0, 0.8); 
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(0, 243, 255, 0.5); }
    
    /* CRT Scanline Effect */
    .scanlines { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06)); background-size: 100% 4px, 6px 100%; pointer-events: none; z-index: 9999; }
    
    /* Glowing Text Classes */
    .glow-cyan { text-shadow: 0 0 10px var(--matrix-cyan); }
    .glow-red { text-shadow: 0 0 10px var(--matrix-red); }
    
    /* Canvas background for Particle Engine */
    #particle-lung { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; opacity: 0.7; }
</style>
"""

# The script that powers the Custom Physics Particle Lung
PARTICLE_ENGINE_JS = """
<script>
    const canvas = document.getElementById('particle-lung');
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    let particles = [];
    let current_rr = 15.0; // Modulates breathing speed dynamically!

    class LungNode {
        constructor(x, y, isRightLobe) {
            this.baseX = x;
            this.baseY = y;
            this.x = x;
            this.y = y;
            this.size = Math.random() * 2 + 0.5;
            this.color = Math.random() > 0.8 ? '#00f3ff' : '#00a3ff';
            // Determine expansion physics based on position
            this.isRight = isRightLobe;
            this.expandFactorX = (Math.random() * 15 + 5) * (this.isRight ? 1 : -1);
            this.expandFactorY = Math.random() * 20 + 5;
            this.phase = Math.random() * Math.PI;
        }
        update(time) {
            // Live breathing simulation tied to real-time Respiratory Rate
            let breathCycle = Math.sin(time * (current_rr / 60) * Math.PI * 2);
            // Smoothly move particles
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
        
        // Trachea
        for(let i=0; i<100; i++) {
            particles.push(new LungNode(cx + (Math.random()*30-15), cy - 150 + (Math.random()*100), true));
        }
        // Right Lobe
        for(let i=0; i<600; i++) {
            let r = Math.random() * 80;
            let angle = Math.random() * Math.PI * 2;
            let px = cx + 70 + r * Math.cos(angle);
            let py = cy + 50 + (r * 1.5) * Math.sin(angle);
            particles.push(new LungNode(px, py, true));
        }
        // Left Lobe
        for(let i=0; i<600; i++) {
            let r = Math.random() * 80;
            let angle = Math.random() * Math.PI * 2;
            let px = cx - 70 + r * Math.cos(angle);
            let py = cy + 50 + (r * 1.5) * Math.sin(angle);
            particles.push(new LungNode(px, py, false));
        }
    }

    function animate() {
        ctx.fillStyle = 'rgba(3, 5, 8, 0.15)'; // Trail effect
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        let time = Date.now() / 1000;
        particles.forEach(p => {
            p.update(time);
            p.draw();
        });
        
        // Draw Neural Connections between close nodes
        ctx.strokeStyle = 'rgba(0, 243, 255, 0.05)';
        ctx.beginPath();
        for(let i=0; i<particles.length; i+=15) {
            for(let j=i+1; j<particles.length; j+=15) {
                let dx = particles[i].x - particles[j].x;
                let dy = particles[i].y - particles[j].y;
                if(dx*dx + dy*dy < 1500) {
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
# 4. VIEWS / TEMPLATES
# ==========================================

LOGIN_HTML = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Global Health Matrix</title>{GLOBAL_CSS}</head>
<body class="flex items-center justify-center">
    <div class="scanlines"></div>
    <div class="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
    
    <div class="cyber-panel p-12 rounded-lg w-full max-w-md z-10 text-center relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#00f3ff] to-transparent opacity-50"></div>
        <h1 class="text-5xl font-tech font-black text-white tracking-widest mb-2 glow-cyan">SDG<span class="text-[#00f3ff]">03</span></h1>
        <p class="text-xs text-[#00f3ff] uppercase tracking-[0.4em] mb-10 font-bold">Quantum Telemetry Node</p>
        
        {{% if get_flashed_messages() %}}
            <div class="mb-6 p-3 text-xs text-[#ff003c] border border-[#ff003c] bg-[#ff003c]/10 uppercase glow-red">
                {{% for msg in get_flashed_messages() %}} {{ msg }} {{% endfor %}}
            </div>
        {{% endif %}}

        <form action="/login" method="POST" class="space-y-6 text-left">
            <div>
                <label class="block text-[10px] text-[#00f3ff] uppercase tracking-widest mb-2">Architect ID</label>
                <input type="text" name="username" class="w-full bg-transparent border-b border-[#00f3ff]/50 text-white p-2 focus:outline-none focus:border-[#00f3ff] transition-colors" required>
            </div>
            <div>
                <label class="block text-[10px] text-[#00f3ff] uppercase tracking-widest mb-2">Decryption Key</label>
                <input type="password" name="password" class="w-full bg-transparent border-b border-[#00f3ff]/50 text-white p-2 focus:outline-none focus:border-[#00f3ff] transition-colors" required>
            </div>
            <button type="submit" class="w-full mt-8 py-4 bg-[#00f3ff]/10 hover:bg-[#00f3ff]/30 text-[#00f3ff] border border-[#00f3ff] font-bold tracking-[0.3em] uppercase transition-all shadow-[0_0_15px_rgba(0,243,255,0.2)]">
                Initialize Matrix
            </button>
        </form>
        
        <div class="mt-8 text-[9px] text-gray-500 tracking-widest uppercase flex justify-center gap-2 items-center">
            &copy; 2026 <span class="w-1 h-1 bg-[#00f3ff] rounded-full animate-pulse"></span> Shreesh Santoshkumar Rolli
        </div>
    </div>
</body></html>
"""

DASHBOARD_HTML = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>SDG Quantum Dashboard</title>{GLOBAL_CSS}</head>
<body class="flex flex-col relative">
    <div class="scanlines"></div>
    
    <div class="absolute inset-0 z-0 pointer-events-none"><canvas id="particle-lung" class="w-full h-full"></canvas></div>

    <header class="cyber-panel border-b border-t-0 border-l-0 border-r-0 flex justify-between items-center px-8 py-4 z-10">
        <div class="flex items-center gap-4">
            <div class="text-3xl font-tech font-black text-white glow-cyan">SDG<span class="text-[#00f3ff]">03</span></div>
            <div class="border-l border-[#00f3ff]/30 pl-4">
                <div class="text-[10px] text-[#00f3ff] tracking-[0.2em] uppercase font-bold">Global Health AI</div>
                <div class="text-xs text-gray-400">Authenticated: {{ session.user }}</div>
            </div>
        </div>
        <div class="flex items-center gap-6">
            <div class="text-right">
                <div id="clock" class="text-xl font-tech text-[#00ff88]"></div>
                <div class="text-[9px] text-[#00ff88]/60 uppercase tracking-widest">Live Sync Active</div>
            </div>
            <a href="/logout" class="text-[10px] border border-[#ff003c]/50 text-[#ff003c] px-4 py-2 hover:bg-[#ff003c]/20 transition-all uppercase tracking-widest">Terminate</a>
        </div>
    </header>

    <main class="flex-1 grid grid-cols-12 gap-6 p-6 z-10 overflow-hidden h-full">
        
        <div class="col-span-3 flex flex-col gap-6 h-full">
            <div class="cyber-panel p-4 flex-1 flex flex-col relative">
                <div class="absolute top-0 right-0 bg-[#00f3ff]/20 text-[#00f3ff] text-[9px] px-2 py-1 uppercase tracking-widest">Live EKG / HR</div>
                <div class="text-4xl font-tech font-bold text-[#00f3ff] mt-4 mb-2" id="val-hr">--</div>
                <div class="flex-1 relative"><canvas id="chart-hr"></canvas></div>
            </div>
            
            <div class="cyber-panel p-4 flex-1 flex flex-col relative">
                <div class="absolute top-0 right-0 bg-[#00ff88]/20 text-[#00ff88] text-[9px] px-2 py-1 uppercase tracking-widest">SpO2 Level</div>
                <div class="text-4xl font-tech font-bold text-[#00ff88] mt-4 mb-2" id="val-spo2">--</div>
                <div class="flex-1 relative"><canvas id="chart-spo2"></canvas></div>
            </div>
            
            <div class="cyber-panel p-4 flex-1 flex flex-col relative">
                <div class="absolute top-0 right-0 bg-yellow-500/20 text-yellow-400 text-[9px] px-2 py-1 uppercase tracking-widest">Resp Rate</div>
                <div class="text-4xl font-tech font-bold text-yellow-400 mt-4 mb-2" id="val-rr">--</div>
                <div class="flex-1 relative"><canvas id="chart-rr"></canvas></div>
            </div>
        </div>

        <div class="col-span-6 flex flex-col justify-end items-center pb-12">
            <div class="cyber-panel w-full p-6 text-center">
                <div class="text-[10px] text-[#00f3ff] uppercase tracking-[0.4em] mb-2">System AI Diagnosis</div>
                <div id="ai-status" class="text-2xl font-tech font-black text-white glow-cyan uppercase tracking-widest">Analyzing Biometrics...</div>
            </div>
        </div>

        <div class="col-span-3 flex flex-col gap-6 h-full">
            
            <div class="cyber-panel p-5">
                <h3 class="text-[10px] text-[#00f3ff] uppercase tracking-[0.2em] mb-4 border-b border-[#00f3ff]/30 pb-2">Medical Protocols</h3>
                <div class="grid grid-cols-1 gap-3">
                    <button onclick="inject('oxygen')" class="border border-blue-500/50 hover:bg-blue-500/20 text-blue-400 py-3 text-xs uppercase tracking-widest font-bold flex justify-between px-4">
                        <span>[100% FiO2]</span> <span>Deploy</span>
                    </button>
                    <button onclick="inject('epinephrine')" class="border border-red-500/50 hover:bg-red-500/20 text-red-400 py-3 text-xs uppercase tracking-widest font-bold flex justify-between px-4">
                        <span>[Epinephrine]</span> <span>Inject</span>
                    </button>
                    <button onclick="inject('bronchodilator')" class="border border-[#00ff88]/50 hover:bg-[#00ff88]/20 text-[#00ff88] py-3 text-xs uppercase tracking-widest font-bold flex justify-between px-4">
                        <span>[Albuterol]</span> <span>Nebulize</span>
                    </button>
                    <button onclick="inject('sedative')" class="border border-purple-500/50 hover:bg-purple-500/20 text-purple-400 py-3 text-xs uppercase tracking-widest font-bold flex justify-between px-4">
                        <span>[Propofol]</span> <span>Sedate</span>
                    </button>
                </div>
            </div>

            <div class="cyber-panel p-5 flex-1 flex flex-col">
                <h3 class="text-[10px] text-[#00f3ff] uppercase tracking-[0.2em] mb-4 border-b border-[#00f3ff]/30 pb-2">AI Neural Terminal</h3>
                <div id="terminal-output" class="flex-1 overflow-y-auto font-tech text-xs text-[#00ff88]/80 space-y-2 flex flex-col justify-end pb-2">
                    </div>
            </div>

        </div>
    </main>

    <footer class="cyber-panel py-2 text-center z-10 border-b-0 border-l-0 border-r-0">
        <div class="text-[9px] font-tech text-gray-500 uppercase tracking-widest">
            &copy; 2026 | Shreesh Santoshkumar Rolli | Advanced SDG3 AI Architecture
        </div>
    </footer>

    {PARTICLE_ENGINE_JS}

    <script>
        // Clock
        setInterval(() => document.getElementById('clock').innerText = new Date().toLocaleTimeString(), 1000);

        // Chart.js Setup for Real-time Streaming
        Chart.defaults.color = 'rgba(255,255,255,0.4)';
        Chart.defaults.font.family = 'Orbitron';
        const chartOptions = {{
            responsive: true, maintainAspectRatio: false, animation: false,
            plugins: {{ legend: {{ display: false }} }},
            elements: {{ point: {{ radius: 0 }}, line: {{ tension: 0.3, borderWidth: 2 }} }},
            scales: {{ x: {{ display: false }}, y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }} }} }}
        }};

        function createChart(ctxId, color) {{
            return new Chart(document.getElementById(ctxId), {{
                type: 'line',
                data: {{ labels: Array(40).fill(''), datasets: [{{ data: Array(40).fill(null), borderColor: color, fill: true, backgroundColor: color+'20' }}] }},
                options: chartOptions
            }});
        }}

        const chartHR = createChart('chart-hr', '#00f3ff');
        const chartSpO2 = createChart('chart-spo2', '#00ff88');
        const chartRR = createChart('chart-rr', '#facc15');

        function logToTerminal(msg) {{
            const term = document.getElementById('terminal-output');
            const p = document.createElement('div');
            p.innerText = `> ${{new Date().toLocaleTimeString()}}: ${{msg}}`;
            term.appendChild(p);
            if(term.children.length > 15) term.removeChild(term.firstChild);
        }}

        // Establish Server-Sent Events (SSE) Connection
        const evtSource = new EventSource("/api/stream");
        
        evtSource.onmessage = function(event) {{
            const data = JSON.parse(event.data);
            
            // 1. Update Numbers
            document.getElementById('val-hr').innerText = data.hr;
            document.getElementById('val-spo2').innerText = data.spo2 + '%';
            document.getElementById('val-rr').innerText = data.rr;
            
            // 2. Pass Respiratory Rate to Custom Particle Physics Engine!
            current_rr = data.rr;

            // 3. Update AI Status
            let status = "OPTIMAL HOMEOSTASIS";
            let color = "text-[#00ff88]";
            if (data.spo2 < 90 || data.hr > 130 || data.rr > 30) {{ status = "CRITICAL INSTABILITY DETECTED"; color = "text-[#ff003c]"; }}
            else if (data.spo2 < 95 || data.hr > 100) {{ status = "COMPENSATORY MECHANISMS ACTIVE"; color = "text-yellow-400"; }}
            
            const statusEl = document.getElementById('ai-status');
            statusEl.className = `text-2xl font-tech font-black glow-cyan uppercase tracking-widest ${{color}}`;
            statusEl.innerText = status;

            // 4. Shift Chart Arrays
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

        // Interventions POST
        async function inject(med) {{
            logToTerminal(`Initiating ${{med}} sequence...`);
            const formData = new FormData();
            formData.append('med_type', med);
            try {{
                const res = await fetch('/api/intervene', {{ method: 'POST', body: formData }});
                const json = await res.json();
                logToTerminal(json.message);
            }} catch(e) {{
                logToTerminal(`ERROR: System uplink failed.`);
            }}
        }}

        logToTerminal("System initialized. Awaiting biological telemetry.");
    </script>
</body></html>
"""


# ==========================================
# 5. ADVANCED FLASK ROUTES
# ==========================================

@app.route('/')
def home():
    """Route to login if not authenticated, else dashboard."""
    if 'user' in session: return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    """Secure Database Authentication"""
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
    
    flash("ACCESS DENIED: Neural link rejected.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    return render_template_string(DASHBOARD_HTML)


# --- ADVANCED API ROUTES (STREAMING & INTERACTION) ---

@app.route('/api/stream')
def stream():
    """
    SERVER-SENT EVENTS (SSE): Yields continuous, real-time simulated data to the frontend 
    without the client needing to refresh or send requests.
    """
    if 'user' not in session: return "Unauthorized", 401

    def generate_telemetry():
        while True:
            data = GLOBAL_PATIENT.tick() # Calculate next physics step
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1) # Send data every 1 second continuously

    return Response(generate_telemetry(), mimetype='text/event-stream')


@app.route('/api/intervene', methods=['POST'])
def intervene():
    """
    Receives chemical/medical interventions from the frontend and pushes them 
    into the physics engine to alter the patient's biological trajectory.
    """
    if 'user' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    med_type = request.form.get('med_type')
    message = GLOBAL_PATIENT.apply_intervention(med_type)
    
    # Log to persistent database
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO logs (timestamp, event, severity) VALUES (?, ?, ?)", 
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"{session['user']} deployed {med_type}", "ACTION"))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": message})


if __name__ == '__main__':
    # 1. Initialize the SQLite DB
    init_db()
    # 2. Start the Matrix
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True, threaded=True)
