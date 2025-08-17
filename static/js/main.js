// Minecraft Bedwars Leaderboard - Enhanced JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎮 Bedwars Leaderboard initialized successfully!');

    // Initialize all components
    initializeCursor();
    initializeRippleEffect();
    initializeAnimations();
    initializeStatCalculators();
    initializeFormValidation();
    initializeMobileOptimizations();
    initializePerformanceMetrics();
    initializeAccessibility();
    initializeAdvancedFeatures();
    initializeGradientSystem();
    initializeLazyLoading();

    // Apply current theme if set
    applyCurrentTheme();

    // Initialize i18n when DOM is loaded
    if (typeof window.bedwarsI18n === 'undefined') {
        window.bedwarsI18n = new I18n();
    }

    // Ensure language switching works
    setTimeout(() => {
        if (window.bedwarsI18n && typeof window.bedwarsI18n.createLanguageSwitcher === 'function') {
            window.bedwarsI18n.createLanguageSwitcher();
        }
    }, 100);

    // Initialize quest timers
    initializeQuestTimers();

    // Initialize quest category switching
    const categoryTabs = document.querySelectorAll('.category-tab');
    categoryTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            handleCategorySwitch(this);
        });
    });

    // Initialize enhanced add player form if present
    setTimeout(() => {
        if (document.querySelector('.enhanced-add-player-section')) {
            console.log('🎯 Initializing enhanced add player form...');
            initializeEnhancedForm();
        }
    }, 100);

    // Initialize social networks management
    initializeSocialNetworks();

    console.log('🎮 Quest system initialized successfully!');
});

// Enhanced Custom Cursor System - Fixed
function initializeCursor() {
    console.log('🖱️ Initializing custom cursor...');

    // Create single cursor element
    const cursor = document.createElement('div');
    cursor.classList.add('custom-cursor');
    cursor.id = 'custom-cursor';
    document.body.appendChild(cursor);

    let mouseX = 0;
    let mouseY = 0;
    let cursorX = 0;
    let cursorY = 0;

    // Mouse move handler
    function handleMouseMove(e) {
        mouseX = e.clientX;
        mouseY = e.clientY;
    }

    // Click handler
    function handleClick(e) {
        cursor.classList.add('clicking');

        // Create ripple effect
        createRipple(e.clientX, e.clientY);

        setTimeout(() => {
            cursor.classList.remove('clicking');
        }, 200);
    }

    // Smooth cursor animation
    function animateCursor() {
        const speed = 0.15;
        cursorX += (mouseX - cursorX) * speed;
        cursorY += (mouseY - cursorY) * speed;

        cursor.style.left = cursorX + 'px';
        cursor.style.top = cursorY + 'px';

        requestAnimationFrame(animateCursor);
    }

    // Event listeners
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('click', handleClick);

    // Cursor effects on interactive elements
    const interactiveElements = 'button, a, .clickable'; // Define interactive elements

    function scaleCursor(isHovering) {
        cursor.classList.toggle('cursor-hover', isHovering);
    }

    // Handle dynamically added elements
        document.addEventListener('mouseenter', (e) => {
            if (e.target && typeof e.target.matches === 'function' && e.target.matches(interactiveElements)) {
                scaleCursor(true);
            }
        }, true);

        document.addEventListener('mouseleave', (e) => {
            if (e.target && typeof e.target.matches === 'function' && e.target.matches(interactiveElements)) {
                scaleCursor(false);
            }
        }, true);

        // Initialize dropdown functionality
        initializeDropdowns();

    // Start animation
    animateCursor();
}

function initializeRippleEffect() {
    function createRipple(x, y) {
        const ripple = document.createElement('div');
        ripple.className = 'ripple';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';

        document.body.appendChild(ripple);

        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 800);
    }

    // Make createRipple available globally
    window.createRipple = createRipple;

    document.addEventListener('click', function(e) {
        const target = e.target;
        if (target && target.closest) {
            const clickableElement = target.closest('button, .btn, .card, .ripple');
            if (clickableElement) {
                createRippleFromEvent(e);
            }
        }
    });
}

