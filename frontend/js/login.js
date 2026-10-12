/**
 * Login Page — Handles login form interactions, role switching,
 * animated particles, and form submission.
 */
(function () {
    'use strict';

    // Redirect if already logged in
    if (Auth.redirectIfLoggedIn()) return;

    // --- DOM Refs ---
    const form         = document.getElementById('login-form');
    const roleTabsEl   = document.getElementById('role-tabs');
    const tabIndicator = document.getElementById('tab-indicator');
    const tabAdmin     = document.getElementById('tab-admin');
    const tabGuest     = document.getElementById('tab-guest');
    const adminFields  = document.getElementById('admin-fields');
    const guestFields  = document.getElementById('guest-fields');
    const guestSelect  = document.getElementById('guest-select-existing');
    const guestIdInput = document.getElementById('guest-id');
    const guestName    = document.getElementById('guest-name');
    const guestEmail   = document.getElementById('guest-email');
    const guestPhone   = document.getElementById('guest-phone');
    const guestNat     = document.getElementById('guest-nationality');
    const guestGender  = document.getElementById('guest-gender');
    const guestPwInput = document.getElementById('guest-password');
    const toggleGuestPw = document.getElementById('toggle-guest-pw');
    const eyeGuest     = document.getElementById('eye-guest');
    const guestSuccessBox = document.getElementById('guest-success-box');
    const guestSuccessText = document.getElementById('guest-success-text');
    const loginBtn     = document.getElementById('login-btn');
    const btnText      = document.getElementById('btn-text');
    const btnSpinner   = document.getElementById('btn-spinner');
    const errorBox     = document.getElementById('login-error');
    const errorText    = document.getElementById('error-text');
    const footerHint   = document.getElementById('footer-hint');
    const toggleAdmPw  = document.getElementById('toggle-admin-pw');
    const adminPwInput = document.getElementById('admin-password');

    let currentRole = 'admin';
    let loadedGuests = [];

    // --- Role Tab Switching ---
    function switchRole(role) {
        currentRole = role;

        // Update tab active states
        tabAdmin.classList.toggle('active', role === 'admin');
        tabGuest.classList.toggle('active', role === 'guest');

        // Slide the indicator
        tabIndicator.classList.toggle('guest', role === 'guest');

        // Toggle field visibility
        adminFields.classList.toggle('hidden', role !== 'admin');
        guestFields.classList.toggle('hidden', role !== 'guest');

        // Update button style & text
        loginBtn.classList.toggle('guest-mode', role === 'guest');
        if (role === 'admin') {
            btnText.textContent = 'Sign In as Admin';
        } else {
            updateGuestButtonText();
            loadExistingGuests();
        }

        // Update footer hint
        footerHint.textContent = role === 'admin'
            ? 'Admin credentials required for full dashboard access'
            : 'Enter details to sign in or register as Guest in Neo4j';

        // Hide any error
        hideError();
    }

    function updateGuestButtonText() {
        if (guestSelect && guestSelect.value && guestSelect.value !== '__new__' && guestSelect.value !== '__auto__') {
            const guest = loadedGuests.find(g => g.guest_id === guestSelect.value);
            btnText.textContent = guest ? `Sign In as ${guest.name}` : 'Sign In as Guest';
        } else if (guestSelect && guestSelect.value === '__new__') {
            btnText.textContent = 'Register & Sign In';
        } else {
            btnText.textContent = 'Sign In or Register';
        }
    }

    async function loadExistingGuests() {
        if (!guestSelect || guestSelect.options.length > 2) return;
        try {
            const guests = (window.API && window.API.getGuests) ?
                await window.API.getGuests() :
                await fetch('/api/guests/').then(r => r.json());

            if (Array.isArray(guests) && guests.length > 0) {
                loadedGuests = guests;
                guestSelect.innerHTML = `
                    <option value="__auto__">✨ Auto-Detect (Sign In or Register)</option>
                    <option value="__new__">+ Register as New Guest</option>
                `;
                guests.forEach(g => {
                    const opt = document.createElement('option');
                    opt.value = g.guest_id;
                    opt.textContent = `👤 ${g.name} (${g.guest_id}) · ${g.nationality || 'Guest'}`;
                    guestSelect.appendChild(opt);
                });
            }
        } catch (e) {
            console.warn('Could not load guests list for dropdown:', e);
        }
    }

    if (guestSelect) {
        guestSelect.addEventListener('change', () => {
            const val = guestSelect.value;
            if (val === '__new__' || val === '__auto__') {
                if (guestIdInput) guestIdInput.value = '';
                guestName.value = '';
                guestEmail.value = '';
                guestPhone.value = '';
                guestNat.value = 'Indian';
                guestGender.value = 'Male';
                if (guestPwInput) guestPwInput.value = '';
                if (val === '__new__') guestName.focus();
            } else {
                const guest = loadedGuests.find(g => g.guest_id === val);
                if (guest) {
                    if (guestIdInput) guestIdInput.value = guest.guest_id || '';
                    guestName.value = guest.name || '';
                    guestEmail.value = guest.contact_info || '';
                    guestPhone.value = '';
                    guestNat.value = guest.nationality || 'Indian';
                    guestGender.value = guest.gender || 'Male';
                    if (guestPwInput) guestPwInput.value = 'password123';
                }
            }
            updateGuestButtonText();
            hideError();
        });
    }

    tabAdmin.addEventListener('click', () => switchRole('admin'));
    tabGuest.addEventListener('click', () => switchRole('guest'));

    // --- Toggle Password Visibility ---
    toggleAdmPw.addEventListener('click', () => {
        const isPassword = adminPwInput.type === 'password';
        adminPwInput.type = isPassword ? 'text' : 'password';
        document.getElementById('eye-admin').textContent = isPassword ? '🙈' : '👁️';
    });

    if (toggleGuestPw && guestPwInput) {
        toggleGuestPw.addEventListener('click', () => {
            const isPassword = guestPwInput.type === 'password';
            guestPwInput.type = isPassword ? 'text' : 'password';
            if (eyeGuest) eyeGuest.textContent = isPassword ? '🙈' : '👁️';
        });
    }

    // --- Error Handling ---
    function showError(msg) {
        errorText.textContent = msg;
        errorBox.classList.remove('hidden');
        errorBox.style.animation = 'none';
        errorBox.offsetHeight; // reflow
        errorBox.style.animation = '';
    }

    function hideError() {
        errorBox.classList.add('hidden');
    }

    // --- Form Submission ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        // Admin validations
        if (currentRole === 'admin') {
            const username = document.getElementById('admin-username').value.trim();
            const password = document.getElementById('admin-password').value;
            if (!username || !password) {
                showError('Please enter both admin username and password');
                return;
            }

            loginBtn.classList.add('loading');
            btnText.textContent = 'Signing in…';
            btnSpinner.classList.remove('hidden');

            const result = Auth.loginAdmin(username, password);
            if (result.success) {
                document.getElementById('login-card').style.animation =
                    'cardExit 0.4s cubic-bezier(0.4, 0, 1, 1) forwards';
                setTimeout(() => { window.location.href = '/'; }, 350);
            } else {
                showError(result.error || 'Invalid credentials');
                loginBtn.classList.remove('loading');
                btnText.textContent = 'Sign In as Admin';
                btnSpinner.classList.add('hidden');
            }
            return;
        }

        // Guest validations
        const isExplicitNew = guestSelect && guestSelect.value === '__new__';
        const hasSelectedGuest = guestSelect && guestSelect.value && guestSelect.value !== '__new__' && guestSelect.value !== '__auto__';
        const selectedGuestId = hasSelectedGuest ? guestSelect.value : (guestIdInput ? guestIdInput.value.trim() : null);
        const name  = guestName.value.trim();
        const email = guestEmail.value.trim();
        const phone = guestPhone.value.trim();
        const nationality = guestNat.value.trim() || 'Indian';
        const gender = guestGender.value || 'Other';

        // Check that at least one identifier is provided
        if (!selectedGuestId && !email && !phone && !name) {
            showError('Please enter your email address, phone number, or Guest ID');
            if (guestEmail) guestEmail.focus();
            return;
        }

        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showError('Please enter a valid email address (e.g. name@example.com)');
            guestEmail.focus();
            return;
        }

        if (phone && phone.replace(/\D/g, '').length < 5) {
            showError('Please enter a valid phone number');
            guestPhone.focus();
            return;
        }

        const password = guestPwInput ? guestPwInput.value.trim() : '';
        if (!password) {
            showError('Password is required. Users cannot be authenticated merely by entering an email, phone, or guest ID.');
            if (guestPwInput) guestPwInput.focus();
            return;
        }

        // Show loading state
        loginBtn.classList.add('loading');
        btnText.textContent = isExplicitNew ? 'Creating guest in Neo4j…' : 'Authenticating with Neo4j…';
        btnSpinner.classList.remove('hidden');

        try {
            const payload = {
                guest_id: selectedGuestId || undefined,
                name: name || undefined,
                email: email || undefined,
                phone: phone || undefined,
                password: password,
                contact_info: phone ? (email ? `${email} | ${phone}` : phone) : (email || undefined),
                nationality: nationality,
                gender: gender,
                action: isExplicitNew ? 'register' : undefined,
            };

            const result = await Auth.loginGuest(payload);

            if (result && result.success) {
                if (guestSuccessBox) {
                    guestSuccessBox.style.display = 'flex';
                    if (result.isNew) {
                        guestSuccessText.textContent = `✨ Created Guest ${result.guest.name} (${result.guest.guest_id}) in Neo4j!`;
                    } else {
                        guestSuccessText.textContent = `✓ Welcome back, ${result.guest.name} (${result.guest.guest_id})!`;
                    }
                    btnText.textContent = 'Redirecting to dashboard…';
                    await new Promise(r => setTimeout(r, 600));
                }

                document.getElementById('login-card').style.animation =
                    'cardExit 0.4s cubic-bezier(0.4, 0, 1, 1) forwards';
                setTimeout(() => { window.location.href = '/'; }, 300);
            } else {
                showError((result && result.error) || 'Failed to authenticate guest');
                loginBtn.classList.remove('loading');
                updateGuestButtonText();
                btnSpinner.classList.add('hidden');
            }
        } catch (err) {
            showError(err.message || 'Error communicating with server');
            loginBtn.classList.remove('loading');
            updateGuestButtonText();
            btnSpinner.classList.add('hidden');
        }
    });

    // Add exit animation keyframes dynamically
    const exitStyle = document.createElement('style');
    exitStyle.textContent = `
        @keyframes cardExit {
            to {
                opacity: 0;
                transform: translateY(-30px) scale(0.96);
                filter: blur(4px);
            }
        }
    `;
    document.head.appendChild(exitStyle);

    // --- Floating Particles ---
    function initParticles() {
        const canvas = document.getElementById('particles-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        let width, height;
        let particles = [];
        const PARTICLE_COUNT = 50;

        function resize() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        }

        function createParticle() {
            return {
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                radius: Math.random() * 1.5 + 0.5,
                alpha: Math.random() * 0.4 + 0.1,
            };
        }

        function init() {
            resize();
            particles = [];
            for (let i = 0; i < PARTICLE_COUNT; i++) {
                particles.push(createParticle());
            }
        }

        function draw() {
            ctx.clearRect(0, 0, width, height);

            particles.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;

                // Wrap around
                if (p.x < 0) p.x = width;
                if (p.x > width) p.x = 0;
                if (p.y < 0) p.y = height;
                if (p.y > height) p.y = 0;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(79, 140, 255, ${p.alpha})`;
                ctx.fill();
            });

            // Draw connections
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 120) {
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = `rgba(79, 140, 255, ${0.08 * (1 - dist / 120)})`;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            }

            requestAnimationFrame(draw);
        }

        window.addEventListener('resize', resize);
        init();
        draw();
    }

    initParticles();
})();
