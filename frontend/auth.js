document.addEventListener('DOMContentLoaded', () => {
    checkSession();
    setupAuthListeners();
});

function switchView(viewId) {
    document.getElementById('view-login').style.display = 'none';
    document.getElementById('view-onboarding').style.display = 'none';
    document.getElementById('view-explore').style.display = 'none';
    
    document.getElementById(viewId).style.display = 'block';
}

async function checkSession() {
    const token = localStorage.getItem('cravingai_token');
    if (!token) {
        switchView('view-login');
        return;
    }
    
    try {
        const res = await fetch('/api/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) {
            if (res.status === 401) {
                localStorage.removeItem('cravingai_token');
            }
            switchView('view-login');
            return;
        }
        
        const data = await res.json();
        if (data.verified) {
            switchView('view-explore');
        } else {
            switchView('view-onboarding');
        }
    } catch (err) {
        console.error('Session check failed', err);
        switchView('view-login');
    }
}

function setupAuthListeners() {
    // 1. Send OTP
    const sendOtpForm = document.getElementById('auth-send-otp-form');
    if (sendOtpForm) {
        sendOtpForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const phoneOrEmail = document.getElementById('auth-phone-email').value;
            const btn = sendOtpForm.querySelector('button');
            const originalText = btn.textContent;
            btn.textContent = 'Sending...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/api/auth/send-otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone_or_email: phoneOrEmail })
                });
                
                if (res.ok) {
                    sendOtpForm.style.display = 'none';
                    document.getElementById('auth-verify-otp-form').style.display = 'flex';
                    document.querySelector('.otp-input').focus();
                } else {
                    const data = await res.json();
                    alert(data.detail || 'Failed to send OTP');
                }
            } catch (err) {
                console.error(err);
                alert('An error occurred.');
            } finally {
                btn.textContent = originalText;
                btn.disabled = false;
            }
        });
    }

    // 2. OTP Input Auto-advance
    const otpInputs = document.querySelectorAll('.otp-input');
    otpInputs.forEach((input, index) => {
        input.addEventListener('input', (e) => {
            // Only allow digits
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
            if (e.target.value.length === 1 && index < otpInputs.length - 1) {
                otpInputs[index + 1].focus();
            }
        });
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && e.target.value.length === 0 && index > 0) {
                otpInputs[index - 1].focus();
            }
        });
    });

    // 3. Verify OTP
    const verifyOtpForm = document.getElementById('auth-verify-otp-form');
    if (verifyOtpForm) {
        verifyOtpForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const phoneOrEmail = document.getElementById('auth-phone-email').value;
            let code = '';
            otpInputs.forEach(input => code += input.value);
            
            if (code.length !== 6) {
                alert('Please enter the 6-digit code.');
                return;
            }
            
            const btn = verifyOtpForm.querySelector('button[type="submit"]');
            const originalText = btn.textContent;
            btn.textContent = 'Verifying...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/api/auth/verify-otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone_or_email: phoneOrEmail, code: code })
                });
                
                if (res.ok) {
                    const data = await res.json();
                    localStorage.setItem('cravingai_token', data.token);
                    
                    if (data.is_new_user) {
                        switchView('view-onboarding');
                    } else {
                        switchView('view-explore');
                    }
                } else {
                    const data = await res.json();
                    alert(data.detail || 'Invalid OTP');
                }
            } catch (err) {
                console.error(err);
                alert('Verification failed.');
            } finally {
                btn.textContent = originalText;
                btn.disabled = false;
            }
        });
        
        document.getElementById('auth-back-btn').addEventListener('click', () => {
            verifyOtpForm.style.display = 'none';
            sendOtpForm.style.display = 'flex';
        });
    }

    // 4. Onboarding Setup
    const onboardingForm = document.getElementById('onboarding-form');
    if (onboardingForm) {
        onboardingForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const name = document.getElementById('onboarding-name').value;
            const avatarRadio = document.querySelector('input[name="avatar_id"]:checked');
            if (!avatarRadio) {
                alert('Please choose an avatar.');
                return;
            }
            const avatar_id = avatarRadio.value;
            
            const prefCheckboxes = document.querySelectorAll('input[name="preferences"]:checked');
            const preferences = Array.from(prefCheckboxes).map(cb => cb.value);
            
            const token = localStorage.getItem('cravingai_token');
            const btn = onboardingForm.querySelector('button[type="submit"]');
            btn.textContent = 'Saving...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/api/auth/setup-profile', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ name, avatar_id, preferences })
                });
                
                if (res.ok) {
                    switchView('view-explore');
                } else {
                    alert('Failed to save profile.');
                }
            } catch (err) {
                console.error(err);
                alert('An error occurred.');
            } finally {
                btn.textContent = 'Get Started';
                btn.disabled = false;
            }
        });
    }

    // 5. Profile / Logout in App Nav
    const profileBtn = document.getElementById('nav-profile-btn');
    if (profileBtn) {
        profileBtn.addEventListener('click', async () => {
            if (confirm('Do you want to log out?')) {
                const token = localStorage.getItem('cravingai_token');
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                localStorage.removeItem('cravingai_token');
                switchView('view-login');
            }
        });
    }
}