function createRippleFromEvent(event) {
    const button = event.currentTarget;
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    const ripple = document.createElement('span');
    ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 600ms linear;
        background-color: rgba(255, 255, 255, 0.6);
        left: ${x}px;
        top: ${y}px;
        width: ${size}px;
        height: ${size}px;
        pointer-events: none;
    `;

    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);

    setTimeout(() => {
        ripple.remove();
    }, 600);
}

function initializeAnimations() {
    console.log('✨ Initializing animations...');

    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
            }
        });
    }, observerOptions);

    // Observe elements for animation
    document.querySelectorAll('.player-row, .stat-card, .achievement-card').forEach(el => {
        observer.observe(el);
    });

    // Animate stat counters
    animateStatCounters();

    // Update winrate colors
    updateWinRateColors();
}

function animateStatCounters() {
    const statNumbers = document.querySelectorAll('.stat-value');

    statNumbers.forEach((stat, index) => {
        const value = parseInt(stat.textContent.replace(/,/g, ''));
        if (!isNaN(value) && value > 0) {
            setTimeout(() => {
                animateNumber(stat, 0, value, 1500);
            }, index * 100);
        }
    });
}

function animateNumber(element, start, end, duration) {
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(start + (end - start) * easeOut);

        element.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// Enhanced Gradient System
function initializeGradientSystem() {
    console.log('🎨 Initializing gradient system...');

    // Load all player gradients on leaderboard
    loadLeaderboardGradients();

    // Initialize gradient inventory system
    initializeGradientInventory();

    // Fix any broken gradients
    fixBrokenGradients();
}

function loadLeaderboardGradients() {
    const playerRows = document.querySelectorAll('.player-row');
    playerRows.forEach(row => {
        const playerId = row.getAttribute('data-player-id');
        if (playerId) {
            loadPlayerGradients(parseInt(playerId));
        }
    });
}

function loadPlayerGradients(playerId) {
    fetch(`/api/player/${playerId}/gradients`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.gradients) {
                applyPlayerGradients(playerId, data.gradients);
            }
        })
        .catch(error => {
            console.error('Error loading player gradients:', error);
        });
}

function applyPlayerGradients(playerId, gradients) {
    Object.entries(gradients).forEach(([elementType, gradientData]) => {
        if (gradientData && gradientData.css_gradient) {
            applyGradientToElement(playerId, elementType, gradientData);
        }
    });
}

function applyGradientToElement(playerId, elementType, gradientData) {
    const elements = document.querySelectorAll(`[data-player-id="${playerId}"][data-element="${elementType}"]`);

    elements.forEach(element => {
        if (gradientData.css_gradient) {
            element.style.background = gradientData.css_gradient;
            element.style.backgroundSize = '200% 200%';
            element.style.webkitBackgroundClip = 'text';
            element.style.webkitTextFillColor = 'transparent';
            element.style.backgroundClip = 'text';

            if (gradientData.is_animated) {
                element.style.animation = 'gradientShift 3s ease-in-out infinite';
            }

            element.classList.add('gradient-text');
        }
    });
}

function initializeGradientInventory() {
    // Initialize gradient inventory if on inventory page
    if (window.location.pathname === '/inventory') {
        initializeInventoryHandlers();
    }
}

function initializeInventoryHandlers() {
    // Apply gradient buttons
    document.querySelectorAll('.apply-gradient-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const gradientId = this.getAttribute('data-gradient-id');
            const elementType = this.getAttribute('data-element-type');
            applyInventoryGradient(gradientId, elementType);
        });
    });

    // Remove gradient buttons
    document.querySelectorAll('.remove-gradient-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const elementType = this.getAttribute('data-element-type');
            removeInventoryGradient(elementType);
        });
    });
}

function applyInventoryGradient(gradientId, elementType) {
    fetch('/api/apply-gradient', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            gradient_id: gradientId,
            element_type: elementType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Градиент применён!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Ошибка применения градиента', 'error');
        }
    })
    .catch(error => {
        console.error('Error applying gradient:', error);
        showToast('Ошибка применения градиента', 'error');
    });
}

function removeInventoryGradient(elementType) {
    fetch('/api/remove-gradient', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            element_type: elementType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Градиент удалён!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.error || 'Ошибка удаления градиента', 'error');
        }
    })
    .catch(error => {
        console.error('Error removing gradient:', error);
        showToast('Ошибка удаления градиента', 'error');
    });
}

function fixBrokenGradients() {
    // Fix gradient fallbacks for unsupported browsers
    document.querySelectorAll('.gradient-text').forEach(element => {
        if (!CSS.supports('-webkit-background-clip', 'text')) {
            const fallbackColor = element.getAttribute('data-fallback-color') || '#ffc107';
            element.style.color = fallbackColor;
            element.style.background = 'none';
        }
    });
}

// Statistics Calculators
function initializeStatCalculators() {
    console.log('🧮 Initializing stat calculators...');

    // Real-time K/D ratio calculator
    const killInputs = document.querySelectorAll('input[name="kills"]');
    const deathInputs = document.querySelectorAll('input[name="deaths"]');

    function updateKDRatio() {
        const kills = parseInt(killInputs[0]?.value || 0);
        const deaths = parseInt(deathInputs[0]?.value || 0);
        const ratio = deaths > 0 ? (kills / deaths).toFixed(2) : kills;

        const kdDisplay = document.querySelector('.kd-preview');
        if (kdDisplay) {
            kdDisplay.textContent = ratio;
            kdDisplay.className = `kd-preview ${ratio >= 2 ? 'text-success' : ratio >= 1 ? 'text-warning' : 'text-danger'}`;
        }
    }

    killInputs.forEach(input => input.addEventListener('input', updateKDRatio));
    deathInputs.forEach(input => input.addEventListener('input', updateKDRatio));

    // Auto-calculate stats in admin forms
    const statsInputs = document.querySelectorAll('input[type="number"][data-stat]');
    statsInputs.forEach(input => {
        input.addEventListener('input', function() {
            calculateDerivedStats();
        });
    });
}

function calculateDerivedStats() {
    const killsInput = document.querySelector('input[name="kills"]');
    const deathsInput = document.querySelector('input[name="deaths"]');
    const winsInput = document.querySelector('input[name="wins"]');
    const gamesInput = document.querySelector('input[name="games_played"]');

    if (killsInput && deathsInput) {
        const kills = parseInt(killsInput.value) || 0;
        const deaths = parseInt(deathsInput.value) || 0;
        const kd = deaths > 0 ? (kills / deaths).toFixed(2) : kills;

        const kdDisplay = document.querySelector('.kd-display');
        if (kdDisplay) {
            kdDisplay.textContent = `K/D: ${kd}`;
        }
    }

    if (winsInput && gamesInput) {
        const wins = parseInt(winsInput.value) || 0;
        const games = parseInt(gamesInput.value) || 0;
        const winRate = games > 0 ? ((wins / games) * 100).toFixed(1) : 0;

        const wrDisplay = document.querySelector('.wr-display');
        if (wrDisplay) {
            wrDisplay.textContent = `Win Rate: ${winRate}%`;
        }
    }
}

// Form Validation
function initializeFormValidation() {
    console.log('✅ Initializing form validation...');

    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
                return false;
            }
        });

        // Real-time validation
        const inputs = form.querySelectorAll('input[type="number"]');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateInput(this);
            });
        });
    });
}

function validateForm(form) {
    let isValid = true;

    // Check required fields
    const required = form.querySelectorAll('[required]');
    required.forEach(input => {
        if (!input.value.trim()) {
            markInputError(input, 'Это поле обязательно');
            isValid = false;
        }
    });

    // Check numeric ranges
    const numbers = form.querySelectorAll('input[type="number"]');
    numbers.forEach(input => {
        const value = parseInt(input.value);
        const min = parseInt(input.min);
        const max = parseInt(input.max);

        if (value < min) {
            markInputError(input, `Минимальное значение: ${min}`);
            isValid = false;
        }

        if (max && value > max) {
            markInputError(input, `Максимальное значение: ${max}`);
            isValid = false;
        }
    });

    // Game logic validation
    const wins = parseInt(form.querySelector('input[name="wins"]')?.value || 0);
    const games = parseInt(form.querySelector('input[name="games_played"]')?.value || 0);

    if (wins > games) {
        showErrorMessage('Количество побед не может превышать количество игр!');
        isValid = false;
    }

    return isValid;
}

function validateInput(input) {
    clearInputError(input);

    const value = parseFloat(input.value);
    const min = parseFloat(input.min);
    const max = parseFloat(input.max);

    if (input.hasAttribute('required') && !input.value.trim()) {
        markInputError(input, 'Обязательное поле');
        return false;
    }

    if (!isNaN(min) && value < min) {
        markInputError(input, `Мин: ${min}`);
        return false;
    }

    if (!isNaN(max) && value > max) {
        markInputError(input, `Макс: ${max}`);
        return false;
    }

    return true;
}

function markInputError(input, message) {
    input.classList.add('is-invalid');

    let errorDiv = input.parentNode.querySelector('.invalid-feedback');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        input.parentNode.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
}

function clearInputError(input) {
    input.classList.remove('is-invalid');
    const errorDiv = input.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Mobile Optimizations
function initializeMobileOptimizations() {
    console.log('📱 Initializing mobile optimizations...');

    // Touch support for cards
    if ('ontouchstart' in window) {
        document.querySelectorAll('.card, .player-row').forEach(element => {
            element.addEventListener('touchstart', function() {
                this.classList.add('touch-active');
            });

            element.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.classList.remove('touch-active');
                }, 150);
            });
        });
    }

    // Responsive table handling
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
        if (window.innerWidth < 768) {
            table.classList.add('mobile-scrollable');
        }
    });

    if (window.innerWidth <= 768) {
        // Disable heavy animations on mobile
        document.body.classList.add('mobile-optimized');

        // Reduce gradient animations
        const animatedGradients = document.querySelectorAll('.gradient-animated');
        animatedGradients.forEach(element => {
            element.style.animation = 'none';
        });
    }
}

// Performance Metrics
function initializePerformanceMetrics() {
    console.log('⚡ Performance Metrics:', {
        'Load Time': `${(performance.now()).toFixed(2)}ms`,
        'DOM Content Loaded': `${(performance.getEntriesByType('navigation')[0]?.domContentLoadedEventEnd - performance.getEntriesByType('navigation')[0]?.domContentLoadedEventStart || 0).toFixed(1)}ms`,
        'Total Page Load': `${(performance.getEntriesByType('navigation')[0]?.loadEventEnd - performance.getEntriesByType('navigation')[0]?.navigationStart || 0).toFixed(1)}ms`
    });
}

// Accessibility Enhancements
function initializeAccessibility() {
    console.log('♿ Initializing accessibility features...');

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        // Tab navigation enhancement
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }

        // Escape key handling
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.show');
            if (activeModal) {
                const modal = bootstrap.Modal.getInstance(activeModal);
                if (modal) modal.hide();
            }
        }
    });

    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-navigation');
    });

    // Screen reader announcements
    const announceRegion = document.createElement('div');
    announceRegion.setAttribute('aria-live', 'polite');
    announceRegion.setAttribute('aria-atomic', 'true');
    announceRegion.style.cssText = 'position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;';
    document.body.appendChild(announceRegion);

    window.announceToScreenReader = function(message) {
        announceRegion.textContent = message;
    };

    // Add ARIA labels to interactive elements
    document.querySelectorAll('button, a, input, select').forEach(element => {
        if (!element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')) {
            const text = element.textContent?.trim() || element.getAttribute('title') || element.getAttribute('placeholder');
            if (text) {
                element.setAttribute('aria-label', text);
            }
        }
    });

    // Keyboard navigation for custom elements
    document.querySelectorAll('.player-row').forEach(row => {
        row.setAttribute('tabindex', '0');
        row.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const link = this.querySelector('a');
                if (link) link.click();
            }
        });
    });
}

// Advanced Features
function initializeAdvancedFeatures() {
    console.log('🚀 Initializing advanced features...');

    initializeQuickFilters();
    initializeKeyboardShortcuts();
    initializeTableEnhancements();
    initializeSearchEnhancements();
    initializeTooltips();
}

function initializeQuickFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const playerRows = document.querySelectorAll('.player-row');

    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');

            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // Filter rows
            playerRows.forEach(row => {
                const shouldShow = filter === 'all' || row.getAttribute('data-filter') === filter;
                row.style.display = shouldShow ? '' : 'none';
            });
        });
    });
}

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + F to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }

        // Escape to clear search
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput && searchInput.value) {
                searchInput.value = '';
                searchInput.form.submit();
            }
        }
    });
}

function initializeTableEnhancements() {
    const tables = document.querySelectorAll('.leaderboard-table');

    tables.forEach(table => {
        // Add zebra striping enhancement
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach((row, index) => {
            if (index % 2 === 0) {
                row.style.backgroundColor = 'rgba(255, 255, 255, 0.02)';
            }
        });

        // Enhanced row hover effects
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.transform = 'translateX(5px)';
                this.style.boxShadow = '0 4px 15px rgba(255, 193, 7, 0.3)';
            });

            row.addEventListener('mouseleave', function() {
                this.style.transform = 'translateX(0)';
                this.style.boxShadow = 'none';
            });
        });
    });
}

function initializeTooltips() {
    // Simple tooltip implementation
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            tooltip.style.cssText = `
                position: absolute;
                background: rgba(0,0,0,0.9);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 0.875rem;
                pointer-events: none;
                z-index: 10000;
                white-space: nowrap;
            `;

            document.body.appendChild(tooltip);

            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';

            this._tooltip = tooltip;
        });

        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                delete this._tooltip;
            }
        });
    });
}

function initializeSearchEnhancements() {
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        // Debounced search
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 2 || this.value.length === 0) {
                    this.form.submit();
                }
            }, 300);
        });

        // Search suggestions
        searchInput.addEventListener('focus', function() {
            // Could implement search suggestions here
        });
    }
}

// Theme System
function applyCurrentTheme() {
    const savedTheme = localStorage.getItem('selected_theme');
    if (savedTheme) {
        try {
            const theme = JSON.parse(savedTheme);
            updateThemeVariables(theme);
        } catch (e) {
            console.error('Error parsing saved theme:', e);
        }
    }

    // Also update variables if there's a session theme
    const sessionTheme = window.sessionTheme;
    if (sessionTheme) {
        updateThemeVariables(sessionTheme);
    }
}

function updateThemeVariables(theme) {
    const root = document.documentElement;

    if (theme.primary_color) root.style.setProperty('--primary-color', theme.primary_color);
    if (theme.secondary_color) root.style.setProperty('--secondary-color', theme.secondary_color);
    if (theme.background_color) root.style.setProperty('--background-color', theme.background_color);
    if (theme.card_background) root.style.setProperty('--card-background', theme.card_background);
    if (theme.text_color) root.style.setProperty('--text-color', theme.text_color);
    if (theme.accent_color) root.style.setProperty('--accent-color', theme.accent_color);
}

// Update winrate colors on load and after animations
function updateWinRateColors() {
    document.querySelectorAll('.winrate').forEach(element => {
        const winrate = parseFloat(element.textContent);
        element.classList.remove('winrate-low', 'winrate-medium', 'winrate-high');

        if (winrate >= 50) {
            element.classList.add('winrate-high');    // Green for 50%+
        } else if (winrate >= 40) {
            element.classList.add('winrate-medium');  // Yellow for 40-49%
        } else {
            element.classList.add('winrate-low');     // Red for 0-39%
        }
    });
}

// Lazy loading function
function initializeLazyLoading() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        lazyImages.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for browsers without IntersectionObserver
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
        });
    }
}

// Enhanced Feedback System
function showSuccessMessage(message, details = '') {
    showAdvancedToast(message, 'success', details);
}

function showErrorMessage(message, details = '') {
    showAdvancedToast(message, 'error', details);
}

function showInfoMessage(message, details = '') {
    showAdvancedToast(message, 'info', details);
}

function showWarningMessage(message, details = '') {
    showAdvancedToast(message, 'warning', details);
}

// Enhanced loading states
function setButtonLoading(button, loading = true) {
    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            Загрузка...
        `;
        button.classList.add('loading');
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || button.innerHTML;
        button.classList.remove('loading');
    }
}

