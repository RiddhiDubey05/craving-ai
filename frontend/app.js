/**
 * CravingAI Frontend Logic
 * Premium, mobile-first, and emotionally warm UI orchestrations.
 */

// ── State ──
let currentSessionId = null;
let chatHistory = [];
let savedDishesMap = new Map();
let userProfile = null;

// ── Initialization ──
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    lucide.createIcons();

    setupTabs();
    setupSearch();
    setupMoods();
    setupChat();
    
    // Phase 2.5: Immersive UI Enhancements
    applyMagneticEffect('.magnetic-btn');
    loadDiscoveryCategories();
    setupChefSurprise();
    
    if (localStorage.getItem('cravingai_token')) {
        fetchProfileData();
    }
});

// ── Playful Discovery Categories ──
async function loadDiscoveryCategories() {
    const fetchCategory = async (endpoint, limit) => {
        try {
            const res = await fetch(`/api/discovery/${endpoint}?limit=${limit}`);
            if (res.ok) {
                return await res.json();
            }
            return [];
        } catch { return []; }
    };

    const trending = await fetchCategory("trending", 6);
    const budget = await fetchCategory("budget", 6);
    const gems = await fetchCategory("hidden-gems", 6);

    renderCarouselCards(trending, 'carousel-trending');
    renderCarouselCards(budget, 'carousel-budget');
    renderCarouselCards(gems, 'carousel-gems');
}

function renderCarouselCards(dishes, elementId) {
    const container = document.getElementById(elementId);
    if (!container) return;
    
    container.innerHTML = '';
    dishes.forEach((dish) => {
        const imageUrl = dish.image_url || `/api/images/${dish.id}`;
        
        // Render a mini food card for the carousel
        const card = document.createElement('div');
        card.className = 'food-card';
        card.style.flex = '0 0 240px';
        
        card.innerHTML = `
            <div class="food-card-image-wrap" style="height: 180px;">
                <img src="${imageUrl}" alt="${dish.name}" class="food-card-image" loading="lazy">
                <div class="cuisine-badge">${dish.cuisine}</div>
            </div>
            <div class="food-card-content" style="padding: 12px; background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.2) 80%, transparent 100%);">
                <h4 class="food-title" style="font-size: 1rem;">${dish.name}</h4>
                <div class="food-rating" style="padding: 2px 6px; font-size: 0.75rem;">
                    <i data-lucide="star" style="width: 10px; height: 10px;"></i> ${dish.rating.toFixed(1)}
                </div>
            </div>
        `;
        container.appendChild(card);
    });
    lucide.createIcons();
}

function setupChefSurprise() {
    const btn = document.getElementById('btn-chef-surprise');
    if(btn) {
        btn.addEventListener('click', () => {
            const surprises = ["Spicy Discoveries", "Hidden Asian Gems", "Comforting Italian", "Sweet Rich Desserts"];
            const random = surprises[Math.floor(Math.random() * surprises.length)];
            const searchInput = document.getElementById('search-input');
            searchInput.value = random;
            fetchRecommendations(random);
            window.scrollTo({ top: document.getElementById('search-form').offsetTop - 20, behavior: 'smooth' });
        });
    }
}

// ── Tab Navigation ──
function setupTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navItems.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            navItems.forEach(n => n.classList.remove('active'));
            tabPanes.forEach(t => t.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`tab-${targetTab}`).classList.add('active');
            
            // Re-render icons if needed
            lucide.createIcons();
        });
    });
}

// ── Search & Recommendations ──
function setupSearch() {
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    
    // Animated placeholder rotation
    const placeholders = [
        "Spicy comforting noodles...",
        "Creamy rich desserts...",
        "Late-night cheesy cravings...",
        "Healthy high-protein meals..."
    ];
    let pIdx = 0;
    setInterval(() => {
        if (document.activeElement !== searchInput) {
            searchInput.placeholder = placeholders[pIdx];
            pIdx = (pIdx + 1) % placeholders.length;
        }
    }, 4000);

    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        if (query) fetchRecommendations(query);
    });

    // Debounced live search
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        if (query.length > 2) {
            searchTimeout = setTimeout(() => {
                fetchRecommendations(query);
                // Also hide discovery categories when searching natively
                const discoveryCategories = document.getElementById('discovery-categories');
                if (discoveryCategories) discoveryCategories.style.display = 'none';
            }, 500);
        }
    });
}

