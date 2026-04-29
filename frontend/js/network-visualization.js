(function(){
  // Live Student Network Visualization
  // Vanilla JS + HTML5 Canvas
  // Place this file at frontend/js/network-visualization.js

  function $(s, root=document){ return root.querySelector(s); }

  document.addEventListener('DOMContentLoaded', () => {
    const parent = document.querySelector('main.canvas');
    if (!parent) return;

    // Skip initialization on small screens where panel is hidden
    const parentStyle = window.getComputedStyle(parent);
    if (parentStyle.display === 'none' || parent.clientWidth === 0) return;

    const canvas = document.getElementById('network-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Canvas sizing
    let DPR = window.devicePixelRatio || 1;
    function resizeCanvas(){
      const w = parent.clientWidth;
      const h = parent.clientHeight;
      canvas.style.width = w + 'px';
      canvas.style.height = h + 'px';
      canvas.width = Math.max(1, Math.floor(w * DPR));
      canvas.height = Math.max(1, Math.floor(h * DPR));
      ctx.setTransform(DPR,0,0,DPR,0,0);
    }
    resizeCanvas();
    window.addEventListener('resize', () => { DPR = window.devicePixelRatio || 1; resizeCanvas(); });

    // Style background fill (very dark)
    function clear(){
      ctx.clearRect(0,0,canvas.width, canvas.height);
      // fill a very dark background so canvas looks consistent
      ctx.fillStyle = '#050505';
      ctx.fillRect(0,0,canvas.width/DPR, canvas.height/DPR);
    }

    // Utilities
    const rand = (a,b)=> Math.random()*(b-a)+a;
    const clamp = (v,a,b)=> Math.max(a,Math.min(b,v));

    // Configuration
    const MAX_NODES = 100;
    const BOOT_NODES = Math.floor(rand(20,30));
    const MAX_ACTIVE_NODES = Math.min(100, MAX_NODES);

    // Colors
    const PURPLE = { r:123, g:66, b:250 }; // hub
    const CYAN = { r:0, g:255, b:200 }; // transactions
    const SOFT = { r:255, g:255, b:255 }; // nodes

    // Storage
    const nodes = [];
    const transactions = [];
    const ripples = [];
    const ambientLines = [];

    let W = canvas.width / DPR;
    let H = canvas.height / DPR;
    let center = { x: W/2, y: H/2 };

    function onResizeAdjust(){
      const oldW = W, oldH = H;
      W = canvas.width / DPR; H = canvas.height / DPR;
      const sx = W/oldW || 1, sy = H/oldH || 1;
      center.x = W/2; center.y = H/2;
      nodes.forEach(n => { n.x *= sx; n.y *= sy; });
    }

    // Node class
    class Node {
      constructor(x,y){
        this.x = x; this.y = y;
        this.vx = 0; this.vy = 0;
        this.spawnTime = performance.now();
        this.r = rand(2.5,5.5);
        this.speed = rand(0.35, 0.8);
        this.phase = rand(0,Math.PI*2);
        this.state = 'boot'; // boot, idle, active, dimmed
        this.arrived = false;
        this.label = '';
        this.pulse = 0; // visual pulse multiplier
      }

      update(dt){
        // floating motion
        this.phase += dt*0.003 * (0.5 + this.r*0.1);
        const floatX = Math.cos(this.phase)*0.3;
        const floatY = Math.sin(this.phase*1.3)*0.3;

        if (this.state === 'boot'){
          // move toward center
          const dx = center.x - this.x; const dy = center.y - this.y;
          const d = Math.hypot(dx,dy) || 1;
          const nx = dx/d, ny = dy/d;
          this.vx += nx * (this.speed * 0.02);
          this.vy += ny * (this.speed * 0.02);
          // slow down near center
          if (d < 24){ this.state = 'idle'; this.arrived = true; ripples.push(new Ripple(this.x,this.y, this.r)); }
        }

        // idle gentle movement
        this.x += (this.vx + floatX) * dt * 0.016;
        this.y += (this.vy + floatY) * dt * 0.016;

        // damping
        this.vx *= 0.985; this.vy *= 0.985;

        // keep inside
        if (this.x < 2) this.x = 2; if (this.x > W-2) this.x = W-2;
        if (this.y < 2) this.y = 2; if (this.y > H-2) this.y = H-2;
      }

      draw(ctx){
        // glow
        ctx.save();
        ctx.beginPath();
        ctx.shadowBlur = 12 * (1 + this.pulse);
        ctx.shadowColor = 'rgba(255,255,255,0.8)';
        ctx.fillStyle = `rgba(${SOFT.r},${SOFT.g},${SOFT.b},0.9)`;
        ctx.arc(this.x, this.y, this.r*(1+this.pulse*0.4), 0, Math.PI*2);
        ctx.fill();
        ctx.restore();

        // optional label
        if (this.label){
          ctx.save();
          ctx.font = '10px Inter, Arial';
          ctx.fillStyle = 'rgba(255,255,255,0.9)';
          ctx.fillText(this.label, this.x + this.r + 4, this.y - this.r - 2);
          ctx.restore();
        }
      }
    }

    // Ripple
    class Ripple {
      constructor(x,y, startR){ this.x=x; this.y=y; this.t0=performance.now(); this.duration=900; this.startR = startR; }
      draw(ctx, now){
        const p = (now - this.t0)/this.duration; if (p>1) return false;
        const R = this.startR + (48 - this.startR)*p;
        ctx.save(); ctx.beginPath(); ctx.lineWidth = 2*(1-p);
        ctx.strokeStyle = `rgba(${PURPLE.r},${PURPLE.g},${PURPLE.b},${0.5*(1-p)})`;
        ctx.shadowBlur = 20*(1-p);
        ctx.shadowColor = `rgba(${PURPLE.r},${PURPLE.g},${PURPLE.b},${0.4*(1-p)})`;
        ctx.arc(this.x,this.y,R,0,Math.PI*2); ctx.stroke(); ctx.restore();
        return true;
      }
    }

    // Transaction (edge) lifecycle
    class Transaction {
      constructor(a,b){
        this.a = a; this.b = b; this.t0 = performance.now();
        this.state = 'start'; // start -> link -> solid -> done
        this.duration = 2200; // lifecycle
        this.label = 'REQUEST_POSTED +50pts';
      }
      update(now){
        const p = (now - this.t0)/this.duration;
        if (p < 0.25) this.state = 'start';
        else if (p < 0.6) this.state = 'link';
        else if (p < 0.9) this.state = 'solid';
        else this.state = 'done';
        return this.state !== 'done';
      }
      draw(ctx, now){
        const ax = this.a.x, ay = this.a.y, bx = this.b.x, by = this.b.y;
        const p = clamp((now - this.t0)/this.duration, 0, 1);

        if (this.state === 'start'){
          // dotted line
          ctx.save(); ctx.strokeStyle = `rgba(${SOFT.r},${SOFT.g},${SOFT.b},${0.18})`; ctx.lineWidth = 1;
          drawDottedLine(ctx, ax, ay, bx, by, 6);
          ctx.restore();
        } else if (this.state === 'link'){
          // brighter dotted
          ctx.save(); ctx.strokeStyle = `rgba(${CYAN.r},${CYAN.g},${CYAN.b},${0.22})`; ctx.lineWidth = 1.2;
          drawDottedLine(ctx, ax, ay, bx, by, 4);
          ctx.restore();
        } else if (this.state === 'solid'){
          // solid cyan line with glow
          ctx.save(); ctx.beginPath(); ctx.lineWidth = 1.8; ctx.strokeStyle = `rgba(${CYAN.r},${CYAN.g},${CYAN.b},${0.9 - p*0.3})`;
          ctx.shadowBlur = 18; ctx.shadowColor = `rgba(${CYAN.r},${CYAN.g},${CYAN.b},0.7)`;
          ctx.moveTo(ax,ay); ctx.lineTo(bx,by); ctx.stroke(); ctx.restore();

          // bright pulse on target
          this.b.pulse = 0.8 * (1 - Math.abs(0.75 - p));
        }

        // label near origin (rising text)
        if (p < 0.5){
          ctx.save(); ctx.font = '11px Inter, Arial'; ctx.fillStyle = `rgba(255,255,255,${1-p})`;
          ctx.fillText(this.label, ax + (bx-ax)*0.15, ay + (by-ay)*0.15 - p*12);
          ctx.restore();
        }

        return true;
      }
    }

    function drawDottedLine(ctx,x1,y1,x2,y2,gap){
      const dx = x2-x1; const dy = y2-y1; const dist = Math.hypot(dx,dy);
      const steps = Math.floor(dist / gap);
      const ux = dx/steps; const uy = dy/steps;
      for(let i=0;i<steps;i+=2){ ctx.beginPath(); ctx.moveTo(x1 + ux*i, y1 + uy*i); ctx.lineTo(x1 + ux*(i+1), y1 + uy*(i+1)); ctx.stroke(); }
    }

    // central hub
    function drawHub(ctx, now, scale){
      const s = 1 + (scale||0);
      ctx.save(); ctx.beginPath(); ctx.shadowBlur = 36 * s; ctx.shadowColor = `rgba(${PURPLE.r},${PURPLE.g},${PURPLE.b},0.9)`;
      ctx.fillStyle = `rgba(${PURPLE.r},${PURPLE.g},${PURPLE.b},0.92)`;
      ctx.arc(center.x, center.y, 28 * s, 0, Math.PI*2); ctx.fill(); ctx.restore();

      // label
      ctx.save(); ctx.font = '12px Inter, Arial'; ctx.fillStyle = 'rgba(255,255,255,0.9)'; ctx.fillText('NETWORK_ONLINE', center.x - 44, center.y + 48); ctx.restore();
    }

    // Node counter animation
    let nodeCounter = 0; let targetCounter = 3000; let lastCounterUpdate = performance.now();

    function drawNodeCounter(ctx, now){
      const elapsed = (now - lastCounterUpdate) / 1000;
      nodeCounter += (targetCounter - nodeCounter) * 0.02; // smooth ease
      ctx.save(); ctx.font = '12px Inter, Arial'; ctx.fillStyle = 'rgba(255,255,255,0.9)';
      const txt = 'NODES_ACTIVE: ' + Math.floor(nodeCounter).toString().padStart(4,'0');
      ctx.fillText(txt, W - 140, 24);
      ctx.restore();
    }

    // Ambient random lines
    function maybeAmbient(now){
      if (Math.random() < 0.02){
        const a = nodes[Math.floor(Math.random()*nodes.length)];
        const b = nodes[Math.floor(Math.random()*nodes.length)];
        if (a && b && a !== b) ambientLines.push({x1:a.x,y1:a.y,x2:b.x,y2:b.y,t:now,d:300});
      }
      for (let i=ambientLines.length-1;i>=0;i--){ const L = ambientLines[i]; const p=(now-L.t)/L.d; if (p>1) ambientLines.splice(i,1); else{
        ctx.save(); ctx.strokeStyle = `rgba(255,255,255,${0.04*(1-p)})`; ctx.lineWidth=0.6; ctx.beginPath(); ctx.moveTo(L.x1,L.y1); ctx.lineTo(L.x2,L.y2); ctx.stroke(); ctx.restore(); }
      }
    }

    // Initialization: spawn nodes from edges
    function spawnBootNodes(){
      for (let i=0;i<BOOT_NODES;i++){
        // pick an edge and spawn point
        const edge = Math.floor(Math.random()*4);
        let x,y;
        if (edge===0){ x = rand(0,W); y = -10; }
        else if (edge===1){ x = W+10; y = rand(0,H); }
        else if (edge===2){ x = rand(0,W); y = H+10; }
        else { x = -10; y = rand(0,H); }
        const n = new Node(x,y);
        // small initial random velocity
        n.vx = rand(-0.4,0.4); n.vy = rand(-0.4,0.4);
        nodes.push(n);
      }
    }

    // Transaction timer
    let lastTx = performance.now();
    function maybeTriggerTransaction(now){
      if (nodes.length < 2) return;
      if (now - lastTx > rand(3000,5000)){
        lastTx = now;
        const a = nodes[Math.floor(Math.random()*nodes.length)];
        let b = nodes[Math.floor(Math.random()*nodes.length)];
        if (a===b){ b = nodes[(nodes.indexOf(a)+1)%nodes.length]; }
        transactions.push(new Transaction(a,b));
        // hub pulse
        ripples.push(new Ripple(center.x, center.y, 8));
      }
    }

    // main loop
    let last = performance.now();
    function loop(now){
      const dt = now - last; last = now;
      clear();

      // update
      nodes.forEach(n => n.update(dt));
      for (let i=transactions.length-1;i>=0;i--){ const t = transactions[i]; if(!t.update(now)) transactions.splice(i,1); }

      // draw ambient thin lines
      maybeAmbient(now);

      // draw hub
      drawHub(ctx, now, 0);

      // draw ripples
      for (let i=ripples.length-1;i>=0;i--){ if(!ripples[i].draw(ctx, now)) ripples.splice(i,1); }

      // draw transactions (behind nodes)
      transactions.forEach(t => t.draw(ctx, now));

      // draw nodes
      nodes.forEach(n => { n.draw(ctx); n.pulse *= 0.92; });

      // draw node counter
      drawNodeCounter(ctx, now);

      // ambient
      // (ambient lines drawn inside maybeAmbient via direct draw calls)

      // spawn ambient occasional node if under limit
      if (nodes.length < MAX_ACTIVE_NODES && Math.random() < 0.005) nodes.push(new Node(rand(0,W), rand(0,H)));

      // maybe transaction trigger
      maybeTriggerTransaction(now);

      requestAnimationFrame(loop);
    }

    // Boot sequence timing
    setTimeout(()=>{ // central node glow appears at 300ms
      // central visual pulse
      ripples.push(new Ripple(center.x, center.y, 6));
      // spawn boot nodes
      spawnBootNodes();
    }, 300);

    // also spawn a few delayed nodes over first 3 seconds
    for (let i=1;i<6;i++){
      setTimeout(()=>{ if(nodes.length < MAX_ACTIVE_NODES) nodes.push(new Node(rand(0,W), rand(0,H))); }, 300 + i*400);
    }

    // handle resize adjustments
    let resizeTimer = null;
    window.addEventListener('resize', ()=>{ clearTimeout(resizeTimer); resizeTimer=setTimeout(()=>{ onResizeAdjust(); }, 120); });

    // start loop
    requestAnimationFrame(loop);
  });
})();