// Progress indicator
function showProgress(percentage, message = 'Загрузка...') {
    let progressContainer = document.getElementById('global-progress');

    if (!progressContainer) {
        progressContainer = document.createElement('div');
        progressContainer.id = 'global-progress';
        progressContainer.className = 'global-progress-container';
        progressContainer.innerHTML = `
            <div class="progress-backdrop"></div>
            <div class="progress-content">
                <div class="progress-spinner">
                    <div class="spinner-ring"></div>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: 0%"></div>
                </div>
                <div class="progress-message">Инициализация...</div>
                <div class="progress-percentage">0%</div>
            </div>
        `;
        document.body.appendChild(progressContainer);
    }

    const progressBar = progressContainer.querySelector('.progress-bar');
    const progressMessage = progressContainer.querySelector('.progress-message');
    const progressPercentage = progressContainer.querySelector('.progress-percentage');

    progressContainer.style.display = 'flex';
    progressBar.style.width = percentage + '%';
    progressMessage.textContent = message;
    progressPercentage.textContent = Math.round(percentage) + '%';

    if (percentage >= 100) {
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 500);
    }
}

// Enhanced notification system
function showAdvancedToast(message, type = 'info', details = '', duration = 4000) {
    const toastContainer = getOrCreateToastContainer();

    const toast = document.createElement('div');
    toast.className = `advanced-toast toast-${type}`;

    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-triangle',
        warning: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle'
    };

    toast.innerHTML = `
        <div class="toast-icon">
            <i class="${icons[type]}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-message">${message}</div>
            ${details ? `<div class="toast-details">${details}</div>` : ''}
        </div>
        <div class="toast-progress">
            <div class="toast-progress-bar"></div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    toastContainer.appendChild(toast);

    // Animate in
    setTimeout(() => toast.classList.add('show'), 10);

    // Auto remove
    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    }, duration);

    // Progress bar animation
    const progressBar = toast.querySelector('.toast-progress-bar');
    progressBar.style.animation = `toastProgress ${duration}ms linear`;
}

function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    return container;
}

// Form validation feedback
function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (!field) return;

    // Remove existing error
    clearFieldError(fieldId);

    field.classList.add('is-invalid');

    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    errorDiv.id = fieldId + '_error';

    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return;

    field.classList.remove('is-invalid');

    const errorDiv = document.getElementById(fieldId + '_error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Action confirmations
function confirmAction(message, callback, options = {}) {
    const {
        title = 'Подтверждение',
        confirmText = 'Подтвердить',
        cancelText = 'Отмена',
        type = 'warning'
    } = options;

    const modal = document.createElement('div');
    modal.className = 'confirmation-modal';
    modal.innerHTML = `
        <div class="confirmation-backdrop"></div>
        <div class="confirmation-content">
            <div class="confirmation-header">
                <h5 class="confirmation-title">${title}</h5>
            </div>
            <div class="confirmation-body">
                <div class="confirmation-icon confirmation-${type}">
                    <i class="fas fa-${type === 'danger' ? 'exclamation-triangle' : 'question-circle'}"></i>
                </div>
                <p class="confirmation-message">${message}</p>
            </div>
            <div class="confirmation-footer">
                <button class="btn btn-secondary confirmation-cancel">${cancelText}</button>
                <button class="btn btn-${type === 'danger' ? 'danger' : 'warning'} confirmation-confirm">${confirmText}</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Event listeners
    modal.querySelector('.confirmation-cancel').onclick = () => {
        modal.remove();
    };

    modal.querySelector('.confirmation-confirm').onclick = () => {
        callback();
        modal.remove();
    };

    modal.querySelector('.confirmation-backdrop').onclick = () => {
        modal.remove();
    };

    // Animate in
    setTimeout(() => modal.classList.add('show'), 10);
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-message toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
            <span>${message}</span>
        </div>
    `;

    // Add to page
    document.body.appendChild(toast);

    // Animate in
    setTimeout(() => toast.classList.add('show'), 10);

    // Remove after delay
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Error Handling
window.addEventListener('error', function(e) {
    console.error('🚨 JavaScript Error:', {
        message: e.message,
        filename: e.filename,
        line: e.lineno,
        column: e.colno
    });
});

// Initialize Elite Squad specific features
console.log('🎮 Elite Squad Bedwars initialized successfully!');

// Admin Calculator Functions
function showCalculator() {
    const calculator = document.getElementById('quick_calculator');
    if (calculator) {
        calculator.style.display = calculator.style.display === 'none' ? 'block' : 'none';
    }
}

function setOperation(operation, value) {
    document.getElementById('operation').value = operation;
    document.getElementById('value').value = value;

    // Auto-set common stat types based on value
    const statType = document.getElementById('stat_type');
    if (value >= 1000) {
        statType.value = 'experience';
    } else if (value >= 100) {
        statType.value = 'coins';
    } else if (value <= 50 && value > 0) {
        statType.value = 'reputation';
    }

    // Visual feedback
    showInfoMessage(`Операция установлена: ${operation === 'add' ? 'Добавить' : operation === 'subtract' ? 'Убавить' : 'Установить'} ${value}`);
}

// Enhanced form submissions with feedback
function enhanceFormSubmissions() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                setButtonLoading(submitBtn, true);

                // Re-enable button after timeout (fallback)
                setTimeout(() => {
                    setButtonLoading(submitBtn, false);
                }, 5000);
            }
        });
    });
}

// Initialize enhanced features
document.addEventListener('DOMContentLoaded', function() {
    enhanceFormSubmissions();
    initializeAdminCategories();

    // Auto-hide flash messages after delay
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            if (alert.classList.contains('alert-success')) {
                alert.style.transition = 'opacity 0.5s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            }
        });
    }, 3000);
});

// Admin categories management
function initializeAdminCategories() {
    const categoryTabs = document.querySelectorAll('.category-tab');
    const actionCategories = document.querySelectorAll('.action-category');

    if (categoryTabs.length === 0) return;

    categoryTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const category = this.dataset.category;

            // Update active tab
            categoryTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            // Show/hide categories
            actionCategories.forEach(cat => {
                if (cat.dataset.category === category) {
                    cat.classList.add('active');
                    cat.style.display = 'block';
                } else {
                    cat.classList.remove('active');
                    cat.style.display = 'none';
                }
            });
        });
    });

    // Show first category by default
    if (actionCategories.length > 0) {
        actionCategories[0].classList.add('active');
        actionCategories[0].style.display = 'block';
    }
}


// Enhanced dropdown functionality with smooth animations
function initializeDropdowns() {
    console.log('🎯 Initializing enhanced dropdown with animations...');

    const dropdownToggle = document.getElementById('user-dropdown-toggle');
    const dropdownMenu = document.getElementById('user-dropdown-menu');

    if (!dropdownToggle || !dropdownMenu) return;

    // Handle dropdown show event
    dropdownToggle.addEventListener('show.bs.dropdown', function() {
        dropdownMenu.classList.remove('show');
        // Trigger reflow to ensure transition works
        dropdownMenu.offsetHeight;
        dropdownMenu.classList.add('show');
    });

    // Handle dropdown hide event
    dropdownToggle.addEventListener('hide.bs.dropdown', function() {
        dropdownMenu.classList.remove('show');
    });

    // Ensure proper cleanup on hide
    dropdownToggle.addEventListener('hidden.bs.dropdown', function() {
        dropdownMenu.style.transform = '';
        dropdownMenu.style.opacity = '';
    });

    console.log('🎯 Enhanced dropdown initialized successfully');
}


// Enhanced ripple effect for buttons
    function createRipple(button, event) {
        if (!button || typeof button.getBoundingClientRect !== 'function') {
            return;
        }

        const circle = document.createElement("span");
        const diameter = Math.max(button.clientWidth, button.clientHeight);
        const radius = diameter / 2;

        try {
            const rect = button.getBoundingClientRect();
            circle.style.width = circle.style.height = `${diameter}px`;
            circle.style.left = `${event.clientX - rect.left - radius}px`;
            circle.style.top = `${event.clientY - rect.top - radius}px`;
            circle.classList.add("ripple");

            const ripple = button.getElementsByClassName("ripple")[0];
            if (ripple) {
                ripple.remove();
            }

            button.appendChild(circle);
        } catch (error) {
            console.warn('Ripple effect error:', error);
        }
    }

// Enhanced event delegation with browser compatibility
    document.addEventListener('click', function(e) {
        var target = e.target;
        // Check if target is a link in player name using compatible method
        if (target && target.nodeName === 'A' && target.closest && target.closest('.player-name')) {
            // Handle player link clicks with enhanced animation
            target.style.transform = 'scale(0.95)';
            setTimeout(function() {
                target.style.transform = 'scale(1)';
            }, 150);
        }
    });

    document.addEventListener('mouseover', function(e) {
        var target = e.target;
        if (target && target.classList && typeof target.classList.contains === 'function' && target.classList.contains('leaderboard-row')) {
            target.style.transform = 'translateX(5px)';
        }
    });

    document.addEventListener('mouseout', function(e) {
        var target = e.target;
        if (target && target.classList && typeof target.classList.contains === 'function' && target.classList.contains('leaderboard-row')) {
            target.style.transform = 'translateX(0)';
        }
    });

// Enhanced gradient application function
function applyGradientFromInventory(gradientId, elementType) {
    if (!confirm(`Применить градиент к ${elementType}?`)) return;

    fetch('/api/apply-gradient', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            gradient_id: gradientId,
            element_type: elementType
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Градиент успешно применен!', 'success');
            location.reload();
        } else {
            showToast('Ошибка при применении градиента: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error applying gradient:', error);
        showToast('Произошла ошибка', 'error');
    });
}

// Quest Category Management
function handleCategorySwitch(tab) {
    const category = tab.dataset.category;

    // Update active tab
    document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    // Show/hide quest categories
    document.querySelectorAll('.quest-category').forEach(cat => {
        if (category === 'all' || cat.dataset.category === category) {
            cat.style.display = 'block';
        } else {
            cat.style.display = 'none';
        }
    });
}

// Enhanced add player form steps
function initializeEnhancedForm() {
    console.log('🎯 Setting up form navigation...');

    const formSteps = document.querySelectorAll('.form-step');
    const progressSteps = document.querySelectorAll('.progress-step');
    const prevBtn = document.querySelector('.prev-step');
    const nextBtn = document.querySelector('.next-step');
    const submitBtn = document.querySelector('button[type="submit"]');

    console.log('📋 Found elements:', {
        formSteps: formSteps.length,
        progressSteps: progressSteps.length,
        prevBtn: !!prevBtn,
        nextBtn: !!nextBtn,
        submitBtn: !!submitBtn
    });

    // Check if all required elements are present
    if (!formSteps.length || !progressSteps.length || !prevBtn || !nextBtn || !submitBtn) {
        console.error('❌ Missing required form elements');
        return;
    }

    let currentStep = 1;

    function showStep(step) {
        console.log(`🎯 Showing step ${step}`);

        // Hide all steps
        formSteps.forEach(s => s.classList.remove('active'));
        progressSteps.forEach(s => s.classList.remove('active'));

        // Show target step
        const targetStep = document.querySelector(`[data-step="${step}"]`);
        const targetProgress = document.querySelector(`.progress-step[data-step="${step}"]`);

        if (targetStep) targetStep.classList.add('active');
        if (targetProgress) targetProgress.classList.add('active');

        currentStep = step;
        updateNavigationButtons();
    }

    function updateNavigationButtons() {
        console.log(`🎯 Updating navigation for step ${currentStep}`);

        // Update prev button
        if (prevBtn) {
            prevBtn.disabled = currentStep === 1;
            console.log(`⬅️ Prev button disabled: ${currentStep === 1}`);
        }

        // Update next button and submit button
        if (nextBtn && submitBtn) {
            if (currentStep < 4) {
                nextBtn.style.display = 'inline-block';
                submitBtn.style.display = 'none';
                console.log(`➡️ Showing next button`);
            } else {
                nextBtn.style.display = 'none';
                submitBtn.style.display = 'inline-block';
                console.log(`✅ Showing submit button`);
            }
        }

        // Update progress steps
        progressSteps.forEach((step, index) => {
            if (index + 1 <= currentStep) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });
    }

    // Event listeners for navigation buttons
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            console.log(`⬅️ Prev button clicked, current step: ${currentStep}`);
            if (currentStep > 1) {
                showStep(currentStep - 1);
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            console.log(`➡️ Next button clicked, current step: ${currentStep}`);
            if (currentStep < 4) {
                showStep(currentStep + 1);
            }
        });
    }

    // Initialize form
    try {
        console.log('🎯 Initializing form with step 1');
        showStep(1);
        console.log('✅ Form initialization complete');
    } catch (error) {
        console.error('❌ Error initializing form:', error);
    }
}

// Initialize quest timers
function initializeQuestTimers() {
    updateQuestTimers(); // Initial call
    setInterval(updateQuestTimers, 1000); // Update every second
}

// Social networks management
function initializeSocialNetworks() {
    console.log('🌐 Initializing social networks management...');

    const addSocialBtn = document.getElementById('add-social');
    const socialContainer = document.getElementById('social-networks-container');

    if (!addSocialBtn || !socialContainer) return;

    // Add new social network field
    addSocialBtn.addEventListener('click', function() {
        const socialItem = document.createElement('div');
        socialItem.className = 'social-network-item d-flex align-items-center mb-2';
        socialItem.innerHTML = `
            <select class="form-select me-2" name="social_type[]" style="max-width: 150px;">
                <option value="discord">Discord</option>
                <option value="telegram">Telegram</option>
                <option value="vk">VK</option>
                <option value="twitter">Twitter</option>
                <option value="instagram">Instagram</option>
                <option value="tiktok">TikTok</option>
                <option value="steam">Steam</option>
            </select>
            <input type="text" class="form-control me-2" name="social_value[]" 
                   placeholder="Ссылка или никнейм">
            <button type="button" class="btn btn-danger btn-sm remove-social">
                <i class="fas fa-trash"></i>
            </button>
        `;
        socialContainer.appendChild(socialItem);

        // Add remove functionality to the new item
        const removeBtn = socialItem.querySelector('.remove-social');
        removeBtn.addEventListener('click', function() {
            socialItem.remove();
        });

        // Smooth animation
        socialItem.style.opacity = '0';
        socialItem.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            socialItem.style.transition = 'all 0.3s ease';
            socialItem.style.opacity = '1';
            socialItem.style.transform = 'translateY(0)';
        }, 10);
    });

    // Handle existing remove buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-social') || e.target.closest('.remove-social')) {
            const socialItem = e.target.closest('.social-network-item');
            if (socialItem) {
                socialItem.style.transition = 'all 0.3s ease';
                socialItem.style.opacity = '0';
                socialItem.style.transform = 'translateY(-20px)';
                setTimeout(() => {
                    socialItem.remove();
                }, 300);
            }
        }
    });

    console.log('🌐 Social networks management initialized');
}

// Quest timers
function updateQuestTimers() {
    const now = new Date();

    // Daily timer - reset at midnight UTC
    const tomorrow = new Date(now);
    tomorrow.setUTCDate(now.getUTCDate() + 1);
    tomorrow.setUTCHours(0, 0, 0, 0);
    const dailyMs = tomorrow - now;

    // Weekly timer - reset on Monday UTC
    const nextMonday = new Date(now);
    const daysUntilMonday = (8 - nextMonday.getUTCDay()) % 7 || 7; // 0 for Sunday, 1 for Monday, etc.
    nextMonday.setUTCDate(nextMonday.getUTCDate() + daysUntilMonday);
    nextMonday.setUTCHours(0, 0, 0, 0);
    const weeklyMs = nextMonday - now;

    // Monthly timer - reset on 1st of next month UTC
    const nextMonth = new Date(now);
    nextMonth.setUTCMonth(now.getUTCMonth() + 1, 1);
    nextMonth.setUTCHours(0, 0, 0, 0);
    const monthlyMs = nextMonth - now;

    // Update displays
    updateTimerDisplay('dailyTimer', dailyMs);
    updateTimerDisplay('weeklyTimer', weeklyMs);
    updateTimerDisplay('monthlyTimer', monthlyMs);
}

function updateTimerDisplay(elementId, ms) {
    const element = document.getElementById(elementId);
    if (!element || ms < 0) return; // Don't update if element not found or time is negative

    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    element.textContent = `Обновление через: ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Achievement filter animations