function setupMoods() {
    const moodCards = document.querySelectorAll('.mood-card');
    moodCards.forEach(card => {
        card.addEventListener('click', () => {
            const mood = card.getAttribute('data-mood');
            const cuisine = card.getAttribute('data-cuisine');
            
            const searchInput = document.getElementById('search-input');
            
            if (mood) {
                searchInput.value = mood;
                fetchRecommendations(mood);
            } else if (cuisine) {
                searchInput.value = `${cuisine} food`;
                fetchRecommendations(`${cuisine} food`);
            }
            
            // Scroll to results smoothly
            window.scrollTo({ top: document.getElementById('search-form').offsetTop - 20, behavior: 'smooth' });
        });
    });
}

async function fetchRecommendations(query) {
    const resultsSection = document.getElementById('results-section');
    const discoveryCategories = document.getElementById('discovery-categories');
    const grid = document.getElementById('recommendations-grid');
    const resultsTitle = document.getElementById('results-title');
    
    // Silky fade transition logic
    if (discoveryCategories) discoveryCategories.style.display = 'none';
    resultsSection.style.display = 'block';
    resultsSection.style.animation = 'fadeSlideUp 0.5s ease forwards';
    
    // Show skeletons
    grid.innerHTML = `
        <div class="food-card skeleton" style="height: 350px;"></div>
        <div class="food-card skeleton" style="height: 350px;"></div>
        <div class="food-card skeleton" style="height: 350px;"></div>
    `;
    
    try {
        const headers = { 'Content-Type': 'application/json' };
        const token = localStorage.getItem('cravingai_token');
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch('/api/query', {
            method: 'POST',
            headers,
            body: JSON.stringify({ query, top_k: 12, include_craving_analysis: true })
        });
        
        if (!res.ok) throw new Error('Failed to fetch');
        
        const data = await res.json();
        renderFoodCards(data.results);
        
        if (data.craving_profile) {
            resultsTitle.textContent = `Matched to your ${data.craving_profile.mood} mood`;
        } else {
            // Storytelling titles based on query
            const q = query.toLowerCase();
            if (q.includes("comfort")) resultsTitle.textContent = "Warm comforting classics, perfectly matched for tonight";
            else if (q.includes("spicy")) resultsTitle.textContent = "Spicy discoveries to heat up your day";
            else if (q.includes("sweet") || q.includes("dessert")) resultsTitle.textContent = "Sweet indulgences, just for you";
            else if (q.includes("healthy") || q.includes("vegan") || q.includes("salad")) resultsTitle.textContent = "Fresh, healthy, and beautifully crafted";
            else resultsTitle.textContent = `Curated for your craving: "${query}"`;
        }
        
    } catch (err) {
        console.error(err);
        grid.innerHTML = `<p style="color: var(--accent-primary);">Could not load recommendations at this time. Please try again.</p>`;
    }
}

