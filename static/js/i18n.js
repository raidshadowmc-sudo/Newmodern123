
// Система интернационализации для сайта
class I18n {
    constructor() {
        this.currentLanguage = this.detectLanguage();
        this.translations = {
            'ru': {
                // Navigation
                'leaders': 'Лидеры',
                'statistics': 'Статистика',
                'quests': 'Квесты',
                'achievements': 'Достижения',
                'clans': 'Кланы',
                'tournaments': 'Турниры',
                'shop': 'Магазин',
                'profile': 'Профиль',
                'login': 'Вход',
                'logout': 'Выйти',
                'themes': 'Темы',
                'admin_panel': 'Админ панель',
                'role_management': 'Управление ролями',
                
                // Stats
                'level': 'Уровень',
                'kills': 'Киллы',
                'deaths': 'Смерти',
                'wins': 'Победы',
                'games': 'Игры',
                'kd_ratio': 'K/D',
                'win_rate': '% побед',
                'beds_broken': 'Кровати',
                'final_kills': 'Финальные киллы',
                'coins': 'Койны',
                'reputation': 'Репутация',
                
                // UI
                'search': 'Поиск...',
                'save': 'Сохранить',
                'cancel': 'Отмена',
                'edit': 'Редактировать',
                'delete': 'Удалить',
                'back': 'Назад',
                'next': 'Далее',
                'loading': 'Загрузка...',
                'error': 'Ошибка',
                'success': 'Успешно',
                'actions': 'Действия',
                'view': 'Просмотреть',
                'remove': 'Удалить',
                
                // Profile
                'my_profile': 'Мой профиль',
                'edit_profile': 'Редактировать профиль',
                'social_networks': 'Социальные сети',
                'about_player': 'О игроке',
                'gaming_preferences': 'Игровые предпочтения',
                'personal_info': 'Личная информация',
                
                // Roles
                'create_role': 'Создать роль',
                'role_name': 'Название роли',
                'role_color': 'Цвет роли',
                'role_emoji': 'Эмодзи роли',
                'gradient': 'Градиент',
                'visible': 'Видимая',
                'custom_roles': 'Кастомные роли',
                'assign_role': 'Назначить роль',
                'players_with_role': 'Игроки с ролью',
                'select_player': 'Выберите игрока',
                'select_role': 'Выберите роль',
                
                // Time
                'created_at': 'Регистрация',
                'last_updated': 'Последняя активность',
                'birthday': 'День рождения',
                'created': 'Создано',
                'assigned': 'Назначено'
            },
            'ua': {
                // Navigation
                'leaders': 'Лідери',
                'statistics': 'Статистика',
                'quests': 'Квести',
                'achievements': 'Досягнення',
                'clans': 'Клани',
                'tournaments': 'Турніри',
                'shop': 'Магазин',
                'profile': 'Профіль',
                'login': 'Вхід',
                'logout': 'Вийти',
                'themes': 'Теми',
                'admin_panel': 'Адмін панель',
                'role_management': 'Управління ролями',
                
                // Stats
                'level': 'Рівень',
                'kills': 'Вбивства',
                'deaths': 'Смерті',
                'wins': 'Перемоги',
                'games': 'Ігри',
                'kd_ratio': 'K/D',
                'win_rate': '% перемог',
                'beds_broken': 'Ліжка',
                'final_kills': 'Фінальні вбивства',
                'coins': 'Монети',
                'reputation': 'Репутація',
                
                // UI
                'search': 'Пошук...',
                'save': 'Зберегти',
                'cancel': 'Скасувати',
                'edit': 'Редагувати',
                'delete': 'Видалити',
                'back': 'Назад',
                'next': 'Далі',
                'loading': 'Завантаження...',
                'error': 'Помилка',
                'success': 'Успішно',
                'actions': 'Дії',
                'view': 'Переглянути',
                'remove': 'Видалити',
                
                // Profile
                'my_profile': 'Мій профіль',
                'edit_profile': 'Редагувати профіль',
                'social_networks': 'Соціальні мережі',
                'about_player': 'Про гравця',
                'gaming_preferences': 'Ігрові налаштування',
                'personal_info': 'Особиста інформація',
                
                // Roles
                'create_role': 'Створити роль',
                'role_name': 'Назва ролі',
                'role_color': 'Колір ролі',
                'role_emoji': 'Емодзі ролі',
                'gradient': 'Градієнт',
                'visible': 'Видима',
                'custom_roles': 'Кастомні ролі',
                'assign_role': 'Призначити роль',
                'players_with_role': 'Гравці з роллю',
                'select_player': 'Виберіть гравця',
                'select_role': 'Виберіть роль',
                
                // Time
                'created_at': 'Реєстрація',
                'last_updated': 'Остання активність',
                'birthday': 'День народження',
                'created': 'Створено',
                'assigned': 'Призначено'
            },
            'en': {
                // Navigation
                'leaders': 'Leaders',
                'statistics': 'Statistics',
                'quests': 'Quests',
                'achievements': 'Achievements',
                'clans': 'Clans',
                'tournaments': 'Tournaments',
                'shop': 'Shop',
                'profile': 'Profile',
                'login': 'Login',
                'logout': 'Logout',
                'themes': 'Themes',
                'admin_panel': 'Admin Panel',
                'role_management': 'Role Management',
                
                // Stats
                'level': 'Level',
                'kills': 'Kills',
                'deaths': 'Deaths',
                'wins': 'Wins',
                'games': 'Games',
                'kd_ratio': 'K/D',
                'win_rate': 'Win Rate',
                'beds_broken': 'Beds',
                'final_kills': 'Final Kills',
                'coins': 'Coins',
                'reputation': 'Reputation',
                
                // UI
                'search': 'Search...',
                'save': 'Save',
                'cancel': 'Cancel',
                'edit': 'Edit',
                'delete': 'Delete',
                'back': 'Back',
                'next': 'Next',
                'loading': 'Loading...',
                'error': 'Error',
                'success': 'Success',
                'actions': 'Actions',
                'view': 'View',
                'remove': 'Remove',
                
                // Profile
                'my_profile': 'My Profile',
                'edit_profile': 'Edit Profile',
                'social_networks': 'Social Networks',
                'about_player': 'About Player',
                'gaming_preferences': 'Gaming Preferences',
                'personal_info': 'Personal Info',
                
                // Roles
                'create_role': 'Create Role',
                'role_name': 'Role Name',
                'role_color': 'Role Color',
                'role_emoji': 'Role Emoji',
                'gradient': 'Gradient',
                'visible': 'Visible',
                'custom_roles': 'Custom Roles',
                'assign_role': 'Assign Role',
                'players_with_role': 'Players with Role',
                'select_player': 'Select Player',
                'select_role': 'Select Role',
                
                // Time
                'created_at': 'Registration',
                'last_updated': 'Last Activity',
                'birthday': 'Birthday',
                'created': 'Created',
                'assigned': 'Assigned'
            }
        };
        
        this.init();
    }