document.addEventListener('DOMContentLoaded', function() {
    const achievementItems = document.querySelectorAll('.achievement-item');
    const filterBtns = document.querySelectorAll('.filter-btn');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            const filterValue = this.dataset.filter;

            achievementItems.forEach((item, index) => {
                const rarity = item.dataset.rarity;
                const shouldShow = filterValue === 'all' || rarity === filterValue;

                if (shouldShow) {
                    item.style.display = '';
                    // Apply animation with a delay based on index for staggered effect
                    item.style.animation = `fadeInUp 0.6s ease ${index * 0.05}s both`;
                } else {
                    item.style.animation = 'fadeOut 0.3s ease both';
                    // Hide element after fade-out animation completes
                    setTimeout(() => {
                        item.style.display = 'none';
                    }, 300);
                }
            });
        });
    });
});


// Enhanced inventory interactions
document.addEventListener('DOMContentLoaded', function() {
    const inventoryItems = document.querySelectorAll('.inventory-item');
    inventoryItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.05)';
            this.style.transition = 'transform 0.3s ease'; // Add transition for smooth effect
        });

        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Currency card animations
    const currencyCards = document.querySelectorAll('.currency-card');
    currencyCards.forEach(card => {
        card.addEventListener('click', function() {
            this.style.animation = 'pulse 0.6s ease';
            setTimeout(() => {
                this.style.animation = '';
            }, 600);
        });
    });
});


