/**
 * Graph Visualizer Component — Interactive Force-Directed Network Graph.
 * Visualizes nodes (Hotel, Room, Guest, etc.) and directed relationships
 * with real-time physics, zoom/pan, dragging, filtering, and node inspection.
 */
const GraphVisualizerComponent = {
    canvas: null,
    ctx: null,
    animId: null,
    nodes: [],
    links: [],
    filteredNodes: [],
    filteredLinks: [],
    activeFilter: 'ALL',
    selectedNode: null,
    hoveredNode: null,
    isDragging: false,
    dragNode: null,
    isPanning: false,
    panStart: { x: 0, y: 0 },
    transform: { x: 0, y: 0, scale: 1 },
    physicsRunning: true,

    colorMap: {
        Hotel: '#ef4444',
        RoomCategory: '#8b5cf6',
        Room: '#3b82f6',
        Department: '#06b6d4',
        Staff: '#f59e0b',
        Guest: '#10b981',
        Reservation: '#ec4899',
    },

    async render() {
        const content = document.getElementById('content-area');
        content.innerHTML = `
            <div class="graph-visualizer-container">
                <!-- Toolbar -->
                <div class="graph-toolbar">
                    <div class="toolbar-left">
                        <div class="filter-pills" id="graph-filter-pills">
                            <button class="pill active" data-filter="ALL">All Nodes</button>
                            <button class="pill" data-filter="Hotel">Hotels</button>
                            <button class="pill" data-filter="Room">Rooms</button>
                            <button class="pill" data-filter="Guest">Guests</button>
                            <button class="pill" data-filter="Reservation">Reservations</button>
                            <button class="pill" data-filter="Staff">Staff</button>
                            <button class="pill" data-filter="Department">Depts</button>
                            <button class="pill" data-filter="RoomCategory">Categories</button>
                        </div>
                    </div>
                    <div class="toolbar-right">
                        <input type="text" id="graph-search" class="search-input-small" placeholder="Find node by name or ID...">
                        <button class="btn btn-secondary btn-sm" id="btn-recenter" title="Recenter View">🎯 Center</button>
                        <button class="btn btn-secondary btn-sm" id="btn-toggle-physics" title="Pause / Resume physics">⏸ Physics</button>
                        <button class="btn btn-primary btn-sm" id="btn-export-graph" title="Export as PNG image">📸 Export PNG</button>
                    </div>
                </div>

                <!-- Main Viewport -->
                <div class="graph-viewport-wrapper">
                    <canvas id="graph-canvas"></canvas>
                    
                    <!-- Legend Overlay -->
                    <div class="graph-legend">
                        <span class="legend-item"><span class="legend-dot" style="background:#ef4444;"></span> Hotel</span>
                        <span class="legend-item"><span class="legend-dot" style="background:#3b82f6;"></span> Room</span>
                        <span class="legend-item"><span class="legend-dot" style="background:#8b5cf6;"></span> Category</span>
                        <span class="legend-item"><span class="legend-dot" style="background:#10b981;"></span> Guest</span>
                        <span class="legend-item"><span class="legend-dot" style="background:#ec4899;"></span> Reservation</span>
                        <span class="legend-item"><span class="legend-dot" style="background:#f59e0b;"></span> Staff</span>
                        <span class="legend-item"><span class="legend-dot" style="background:#06b6d4;"></span> Department</span>
                    </div>

                    <!-- Node Inspector Sidebar -->
                    <div class="node-inspector" id="node-inspector" style="display:none;">
                        <div class="inspector-header">
                            <span class="inspector-badge" id="insp-badge">Node</span>
                            <button class="inspector-close" id="insp-close">&times;</button>
                        </div>
                        <h3 class="inspector-title" id="insp-title">Title</h3>
                        <div class="inspector-body" id="insp-body"></div>
                        <div class="inspector-connections" id="insp-connections"></div>
                    </div>

                    <!-- Instructions hint -->
                    <div class="graph-hint">
                        💡 <strong>Controls:</strong> Drag nodes • Scroll to Zoom • Drag background to Pan • Click node to Inspect
                    </div>
                </div>
            </div>
        `;

        this.initVisualizer();
    },

    async initVisualizer() {
        this.canvas = document.getElementById('graph-canvas');
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');

        // Resize canvas to fill container
        this.resize();
        window.addEventListener('resize', () => this.resize());

        // Event listeners for UI
        document.getElementById('graph-filter-pills').addEventListener('click', (e) => {
            if (e.target.classList.contains('pill')) {
                document.querySelectorAll('#graph-filter-pills .pill').forEach(p => p.classList.remove('active'));
                e.target.classList.add('active');
                this.setFilter(e.target.dataset.filter);
            }
        });

        document.getElementById('graph-search').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            if (!query) {
                this.selectedNode = null;
                return;
            }
            const match = this.nodes.find(n => 
                n.id.toLowerCase().includes(query) || 
                (n.name && n.name.toLowerCase().includes(query)) ||
                (n.caption && n.caption.toLowerCase().includes(query))
            );
            if (match) {
                this.selectNode(match);
                // Pan smoothly to node
                this.transform.x = this.canvas.width / 2 - match.x * this.transform.scale;
                this.transform.y = this.canvas.height / 2 - match.y * this.transform.scale;
            }
        });

        document.getElementById('btn-recenter').addEventListener('click', () => this.recenter());
        
        document.getElementById('btn-toggle-physics').addEventListener('click', (e) => {
            this.physicsRunning = !this.physicsRunning;
            e.target.textContent = this.physicsRunning ? '⏸ Physics' : '▶ Physics';
        });

        document.getElementById('btn-export-graph').addEventListener('click', () => this.exportImage());

        document.getElementById('insp-close').addEventListener('click', () => {
            document.getElementById('node-inspector').style.display = 'none';
            this.selectedNode = null;
        });

        // Mouse & Touch interactions
        this.bindEvents();

        // Load data from API
        try {
            const data = await API.getGraphData();
            this.loadGraphData(data);
        } catch (err) {
            console.error('Failed to load graph data:', err);
            App.toast('Failed to load graph topology: ' + err.message, 'error');
        }
    },

    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.canvas.style.width = `${rect.width}` + 'px';
        this.canvas.style.height = `${rect.height}` + 'px';
        if (this.ctx) {
            this.ctx.resetTransform();
            this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        }
    },

    loadGraphData(data) {
        const width = this.canvas.width / window.devicePixelRatio;
        const height = this.canvas.height / window.devicePixelRatio;

        // Initialize node positions in circular clusters
        this.nodes = (data.nodes || []).map((n, i) => {
            const angle = (i / data.nodes.length) * Math.PI * 2;
            const radius = 180 + Math.random() * 120;
            return {
                ...n,
                x: width / 2 + Math.cos(angle) * radius,
                y: height / 2 + Math.sin(angle) * radius,
                vx: (Math.random() - 0.5) * 2,
                vy: (Math.random() - 0.5) * 2,
                radius: n.radius || 15,
                color: n.color || this.colorMap[n.label] || '#94a3b8',
            };
        });

        // Link references
        const nodeMap = new Map(this.nodes.map(n => [n.id, n]));
        this.links = (data.links || []).filter(l => nodeMap.has(l.source) && nodeMap.has(l.target)).map(l => ({
            ...l,
            sourceNode: nodeMap.get(l.source),
            targetNode: nodeMap.get(l.target),
        }));

        this.applyFilter();
        this.recenter();

        if (this.animId) cancelAnimationFrame(this.animId);
        this.animate();
    },

    setFilter(filter) {
        this.activeFilter = filter;
        this.applyFilter();
    },

    applyFilter() {
        if (this.activeFilter === 'ALL') {
            this.filteredNodes = [...this.nodes];
        } else {
            this.filteredNodes = this.nodes.filter(n => n.label === this.activeFilter);
        }
        const activeIds = new Set(this.filteredNodes.map(n => n.id));
        this.filteredLinks = this.links.filter(l => activeIds.has(l.source) && activeIds.has(l.target));
    },

    recenter() {
        const width = this.canvas.width / window.devicePixelRatio;
        const height = this.canvas.height / window.devicePixelRatio;
        this.transform = { x: 0, y: 0, scale: 0.95 };
    },

    // --- Physics Simulation Step ---
    stepPhysics() {
        if (!this.physicsRunning) return;
        const width = this.canvas.width / window.devicePixelRatio;
        const height = this.canvas.height / window.devicePixelRatio;
        const cx = width / 2;
        const cy = height / 2;

        const nodes = this.filteredNodes;
        const links = this.filteredLinks;

        // 1. Coulomb Repulsion between all nodes
        for (let i = 0; i < nodes.length; i++) {
            const na = nodes[i];
            for (let j = i + 1; j < nodes.length; j++) {
                const nb = nodes[j];
                const dx = nb.x - na.x;
                const dy = nb.y - na.y;
                const distSq = dx * dx + dy * dy + 1;
                const dist = Math.sqrt(distSq);
                
                // Repulsion constant
                const force = 3200 / distSq;
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;

                if (na !== this.dragNode) {
                    na.vx -= fx;
                    na.vy -= fy;
                }
                if (nb !== this.dragNode) {
                    nb.vx += fx;
                    nb.vy += fy;
                }
            }
        }

        // 2. Hooke's Law Spring attraction for links
        const targetLen = 110;
        for (const l of links) {
            const na = l.sourceNode;
            const nb = l.targetNode;
            if (!na || !nb) continue;
            const dx = nb.x - na.x;
            const dy = nb.y - na.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const displacement = dist - targetLen;
            const springForce = displacement * 0.045;

            const fx = (dx / dist) * springForce;
            const fy = (dy / dist) * springForce;

            if (na !== this.dragNode) {
                na.vx += fx;
                na.vy += fy;
            }
            if (nb !== this.dragNode) {
                nb.vx -= fx;
                nb.vy -= fy;
            }
        }

        // 3. Center Gravity & Velocity integration
        for (const n of nodes) {
            if (n === this.dragNode) continue;

            // Gravity towards center
            n.vx += (cx - n.x) * 0.004;
            n.vy += (cy - n.y) * 0.004;

            // Damping friction
            n.vx *= 0.88;
            n.vy *= 0.88;

            // Update position
            n.x += n.vx;
            n.y += n.vy;
        }
    },

    // --- Main Render Loop ---
    animate() {
        this.stepPhysics();
        this.draw();
        this.animId = requestAnimationFrame(() => this.animate());
    },

    draw() {
        const ctx = this.ctx;
        if (!ctx) return;
        const width = this.canvas.width / window.devicePixelRatio;
        const height = this.canvas.height / window.devicePixelRatio;

        ctx.clearRect(0, 0, width, height);

        ctx.save();
        // Apply camera pan & zoom
        ctx.translate(this.transform.x, this.transform.y);
        ctx.scale(this.transform.scale, this.transform.scale);

        // Draw Links
        for (const l of this.filteredLinks) {
            const na = l.sourceNode;
            const nb = l.targetNode;
            if (!na || !nb) continue;

            const isHighlighted = (this.selectedNode && (na === this.selectedNode || nb === this.selectedNode)) ||
                                  (this.hoveredNode && (na === this.hoveredNode || nb === this.hoveredNode));

            ctx.beginPath();
            ctx.moveTo(na.x, na.y);
            ctx.lineTo(nb.x, nb.y);
            ctx.strokeStyle = isHighlighted ? 'rgba(99, 102, 241, 0.9)' : 'rgba(148, 163, 184, 0.28)';
            ctx.lineWidth = isHighlighted ? 2.5 : 1.2;
            ctx.stroke();

            // Arrow head
            const angle = Math.atan2(nb.y - na.y, nb.x - na.x);
            const arrowDist = nb.radius + 6;
            const arrowX = nb.x - Math.cos(angle) * arrowDist;
            const arrowY = nb.y - Math.sin(angle) * arrowDist;

            ctx.save();
            ctx.translate(arrowX, arrowY);
            ctx.rotate(angle);
            ctx.fillStyle = isHighlighted ? '#6366f1' : 'rgba(148, 163, 184, 0.6)';
            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.lineTo(-6, -3.5);
            ctx.lineTo(-6, 3.5);
            ctx.closePath();
            ctx.fill();
            ctx.restore();

            // Link text label if highlighted or zoom > 1
            if (isHighlighted || this.transform.scale > 1.2) {
                const midX = (na.x + nb.x) / 2;
                const midY = (na.y + nb.y) / 2;
                ctx.font = '9px Inter, sans-serif';
                ctx.fillStyle = isHighlighted ? '#a5b4fc' : 'rgba(148, 163, 184, 0.65)';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(l.type, midX, midY - 6);
            }
        }

        // Draw Nodes
        for (const n of this.filteredNodes) {
            const isSelected = n === this.selectedNode;
            const isHovered = n === this.hoveredNode;
            const isConnected = isSelected || isHovered || this.isNodeConnectedToActive(n);

            ctx.save();
            ctx.translate(n.x, n.y);

            // Glow ring for selected/hovered node
            if (isSelected || isHovered) {
                ctx.beginPath();
                ctx.arc(0, 0, n.radius + 6, 0, Math.PI * 2);
                ctx.fillStyle = isSelected ? 'rgba(99, 102, 241, 0.35)' : 'rgba(255, 255, 255, 0.2)';
                ctx.fill();
            }

            // Node Circle
            ctx.beginPath();
            ctx.arc(0, 0, n.radius, 0, Math.PI * 2);
            ctx.fillStyle = n.color;
            ctx.shadowColor = n.color;
            ctx.shadowBlur = isSelected ? 15 : 6;
            ctx.fill();
            ctx.shadowBlur = 0;

            // Border
            ctx.strokeStyle = isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.4)';
            ctx.lineWidth = isSelected ? 2.5 : 1.2;
            ctx.stroke();

            // Node Caption inside or below
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 9px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            const cap = n.caption || n.name || n.id;
            ctx.fillText(cap.length > 7 ? cap.slice(0, 6) + '…' : cap, 0, 0);

            // Full Label beneath
            if (this.transform.scale > 0.8 || isSelected || isHovered) {
                ctx.font = '10px Inter, sans-serif';
                ctx.fillStyle = isSelected ? '#ffffff' : 'rgba(226, 232, 240, 0.85)';
                ctx.fillText(n.name, 0, n.radius + 12);
            }

            ctx.restore();
        }

        ctx.restore();
    },

    isNodeConnectedToActive(node) {
        const active = this.selectedNode || this.hoveredNode;
        if (!active) return false;
        return this.filteredLinks.some(l => 
            (l.sourceNode === active && l.targetNode === node) ||
            (l.targetNode === active && l.sourceNode === node)
        );
    },

    // --- Interactive Mouse & Touch Bindings ---
    bindEvents() {
        const canvas = this.canvas;

        const getPos = (e) => {
            const rect = canvas.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            return {
                screenX: clientX - rect.left,
                screenY: clientY - rect.top,
                worldX: (clientX - rect.left - this.transform.x) / this.transform.scale,
                worldY: (clientY - rect.top - this.transform.y) / this.transform.scale,
            };
        };

        const findNodeAt = (wx, wy) => {
            for (let i = this.filteredNodes.length - 1; i >= 0; i--) {
                const n = this.filteredNodes[i];
                const distSq = (n.x - wx) ** 2 + (n.y - wy) ** 2;
                if (distSq <= (n.radius + 4) ** 2) return n;
            }
            return null;
        };

        canvas.addEventListener('mousedown', (e) => {
            const pos = getPos(e);
            const clicked = findNodeAt(pos.worldX, pos.worldY);
            if (clicked) {
                this.isDragging = true;
                this.dragNode = clicked;
                this.selectNode(clicked);
            } else {
                this.isPanning = true;
                this.panStart = { x: pos.screenX - this.transform.x, y: pos.screenY - this.transform.y };
            }
        });

        window.addEventListener('mousemove', (e) => {
            const pos = getPos(e);
            if (this.isDragging && this.dragNode) {
                this.dragNode.x = pos.worldX;
                this.dragNode.y = pos.worldY;
                this.dragNode.vx = 0;
                this.dragNode.vy = 0;
            } else if (this.isPanning) {
                this.transform.x = pos.screenX - this.panStart.x;
                this.transform.y = pos.screenY - this.panStart.y;
            } else {
                const hovered = findNodeAt(pos.worldX, pos.worldY);
                this.hoveredNode = hovered;
                canvas.style.cursor = hovered ? 'pointer' : 'default';
            }
        });

        window.addEventListener('mouseup', () => {
            this.isDragging = false;
            this.dragNode = null;
            this.isPanning = false;
        });

        // Zoom with mouse wheel
        canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const pos = getPos(e);
            const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
            const newScale = Math.min(Math.max(this.transform.scale * zoomFactor, 0.3), 3.5);

            this.transform.x = pos.screenX - (pos.screenX - this.transform.x) * (newScale / this.transform.scale);
            this.transform.y = pos.screenY - (pos.screenY - this.transform.y) * (newScale / this.transform.scale);
            this.transform.scale = newScale;
        }, { passive: false });
    },

    selectNode(node) {
        this.selectedNode = node;
        const inspector = document.getElementById('node-inspector');
        if (!inspector) return;
        inspector.style.display = 'block';

        document.getElementById('insp-badge').textContent = node.label;
        document.getElementById('insp-badge').style.background = node.color;
        document.getElementById('insp-title').textContent = node.name || node.id;

        // Render properties table
        const props = node.properties || {};
        let bodyHtml = '<table class="inspector-table">';
        for (const [k, v] of Object.entries(props)) {
            bodyHtml += `<tr><td><strong>${k}</strong></td><td>${v}</td></tr>`;
        }
        bodyHtml += '</table>';
        document.getElementById('insp-body').innerHTML = bodyHtml;

        // Connected edges
        const connectedLinks = this.links.filter(l => l.sourceNode === node || l.targetNode === node);
        let connsHtml = `<h4 style="margin: 12px 0 6px; font-size: 11px; text-transform: uppercase; color: #94a3b8;">Connected Relationships (${connectedLinks.length})</h4><ul class="inspector-link-list">`;
        connectedLinks.forEach(l => {
            const isOutgoing = l.sourceNode === node;
            const neighbor = isOutgoing ? l.targetNode : l.sourceNode;
            const arrow = isOutgoing ? '→' : '←';
            connsHtml += `<li><span class="rel-tag">${l.type}</span> ${arrow} <span class="neighbor-link" onclick="GraphVisualizerComponent.focusNodeById('${neighbor.id}')">${neighbor.name}</span></li>`;
        });
        connsHtml += '</ul>';
        document.getElementById('insp-connections').innerHTML = connsHtml;
    },

    focusNodeById(id) {
        const target = this.nodes.find(n => n.id === id);
        if (target) {
            this.selectNode(target);
            const width = this.canvas.width / window.devicePixelRatio;
            const height = this.canvas.height / window.devicePixelRatio;
            this.transform.x = width / 2 - target.x * this.transform.scale;
            this.transform.y = height / 2 - target.y * this.transform.scale;
        }
    },

    exportImage() {
        if (!this.canvas) return;
        const link = document.createElement('a');
        link.download = 'hotel_management_neo4j_graph.png';
        link.href = this.canvas.toDataURL('image/png');
        link.click();
        App.toast('Graph visualization exported as PNG image!', 'success');
    }
};