function renderFoodCards(dishes) {
    const grid = document.getElementById('recommendations-grid');
    grid.innerHTML = '';
    
    if (!dishes || dishes.length === 0) {
        grid.innerHTML = `<p style="color: var(--text-secondary);">No dishes found matching your craving. Try a different mood.</p>`;
        return;
    }
    
    dishes.forEach((dish, idx) => {
        // Now using our new dynamic AI image cache proxy
        const imageUrl = dish.image_url || `/api/images/${dish.id}`;
        
        const card = document.createElement('div');
        card.className = 'food-card';
        card.style.animationDelay = `${idx * 0.05}s`;
        
        card.innerHTML = `
            <div class="food-card-image-wrap">
                <img src="${imageUrl}" alt="${dish.name}" class="food-card-image" loading="lazy">
                <div class="cuisine-badge">${dish.cuisine}</div>
            </div>
            <div class="food-card-content">
                <h4 class="food-title">${dish.name}</h4>
                <div class="food-restaurant">
                    <i data-lucide="map-pin"></i> ${dish.restaurant_name}
                </div>
                <p class="food-desc">${dish.reasoning || dish.description}</p>
                
                <div class="food-meta">
                    <div class="food-price">$${dish.price.toFixed(2)}</div>
                    <div class="food-rating">
                        <i data-lucide="star"></i> ${dish.rating.toFixed(1)}
                    </div>
                </div>
                <button class="btn btn-primary magnetic-btn btn-add-cart" style="width: 100%; margin-top: 12px; font-weight: bold; border-radius: 20px; padding: 8px;">
                    <i data-lucide="shopping-bag" style="width: 16px; height: 16px; margin-right: 6px;"></i> Add to Cart
                </button>
            </div>
            <button class="btn-save-cta ${savedDishesMap.has(dish.id) ? 'active' : ''}" aria-label="Save ${dish.name}">
                <i data-lucide="heart" style="fill: ${savedDishesMap.has(dish.id) ? 'white' : 'none'}"></i>
            </button>
        `;
        
        const saveBtn = card.querySelector('.btn-save-cta');
        saveBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSaveDish(dish, saveBtn);
        });

        const addCartBtn = card.querySelector('.btn-add-cart');
        addCartBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            addToCart(dish);
            
            // Micro-animation
            const originalText = addCartBtn.innerHTML;
            addCartBtn.innerHTML = `<i data-lucide="check" style="width: 16px; height: 16px; margin-right: 6px;"></i> Added`;
            addCartBtn.style.background = '#2ecc71';
            lucide.createIcons();
            
            setTimeout(() => {
                addCartBtn.innerHTML = originalText;
                addCartBtn.style.background = '';
                lucide.createIcons();
            }, 1500);
        });
        
        grid.appendChild(card);
    });
    
    lucide.createIcons();
}