// Add CSS animations
const animationStyles = `
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeOut {
    from {
        opacity: 1;
        transform: scale(1);
    }
    to {
        opacity: 0;
        transform: scale(0.8);
    }
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Tooltip styles */
.tooltip {
    position: absolute;
    background: rgba(0,0,0,0.9);
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.875rem;
    pointer-events: none;
    z-index: 10000;
    white-space: nowrap;
    opacity: 0;
    animation: tooltipFadeIn 0.3s forwards;
}

@keyframes tooltipFadeIn {
    to { opacity: 1; }
}

/* Custom cursor styles */
.custom-cursor {
    position: fixed;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background-color: rgba(255, 193, 7, 0.7);
    transform: translate(-50%, -50%);
    pointer-events: none;
    z-index: 9999;
    transition: left 0.05s ease-out, top 0.05s ease-out, transform 0.2s ease-out;
}

.custom-cursor.cursor-hover {
    transform: translate(-50%, -50%) scale(1.3);
    background-color: rgba(255, 193, 7, 0.9);
}

.custom-cursor.clicking {
    transform: translate(-50%, -50%) scale(0.9);
    background-color: rgba(255, 193, 7, 0.5);
}

/* Ripple effect */
.ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.6);
    transform: scale(0);
    animation: ripple 600ms linear;
}

@keyframes ripple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

/* Toast styles */
.toast-container {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 1050;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}

.advanced-toast {
    position: relative;
    padding: 12px 20px;
    margin-bottom: 10px;
    border-radius: 6px;
    color: #fff;
    display: flex;
    align-items: center;
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.3s ease, transform 0.3s ease;
    min-width: 250px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

.advanced-toast.show {
    opacity: 1;
    transform: translateY(0);
}

.advanced-toast.hide {
    opacity: 0;
    transform: translateY(20px);
}

.toast-icon {
    margin-right: 15px;
    font-size: 1.2em;
}

.toast-content {
    flex-grow: 1;
}

.toast-message {
    font-weight: 500;
}

.toast-details {
    font-size: 0.9em;
    opacity: 0.8;
}

.toast-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    height: 3px;
    width: 100%;
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 0 0 6px 6px;
}

.toast-progress-bar {
    height: 100%;
    background-color: rgba(255, 255, 255, 0.7);
    border-radius: 0 0 6px 6px;
}

.toast-close {
    background: none;
    border: none;
    color: inherit;
    font-size: 1.2em;
    cursor: pointer;
    margin-left: 15px;
    opacity: 0.7;
    transition: opacity 0.2s ease;
}

.toast-close:hover {
    opacity: 1;
}

.toast-success { background-color: #28a745; }
.toast-error { background-color: #dc3545; }
.toast-warning { background-color: #ffc107; color: #212529; }
.toast-info { background-color: #17a2b8; }

/* Progress indicator styles */
.global-progress-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10000;
    flex-direction: column;
}

.progress-backdrop {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.8);
}

.progress-content {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    color: #fff;
}

.progress-spinner .spinner-ring {
    display: block;
    width: 50px;
    height: 50px;
    border: 5px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: #ffc107;
    animation: spinner 1s linear infinite;
}

@keyframes spinner {
    to { transform: rotate(360deg); }
}

.progress-bar-container {
    width: 200px;
    height: 10px;
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 5px;
    margin-top: 20px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background-color: #ffc107;
    border-radius: 5px;
    transition: width 0.3s ease-out;
}

.progress-message {
    margin-top: 10px;
    font-size: 1.1em;
}

.progress-percentage {
    font-size: 1.5em;
    font-weight: bold;
    margin-top: 5px;
}

/* Form Step Styles */
.form-step {
    display: none;
    opacity: 0;
    transition: opacity 0.5s ease-in-out;
}

.form-step.active {
    display: block;
    opacity: 1;
}

.step-navigation {
    margin-top: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.step-navigation .btn {
    padding: 10px 20px;
}

.step-navigation .ms-auto {
    margin-left: auto !important;
}

/* Quest Category Styles */
.category-tab {
    cursor: pointer;
    padding: 8px 15px;
    margin-right: 5px;
    border-bottom: 2px solid transparent;
    transition: border-color 0.3s ease;
}

.category-tab.active {
    border-bottom-color: #ffc107;
}

.quest-category {
    margin-top: 20px;
    padding: 15px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}

/* Quest Timers */
.quest-timers-section {
    margin-top: 25px;
    padding: 15px;
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    text-align: center;
}

.quest-timers-section h4 {
    margin-bottom: 10px;
    color: #ffc107;
}

.quest-timers-section p {
    margin: 5px 0;
    font-size: 0.95em;
}
`;

