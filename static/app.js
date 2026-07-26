document.addEventListener('DOMContentLoaded', () => {
    const wsUrl = `ws://${window.location.host}/ws`;
    let ws;
    
    // UI Elements
    const statusDot = document.querySelector('#header-status .dot');
    const statusText = document.querySelector('#header-status .text');
    const headerStatus = document.getElementById('header-status');
    const ldrValueEl = document.getElementById('ldr-value');
    const statusValueEl = document.getElementById('status-value');
    const intrusionCountEl = document.getElementById('intrusion-count');
    const statusCard = document.getElementById('status-card');
    
    const modeSelect = document.getElementById('mode-select');
    const serialConfig = document.getElementById('serial-config');
    const manualConfig = document.getElementById('manual-config');
    const serialPortInput = document.getElementById('serial-port');
    const baudRateInput = document.getElementById('baud-rate');
    const manualSlider = document.getElementById('manual-slider');
    const manualValDisplay = document.getElementById('manual-val-display');
    const resetBtn = document.getElementById('reset-btn');
    const logTableBody = document.querySelector('#log-table tbody');
    const canvasContainer = document.getElementById('canvas-container');
    
    // Chart
    const ctx = document.getElementById('historyChart').getContext('2d');
    const historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'LDR Value',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 }, // For real-time feel without sliding delays
            scales: {
                y: { min: 0, max: 1023, grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8', maxTicksLimit: 10 } }
            },
            plugins: { legend: { display: false } }
        }
    });

    function connect() {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            headerStatus.className = 'status-indicator connected';
            statusText.textContent = 'Connected';
            sendConfig();
        };
        
        ws.onclose = () => {
            headerStatus.className = 'status-indicator disconnected';
            statusText.textContent = 'Disconnected - Reconnecting...';
            setTimeout(connect, 2000);
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };
    }

    function sendConfig() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                action: 'set_mode',
                mode: modeSelect.value,
                serial_port: serialPortInput.value,
                baud_rate: baudRateInput.value
            }));
        }
    }

    function sendManual() {
        if (ws && ws.readyState === WebSocket.OPEN && modeSelect.value === 'Manual Input') {
            ws.send(JSON.stringify({
                action: 'manual_input',
                ldr_value: manualSlider.value
            }));
        }
    }

    function updateDashboard(data) {
        // Mode switch check
        if (data.mode !== modeSelect.value) {
            modeSelect.value = data.mode;
            updateConfigVisibility();
        }

        // Metrics
        ldrValueEl.textContent = data.ldr;
        statusValueEl.textContent = data.status;
        intrusionCountEl.textContent = data.intrusion_count;
        
        if (data.status === 'INTRUSION') {
            statusValueEl.className = 'value status-intrusion';
            statusCard.classList.add('intrusion-active');
        } else {
            statusValueEl.className = 'value status-secure';
            statusCard.classList.remove('intrusion-active');
        }
        
        // Chart
        historyChart.data.labels = data.history.map(h => h.time);
        historyChart.data.datasets[0].data = data.history.map(h => h.ldr);
        historyChart.update();
        
        // Logs (only show intrusions)
        const intrusions = [...data.history].reverse().filter(h => h.status === 'INTRUSION');
        const intrusionsStr = JSON.stringify(intrusions);
        if (logTableBody.dataset.last === intrusionsStr) return;
        logTableBody.dataset.last = intrusionsStr;
        
        logTableBody.innerHTML = '';
        intrusions.forEach(log => {
            const tr = document.createElement('tr');
            tr.className = 'row-intrusion';
            tr.innerHTML = `<td>${log.time}</td><td>${log.ldr}</td><td>⚠️ INTRUSION</td>`;
            logTableBody.appendChild(tr);
        });
        if (intrusions.length === 0) {
            logTableBody.innerHTML = '<tr><td colspan="3" style="text-align:center; color:#94a3b8;">No intrusions recorded yet.</td></tr>';
        }
    }

    // Event Listeners
    function updateConfigVisibility() {
        serialConfig.classList.add('hidden');
        manualConfig.classList.add('hidden');
        canvasContainer.classList.add('hidden');
        
        if (modeSelect.value === 'Serial Port (Hardware)') serialConfig.classList.remove('hidden');
        if (modeSelect.value === 'Manual Input') manualConfig.classList.remove('hidden');
        if (modeSelect.value === 'Embedded Simulation') {
            canvasContainer.classList.remove('hidden');
            if(!simRunning) startSimulation();
        } else {
            simRunning = false; // Stop sim if not embedded
        }
    }

    modeSelect.addEventListener('change', () => {
        updateConfigVisibility();
        sendConfig();
    });
    
    serialPortInput.addEventListener('change', sendConfig);
    baudRateInput.addEventListener('change', sendConfig);
    
    manualSlider.addEventListener('input', (e) => {
        manualValDisplay.textContent = e.target.value;
        sendManual();
    });
    
    resetBtn.addEventListener('click', () => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'reset_count' }));
        }
    });

    // --- Embedded Simulation Logic ---
    const canvas = document.getElementById("farmCanvas");
    const ctxCanvas = canvas.getContext("2d");
    const FENCE_X = 200, FENCE_Y = 50, FENCE_W = 400, FENCE_H = 300;
    
    let audioCtx = null;
    let lastBuzzerTime = 0;
    
    function initAudio() {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    function playBuzzer(timestamp) {
        if (timestamp - lastBuzzerTime < 500) return;
        lastBuzzerTime = timestamp;
        if (!audioCtx) return;
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(100, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.3);
    }
    
    let keys = { ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false, w: false, a: false, s: false, d: false };
    
    // Key listeners must be on canvas or document, let's do window but require focus logic if needed.
    // For simplicity, window listeners.
    window.addEventListener('keydown', e => {
        if (keys.hasOwnProperty(e.key)) keys[e.key] = true;
        if (keys.hasOwnProperty(e.key.toLowerCase())) keys[e.key.toLowerCase()] = true;
        initAudio();
    });
    window.addEventListener('keyup', e => {
        if (keys.hasOwnProperty(e.key)) keys[e.key] = false;
        if (keys.hasOwnProperty(e.key.toLowerCase())) keys[e.key.toLowerCase()] = false;
    });
    
    canvas.addEventListener('mousedown', () => initAudio());

    function intersectsFence(x, y, radius) {
        let left = x - radius, right = x + radius, top = y - radius, bottom = y + radius;
        return (right > FENCE_X && left < FENCE_X + FENCE_W && bottom > FENCE_Y && top < FENCE_Y + FENCE_H);
    }

    class Animal {
        constructor(isPlayer = false) {
            this.isPlayer = isPlayer;
            if (Math.random() > 0.5) {
                this.x = Math.random() > 0.5 ? Math.random() * (FENCE_X - 50) : FENCE_X + FENCE_W + 50 + Math.random() * 100;
                this.y = Math.random() * canvas.height;
            } else {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() > 0.5 ? Math.random() * (FENCE_Y - 50) : FENCE_Y + FENCE_H + 50 + Math.random() * 50;
            }
            this.radius = 18;
            this.emoji = this.isPlayer ? "🐕" : (Math.random() > 0.5 ? "🐄" : "🐑");
            this.baseSpeed = this.isPlayer ? 3.5 : 0.2 + Math.random() * 0.4;
            this.state = "grazing";
            this.timer = Math.floor(60 + Math.random() * 120);
            this.angle = Math.random() * Math.PI * 2;
            this.vx = 0;
            this.vy = 0;
            this.isDragging = false;
            this.isColliding = false;
        }

        move(timestamp) {
            if (this.isDragging) return;
            if (this.isPlayer) {
                this.vx = 0; this.vy = 0;
                if (keys.ArrowUp || keys.w) this.vy = -this.baseSpeed;
                if (keys.ArrowDown || keys.s) this.vy = this.baseSpeed;
                if (keys.ArrowLeft || keys.a) this.vx = -this.baseSpeed;
                if (keys.ArrowRight || keys.d) this.vx = this.baseSpeed;
                if (this.vx !== 0 && this.vy !== 0) { this.vx *= 0.7071; this.vy *= 0.7071; }
            } else {
                this.timer--;
                if (this.timer <= 0) {
                    if (this.state === "grazing") {
                        this.state = "walking";
                        this.timer = Math.floor(120 + Math.random() * 300);
                        this.angle += (Math.random() - 0.5) * Math.PI; 
                        this.vx = Math.cos(this.angle) * this.baseSpeed;
                        this.vy = Math.sin(this.angle) * this.baseSpeed;
                    } else {
                        this.state = "grazing";
                        this.timer = Math.floor(180 + Math.random() * 300);
                        this.vx = 0; this.vy = 0;
                    }
                }
                if (this.state === "walking") {
                    this.angle += (Math.random() - 0.5) * 0.05;
                    this.vx = Math.cos(this.angle) * this.baseSpeed;
                    this.vy = Math.sin(this.angle) * this.baseSpeed;
                }
            }

            let newX = this.x + this.vx;
            let newY = this.y + this.vy;

            if (newX < this.radius || newX > canvas.width - this.radius) {
                if (!this.isPlayer) { this.vx *= -1; this.angle = Math.atan2(this.vy, this.vx); }
                newX = this.x;
            }
            if (newY < this.radius || newY > canvas.height - this.radius) {
                if (!this.isPlayer) { this.vy *= -1; this.angle = Math.atan2(this.vy, this.vx); }
                newY = this.y;
            }
            
            if (intersectsFence(newX, newY, this.radius)) {
                this.isColliding = true;
                if (!this.isPlayer) {
                    this.vx *= -1; this.vy *= -1;
                    this.angle = Math.atan2(this.vy, this.vx);
                }
                playBuzzer(timestamp);
            } else {
                this.x = newX;
                this.y = newY;
                this.isColliding = false;
            }
            
            this.x = Math.max(this.radius, Math.min(this.x, canvas.width - this.radius));
            this.y = Math.max(this.radius, Math.min(this.y, canvas.height - this.radius));
        }
    }

    let animals = [];
    function initSim() {
        animals = [new Animal(true)];
        for (let i=0; i<7; i++) animals.push(new Animal(false));
    }

    let draggingAnimal = null;
    canvas.addEventListener('mousedown', e => {
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left, my = e.clientY - rect.top;
        for (let a of animals) {
            if (Math.hypot(a.x - mx, a.y - my) < a.radius * 1.5) {
                draggingAnimal = a;
                a.isDragging = true;
                break;
            }
        }
    });

    canvas.addEventListener('mouseup', () => { if (draggingAnimal) { draggingAnimal.isDragging = false; draggingAnimal.isColliding = false; draggingAnimal = null; } });
    canvas.addEventListener('mouseleave', () => { if (draggingAnimal) { draggingAnimal.isDragging = false; draggingAnimal.isColliding = false; draggingAnimal = null; } });
    canvas.addEventListener('mousemove', e => {
        if (draggingAnimal) {
            const rect = canvas.getBoundingClientRect();
            let tx = e.clientX - rect.left, ty = e.clientY - rect.top;
            if (intersectsFence(tx, ty, draggingAnimal.radius)) {
                draggingAnimal.isColliding = true;
                playBuzzer(performance.now());
            } else {
                draggingAnimal.x = tx; draggingAnimal.y = ty;
                draggingAnimal.isColliding = false;
            }
        }
    });

    let simRunning = false;
    let lastReportTime = 0;
    
    function simLoop(timestamp) {
        if (!simRunning) return;
        
        let intrusion = false;
        for (let a of animals) {
            a.move(timestamp);
            if (a.isColliding) intrusion = true;
        }

        if (timestamp - lastReportTime > 500) {
            // Updated LDR logic: Low Light (Intrusion) -> High Number
            let ldrVal = intrusion ? 800 + Math.floor(Math.random() * 150) : 100 + Math.floor(Math.random() * 200);
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    action: 'embedded_input',
                    ldr_value: ldrVal,
                    status: intrusion ? "INTRUSION" : "SECURE"
                }));
            }
            lastReportTime = timestamp;
        }

        ctxCanvas.fillStyle = "#1e293b"; // Dark mode grass
        ctxCanvas.fillRect(0, 0, canvas.width, canvas.height);

        ctxCanvas.fillStyle = "rgba(16, 185, 129, 0.1)"; // Crop area
        ctxCanvas.fillRect(FENCE_X, FENCE_Y, FENCE_W, FENCE_H);
        ctxCanvas.fillStyle = "#10b981";
        ctxCanvas.font = "bold 24px Inter";
        ctxCanvas.textAlign = "center";
        ctxCanvas.textBaseline = "middle";
        ctxCanvas.fillText("Protected Crops", FENCE_X + FENCE_W/2, FENCE_Y + FENCE_H/2);

        ctxCanvas.lineWidth = intrusion ? 4 : 2;
        if (intrusion && Math.floor(timestamp / 100) % 2 === 0) {
            ctxCanvas.strokeStyle = "#fbbf24";
            ctxCanvas.shadowBlur = 15;
            ctxCanvas.shadowColor = "#fbbf24";
        } else {
            ctxCanvas.strokeStyle = "#ef4444";
            ctxCanvas.shadowBlur = 10;
            ctxCanvas.shadowColor = "#ef4444";
        }
        ctxCanvas.strokeRect(FENCE_X, FENCE_Y, FENCE_W, FENCE_H);
        ctxCanvas.shadowBlur = 0;

        ctxCanvas.font = "30px sans-serif";
        for (let a of animals) {
            if (a.isDragging || a.isPlayer) ctxCanvas.font = "40px sans-serif";
            else ctxCanvas.font = "30px sans-serif";
            ctxCanvas.fillText(a.emoji, a.x - 15, a.y + 10);
        }

        requestAnimationFrame(simLoop);
    }
    
    function startSimulation() {
        simRunning = true;
        initSim();
        requestAnimationFrame(simLoop);
    }

    // Initialize
    updateConfigVisibility();
    connect();
});