// ── Magnetic Button Physics ──
function applyMagneticEffect(selector) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            btn.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px)`;
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = `translate(0px, 0px)`;
        });
    });
}

// ── Chat Concierge ──
function setupChat() {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const messages = document.getElementById('chat-messages');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;
        
        // Add User message
        addMessage(text, 'user');
        input.value = '';
        
        // Show typing
        const typingId = 'typing-' + Date.now();
        addMessage('...', 'assistant', typingId);
        
        try {
            const headers = { 'Content-Type': 'application/json' };
            const token = localStorage.getItem('cravingai_token');
            if (token) headers['Authorization'] = `Bearer ${token}`;
            
            const payload = {
                message: text,
                history: chatHistory,
                session_id: currentSessionId
            };
            
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers,
                body: JSON.stringify(payload)
            });
            
            const data = await res.json();
            
            // Remove typing
            document.getElementById(typingId)?.remove();
            
            // Add Assistant message
            addMessage(data.reply, 'assistant');
            
            currentSessionId = data.session_id;
            
            // Append history
            chatHistory.push({ role: 'user', content: text });
            chatHistory.push({ role: 'assistant', content: data.reply });
            
        } catch (err) {
            console.error(err);
            document.getElementById(typingId)?.remove();
            addMessage("I'm sorry, my kitchen connection dropped. Try again?", 'assistant');
        }
    });
}

function addMessage(text, role, id = null) {
    const messages = document.getElementById('chat-messages');
    const el = document.createElement('div');
    el.className = `msg msg-${role}`;
    if (id) el.id = id;
    
    // parse basic markdown bold/italics
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formattedText = formattedText.replace(/\n/g, '<br>');
    
    el.innerHTML = formattedText;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
}

window.logout = function() {
    localStorage.removeItem('cravingai_token');
    location.reload();
}

// ── Profile & Save System ──
async function fetchProfileData() {
    const token = localStorage.getItem('cravingai_token');
    if (!token) return;
    
    try {
        // Fetch User Info
        const res = await fetch('/api/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            userProfile = await res.json();
            const nameEl = document.getElementById('profile-name-display');
            if (nameEl) nameEl.textContent = userProfile.name || 'Foodie';
            
            // Emoji avatar fallback mapping
            const avatars = { 'avatar1': '🍜', 'avatar2': '🍕', 'avatar3': '🥗', 'avatar4': '🍰', 'avatar5': '🍔', 'avatar6': '🍣' };
            const avatarEl = document.getElementById('profile-avatar-display');
            if (avatarEl) avatarEl.textContent = avatars[userProfile.avatar_id] || '👤';
            
            const prefsContainer = document.getElementById('profile-prefs-display');
            if (prefsContainer) {
                if (userProfile.preferences && userProfile.preferences.length > 0) {
                    prefsContainer.innerHTML = userProfile.preferences.map(p => `<span class="cuisine-badge" style="position:relative; top:0; left:0; display:inline-block; font-size: 0.75rem;">${p}</span>`).join('');
                } else {
                    prefsContainer.innerHTML = `<span style="color: var(--text-secondary); font-size: 0.85rem;">No specific dietary preferences</span>`;
                }
            }
        }
        
        // Fetch Saved Dishes
        const favRes = await fetch('/api/profile/favorites', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (favRes.ok) {
            const favorites = await favRes.json();
            savedDishesMap.clear();
            favorites.forEach(f => savedDishesMap.set(f.dish_id, f));
            renderSavedDishes();
        }
    } catch (err) {
        console.error('Error fetching profile data', err);
    }
}

function renderSavedDishes() {
    const grid = document.getElementById('saved-dishes-grid');
    if (!grid) return;
    
    if (savedDishesMap.size === 0) {
        grid.innerHTML = `<p style="color: var(--text-secondary);">No saved dishes yet. Heart a dish in Explore to save it!</p>`;
        return;
    }
    
    const dishes = Array.from(savedDishesMap.values()).map(f => ({
        id: f.dish_id,
        name: f.name,
        cuisine: f.cuisine,
        price: f.price,
        rating: f.rating,
        restaurant_name: f.restaurant_name,
        image_url: f.image_url
    }));
    
    grid.innerHTML = '';
    dishes.forEach((dish, idx) => {
        const imageUrl = dish.image_url || `/api/images/${dish.id}`;
        const card = document.createElement('div');
        card.className = 'food-card';
        card.style.animationDelay = `${idx * 0.05}s`;
        
        card.innerHTML = `
            <div class="food-card-image-wrap">
                <img src="${imageUrl}" alt="${dish.name}" class="food-card-image" loading="lazy">
                <div class="cuisine-badge">${dish.cuisine}</div>
            </div>
            <div class="food-card-content">
                <h4 class="food-title">${dish.name}</h4>
                <div class="food-restaurant"><i data-lucide="map-pin"></i> ${dish.restaurant_name}</div>
                <div class="food-meta">
                    <div class="food-price">$${dish.price.toFixed(2)}</div>
                    <div class="food-rating"><i data-lucide="star"></i> ${dish.rating.toFixed(1)}</div>
                </div>
            </div>
            <button class="btn-save-cta active" aria-label="Unsave ${dish.name}">
                <i data-lucide="heart" style="fill: white"></i>
            </button>
        `;
        
        const saveBtn = card.querySelector('.btn-save-cta');
        saveBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSaveDish(dish, saveBtn);
        });
        
        grid.appendChild(card);
    });
    lucide.createIcons();
}

async function toggleSaveDish(dish, btnEl) {
    const token = localStorage.getItem('cravingai_token');
    if (!token) return;
    
    const isSaved = savedDishesMap.has(dish.id);
    const method = isSaved ? 'DELETE' : 'POST';
    const url = isSaved ? `/api/profile/favorites/${dish.id}` : `/api/profile/favorites`;
    
    try {
        if (isSaved) {
            savedDishesMap.delete(dish.id);
            btnEl.classList.remove('active');
            const icon = btnEl.querySelector('svg');
            if(icon) icon.style.fill = 'none';
        } else {
            savedDishesMap.set(dish.id, {
                dish_id: dish.id,
                name: dish.name,
                cuisine: dish.cuisine,
                price: dish.price,
                rating: dish.rating,
                restaurant_name: dish.restaurant_name,
                image_url: dish.image_url
            });
            btnEl.classList.add('active');
            const icon = btnEl.querySelector('svg');
            if(icon) icon.style.fill = 'white';
        }
        
        renderSavedDishes();
        
        await fetch(url, {
            method: method,
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: isSaved ? null : JSON.stringify({
                id: dish.id,
                name: dish.name,
                cuisine: dish.cuisine || 'Global',
                price: dish.price || 15.0,
                rating: dish.rating || 4.5,
                restaurant_name: dish.restaurant_name || 'CravingAI Kitchen',
                image_url: dish.image_url
            })
        });
    } catch (err) {
        console.error(err);
    }
}

// ── Cart Logic ──
let currentCart = [];

async function fetchCart() {
    const token = localStorage.getItem('cravingai_token');
    if (!token) return;
    try {
        const res = await fetch('/api/cart/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            currentCart = await res.json();
            updateCartUI();
        }
    } catch (e) {
        console.error("Failed to fetch cart", e);
    }
}

async function addToCart(dish) {
    const token = localStorage.getItem('cravingai_token');
    if (!token) return;
    try {
        await fetch('/api/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({
                dish_id: dish.id,
                name: dish.name,
                price: dish.price || 15.0,
                image_url: dish.image_url || `/api/images/${dish.id}`,
                restaurant_name: dish.restaurant_name || "CravingAI Kitchen"
            })
        });
        fetchCart();
    } catch (e) {
        console.error("Failed to add to cart", e);
    }
}

async function removeFromCart(dishId) {
    const token = localStorage.getItem('cravingai_token');
    if (!token) return;
    try {
        await fetch('/api/cart/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ dish_id: dishId })
        });
        fetchCart();
    } catch (e) {
        console.error("Failed to remove from cart", e);
    }
}

async function checkoutCart() {
    const token = localStorage.getItem('cravingai_token');
    if (!token) return;
    try {
        const res = await fetch('/api/cart/checkout', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            alert("Order placed successfully! Your food will be prepared soon.");
            currentCart = [];
            updateCartUI();
            toggleCartPanel();
        }
    } catch (e) {
        console.error("Failed to checkout", e);
    }
}

function updateCartUI() {
    const badge = document.getElementById('cart-badge');
    const container = document.getElementById('cart-items-container');
    const totalEl = document.getElementById('cart-total-price');
    const checkoutBtn = document.getElementById('checkout-btn');

    if (!badge || !container) return;

    let totalQty = 0;
    let totalPrice = 0;

    container.innerHTML = '';

    if (currentCart.length === 0) {
        badge.style.display = 'none';
        container.innerHTML = '<div class="empty-cart-msg">Your cart is empty</div>';
        totalEl.textContent = '$0.00';
        checkoutBtn.disabled = true;
        return;
    }

    checkoutBtn.disabled = false;

    currentCart.forEach(item => {
        totalQty += item.quantity;
        totalPrice += (item.price * item.quantity);

        const el = document.createElement('div');
        el.className = 'cart-item';
        el.innerHTML = `
            <img src="${item.image_url}" class="cart-item-img" alt="${item.name}">
            <div class="cart-item-details">
                <h4 class="cart-item-title">${item.name}</h4>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="cart-item-price">$${(item.price * item.quantity).toFixed(2)}</span>
                    <div class="cart-item-actions">
                        <button class="cart-qty-btn" onclick="removeFromCart('${item.dish_id}')">-</button>
                        <span>${item.quantity}</span>
                        <button class="cart-qty-btn" onclick="addToCart({id: '${item.dish_id}', name: '${item.name}', price: ${item.price}, image_url: '${item.image_url}', restaurant_name: '${item.restaurant_name}'})">+</button>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(el);
    });

    badge.textContent = totalQty;
    badge.style.display = totalQty > 0 ? 'flex' : 'none';
    totalEl.textContent = '$' + totalPrice.toFixed(2);
}

function toggleCartPanel() {
    const panel = document.getElementById('cart-panel');
    const overlay = document.getElementById('cart-overlay');
    if (panel.classList.contains('open')) {
        panel.classList.remove('open');
        overlay.classList.remove('active');
    } else {
        panel.classList.add('open');
        overlay.classList.add('active');
        fetchCart();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const topCartBtn = document.getElementById('top-cart-btn');
    if (topCartBtn) topCartBtn.addEventListener('click', toggleCartPanel);
    
    const closeCartBtn = document.getElementById('close-cart-btn');
    if (closeCartBtn) closeCartBtn.addEventListener('click', toggleCartPanel);
    
    const overlay = document.getElementById('cart-overlay');
    if (overlay) overlay.addEventListener('click', toggleCartPanel);
    
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) checkoutBtn.addEventListener('click', checkoutCart);
    
    // Fetch cart on load if logged in
    if(localStorage.getItem('cravingai_token')) {
        fetchCart();
    }
});