// Inject animations
if (!document.querySelector('#enhanced-animations')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'enhanced-animations';
    styleSheet.textContent = animationStyles;
    document.head.appendChild(styleSheet);
}

// Custom Role Functions
function showEmojiPicker() {
    // Simple emoji picker - you can enhance this with a proper emoji picker library
    const emoji = prompt('Введите эмодзи (например: 👑, ⭐, 🔥):', '👑');
    if (emoji) {
        document.getElementById('customRoleEmoji').value = emoji;
        updateRolePreview();
    }
}

function selectEmoji(emoji) {
    document.getElementById('customRoleEmoji').value = emoji;
    updateRolePreview();
}

function updateRolePreview() {
    const emoji = document.getElementById('customRoleEmoji').value || '🎭';
    const roleName = document.getElementById('customRoleName').value || 'Кастомная роль';
    const color = document.getElementById('customRoleColor').value;
    const useGradient = document.getElementById('useGradient').checked;
    const gradientDirection = document.getElementById('gradientDirection').value;
    const gradientEndColor = document.getElementById('gradientEndColor').value;
    const isAnimated = document.getElementById('gradientAnimated').checked;

    const preview = document.getElementById('rolePreview');
    const roleDisplay = preview.querySelector('.role-display');

    roleDisplay.textContent = `${emoji} ${roleName}`;

    if (useGradient) {
        const gradient = `linear-gradient(${gradientDirection}, ${color}, ${gradientEndColor})`;
        roleDisplay.style.background = gradient;
        roleDisplay.style.backgroundClip = 'text';
        roleDisplay.style.webkitBackgroundClip = 'text';
        roleDisplay.style.webkitTextFillColor = 'transparent';

        if (isAnimated) {
            roleDisplay.style.animation = 'gradientShift 3s ease-in-out infinite';
        } else {
            roleDisplay.style.animation = 'none';
        }
    } else {
        roleDisplay.style.background = 'none';
        roleDisplay.style.backgroundClip = 'unset';
        roleDisplay.style.webkitBackgroundClip = 'unset';
        roleDisplay.style.webkitTextFillColor = 'unset';
        roleDisplay.style.color = color;
        roleDisplay.style.animation = 'none';
    }
}