    detectLanguage() {
        // Check localStorage first
        const saved = localStorage.getItem('selectedLanguage');
        if (saved && this.translations[saved]) {
            return saved;
        }

        // Auto-detect from browser
        const browserLang = navigator.language.toLowerCase();
        if (browserLang.startsWith('uk') || browserLang.startsWith('ua')) {
            return 'ua';
        } else if (browserLang.startsWith('en')) {
            return 'en';
        } else {
            return 'ru'; // Default
        }
    }

    init() {
        this.createLanguageSwitcher();
        this.applyTranslations();
    }

    createLanguageSwitcher() {
        // Добавляем обработчики событий к кнопкам выбора языка
        const handleLanguageOptionClick = (e) => {
            e.preventDefault();
            const lang = e.target.closest('[data-lang]')?.dataset.lang;
            if (lang) {
                this.changeLanguage(lang);
            }
        };

        // Добавляем обработчики к существующим кнопкам
        document.querySelectorAll('.language-option').forEach(option => {
            option.addEventListener('click', handleLanguageOptionClick);
        });

        // Следим за динамически добавляемыми элементами
        document.addEventListener('click', (e) => {
            if (e.target.closest('.language-option')) {
                handleLanguageOptionClick(e);
            }
        });
    }

    getCurrentLanguageFlag() {
        const flags = { 'ru': '🇷🇺', 'ua': '🇺🇦', 'en': '🇺🇸' };
        return flags[this.currentLanguage] || '🇷🇺';
    }

    changeLanguage(lang) {
        if (!this.translations[lang]) return;

        this.currentLanguage = lang;
        localStorage.setItem('selectedLanguage', lang);
        
        this.applyTranslations();

        // Announce language change to screen readers
        if (window.announceToScreenReader) {
            const langNames = { 'ru': 'русский', 'ua': 'українська', 'en': 'English' };
            window.announceToScreenReader(`Язык изменен на ${langNames[lang]}`);
        }

        // Show notification about language change
        const notification = document.createElement('div');
        notification.className = 'alert alert-success position-fixed';
        notification.style.cssText = `
            top: 100px;
            right: 20px;
            z-index: 9999;
            min-width: 200px;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        const langNames = { 'ru': 'Русский', 'ua': 'Українська', 'en': 'English' };
        notification.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            Язык изменен на ${langNames[lang]}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => notification.style.opacity = '1', 100);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    translate(key, fallback = null) {
        const translation = this.translations[this.currentLanguage]?.[key];
        return translation || fallback || key;
    }

    applyTranslations() {
        // Translate elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.dataset.i18n;
            const translation = this.translate(key);
            
            if (element.tagName === 'INPUT' && (element.type === 'text' || element.type === 'search')) {
                element.placeholder = translation;
            } else if (element.hasAttribute('title')) {
                element.title = translation;
            } else if (element.hasAttribute('aria-label')) {
                element.setAttribute('aria-label', translation);
            } else {
                element.textContent = translation;
            }
        });

        // Update document language
        document.documentElement.lang = this.currentLanguage === 'ua' ? 'uk' : this.currentLanguage;
    }
}

// Initialize i18n when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.bedwarsI18n === 'undefined') {
        window.bedwarsI18n = new I18n();
    }
});

// Export for use in other scripts
window.I18n = I18n;