// Initialize custom role functionality
document.addEventListener('DOMContentLoaded', function() {
    const roleSelect = document.getElementById('roleSelect');
    const customRoleSection = document.getElementById('customRoleSection');
    const useGradient = document.getElementById('useGradient');
    const gradientOptions = document.getElementById('gradientOptions');

    if (roleSelect) {
        roleSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                customRoleSection.style.display = 'block';
            } else {
                customRoleSection.style.display = 'none';
            }
        });
    }

    if (useGradient) {
        useGradient.addEventListener('change', function() {
            if (this.checked) {
                gradientOptions.style.display = 'block';
            } else {
                gradientOptions.style.display = 'none';
            }
        });
    }

    // Initialize color text inputs
    const colorInputs = document.querySelectorAll('input[type="color"]');
    colorInputs.forEach(input => {
        const textInput = input.parentNode.querySelector('.color-text');
        if (textInput) {
            textInput.value = input.value;
            input.addEventListener('input', function() {
                textInput.value = this.value;
                updateRolePreview();
            });
        }
    });

    // Initialize emoji input
    const emojiInput = document.getElementById('customRoleEmoji');
    if (emojiInput) {
        emojiInput.addEventListener('input', updateRolePreview);
    }

    // Initialize role name input
    const roleNameInput = document.getElementById('customRoleName');
    if (roleNameInput) {
        roleNameInput.addEventListener('input', updateRolePreview);
    }

    // Initialize gradient direction
    const gradientDirectionSelect = document.getElementById('gradientDirection');
    if (gradientDirectionSelect) {
        gradientDirectionSelect.addEventListener('change', updateRolePreview);
    }

    // Initialize gradient end color
    const gradientEndColorInput = document.getElementById('gradientEndColor');
    if (gradientEndColorInput) {
        gradientEndColorInput.addEventListener('input', updateRolePreview);
    }

    // Initialize gradient animation
    const gradientAnimatedInput = document.getElementById('gradientAnimated');
    if (gradientAnimatedInput) {
        gradientAnimatedInput.addEventListener('change', updateRolePreview);
    }

    // Initialize form validation and statistics calculation
    initializeFormValidation();
});

// Form validation and statistics calculation
function initializeFormValidation() {
    // Statistics inputs
    const statInputs = document.querySelectorAll('.stat-input');
    const resourceInputs = document.querySelectorAll('.resource-input');
    const economyInputs = document.querySelectorAll('.economy-input');

    // Add event listeners for real-time calculation
    statInputs.forEach(input => {
        input.addEventListener('input', updateCalculatedStats);
    });

    resourceInputs.forEach(input => {
        input.addEventListener('input', updateCalculatedStats);
    });

    economyInputs.forEach(input => {
        input.addEventListener('input', updateCalculatedStats);
    });

    // Form submission validation
    const form = document.getElementById('addPlayerForm');
    if (form) {
        form.addEventListener('submit', validateForm);
    }
}

function updateCalculatedStats() {
    // Get values from form
    const kills = parseInt(document.querySelector('input[name="kills"]').value) || 0;
    const finalKills = parseInt(document.querySelector('input[name="final_kills"]').value) || 0;
    const deaths = parseInt(document.querySelector('input[name="deaths"]').value) || 0;
    const finalDeaths = parseInt(document.querySelector('input[name="final_deaths"]').value) || 0;
    const gamesPlayed = parseInt(document.querySelector('input[name="games_played"]').value) || 0;
    const wins = parseInt(document.querySelector('input[name="wins"]').value) || 0;

    // Calculate K/D ratios
    const kdRatio = deaths > 0 ? (kills / deaths).toFixed(2) : kills > 0 ? '∞' : '0.00';
    const fkdRatio = finalDeaths > 0 ? (finalKills / finalDeaths).toFixed(2) : finalKills > 0 ? '∞' : '0.00';

    // Calculate win rate
    const winRate = gamesPlayed > 0 ? ((wins / gamesPlayed) * 100).toFixed(1) : '0.0';

    // Calculate level (simplified formula)
    const totalXP = kills * 10 + finalKills * 25 + wins * 100;
    const level = Math.floor(totalXP / 1000) + 1;

    // Update display
    const kdElement = document.getElementById('calc-kd');
    const fkdElement = document.getElementById('calc-fkd');
    const winRateElement = document.getElementById('calc-winrate');
    const levelElement = document.getElementById('calc-level');

    if (kdElement) kdElement.textContent = kdRatio;
    if (fkdElement) fkdElement.textContent = fkdRatio;
    if (winRateElement) winRateElement.textContent = winRate + '%';
    if (levelElement) levelElement.textContent = level;
}

function validateForm(event) {
    const form = event.target;
    const nickname = form.querySelector('input[name="nickname"]').value.trim();
    const wins = parseInt(form.querySelector('input[name="wins"]').value) || 0;
    const gamesPlayed = parseInt(form.querySelector('input[name="games_played"]').value) || 0;

    // Basic validation
    if (!nickname) {
        event.preventDefault();
        showValidationError('Никнейм обязателен для заполнения');
        return false;
    }

    if (nickname.length > 16) {
        event.preventDefault();
        showValidationError('Никнейм не может быть длиннее 16 символов');
        return false;
    }

    if (wins > gamesPlayed) {
        event.preventDefault();
        showValidationError('Количество побед не может превышать количество игр');
        return false;
    }

    // Validate custom role if selected
    const roleSelect = form.querySelector('select[name="role"]');
    if (roleSelect && roleSelect.value === 'custom') {
        const customRoleName = form.querySelector('input[name="custom_role"]').value.trim();
        if (!customRoleName) {
            event.preventDefault();
            showValidationError('Введите название кастомной роли');
            return false;
        }
    }

    return true;
}

function showValidationError(message) {
    // Create or update error message
    let errorDiv = document.querySelector('.validation-error');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger validation-error mt-3';
        errorDiv.style.animation = 'fadeInDown 0.5s ease';
        const form = document.getElementById('addPlayerForm');
        form.insertBefore(errorDiv, form.firstChild);
    }

    errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i>${message}`;
    errorDiv.style.display = 'block';

    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);

    // Scroll to error
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
}