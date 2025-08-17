from flask import render_template, request, redirect, url_for, flash, session, jsonify, make_response
from app import app, db
from models import Player, Quest, PlayerQuest, Achievement, PlayerAchievement, CustomTitle, PlayerTitle, GradientTheme, PlayerGradientSetting, SiteTheme, ShopItem, ShopPurchase, Clan, ClanMember, Tournament, TournamentParticipant, PlayerActiveBooster, AdminCustomRole, PlayerAdminRole, Badge, PlayerBadge, ReputationLog, ASCENDData
import os
import csv
import io
from datetime import datetime, date
import json

# Import routes first
import routes
import api_routes

# Admin password
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Decorator to ensure admin access
def admin_required(f):
    """Decorator to check if the current user is an admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin', False):
            flash('Доступ запрещен! Требуется авторизация администратора.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_current_player():
    """Inject current player data into all templates"""
    current_player = None
    player_nickname = session.get('player_nickname')
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()

    # Set default language if not set
    if 'language' not in session:
        session['language'] = 'ru'

    return dict(current_player=current_player, current_language=session.get('language', 'ru'))

@app.route('/')
def index():
    """Display the enhanced leaderboard"""
    sort_by = request.args.get('sort', 'experience')
    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    limit = min(int(request.args.get('limit', 50)), 50)  # Max 50 records
    offset = (page - 1) * limit

    if search:
        players = Player.search_players(search, limit=limit, offset=offset)
    else:
        players = Player.get_leaderboard(sort_by=sort_by, limit=limit, offset=offset)

    is_admin = session.get('is_admin', False)
    stats = Player.get_statistics()

    # Initialize theme in session if not set
    if 'current_theme' not in session:
        player_nickname = session.get('player_nickname')
        if player_nickname:
            player = Player.query.filter_by(nickname=player_nickname).first()
            if player and player.selected_theme:
                theme = player.selected_theme
                session['current_theme'] = {
                    'id': theme.id,
                    'name': theme.name,
                    'display_name': theme.display_name,
                    'primary_color': theme.primary_color,
                    'secondary_color': theme.secondary_color,
                    'background_color': theme.background_color,
                    'card_background': theme.card_background,
                    'text_color': theme.text_color,
                    'accent_color': theme.accent_color
                }

    return render_template('index.html',
                         players=players,
                         current_sort=sort_by,
                         search_query=search,
                         is_admin=is_admin,
                         stats=stats,
                         limit=limit)

@app.route('/player/<int:player_id>')
def player_profile(player_id):
    """Display detailed player profile (admin view)"""
    player = Player.query.get_or_404(player_id)
    is_admin = session.get('is_admin', False)
    current_player = None

    # Check if current user is the player owner
    player_nickname = session.get('player_nickname')
    is_owner = False
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()
        is_owner = current_player and current_player.id == player.id

    # Get player's badges
    player_badges = PlayerBadge.query.filter_by(player_id=player.id, is_visible=True).all()
    badges_data = []
    for pb in player_badges:
        badge = Badge.query.get(pb.badge_id)
        if badge and badge.is_active:
            badges_data.append({
                'badge': badge,
                'display_name': badge.display_name,
                'icon': badge.icon,
                'color': badge.color,
                'background_color': badge.background_color,
                'border_color': badge.border_color,
                'rarity': badge.rarity,
                'has_gradient': badge.has_gradient,
                'gradient_start': badge.gradient_start,
                'gradient_end': badge.gradient_end,
                'is_animated': badge.is_animated
            })

    # Get player skill rating
    skill_rating = None
    try:
        from models import PlayerSkillRating
        skill_rating = PlayerSkillRating.get_or_create_rating(player.id)
    except Exception as e:
        app.logger.error(f"Error getting skill rating: {e}")

    return render_template('player_profile.html',
                         player=player,
                         is_admin=is_admin,
                         is_owner=is_owner,
                         player_badges=badges_data,
                         skill_rating=skill_rating)

@app.route('/public/<int:player_id>')
def public_profile(player_id):
    """Display public player profile (read-only view)"""
    player = Player.query.get_or_404(player_id)
    current_player = None

    # Check if profile is public
    if not player.profile_is_public:
        flash('Профиль игрока скрыт от публичного просмотра', 'warning')
        return redirect(url_for('index'))

    # Check if current user is the player owner
    player_nickname = session.get('player_nickname')
    is_owner = False
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()
        is_owner = current_player and current_player.id == player.id

    # Get player's visible badges
    player_badges = PlayerBadge.query.filter_by(player_id=player.id, is_visible=True).all()
    badges_data = []
    for pb in player_badges:
        badge = Badge.query.get(pb.badge_id)
        if badge and badge.is_active:
            badges_data.append({
                'badge': badge,
                'display_name': badge.display_name,
                'icon': badge.icon,
                'color': badge.color,
                'background_color': badge.background_color,
                'border_color': badge.border_color,
                'rarity': badge.rarity,
                'has_gradient': badge.has_gradient,
                'gradient_start': badge.gradient_start,
                'gradient_end': badge.gradient_end,
                'is_animated': badge.is_animated
            })

    return render_template('public_profile.html',
                         player=player,
                         is_owner=is_owner,
                         player_badges=badges_data)

@app.route('/compare')
def compare_players():
    """Player comparison page"""
    players = Player.query.order_by(Player.experience.desc()).all()
    return render_template('compare.html', players=players)

@app.route('/api/compare/<int:player1_id>/<int:player2_id>')
def api_compare_players(player1_id, player2_id):
    """API endpoint for player comparison"""
    try:
        player1 = Player.query.get_or_404(player1_id)
        player2 = Player.query.get_or_404(player2_id)

        comparison_data = {
            'player1': {
                'id': player1.id,
                'nickname': player1.nickname,
                'level': player1.level,
                'experience': player1.experience,
                'kills': player1.kills,
                'final_kills': player1.final_kills,
                'deaths': player1.deaths,
                'kd_ratio': player1.kd_ratio,
                'fkd_ratio': player1.fkd_ratio,
                'beds_broken': player1.beds_broken,
                'wins': player1.wins,
                'games_played': player1.games_played,
                'win_rate': player1.win_rate,
                'role': player1.display_role,
                'skin_url': player1.minecraft_skin_url,
                'star_rating': player1.star_rating
            },
            'player2': {
                'id': player2.id,
                'nickname': player2.nickname,
                'level': player2.level,
                'experience': player2.experience,
                'kills': player2.kills,
                'final_kills': player2.final_kills,
                'deaths': player2.deaths,
                'kd_ratio': player2.kd_ratio,
                'fkd_ratio': player2.fkd_ratio,
                'beds_broken': player2.beds_broken,
                'wins': player2.wins,
                'games_played': player2.games_played,
                'win_rate': player2.win_rate,
                'role': player2.display_role,
                'skin_url': player2.minecraft_skin_url,
                'star_rating': player2.star_rating
            }
        }

        return jsonify(comparison_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/statistics')
def statistics():
    """Display detailed statistics page"""
    stats = Player.get_statistics()
    top_players = {
        'experience': Player.get_leaderboard('experience', 5),
        'kills': Player.get_leaderboard('kills', 5),
        'final_kills': Player.get_leaderboard('final_kills', 5),
        'beds_broken': Player.get_leaderboard('beds_broken', 5),
        'wins': Player.get_leaderboard('wins', 5)
    }

    is_admin = session.get('is_admin', False)

    return render_template('statistics.html',
                         stats=stats,
                         top_players=top_players,
                         is_admin=is_admin)

@app.route('/admin')
def admin():
    """Admin panel"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен! Требуется авторизация администратора.', 'error')
        return redirect(url_for('login'))

    stats = Player.get_statistics()
    recent_players = Player.query.order_by(Player.created_at.desc()).limit(10).all()

    return render_template('admin.html',
                         stats=stats,
                         recent_players=recent_players)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Добро пожаловать, администратор!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Неверный пароль!', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Admin logout"""
    session.pop('is_admin', None)
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('index'))

@app.route('/themes')
def themes():
    """Theme selection page"""
    try:
        # Initialize default themes if none exist
        try:
            if SiteTheme.query.count() == 0:
                SiteTheme.create_default_themes()
        except Exception as e:
            app.logger.error(f"Error checking/creating themes: {e}")
            # Create minimal default theme
            try:
                db.create_all()
                default_theme = SiteTheme(
                    name='default_dark',
                    display_name='Классическая тёмная',
                    description='Элегантная тёмная тема с золотыми акцентами',
                    primary_color='#ffc107',
                    secondary_color='#6c757d',
                    background_color='#0d1117',
                    card_background='#161b22',
                    text_color='#f0f6fc',
                    accent_color='#28a745',
                    is_default=True
                )
                db.session.add(default_theme)
                db.session.commit()
            except Exception as create_error:
                app.logger.error(f"Failed to create default theme: {create_error}")

        try:
            themes = SiteTheme.query.filter_by(is_active=True).all()
        except Exception as e:
            app.logger.error(f"Error querying themes: {e}")
            themes = []

        current_theme = None

        # Get current player's theme if logged in
        player_nickname = session.get('player_nickname')
        if player_nickname:
            try:
                player = Player.query.filter_by(nickname=player_nickname).first()
                if player and player.selected_theme:
                    current_theme = player.selected_theme
            except Exception as e:
                app.logger.error(f"Error getting player theme: {e}")

        # If no current theme, get default
        if not current_theme:
            try:
                current_theme = SiteTheme.query.filter_by(is_default=True).first()
                if not current_theme and themes:
                    current_theme = themes[0]
            except Exception as e:
                app.logger.error(f"Error getting default theme: {e}")

        return render_template('themes.html',
                             themes=themes,
                             current_theme=current_theme)

    except Exception as e:
        app.logger.error(f"Critical error in themes route: {e}")
        flash('Временная проблема с темами. Попробуйте позже.', 'error')
        return redirect(url_for('index'))

@app.route('/select-theme/<int:theme_id>', methods=['POST'])
def select_theme(theme_id):
    """Select a theme for current player"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему для выбора темы!', 'error')
        return redirect(url_for('player_login'))

    try:
        player = Player.query.filter_by(nickname=player_nickname).first_or_404()
        theme = SiteTheme.query.get_or_404(theme_id)

        player.selected_theme_id = theme_id
        db.session.commit()

        # Store theme in session for immediate application
        session['current_theme'] = {
            'id': theme.id,
            'name': theme.name,
            'display_name': theme.display_name,
            'primary_color': theme.primary_color,
            'secondary_color': theme.secondary_color,
            'background_color': theme.background_color,
            'card_background': theme.card_background,
            'text_color': theme.text_color,
            'accent_color': theme.accent_color
        }

        flash(f'Тема "{theme.display_name}" выбрана!', 'success')

    except Exception as e:
        app.logger.error(f"Error selecting theme: {e}")
        flash('Ошибка при выборе темы!', 'error')

    return redirect(url_for('themes'))

@app.route('/player_login', methods=['GET', 'POST'])
def player_login():
    """Player login page"""
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        password = request.form.get('password', '').strip()

        if nickname:
            player = Player.query.filter_by(nickname=nickname).first()
            if player:
                if player.has_password:
                    # Player has password, check it
                    if password:
                        import hashlib
                        password_hash = hashlib.sha256(password.encode()).hexdigest()
                        if player.password_hash == password_hash:
                            session['player_nickname'] = nickname
                            flash(f'Добро пожаловать, {nickname}!', 'success')
                            return redirect(url_for('quests'))
                        else:
                            flash('Неверный пароль!', 'error')
                    else:
                        flash('Введите пароль!', 'error')
                else:
                    # First time login, set password
                    if password:
                        import hashlib
                        password_hash = hashlib.sha256(password.encode()).hexdigest()
                        player.password_hash = password_hash
                        player.has_password = True
                        db.session.commit()
                        session['player_nickname'] = nickname
                        flash(f'Пароль установлен! Добро пожаловать, {nickname}!', 'success')
                        return redirect(url_for('quests'))
                    else:
                        flash('Введите пароль для первого входа!', 'error')
            else:
                flash('Игрок с таким ником не найден!', 'error')
        else:
            flash('Введите ваш игровой ник!', 'error')

    return render_template('player_login.html')

@app.route('/my_profile')
def my_profile():
    """Current player's profile page"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    # Get player's badges
    player_badges = PlayerBadge.query.filter_by(player_id=player.id, is_visible=True).all()
    badges_data = []
    for pb in player_badges:
        badge = Badge.query.get(pb.badge_id)
        if badge and badge.is_active:
            badges_data.append({
                'badge': badge,
                'display_name': badge.display_name,
                'icon': badge.icon,
                'color': badge.color,
                'background_color': badge.background_color,
                'border_color': badge.border_color,
                'rarity': badge.rarity,
                'has_gradient': badge.has_gradient,
                'gradient_start': badge.gradient_start,
                'gradient_end': badge.gradient_end,
                'is_animated': badge.is_animated
            })

    return render_template('my_profile.html',
                         player=player,
                         is_owner=True,
                         player_badges=badges_data)

@app.route('/player_logout')
def player_logout():
    """Player logout"""
    player_name = session.get('player_nickname', '')
    session.pop('player_nickname', None)
    flash(f'До свидания, {player_name}!', 'success')
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_player():
    """Add a new player to the leaderboard (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен! Только администратор может добавлять игроков.', 'error')
        return redirect(url_for('index'))

    try:
        # Basic fields
        nickname = request.form.get('nickname', '').strip()
        kills = request.form.get('kills', type=int, default=0)
        final_kills = request.form.get('final_kills', type=int, default=0)
        deaths = request.form.get('deaths', type=int, default=0)
        final_deaths = request.form.get('final_deaths', type=int, default=0)
        beds_broken = request.form.get('beds_broken', type=int, default=0)
        games_played = request.form.get('games_played', type=int, default=0)
        wins = request.form.get('wins', type=int, default=0)
        experience = request.form.get('experience', type=int, default=0)
        server_ip = request.form.get('server_ip', '').strip()

        # Enhanced fields
        iron_collected = request.form.get('iron_collected', type=int, default=0)
        gold_collected = request.form.get('gold_collected', type=int, default=0)
        diamond_collected = request.form.get('diamond_collected', type=int, default=0)
        emerald_collected = request.form.get('emerald_collected', type=int, default=0)
        items_purchased = request.form.get('items_purchased', type=int, default=0)

        # Skin fields
        skin_type = request.form.get('skin_type', 'auto')
        is_premium = request.form.get('is_premium') == 'on'

        # Validation
        if not nickname:
            flash('Ник не может быть пустым!', 'error')
            return redirect(url_for('admin'))

        if len(nickname) > 20:
            flash('Ник не может быть длиннее 20 символов!', 'error')
            return redirect(url_for('admin'))

        # Check if player already exists
        existing_player = Player.query.filter_by(nickname=nickname).first()
        if existing_player:
            flash(f'Игрок с ником {nickname} уже существует!', 'error')
            return redirect(url_for('admin'))

        # Validate numeric fields
        numeric_fields = [
            ('киллы', kills), ('финальные киллы', final_kills),
            ('смерти', deaths), ('кровати', beds_broken),
            ('игры', games_played), ('победы', wins), ('опыт', experience),
            ('железо', iron_collected), ('золото', gold_collected),
            ('алмазы', diamond_collected), ('изумруды', emerald_collected),
            ('покупки', items_purchased)
        ]

        for field_name, value in numeric_fields:
            if value is None or value < 0:
                flash(f'{field_name.capitalize()} должны быть неотрицательным числом!', 'error')
                return redirect(url_for('admin'))
            if value > 999999:
                flash(f'{field_name.capitalize()} не могут превышать 999,999!', 'error')
                return redirect(url_for('admin'))

        # Logical validation
        if wins > games_played:
            flash('Количество побед не может превышать количество игр!', 'error')
            return redirect(url_for('admin'))

        # Handle role assignment
        role = request.form.get('role', '').strip() or 'Игрок'
        custom_role = None
        custom_role_color = None
        custom_role_gradient = None
        custom_role_emoji = None
        custom_role_animated = False

        if role == 'custom':
            custom_role = request.form.get('custom_role', '').strip()
            if custom_role:
                role = custom_role
                # Handle custom role styling
                custom_role_color = request.form.get('custom_role_color', '#ffc107')
                custom_role_gradient = request.form.get('custom_role_gradient', '')
                custom_role_emoji = request.form.get('custom_role_emoji', '')
                custom_role_animated = request.form.get('custom_role_animated', 'false') == 'true'
            else:
                role = 'Игрок'

        # Create player using add_player method
        karma = request.form.get('karma', type=int, default=0) # Add karma here
        player = Player.add_player(
            nickname=nickname, kills=kills, final_kills=final_kills,
            deaths=deaths, beds_broken=beds_broken, games_played=games_played,
            wins=wins, experience=experience, role=role, server_ip=server_ip,
            iron_collected=iron_collected, gold_collected=gold_collected,
            diamond_collected=diamond_collected, emerald_collected=emerald_collected,
            items_purchased=items_purchased,
            karma=karma # Add karma here
        )

        # Set skin settings and auto-calculate experience if not set
        if player:
            player.skin_type = skin_type
            player.is_premium = is_premium

            # Set custom role properties if applicable
            if custom_role:
                player.custom_role = custom_role
                player.custom_role_color = custom_role_color
                player.custom_role_gradient = custom_role_gradient
                player.custom_role_emoji = custom_role_emoji
                player.custom_role_animated = custom_role_animated
                player.custom_role_purchased = True

            # Auto-calculate experience if not manually set or if set to 0
            if experience == 0:
                calculated_xp = player.calculate_auto_experience()
                player.experience = calculated_xp

            db.session.commit()

            # Очистка кэша статистики
            Player.clear_statistics_cache()

            flash(f'Игрок {nickname} успешно добавлен!', 'success')

    except Exception as e:
        app.logger.error(f"Error adding player: {e}")
        flash('Произошла ошибка при добавлении игрока!', 'error')

    return redirect(url_for('admin'))

@app.route('/edit/<int:player_id>', methods=['POST'])
def edit_player(player_id):
    """Edit player statistics (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('index'))

    player = Player.query.get_or_404(player_id)

    try:
        # Update fields
        player.kills = request.form.get('kills', type=int, default=player.kills)
        player.final_kills = request.form.get('final_kills', type=int, default=player.final_kills)
        player.deaths = request.form.get('deaths', type=int, default=player.deaths)
        player.final_deaths = request.form.get('final_deaths', type=int, default=player.final_deaths)
        player.beds_broken = request.form.get('beds_broken', type=int, default=player.beds_broken)
        player.games_played = request.form.get('games_played', type=int, default=player.games_played)
        player.wins = request.form.get('wins', type=int, default=player.wins)
        player.experience = request.form.get('experience', type=int, default=player.experience)
        # Handle role assignment
        role = request.form.get('role', '').strip() or 'Игрок'
        if role == 'custom':
            custom_role = request.form.get('custom_role', '').strip()
            if custom_role:
                role = custom_role
                # Handle custom role styling
                custom_role_color = request.form.get('custom_role_color', '#ffc107')
                custom_role_gradient = request.form.get('custom_role_gradient', '')
                custom_role_emoji = request.form.get('custom_role_emoji', '')
                custom_role_animated = request.form.get('custom_role_animated', 'false') == 'true'

                player.custom_role = custom_role
                player.custom_role_color = custom_role_color
                player.custom_role_gradient = custom_role_gradient
                player.custom_role_emoji = custom_role_emoji
                player.custom_role_animated = custom_role_animated
                player.custom_role_purchased = True
            else:
                role = 'Игрок'

        player.role = role
        player.server_ip = request.form.get('server_ip', default=player.server_ip)

        # Enhanced fields
        player.iron_collected = request.form.get('iron_collected', type=int, default=player.iron_collected)
        player.gold_collected = request.form.get('gold_collected', type=int, default=player.gold_collected)
        player.diamond_collected = request.form.get('diamond_collected', type=int, default=player.diamond_collected)
        player.emerald_collected = request.form.get('emerald_collected', type=int, default=player.emerald_collected)
        player.items_purchased = request.form.get('items_purchased', type=int, default=player.items_purchased)

        # Auto-update experience based on new statistics
        calculated_xp = player.calculate_auto_experience()
        if calculated_xp > player.experience:
            player.experience = calculated_xp

        player.last_updated = datetime.utcnow()
        db.session.commit()

        # Очистка кэша статистики
        Player.clear_statistics_cache()

        # Check for new achievements
        new_achievements = Achievement.check_player_achievements(player)

        success_message = f'Статистика игрока {player.nickname} обновлена!'
        if new_achievements:
            achievement_names = [a.title for a in new_achievements]
            success_message += f' Получены достижения: {", ".join(achievement_names)}'

        flash(success_message, 'success')

    except Exception as e:
        app.logger.error(f"Error editing player: {e}")
        flash('Произошла ошибка при редактировании игрока!', 'error')

    return redirect(url_for('player_profile', player_id=player_id))

@app.route('/modify/<int:player_id>', methods=['POST'])
def modify_player_stats(player_id):
    """Modify player statistics by adding/subtracting values (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('index'))

    player = Player.query.get_or_404(player_id)

    try:
        operation = request.form.get('operation', 'add')  # 'add' or 'subtract'
        changes_made = []

        # Define stat fields and their names for logging
        stat_fields = {
            'kills': 'киллы',
            'final_kills': 'финальные киллы',
            'deaths': 'смерти',
            'final_deaths': 'финальные смерти',
            'beds_broken': 'кровати',
            'games_played': 'игры',
            'wins': 'победы',
            'experience': 'опыт',
            'iron_collected': 'железо',
            'gold_collected': 'золото',
            'diamond_collected': 'алмазы',
            'emerald_collected': 'изумруды',
            'items_purchased': 'покупки'
        }

        for field, display_name in stat_fields.items():
            value = request.form.get(field, type=int)
            if value and value != 0:
                current_value = getattr(player, field, 0)

                if operation == 'add':
                    new_value = current_value + value
                    changes_made.append(f"+{value} {display_name}")
                else:  # subtract
                    new_value = max(0, current_value - value)  # Не даем опускаться ниже 0
                    changes_made.append(f"-{value} {display_name}")

                setattr(player, field, new_value)

        if changes_made:
            # Auto-update experience based on new statistics
            calculated_xp = player.calculate_auto_experience()
            if calculated_xp > player.experience:
                player.experience = calculated_xp

            player.last_updated = datetime.utcnow()
            db.session.commit()

            # Очистка кэша статистики
            Player.clear_statistics_cache()

            operation_text = "Добавлено" if operation == 'add' else "Вычтено"
            flash(f'{operation_text} для {player.nickname}: {", ".join(changes_made)}', 'success')
        else:
            flash('Нет изменений для применения!', 'warning')

    except Exception as e:
        app.logger.error(f"Error modifying player stats: {e}")
        flash('Произошла ошибка при изменении статистики!', 'error')

    return redirect(url_for('player_profile', player_id=player_id))

@app.route('/delete/<int:player_id>', methods=['POST'])
def delete_player(player_id):
    """Delete a player (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('index'))

    try:
        player = Player.query.get_or_404(player_id)
        nickname = player.nickname
        db.session.delete(player)
        db.session.commit()

        # Очистка кэша статистики
        Player.clear_statistics_cache()

        flash(f'Игрок {nickname} удален из таблицы лидеров!', 'success')
    except Exception as e:
        app.logger.error(f"Error deleting player: {e}")
        flash('Произошла ошибка при удалении игрока!', 'error')

    return redirect(url_for('admin'))

@app.route('/clear', methods=['POST'])
def clear_leaderboard():
    """Clear all players from the leaderboard (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен! Только администратор может очистить таблицу.', 'error')
        return redirect(url_for('index'))

    try:
        Player.query.delete()
        db.session.commit()

        # Очистка кэша статистики
        Player.clear_statistics_cache()

        flash('Таблица лидеров очищена!', 'success')
    except Exception as e:
        app.logger.error(f"Error clearing leaderboard: {e}")
        flash('Произошла ошибка при очистке таблицы!', 'error')

    return redirect(url_for('admin'))

@app.route('/export')
def export_leaderboard():
    """Export leaderboard data as CSV"""
    try:
        players = Player.query.order_by(Player.experience.desc()).all()

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Ник', 'Уровень', 'Опыт', 'Киллы', 'Финальные киллы', 'Смерти',
            'K/D', 'FK/D', 'Кровати', 'Игры', 'Победы', 'Процент побед',
            'Роль', 'Сервер', 'Железо', 'Золото', 'Алмазы', 'Изумруды',
            'Покупки', 'Дата создания', 'Последнее обновление'
        ])

        # Data
        for player in players:
            writer.writerow([
                player.nickname, player.level, player.experience,
                player.kills, player.final_kills, player.deaths,
                player.kd_ratio, player.fkd_ratio, player.beds_broken,
                player.games_played, player.wins, player.win_rate,
                player.role, player.server_ip, player.iron_collected,
                player.gold_collected, player.diamond_collected,
                player.emerald_collected, player.items_purchased,
                player.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                player.last_updated.strftime('%Y-%m-%d %H:%M:%S')
            ])

        output.seek(0)

        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=bedwars_leaderboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        return response

    except Exception as e:
        app.logger.error(f"Error exporting data: {e}")
        flash('Произошла ошибка при экспорте данных!', 'error')
        return redirect(url_for('index'))

@app.route('/admin/export-db')
def export_database():
    """Export full database as JSON (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        import json

        # Export all data
        data = {
            'players': [],
            'quests': [],
            'achievements': [],
            'custom_titles': [],
            'gradient_themes': [],
            'player_quests': [],
            'player_achievements': [],
            'player_titles': [],
            'player_gradient_settings': [],
            'shop_items': [],
            'shop_purchases': []
        }

        # Export players
        for player in Player.query.all():
            player_data = {
                'nickname': player.nickname,
                'kills': player.kills,
                'final_kills': player.final_kills,
                'deaths': player.deaths,
                'beds_broken': player.beds_broken,
                'games_played': player.games_played,
                'wins': player.wins,
                'experience': player.experience,
                'role': player.role,
                'server_ip': player.server_ip,
                'iron_collected': player.iron_collected,
                'gold_collected': player.gold_collected,
                'diamond_collected': player.diamond_collected,
                'emerald_collected': player.emerald_collected,
                'items_purchased': player.items_purchased,
                'skin_url': player.skin_url,
                'skin_type': player.skin_type,
                'is_premium': player.is_premium,
                'real_name': player.real_name,
                'bio': player.bio,
                'discord_tag': player.discord_tag,
                'youtube_channel': player.youtube_channel,
                'twitch_channel': player.twitch_channel,
                'favorite_server': player.favorite_server,
                'favorite_map': player.favorite_map,
                'preferred_gamemode': player.preferred_gamemode,
                'profile_banner_color': player.profile_banner_color,
                'profile_is_public': player.profile_is_public,
                'custom_status': player.custom_status,
                'location': player.location,
                'birthday': player.birthday.isoformat() if player.birthday else None,
                'custom_avatar_url': player.custom_avatar_url,
                'custom_banner_url': player.custom_banner_url,
                'banner_is_animated': player.banner_is_animated,
                'social_networks': player.social_networks,
                'stats_section_color': player.stats_section_color,
                'info_section_color': player.info_section_color,
                'social_section_color': player.social_section_color,
                'prefs_section_color': player.prefs_section_color,
                'password_hash': player.password_hash,
                'has_password': player.has_password,
                'leaderboard_name_color': player.leaderboard_name_color,
                'leaderboard_stats_color': player.leaderboard_stats_color,
                'leaderboard_use_gradient': player.leaderboard_use_gradient,
                'leaderboard_gradient_start': player.leaderboard_gradient_start,
                'leaderboard_gradient_end': player.leaderboard_gradient_end,
                'leaderboard_gradient_animated': player.leaderboard_gradient_animated,
                'created_at': player.created_at.isoformat(),
                'last_updated': player.last_updated.isoformat(),
                'karma': player.karma # Include karma here
            }
            data['players'].append(player_data)

        # Export other tables (simplified)
        for quest in Quest.query.all():
            data['quests'].append({
                'title': quest.title,
                'description': quest.description,
                'type': quest.type,
                'target_value': quest.target_value,
                'reward_xp': quest.reward_xp,
                'reward_title': quest.reward_title,
                'icon': quest.icon,
                'difficulty': quest.difficulty,
                'is_active': quest.is_active
            })

        for achievement in Achievement.query.all():
            data['achievements'].append({
                'title': achievement.title,
                'description': achievement.description,
                'icon': achievement.icon,
                'rarity': achievement.rarity,
                'unlock_condition': achievement.unlock_condition,
                'reward_xp': achievement.reward_xp,
                'reward_title': achievement.reward_title,
                'is_hidden': achievement.is_hidden
            })

        for shop_item in ShopItem.query.all():
            data['shop_items'].append({
                'name': shop_item.name,
                'display_name': shop_item.display_name,
                'description': shop_item.description,
                'category': shop_item.category,
                'price_coins': shop_item.price_coins,
                'price_reputation': shop_item.price_reputation,
                'unlock_level': shop_item.unlock_level,
                'rarity': shop_item.rarity,
                'icon': shop_item.icon,
                'item_data': shop_item.item_data,
                'is_limited_time': shop_item.is_limited_time,
                'is_active': shop_item.is_active
            })

        # Create JSON file
        json_output = json.dumps(data, ensure_ascii=False, indent=2, default=str)

        response = make_response(json_output)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=bedwars_database_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        return response

    except Exception as e:
        app.logger.error(f"Error exporting database: {e}")
        flash('Произошла ошибка при экспорте базы данных!', 'error')
        return redirect(url_for('admin'))

@app.route('/admin/import-db', methods=['GET', 'POST'])
def import_database():
    """Import database from JSON file (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            import json
            from datetime import datetime, date

            if 'database_file' not in request.files:
                flash('Файл не выбран!', 'error')
                return redirect(url_for('import_database'))

            file = request.files['database_file']
            if file.filename == '':
                flash('Файл не выбран!', 'error')
                return redirect(url_for('import_database'))

            if not file.filename.endswith('.json'):
                flash('Неверный формат файла! Требуется JSON.', 'error')
                return redirect(url_for('import_database'))

            # Read and parse JSON
            content = file.read().decode('utf-8')
            data = json.loads(content)

            # Clear existing data (optional - ask user)
            clear_existing = request.form.get('clear_existing') == 'on'
            if clear_existing:
                # Clear all tables
                ShopPurchase.query.delete()
                ShopItem.query.delete()
                PlayerGradientSetting.query.delete()
                PlayerTitle.query.delete()
                PlayerAchievement.query.delete()
                PlayerQuest.query.delete()
                GradientTheme.query.delete()
                CustomTitle.query.delete()
                Achievement.query.delete()
                Quest.query.delete()
                Player.query.delete()
                db.session.commit()

            # Import players
            for player_data in data.get('players', []):
                existing = Player.query.filter_by(nickname=player_data['nickname']).first()
                if not existing:
                    player = Player(
                        nickname=player_data['nickname'],
                        kills=player_data.get('kills', 0),
                        final_kills=player_data.get('final_kills', 0),
                        deaths=player_data.get('deaths', 0),
                        beds_broken=player_data.get('beds_broken', 0),
                        games_played=player_data.get('games_played', 0),
                        wins=player_data.get('wins', 0),
                        experience=player_data.get('experience', 0),
                        role=player_data.get('role', 'Игрок'),
                        server_ip=player_data.get('server_ip', ''),
                        iron_collected=player_data.get('iron_collected', 0),
                        gold_collected=player_data.get('gold_collected', 0),
                        diamond_collected=player_data.get('diamond_collected', 0),
                        emerald_collected=player_data.get('emerald_collected', 0),
                        items_purchased=player_data.get('items_purchased', 0),
                        skin_url=player_data.get('skin_url'),
                        skin_type=player_data.get('skin_type', 'auto'),
                        is_premium=player_data.get('is_premium', False),
                        real_name=player_data.get('real_name'),
                        bio=player_data.get('bio'),
                        discord_tag=player_data.get('discord_tag'),
                        youtube_channel=player_data.get('youtube_channel'),
                        twitch_channel=player_data.get('twitch_channel'),
                        favorite_server=player_data.get('favorite_server'),
                        favorite_map=player_data.get('favorite_map'),
                        preferred_gamemode=player_data.get('preferred_gamemode'),
                        profile_banner_color=player_data.get('profile_banner_color', '#3498db'),
                        profile_is_public=player_data.get('profile_is_public', True),
                        custom_status=player_data.get('custom_status'),
                        location=player_data.get('location'),
                        custom_avatar_url=player_data.get('custom_avatar_url'),
                        custom_banner_url=player_data.get('custom_banner_url'),
                        banner_is_animated=player_data.get('banner_is_animated', False),
                        social_networks=player_data.get('social_networks'),
                        stats_section_color=player_data.get('stats_section_color', '#343a40'),
                        info_section_color=player_data.get('info_section_color', '#343a40'),
                        social_section_color=player_data.get('social_section_color', '#343a40'),
                        prefs_section_color=player_data.get('prefs_section_color', '#343a40'),
                        password_hash=player_data.get('password_hash'),
                        has_password=player_data.get('has_password', False),
                        leaderboard_name_color=player_data.get('leaderboard_name_color', '#ffffff'),
                        leaderboard_stats_color=player_data.get('leaderboard_stats_color', '#ffffff'),
                        leaderboard_use_gradient=player_data.get('leaderboard_use_gradient', False),
                        leaderboard_gradient_start=player_data.get('leaderboard_gradient_start', '#ff6b35'),
                        leaderboard_gradient_end=player_data.get('leaderboard_gradient_end', '#f7931e'),
                        leaderboard_gradient_animated=player_data.get('leaderboard_gradient_animated', False),
                        karma=player_data.get('karma', 0) # Add karma here
                    )

                    # Handle birthday
                    if player_data.get('birthday'):
                        try:
                            player.birthday = datetime.fromisoformat(player_data['birthday']).date()
                        except:
                            pass

                    # Handle timestamps
                    if player_data.get('created_at'):
                        try:
                            player.created_at = datetime.fromisoformat(player_data['created_at'])
                        except:
                            pass

                    if player_data.get('last_updated'):
                        try:
                            player.last_updated = datetime.fromisoformat(player_data['last_updated'])
                        except:
                            pass

                    db.session.add(player)

            # Import quests
            for quest_data in data.get('quests', []):
                existing = Quest.query.filter_by(title=quest_data['title']).first()
                if not existing:
                    quest = Quest(**quest_data)
                    db.session.add(quest)

            # Import achievements
            for achievement_data in data.get('achievements', []):
                existing = Achievement.query.filter_by(title=achievement_data['title']).first()
                if not existing:
                    achievement = Achievement(**achievement_data)
                    db.session.add(achievement)

            # Import shop items
            for item_data in data.get('shop_items', []):
                existing = ShopItem.query.filter_by(name=item_data['name']).first()
                if not existing:
                    shop_item = ShopItem(**item_data)
                    db.session.add(shop_item)


            db.session.commit()
            # Очистка кэша статистики
            Player.clear_statistics_cache()
            flash('База данных успешно импортирована!', 'success')

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error importing database: {e}")
            flash(f'Ошибка при импорте базы данных: {e}', 'error')

        return redirect(url_for('admin'))

    return render_template('admin_import_db.html')

# Helper function to get current player, used in some routes
def get_current_player():
    """Helper function to get the current logged-in player"""
    player_nickname = session.get('player_nickname')
    if player_nickname:
        return Player.query.filter_by(nickname=player_nickname).first()
    return None

@app.route('/admin/modify-stats', methods=['POST'])
def admin_modify_stats():
    """Modify player statistics (admin only)"""
    if not get_current_player() and not session.get('is_admin', False): # Check for player login or admin status
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('index'))

    try:
        player_nickname = request.form.get('player_nickname')
        stat_type = request.form.get('stat_type')
        operation = request.form.get('operation')
        value = int(request.form.get('value', 0))

        if not all([player_nickname, stat_type, operation]): # Value can be 0, so don't check it directly here
            flash('Все поля должны быть заполнены!', 'error')
            return redirect(url_for('admin'))

        player = Player.query.filter_by(nickname=player_nickname).first()
        if not player:
            flash(f'Игрок {player_nickname} не найден!', 'error')
            return redirect(url_for('admin'))

        # Get current value
        current_value = getattr(player, stat_type, 0)

        # Calculate new value
        if operation == 'add':
            new_value = current_value + value
        elif operation == 'subtract':
            new_value = max(0, current_value - value)  # Don't go below 0
        elif operation == 'set':
            new_value = value
        else:
            flash('Неизвестная операция!', 'error')
            return redirect(url_for('admin'))

        # Ensure value stays within reasonable bounds if needed (optional)
        # Example: max_value = 1000000
        # if new_value > max_value:
        #     new_value = max_value
        # if new_value < 0: # Already handled by max(0, ...) for subtract
        #     new_value = 0

        # Update the value
        setattr(player, stat_type, new_value)

        # Recalculate level if experience was modified
        if stat_type == 'experience':
            player.level = player.calculate_level() # Assuming calculate_level is a method in Player model

        db.session.commit()

        # Log the change
        app.logger.info(f"Admin modified {player_nickname} {stat_type}: {current_value} -> {new_value} (operation: {operation}, value: {value})")

        flash(f'Статистика игрока {player_nickname} обновлена! {stat_type}: {current_value} -> {new_value}', 'success')

    except ValueError:
        flash('Некорректное значение!', 'error')
    except AttributeError:
        flash('Недопустимый тип статистики!', 'error')
    except Exception as e:
        app.logger.error(f"Error modifying player stats: {e}")
        flash('Ошибка при изменении статистики!', 'error')
        db.session.rollback()

    return redirect(url_for('admin'))

# Quest system routes
@app.route('/quests')
def quests():
    """Display quest system with categories"""
    player_nickname = session.get('player_nickname')
    current_player = None
    player_progress = {}

    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()
        if current_player:
            # Get player quest progress
            player_quests = PlayerQuest.query.filter_by(player_id=current_player.id).all()
            for pq in player_quests:
                player_progress[pq.quest_id] = pq

    # Refresh timed quests
    Quest.refresh_timed_quests()

    all_quests = Quest.get_active_quests()

    # Categorize quests
    daily_quests = [q for q in all_quests if q.quest_category == 'daily']
    weekly_quests = [q for q in all_quests if q.quest_category == 'weekly']
    monthly_quests = [q for q in all_quests if q.quest_category == 'monthly']
    permanent_quests = [q for q in all_quests if q.quest_category == 'permanent']
    seasonal_quests = [q for q in all_quests if q.quest_category in ['thematic', 'seasonal']]

    is_admin = session.get('is_admin', False)

    return render_template('quests.html',
                         quests=all_quests,
                         daily_quests=daily_quests,
                         weekly_quests=weekly_quests,
                         monthly_quests=monthly_quests,
                         permanent_quests=permanent_quests,
                         seasonal_quests=seasonal_quests,
                         player_progress=player_progress,
                         current_player=current_player,
                         is_admin=is_admin)

@app.route('/achievements')
def achievements():
    """Display achievements page"""
    is_admin = session.get('is_admin', False)
    current_player = None

    # Check if player is logged in
    player_nickname = session.get('player_nickname')
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()

    # Initialize default achievements if none exist
    if Achievement.query.count() == 0:
        Achievement.create_default_achievements()

    all_achievements = Achievement.query.all()

    # Get player achievements if logged in
    player_achievements = []

    if current_player:
        player_achievements = PlayerAchievement.query.filter_by(
            player_id=current_player.id
        ).all()

    # Add earned count for display
    for achievement in all_achievements:
        achievement.earned_count = PlayerAchievement.query.filter_by(achievement_id=achievement.id).count()

    return render_template('achievements.html',
                         achievements=all_achievements,
                         player_achievements=player_achievements,
                         current_player=current_player,
                         is_admin=is_admin)

@app.route('/quest/<int:quest_id>/accept', methods=['POST'])
def accept_quest(quest_id):
    """Accept a quest (player must be logged in)"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему для принятия квестов!', 'error')
        return redirect(url_for('player_login'))

    try:
        player = Player.query.filter_by(nickname=player_nickname).first_or_404()
        quest = Quest.query.get_or_404(quest_id)

        # Check if quest already accepted
        existing_quest = PlayerQuest.query.filter_by(
            player_id=player.id,
            quest_id=quest_id
        ).first()

        if existing_quest and existing_quest.is_accepted:
            flash('Квест уже принят!', 'warning')
            return redirect(url_for('quests'))

        if not existing_quest:
            existing_quest = PlayerQuest()
            existing_quest.player_id = player.id
            existing_quest.quest_id = quest_id
            db.session.add(existing_quest)

        # Accept the quest and set baseline
        existing_quest.is_accepted = True
        existing_quest.accepted_at = datetime.utcnow()
        existing_quest.started_at = datetime.utcnow()

        # Set baseline value for quest tracking
        quest = Quest.query.get_or_404(quest_id)
        existing_quest.baseline_value = getattr(player, quest.type, 0)

        db.session.commit()
        flash(f'Квест "{quest.title}" принят!', 'success')

    except Exception as e:
        app.logger.error(f"Error accepting quest: {e}")
        flash('Ошибка при принятии квеста!', 'error')

    return redirect(url_for('quests'))

@app.route('/quest/<int:quest_id>/complete', methods=['POST'])
def complete_quest(quest_id):
    """Mark a quest as completed (admin only for demo)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('quests'))

    try:
        quest = Quest.query.get_or_404(quest_id)
        sample_player = Player.query.first()

        if not sample_player:
            flash('Нет игроков для демонстрации!', 'error')
            return redirect(url_for('quests'))

        # Get or create player quest
        player_quest = PlayerQuest.query.filter_by(
            player_id=sample_player.id,
            quest_id=quest_id
        ).first()

        if not player_quest:
            player_quest = PlayerQuest()
            player_quest.player_id = sample_player.id
            player_quest.quest_id = quest_id
            player_quest.is_accepted = True
            player_quest.accepted_at = datetime.utcnow()
            player_quest.baseline_value = getattr(sample_player, quest.type, 0)
            db.session.add(player_quest)

        # Complete the quest only if not already completed
        if not player_quest.is_completed:
            player_quest.is_completed = True
            player_quest.completed_at = datetime.utcnow()
            player_quest.current_progress = quest.target_value

            # Award all rewards
            sample_player.experience += quest.reward_xp
            sample_player.coins += quest.reward_coins
            sample_player.reputation += quest.reward_reputation

            db.session.commit()

            # Очистка кэша статистики
            Player.clear_statistics_cache()

            rewards = []
            if quest.reward_xp > 0:
                rewards.append(f"{quest.reward_xp} XP")
            if quest.reward_coins > 0:
                rewards.append(f"{quest.reward_coins} койнов")
            if quest.reward_reputation > 0:
                rewards.append(f"{quest.reward_reputation} репутации")

            reward_text = ", ".join(rewards) if rewards else "награды"
            flash(f'Квест "{quest.title}" выполнен! Получено: {reward_text}!', 'success')
        else:
            flash('Квест уже выполнен! Награда не начислена повторно.', 'warning')

    except Exception as e:
        app.logger.error(f"Error completing quest: {e}")
        flash('Ошибка при выполнении квеста!', 'error')

    return redirect(url_for('quests'))

@app.route('/admin/quests')
def admin_quests():
    """Admin quest management"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    quests = Quest.query.all()
    quest_stats = []

    for quest in quests:
        total_attempts = PlayerQuest.query.filter_by(quest_id=quest.id).count()
        completed = PlayerQuest.query.filter_by(quest_id=quest.id, is_completed=True).count()
        completion_rate = (completed / total_attempts * 100) if total_attempts > 0 else 0

        quest_stats.append({
            'quest': quest,
            'total_attempts': total_attempts,
            'completed': completed,
            'completion_rate': completion_rate
        })

    return render_template('admin_quests.html', quest_stats=quest_stats)

@app.route('/init_demo', methods=['POST'])
def init_demo():
    """Initialize demo data (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        # Force recreate achievements to ensure mythic ones exist
        Achievement.create_default_achievements()

        # Create demo players if they don't exist
        demo_players = [
            {
                'nickname': 'ProGamer2024',
                'kills': 150,
                'final_kills': 45,
                'deaths': 75,
                'beds_broken': 28,
                'games_played': 85,
                'wins': 52,
                'experience': 8500,
                'role': 'Опытный игрок',
                'iron_collected': 5000,
                'gold_collected': 2500,
                'diamond_collected': 800,
                'emerald_collected': 150,
                'items_purchased': 500
            },
            {
                'nickname': 'BedDestroyer',
                'kills': 89,
                'final_kills': 22,
                'deaths': 45,
                'beds_broken': 65,
                'games_played': 72,
                'wins': 38,
                'experience': 5200,
                'role': 'Разрушитель',
                'iron_collected': 3200,
                'gold_collected': 1800,
                'diamond_collected': 450,
                'emerald_collected': 85,
                'items_purchased': 320
            },
            {
                'nickname': 'NewbieFighter',
                'kills': 25,
                'final_kills': 8,
                'deaths': 32,
                'beds_broken': 12,
                'games_played': 35,
                'wins': 15,
                'experience': 1800,
                'role': 'Новичок',
                'iron_collected': 1200,
                'gold_collected': 600,
                'diamond_collected': 120,
                'emerald_collected': 25,
                'items_purchased': 150
            }
        ]

        for player_data in demo_players:
            existing = Player.query.filter_by(nickname=player_data['nickname']).first()
            if not existing:
                Player.add_player(**player_data)

        # Initialize quests and achievements
        Quest.create_default_quests()
        Achievement.create_default_achievements()
        CustomTitle.create_default_titles()
        GradientTheme.create_default_themes()
        ShopItem.create_default_items() # Initialize default shop items

        # Initialize achievement tracking for existing players
        players = Player.query.all()
        for player in players:
            Achievement.initialize_player_achievement_tracking(player)

        # Initialize game modes for ASCEND system
        from models import GameMode
        if GameMode.query.count() == 0:
            GameMode.create_default_modes()

        # Update quest progress for all players
        for player in players:
            PlayerQuest.update_player_quest_progress(player)

        # Очистка кэша статистики
        Player.clear_statistics_cache()

        flash('Демо-данные успешно инициализированы!', 'success')

    except Exception as e:
        app.logger.error(f"Error initializing demo data: {e}")
        flash('Ошибка при инициализации демо-данных!', 'error')

    return redirect(url_for('admin'))

@app.route('/admin/update_skin/<int:player_id>', methods=['POST'])
def update_player_skin(player_id):
    """Update player skin settings (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    player = Player.query.get_or_404(player_id)

    try:
        skin_type = request.form.get('skin_type', 'auto')
        namemc_url = request.form.get('namemc_url', '').strip()
        is_premium = request.form.get('is_premium') == 'on'

        player.is_premium = is_premium

        if skin_type == 'custom' and namemc_url:
            if player.set_custom_skin(namemc_url):
                flash(f'Кастомный скин установлен для {player.nickname}!', 'success')
            else:
                flash('Ошибка при установке кастомного скина!', 'error')
        else:
            player.skin_type = skin_type
            player.skin_url = None
            flash(f'Тип скина изменен на {skin_type} для {player.nickname}!', 'success')

        db.session.commit()

    except Exception as e:
        app.logger.error(f"Error updating player skin: {e}")
        flash('Ошибка при обновлении скина!', 'error')

    return redirect(url_for('player_profile', player_id=player_id))

@app.route('/admin/create_quest', methods=['POST'])
def create_quest():
    """Create custom quest (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        target_value = request.form.get('target_value', '0')
        reward_experience = request.form.get('reward_experience', '0')

        quest_data = {
            'title': title,
            'description': description,
            'type': request.form.get('quest_type'),
            'difficulty': request.form.get('difficulty'),
            'target_value': int(target_value) if target_value.isdigit() else 0,
            'reward_xp': int(reward_experience) if reward_experience.isdigit() else 0,
            'reward_title': request.form.get('reward_title', '').strip() or None
        }

        quest = Quest(**quest_data)
        db.session.add(quest)
        db.session.commit()

        flash(f'Квест "{quest_data["title"]}" успешно создан!', 'success')

    except Exception as e:
        app.logger.error(f"Error creating quest: {e}")
        flash('Ошибка при создании квеста!', 'error')

    return redirect(url_for('admin_quests'))

@app.route('/admin/delete_quest/<int:quest_id>', methods=['DELETE'])
def delete_quest(quest_id):
    """Delete quest (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        quest = Quest.query.get_or_404(quest_id)
        # Delete related player quests first
        PlayerQuest.query.filter_by(quest_id=quest_id).delete()
        db.session.delete(quest)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error deleting quest: {e}")
        return jsonify({'error': 'Failed to delete quest'}), 500

@app.route('/admin/reset_quest/<int:quest_id>', methods=['POST'])
def reset_quest_progress(quest_id):
    """Reset quest progress for all players (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        PlayerQuest.query.filter_by(quest_id=quest_id).delete()
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error resetting quest progress: {e}")
        return jsonify({'error': 'Failed to reset quest progress'}), 500

@app.route('/admin/titles')
def admin_titles():
    """Admin titles management"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    titles = CustomTitle.query.all()
    players = Player.query.all()

    return render_template('admin_titles.html', titles=titles, players=players)

@app.route('/admin/create_title', methods=['POST'])
def create_title():
    """Create custom title (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        name = request.form.get('name', '').strip().lower()
        display_name = request.form.get('display_name', '').strip()
        color = request.form.get('color', '#ffd700')
        glow_color = request.form.get('glow_color', color)

        if not name or not display_name:
            flash('Название и отображаемое имя обязательны!', 'error')
            return redirect(url_for('admin_titles'))

        # Check if title already exists
        existing = CustomTitle.query.filter_by(name=name).first()
        if existing:
            flash('Титул с таким названием уже существует!', 'error')
            return redirect(url_for('admin_titles'))

        title = CustomTitle(
            name=name,
            display_name=display_name,
            color=color,
            glow_color=glow_color
        )

        db.session.add(title)
        db.session.commit()

        flash(f'Титул "{display_name}" успешно создан!', 'success')

    except Exception as e:
        app.logger.error(f"Error creating title: {e}")
        flash('Ошибка при создании титула!', 'error')

    return redirect(url_for('admin_titles'))

@app.route('/admin/assign_title', methods=['POST'])
def assign_title():
    """Assign title to player (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        player_id = request.form.get('player_id', type=int)
        title_id = request.form.get('title_id', type=int)

        if not player_id or not title_id:
            flash('Выберите игрока и титул!', 'error')
            return redirect(url_for('admin_titles'))

        player = Player.query.get_or_404(player_id)
        title = CustomTitle.query.get_or_404(title_id)

        # Remove any existing active title
        PlayerTitle.query.filter_by(player_id=player_id, is_active=True).update({'is_active': False})

        # Add new title
        player_title = PlayerTitle(
            player_id=player_id,
            title_id=title_id,
            is_active=True
        )

        db.session.add(player_title)
        db.session.commit()

        flash(f'Титул "{title.display_name}" присвоен игроку {player.nickname}!', 'success')

    except Exception as e:
        app.logger.error(f"Error assigning title: {e}")
        flash('Ошибка при присвоении титула!', 'error')

    return redirect(url_for('admin_titles'))

@app.route('/admin/remove_title/<int:player_id>', methods=['POST'])
def remove_title(player_id):
    """Remove title from player (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        PlayerTitle.query.filter_by(player_id=player_id, is_active=True).update({'is_active': False})
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error removing title: {e}")
        return jsonify({'error': 'Failed to remove title'}), 500

@app.route('/admin/remove_all_titles', methods=['POST'])
def remove_all_titles():
    """Remove all custom titles from all players (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        PlayerTitle.query.update({'is_active': False})
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error removing all titles: {e}")
        return jsonify({'error': 'Failed to remove all titles'}), 500


@app.route('/shop')
def shop():
    """Shop page for purchasing items"""
    is_admin = session.get('is_admin', False)
    current_player = None

    # Check if player is logged in
    player_nickname = session.get('player_nickname')
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()

    # Initialize default shop items if none exist
    if ShopItem.query.count() == 0:
        ShopItem.create_default_items()

    # Get all active shop items grouped by category
    categories = {
        'title': ShopItem.query.filter_by(category='title', is_active=True).all(),
        'booster': ShopItem.query.filter_by(category='booster', is_active=True).all(),
        'custom_role': ShopItem.query.filter_by(category='custom_role', is_active=True).all(),
        'emoji_slot': ShopItem.query.filter_by(category='emoji_slot', is_active=True).all(),
        'theme': ShopItem.query.filter_by(category='theme', is_active=True).all(),
        'gradient': ShopItem.query.filter_by(category='gradient', is_active=True).all()
    }

    # Check purchase status and availability for each item
    shop_data = {}
    for category, items in categories.items():
        shop_data[category] = []
        for item in items:
            item_data = {
                'item': item,
                'can_purchase': True,
                'purchase_error': None,
                'already_purchased': False
            }

            if current_player:
                can_purchase, error_msg = item.can_purchase(current_player)
                item_data['can_purchase'] = can_purchase
                item_data['purchase_error'] = error_msg

                # Check if already purchased
                existing_purchase = ShopPurchase.query.filter_by(
                    player_id=current_player.id,
                    item_id=item.id
                ).first()
                item_data['already_purchased'] = bool(existing_purchase)
            else:
                item_data['can_purchase'] = False
                item_data['purchase_error'] = "Требуется авторизация"

            shop_data[category].append(item_data)

    return render_template('shop.html',
                         shop_data=shop_data,
                         current_player=current_player,
                         is_admin=is_admin)

@app.route('/shop/purchase', methods=['POST'])
def purchase_item():
    """Purchase an item from the shop"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        return jsonify({'success': False, 'error': 'Необходимо войти в систему'}), 401

    try:
        data = request.get_json()
        item_id = data.get('item_id')

        if not item_id:
            return jsonify({'success': False, 'error': 'Не указан ID товара'}), 400

        player = Player.query.filter_by(nickname=player_nickname).first()
        if not player:
            return jsonify({'success': False, 'error': 'Игрок не найден'}), 404

        item = ShopItem.query.get(item_id)
        if not item or not item.is_active:
            return jsonify({'success': False, 'error': 'Товар не найден или недоступен'}), 404

        # Check if can purchase
        can_purchase, error_msg = item.can_purchase(player)
        if not can_purchase:
            return jsonify({'success': False, 'error': error_msg}), 400

        # Deduct currency
        player.coins -= item.price_coins
        player.reputation -= item.price_reputation

        # Create purchase record
        purchase = ShopPurchase(
            player_id=player.id,
            item_id=item.id,
            price_paid_coins=item.price_coins,
            price_paid_reputation=item.price_reputation
        )
        db.session.add(purchase)

        # Apply item effect
        item.apply_item_effect(player)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Успешно куплено: {item.display_name}',
            'new_coins': player.coins,
            'new_reputation': player.reputation
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Purchase error: {e}")
        return jsonify({'success': False, 'error': 'Произошла ошибка при покупке'}), 500

@app.route('/admin/shop')
def admin_shop():
    """Shop management page for admins"""
    if not session.get('is_admin'):
        flash('У вас нет доступа к этой функции!', 'error')
        return redirect(url_for('index'))

    shop_items = ShopItem.query.order_by(ShopItem.category, ShopItem.name).all()

    # Преобразуем объекты в словари для JSON сериализации
    shop_items_data = []
    for item in shop_items:
        shop_items_data.append({
            'id': item.id,
            'name': item.name,
            'display_name': item.display_name,
            'description': item.description,
            'category': item.category,
            'price_coins': item.price_coins,
            'price_reputation': item.price_reputation,
            'unlock_level': item.unlock_level,
            'rarity': item.rarity,
            'icon': item.icon,
            'image_url': item.image_url,
            'item_data': item.item_data,
            'is_limited_time': item.is_limited_time,
            'is_active': item.is_active
        })

    return render_template('admin_shop.html', shop_items=shop_items, shop_items_data=shop_items_data)

@app.route('/admin/add_shop_item', methods=['POST'])
def admin_add_shop_item():
    """Add new shop item (admin only)"""
    if not session.get('is_admin', False):
        flash('У вас нет доступа к этой функции!', 'error')
        return redirect(url_for('index'))

    try:
        name = request.form.get('name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        price_coins = int(request.form.get('price_coins', 0))
        price_reputation = int(request.form.get('price_reputation', 0))
        unlock_level = int(request.form.get('unlock_level', 1))
        rarity = request.form.get('rarity', 'common')
        icon = request.form.get('icon', 'fas fa-star')
        item_data = request.form.get('item_data', '').strip()
        is_limited_time = request.form.get('is_limited_time') == 'on'
        duration = int(request.form.get('duration', 0)) # Duration for boosters

        if not name or not display_name or not description or not category:
            flash('Все обязательные поля должны быть заполнены!', 'error')
            return redirect(url_for('admin_shop'))

        # Check if item already exists
        existing = ShopItem.query.filter_by(name=name).first()
        if existing:
            flash('Товар с таким названием уже существует!', 'error')
            return redirect(url_for('admin_shop'))

        # Validate JSON data
        if item_data:
            try:
                import json
                json.loads(item_data)
            except json.JSONDecodeError:
                flash('Некорректный JSON в данных товара!', 'error')
                return redirect(url_for('admin_shop'))

        shop_item = ShopItem(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            price_coins=price_coins,
            price_reputation=price_reputation,
            unlock_level=unlock_level,
            rarity=rarity,
            icon=icon,
            image_url=request.form.get('image_url', '').strip() or None,
            item_data=item_data or None,
            is_limited_time=is_limited_time,
            duration=duration if duration > 0 else None # Store duration only if valid
        )

        db.session.add(shop_item)
        db.session.commit()

        flash(f'Товар "{display_name}" успешно добавлен!', 'success')

    except Exception as e:
        app.logger.error(f"Error adding shop item: {e}")
        flash('Ошибка при добавлении товара!', 'error')

    return redirect(url_for('admin_shop'))

@app.route('/admin/toggle_shop_item/<int:item_id>', methods=['POST'])
def admin_toggle_shop_item(item_id):
    """Toggle shop item active status (admin only)"""
    if not session.get('is_admin', False):
        flash('У вас нет доступа к этой функции!', 'error')
        return redirect(url_for('index'))

    try:
        item = ShopItem.query.get_or_404(item_id)
        item.is_active = not item.is_active
        db.session.commit()

        status = "активирован" if item.is_active else "деактивирован"
        flash(f'Товар "{item.display_name}" {status}!', 'success')

    except Exception as e:
        app.logger.error(f"Error toggling shop item: {e}")
        flash('Ошибка при изменении статуса товара!', 'error')

    return redirect(url_for('admin_shop'))

@app.route('/admin/edit_shop_item/<int:item_id>', methods=['POST'])
def admin_edit_shop_item(item_id):
    """Edit shop item (admin only)"""
    if not session.get('is_admin', False):
        flash('У вас нет доступа к этой функции!', 'error')
        return redirect(url_for('index'))

    try:
        item = ShopItem.query.get_or_404(item_id)

        # Validate required fields
        name = request.form.get('name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()

        if not name or not display_name or not description or not category:
            flash('Все обязательные поля должны быть заполнены!', 'error')
            return redirect(url_for('admin_shop'))

        # Check if name is unique (excluding current item)
        existing = ShopItem.query.filter(ShopItem.name == name, ShopItem.id != item_id).first()
        if existing:
            flash('Товар с таким системным названием уже существует!', 'error')
            return redirect(url_for('admin_shop'))

        # Update item fields
        item.name = name
        item.display_name = display_name
        item.description = description
        item.category = category
        item.price_coins = int(request.form.get('price_coins', 0))
        item.price_reputation = int(request.form.get('price_reputation', 0))
        item.unlock_level = int(request.form.get('unlock_level', 1))
        item.rarity = request.form.get('rarity', 'common')
        item.icon = request.form.get('icon', 'fas fa-star')
        item.image_url = request.form.get('image_url', '').strip() or None
        item.item_data = request.form.get('item_data', '').strip() or None
        item.is_limited_time = request.form.get('is_limited_time') == 'on'
        item.duration = int(request.form.get('duration', 0)) or None # Duration for boosters

        # Validate JSON data if provided
        if item.item_data:
            try:
                import json
                json.loads(item.item_data)
            except json.JSONDecodeError:
                flash('Некорректный JSON в данных товара!', 'error')
                return redirect(url_for('admin_shop'))

        db.session.commit()
        flash(f'Товар "{display_name}" успешно обновлен!', 'success')

    except Exception as e:
        app.logger.error(f"Error editing shop item: {e}")
        flash('Ошибка при редактировании товара!', 'error')

    return redirect(url_for('admin_shop'))

@app.route('/admin/delete_shop_item/<int:item_id>', methods=['POST'])
def admin_delete_shop_item(item_id):
    """Delete shop item (admin only)"""
    if not session.get('is_admin', False):
        flash('У вас нет доступа к этой функции!', 'error')
        return redirect(url_for('index'))

    try:
        item = ShopItem.query.get_or_404(item_id)
        name = item.display_name

        # Delete related purchases first
        ShopPurchase.query.filter_by(item_id=item_id).delete()

        db.session.delete(item)
        db.session.commit()

        flash(f'Товар "{name}" удален!', 'success')

    except Exception as e:
        app.logger.error(f"Error deleting shop item: {e}")
        flash('Ошибка при удалении товара!', 'error')

    return redirect(url_for('admin_shop'))



@app.route('/admin/reputation')
def admin_reputation():
    """Admin reputation management page"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    players = Player.query.all()
    return render_template('admin_reputation.html', players=players)

@app.route('/admin/update_reputation', methods=['POST'])
def admin_update_reputation():
    """Update player reputation (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        target_player = request.form.get('target_player', '').strip()
        reputation_change = int(request.form.get('reputation_change', '0'))
        reason = request.form.get('reason', '').strip()

        if not target_player or reputation_change == 0:
            flash('Укажите никнейм игрока и измените значение репутации!', 'error')
            return redirect(url_for('admin_reputation'))

        player = Player.query.filter_by(nickname=target_player).first()
        if not player:
            flash('Игрок не найден!', 'error')
            return redirect(url_for('admin_reputation'))

        # Update reputation
        old_reputation = player.reputation
        player.reputation = max(0, player.reputation + reputation_change)

        # Log the change
        from models import ReputationLog
        log_entry = ReputationLog(
            player_id=player.id,
            change_amount=reputation_change,
            reason=reason or f"Изменение администратором",
            given_by='admin'
        )
        db.session.add(log_entry)

        db.session.commit()

        # Очистка кэша статистики
        Player.clear_statistics_cache()

        action = "Добавлено" if reputation_change > 0 else "Убрано"
        flash(f'{action} {abs(reputation_change)} репутации игроку {player.nickname}. Было: {old_reputation}, стало: {player.reputation}', 'success')

    except Exception as e:
        app.logger.error(f"Error updating reputation: {e}")
        flash('Ошибка при изменении репутации!', 'error')

    return redirect(url_for('admin_reputation'))



@app.route('/reputation-guide')
def reputation_guide():
    """Reputation earning guide"""
    current_player = None
    player_nickname = session.get('player_nickname')
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()

    return render_template('reputation_guide.html', current_player=current_player)

@app.route('/karma-guide')
def karma_guide():
    """Show karma FAQ page"""
    current_player = None
    player_nickname = session.get('player_nickname')
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()
    return render_template('karma_guide.html', current_player=current_player)

@app.route('/coins-guide')
def coins_guide():
    """Coins earning guide"""
    current_player = None
    player_nickname = session.get('player_nickname')
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()

    return render_template('coins_guide.html', current_player=current_player)

@app.route('/experience_guide')
def experience_guide():
    """Experience earning guide"""
    is_admin = session.get('is_admin', False)
    return render_template('experience_guide.html', is_admin=is_admin)

@app.route('/admin/player-quests')
def admin_player_quests():
    """View all player quests (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    players = Player.query.all()
    player_quests = {}

    for player in players:
        quests = PlayerQuest.query.filter_by(player_id=player.id).all()
        if quests:
            player_quests[player] = quests

    return render_template('admin_player_quests.html', player_quests=player_quests)

@app.route('/admin/player-achievements')
def admin_player_achievements():
    """View all player achievements (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    players = Player.query.all()
    player_achievements = {}

    for player in players:
        achievements = PlayerAchievement.query.filter_by(player_id=player.id).all()
        if achievements:
            player_achievements[player] = achievements

    return render_template('admin_player_achievements.html', player_achievements=player_achievements)

@app.route('/admin/gradients')
def admin_gradients():
    """Admin gradient management"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    # Initialize default themes if none exist
    if GradientTheme.query.count() == 0:
        GradientTheme.create_default_themes()

    themes = GradientTheme.query.all()
    players = Player.query.all()

    # Group themes by element type
    grouped_themes = {}
    for theme in themes:
        if theme.element_type not in grouped_themes:
            grouped_themes[theme.element_type] = []
        grouped_themes[theme.element_type].append(theme)

    return render_template('admin_gradients.html',
                         grouped_themes=grouped_themes,
                         players=players)

@app.route('/admin/create_gradient', methods=['POST'])
def create_gradient():
    """Create new gradient theme (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        name = request.form.get('name', '').strip().lower()
        display_name = request.form.get('display_name', '').strip()
        element_type = request.form.get('element_type', '').strip()
        color1 = request.form.get('color1', '#ffffff')
        color2 = request.form.get('color2', '#000000')
        color3 = request.form.get('color3', '').strip() or None
        gradient_direction = request.form.get('gradient_direction', '45deg')
        animation_enabled = request.form.get('animation_enabled') == 'on'

        if not name or not display_name or not element_type:
            flash('Все обязательные поля должны быть заполнены!', 'error')
            return redirect(url_for('admin_gradients'))

        # Check if theme already exists
        existing = GradientTheme.query.filter_by(name=name).first()
        if existing:
            flash('Градиент с таким названием уже существует!', 'error')
            return redirect(url_for('admin_gradients'))

        theme = GradientTheme(
            name=name,
            display_name=display_name,
            element_type=element_type,
            color1=color1,
            color2=color2,
            color3=color3,
            gradient_direction=gradient_direction,
            animation_enabled=animation_enabled
        )

        db.session.add(theme)
        db.session.commit()

        flash(f'Градиент "{display_name}" успешно создан!', 'success')

    except Exception as e:
        app.logger.error(f"Error creating gradient: {e}")
        flash('Ошибка при создании градиента!', 'error')

    return redirect(url_for('admin_gradients'))

@app.route('/admin/assign_gradient', methods=['POST'])
def assign_gradient():
    """Assign gradient to player (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        player_id = request.form.get('player_id', type=int)
        element_type = request.form.get('element_type', '').strip()
        gradient_theme_id = request.form.get('gradient_theme_id', type=int)
        custom_color1 = request.form.get('custom_color1', '').strip() or None
        custom_color2 = request.form.get('custom_color2', '').strip() or None
        custom_color3 = request.form.get('custom_color3', '').strip() or None

        if not player_id or not element_type:
            flash('Выберите игрока и тип элемента!', 'error')
            return redirect(url_for('admin_gradients'))

        player = Player.query.get_or_404(player_id)

        # Remove existing gradient for this element type
        PlayerGradientSetting.query.filter_by(
            player_id=player_id,
            element_type=element_type
        ).delete()

        # Create new gradient setting
        gradient_setting = PlayerGradientSetting(
            player_id=player_id,
            element_type=element_type,
            gradient_theme_id=gradient_theme_id if gradient_theme_id else None,
            custom_color1=custom_color1,
            custom_color2=custom_color2,
            custom_color3=custom_color3,
            is_enabled=True
        )

        db.session.add(gradient_setting)
        db.session.commit()

        theme_name = "кастомный градиент"
        if gradient_theme_id:
            theme = GradientTheme.query.get(gradient_theme_id)
            theme_name = theme.display_name if theme else "градиент"

        flash(f'Градиент "{theme_name}" присвоен игроку {player.nickname} для {element_type}!', 'success')

    except Exception as e:
        app.logger.error(f"Error assigning gradient: {e}")
        flash('Ошибка при присвоении градиента!', 'error')

    return redirect(url_for('admin_gradients'))

@app.route('/admin/remove_gradient/<int:player_id>/<element_type>', methods=['POST'])
def remove_gradient(player_id, element_type):
    """Remove gradient from player (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        PlayerGradientSetting.query.filter_by(
            player_id=player_id,
            element_type=element_type
        ).delete()
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error removing gradient: {e}")
        return jsonify({'error': 'Failed to remove gradient'}), 500



@app.route('/profile/<nickname>')
def public_profile_by_nickname(nickname):
    """Display public player profile by nickname"""
    player = Player.query.filter_by(nickname=nickname).first_or_404()

    if not player.profile_is_public and session.get('player_nickname') != nickname:
        flash('Профиль этого игрока приватный!', 'error')
        return redirect(url_for('index'))

    is_owner = session.get('player_nickname') == nickname
    is_admin = session.get('is_admin', False)

    # Get player's visible badges
    player_badges = PlayerBadge.query.filter_by(player_id=player.id, is_visible=True).all()
    visible_badges_data = []
    for pb in player_badges:
        badge = Badge.query.get(pb.badge_id)
        if badge and badge.is_active:
            visible_badges_data.append({
                'badge': badge,
                'display_name': badge.display_name,
                'icon': badge.icon,
                'color': badge.color,
                'background_color': badge.background_color,
                'border_color': badge.border_color,
                'rarity': badge.rarity,
                'has_gradient': badge.has_gradient,
                'gradient_start': badge.gradient_start,
                'gradient_end': badge.gradient_end,
                'is_animated': badge.is_animated
            })

    # Get game modes for ASCEND card
    from models import GameMode
    if GameMode.query.count() == 0:
        GameMode.create_default_modes()
    game_modes_query = GameMode.query.filter_by(is_active=True).all()
    game_modes = [
        {
            'id': mode.id,
            'name': mode.name,
            'display_name': mode.display_name,
            'icon': mode.icon,
            'color': mode.color
        }
        for mode in game_modes_query
    ]

    return render_template('public_profile.html',
                         player=player,
                         is_owner=is_owner,
                         is_admin=is_admin,
                         visible_badges=visible_badges_data,
                         game_modes=game_modes)



@app.route('/update-profile', methods=['POST'])
def update_profile():
    """Update current player's profile"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    try:
        # Update personal information
        player.real_name = request.form.get('real_name', '').strip() or None
        player.bio = request.form.get('bio', '').strip() or None
        player.discord_tag = request.form.get('discord_tag', '').strip() or None
        player.youtube_channel = request.form.get('youtube_channel', '').strip() or None
        player.twitch_channel = request.form.get('twitch_channel', '').strip() or None
        player.favorite_server = request.form.get('favorite_server', '').strip() or None
        player.favorite_map = request.form.get('favorite_map', '').strip() or None
        player.preferred_gamemode = request.form.get('preferred_gamemode', '').strip() or None
        player.profile_banner_color = request.form.get('profile_banner_color', '#3498db')
        player.profile_is_public = request.form.get('profile_is_public') == 'on'
        player.custom_status = request.form.get('custom_status', '').strip() or None
        player.location = request.form.get('location', '').strip() or None

        # Handle birthday
        birthday_str = request.form.get('birthday', '').strip()
        if birthday_str:
            from datetime import datetime
            try:
                player.birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
            except ValueError:
                player.birthday = None
        else:
            player.birthday = None

        # Handle custom avatar and banner
        player.custom_avatar_url = request.form.get('custom_avatar_url', '').strip() or None

        # Only allow banner customization for level 20+
        if player.level >= 20:
            player.custom_banner_url = request.form.get('custom_banner_url', '').strip() or None
            player.banner_is_animated = request.form.get('banner_is_animated') == 'on'

        # Profile section colors
        player.stats_section_color = request.form.get('stats_section_color', '#343a40')
        player.info_section_color = request.form.get('info_section_color', '#343a40')
        player.social_section_color = request.form.get('social_section_color', '#343a40')
        player.prefs_section_color = request.form.get('prefs_section_color', '#343a40')

        # Handle extended social networks
        social_types = request.form.getlist('social_type[]')
        social_values = request.form.getlist('social_value[]')

        if social_types and social_values:
            social_networks = []
            for i, (social_type, social_value) in enumerate(zip(social_types, social_values)):
                if social_type and social_value.strip():
                    social_networks.append({
                        'type': social_type,
                        'value': social_value.strip()
                    })
            player.set_social_networks_list(social_networks)
        else:
            player.set_social_networks_list([])

        db.session.commit()
        # Очистка кэша статистики
        Player.clear_statistics_cache()
        flash('Профиль успешно обновлен!', 'success')

    except Exception as e:
        app.logger.error(f"Error updating profile: {e}")
        flash('Ошибка при обновлении профиля!', 'error')

    return redirect(url_for('my_profile'))

@app.route('/apply-gradient', methods=['POST'])
def apply_gradient():
    """Apply gradient to player's elements"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    try:
        element_type = request.form.get('element_type')
        gradient_theme_id = request.form.get('gradient_theme_id', type=int)

        if not element_type:
            flash('Тип элемента обязателен!', 'error')
            return redirect(url_for('my_profile'))

        # Remove existing gradient for this element type
        PlayerGradientSetting.query.filter_by(
            player_id=player.id,
            element_type=element_type
        ).delete()

        # Add new gradient if theme selected
        if gradient_theme_id:
            gradient_setting = PlayerGradientSetting(
                player_id=player.id,
                element_type=element_type,
                gradient_theme_id=gradient_theme_id,
                is_enabled=True
            )
            db.session.add(gradient_setting)

        db.session.commit()
        flash('Градиент применен!', 'success')

    except Exception as e:
        app.logger.error(f"Error applying gradient: {e}")
        flash('Ошибка при применении градиента!', 'error')

    return redirect(url_for('my_profile'))

@app.route('/set-player-role', methods=['POST'])
def set_player_role():
    """Set player's current role (only if reputation >= 500)"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    if not player.can_set_free_custom_role:
        flash('Для установки произвольной роли требуется 500+ репутации!', 'error')
        return redirect(url_for('my_profile'))

    try:
        new_role = request.form.get('role', '').strip()
        if new_role:
            player.role = new_role
            db.session.commit()
            flash(f'Роль изменена на "{new_role}"!', 'success')
        else:
            flash('Роль не может быть пустой!', 'error')

    except Exception as e:
        app.logger.error(f"Error updating role: {e}")
        flash('Ошибка при изменении роли!', 'error')

    return redirect(url_for('my_profile'))



@app.route('/set-custom-role', methods=['POST'])
def set_custom_role():
    """Set player's purchased custom role"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    if not player.custom_role_purchased:
        flash('Сначала приобретите кастомную роль в магазине!', 'error')
        return redirect(url_for('my_profile'))

    try:
        custom_role = request.form.get('custom_role', '').strip()
        custom_role_emoji = request.form.get('custom_role_emoji', '').strip()
        custom_role_color = request.form.get('custom_role_color', '#ffd700')
        use_gradient = request.form.get('use_gradient') == 'on'
        animated_gradient = request.form.get('animated_gradient') == 'on'
        gradient_start = request.form.get('gradient_start', '#ff6b35')
        gradient_end = request.form.get('gradient_end', '#f7931e')

        if custom_role:
            player.custom_role = custom_role
            player.custom_role_emoji = custom_role_emoji if custom_role_emoji else None
            player.custom_role_color = custom_role_color
            player.custom_role_animated = animated_gradient

            if use_gradient:
                direction = "45deg"
                if animated_gradient:
                    player.custom_role_gradient = f"linear-gradient({direction}, {gradient_start}, {gradient_end})"
                else:
                    player.custom_role_gradient = f"linear-gradient({direction}, {gradient_start}, {gradient_end})"
            else:
                player.custom_role_gradient = None

            db.session.commit()
            flash('Кастомная роль успешно обновлена!', 'success')
        else:
            flash('Название роли не может быть пустым!', 'error')

    except Exception as e:
        app.logger.error(f"Error updating custom role: {e}")
        flash('Ошибка при обновлении кастомной роли!', 'error')

    return redirect(url_for('my_profile'))



@app.route('/deactivate-all-titles', methods=['POST'])
def deactivate_all_titles():
    """Deactivate all custom titles for player"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    try:
        # Deactivate all titles for this player
        PlayerTitle.query.filter_by(player_id=player.id, is_active=True).update({'is_active': False})
        db.session.commit()
        flash('Все титулы деактивированы!', 'success')

    except Exception as e:
        app.logger.error(f"Error deactivating titles: {e}")
        flash('Ошибка при деактивации титулов!', 'error')

    return redirect(url_for('my_profile'))

@app.route('/update-leaderboard-style', methods=['POST'])
def update_leaderboard_style():
    """Update player's leaderboard styling"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    if not player.can_customize_colors:
        flash('Кастомизация лидерборда доступна с 20 уровня!', 'error')
        return redirect(url_for('my_profile'))

    try:
        player.leaderboard_name_color = request.form.get('leaderboard_name_color', '#ffffff')
        player.leaderboard_stats_color = request.form.get('leaderboard_stats_color', '#ffffff')

        if player.can_customize_colors: # Check if player has permission to customize gradients
            player.leaderboard_use_gradient = request.form.get('leaderboard_use_gradient') == 'on'
            if player.leaderboard_use_gradient:
                player.leaderboard_gradient_start = request.form.get('leaderboard_gradient_start', '#ff6b35')
                player.leaderboard_gradient_end = request.form.get('leaderboard_gradient_end', '#f7931e')

                if player.can_use_leaderboard_animated_gradients:
                    player.leaderboard_gradient_animated = request.form.get('leaderboard_gradient_animated') == 'on'

        db.session.commit()
        flash('Стиль лидерборда обновлен!', 'success')

    except Exception as e:
        app.logger.error(f"Error updating leaderboard style: {e}")
        flash('Ошибка при обновлении стиля лидерборда!', 'error')

    return redirect(url_for('my_profile'))

@app.route('/activate-player-title', methods=['POST'])
def activate_player_title():
    """Activate a specific title for player"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    try:
        title_id = request.form.get('title_id', type=int)

        if title_id:
            # Deactivate all current titles
            PlayerTitle.query.filter_by(player_id=player.id, is_active=True).update({'is_active': False})

            # Activate the selected title
            player_title = PlayerTitle.query.filter_by(player_id=player.id, title_id=title_id).first()
            if player_title:
                player_title.is_active = True
                db.session.commit()
                flash('Титул активирован!', 'success')
            else:
                flash('Титул не найден!', 'error')

    except Exception as e:
        app.logger.error(f"Error activating title: {e}")
        flash('Ошибка при активации титула!', 'error')

    return redirect(url_for('my_profile'))

@app.route('/activate-admin-role', methods=['POST'])
def activate_admin_role():
    """Activate a specific admin role for player"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    try:
        role_id = request.form.get('role_id', type=int)

        if role_id:
            # Deactivate all current admin roles
            PlayerAdminRole.query.filter_by(player_id=player.id, is_active=True).update({'is_active': False})

            # Activate the selected admin role
            player_role = PlayerAdminRole.query.filter_by(player_id=player.id, role_id=role_id).first()
            if player_role:
                player_role.is_active = True
                db.session.commit()
                flash('Админская роль активирована!', 'success')
            else:
                flash('Роль не найдена!', 'error')

    except Exception as e:
        app.logger.error(f"Error activating admin role: {e}")
        flash('Ошибка при активации роли!', 'error')

    return redirect(url_for('my_profile'))

@app.route('/deactivate-admin-role', methods=['POST'])
def deactivate_admin_role():
    """Deactivate all admin roles for player"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    try:
        # Deactivate all admin roles for this player
        PlayerAdminRole.query.filter_by(player_id=player.id, is_active=True).update({'is_active': False})
        db.session.commit()
        flash('Все админские роли деактивированы!', 'success')

    except Exception as e:
        app.logger.error(f"Error deactivating admin roles: {e}")
        flash('Ошибка при деактивации ролей!', 'error')

    return redirect(url_for('my_profile'))

@app.route('/admin/achievements')
def admin_achievements():
    """Admin achievements management page"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    # Initialize default achievements if none exist
    if Achievement.query.count() == 0:
        Achievement.create_default_achievements()

    badges = Badge.query.order_by(Badge.created_at.desc()).all() # Changed to badges, assuming this was intended
    players = Player.query.order_by(Player.nickname).all()

    return render_template('admin_achievements.html',
                         badges=badges, # Passing badges here
                         players=players,
                         Player=Player,
                         PlayerAchievement=PlayerAchievement,
                         Achievement=Achievement)

@app.route('/admin/create_achievement', methods=['POST'])
def create_achievement():
    """Create custom achievement (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        import json

        # Validate input fields
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        condition_type = request.form.get('condition_type', '').strip()
        condition_value = request.form.get('condition_value', '0')

        if not title or not description or not condition_type:
            flash('Название, описание и тип условия обязательны!', 'error')
            return redirect(url_for('admin_achievements'))

        # Create proper JSON condition
        try:
            condition_val = int(condition_value) if condition_value.isdigit() else 0
        except:
            condition_val = 0

        unlock_condition = json.dumps({condition_type: condition_val})

        achievement_data = {
            'title': title,
            'description': description,
            'unlock_condition': unlock_condition,
            'rarity': request.form.get('rarity', 'common'),
            'reward_xp': int(request.form.get('reward_xp', 0)),
            'reward_title': request.form.get('reward_title', '').strip() or None,
            'icon': request.form.get('icon', '').strip() or 'fas fa-star',
            'is_hidden': request.form.get('is_hidden') == 'on'
        }

        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
        db.session.commit()

        flash(f'Достижение "{achievement_data["title"]}" успешно создано!', 'success')

    except Exception as e:
        app.logger.error(f"Error creating achievement: {e}")
        flash('Ошибка при создании достижения!', 'error')

    return redirect(url_for('admin_achievements'))

@app.route('/admin/generate_achievements', methods=['POST'])
def generate_achievements():
    """Generate seasonal achievements (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        import json

        seasonal_achievements = [
            {
                'title': 'Новогодний воин',
                'description': 'Убейте 100 игроков в зимнем сезоне',
                'unlock_condition': json.dumps({"kills": 100}),
                'rarity': 'epic',
                'reward_xp': 1000,
                'reward_title': 'Зимний воин',
                'icon': 'fas fa-snowflake',
                'is_hidden': False
            },
            {
                'title': 'Летний чемпион',
                'description': 'Выиграйте 50 игр летом',
                'unlock_condition': json.dumps({"wins": 50}),
                'rarity': 'legendary',
                'reward_xp': 2000,
                'reward_title': 'Летняя легенда',
                'icon': 'fas fa-sun',
                'is_hidden': False
            },
            {
                'title': 'Коллекционер ресурсов',
                'description': 'Соберите 10000 единиц ресурсов',
                'unlock_condition': json.dumps({"total_resources": 10000}),
                'rarity': 'rare',
                'reward_xp': 750,
                'reward_title': 'Мастер ресурсов',
                'icon': 'fas fa-gem',
                'is_hidden': True
            },
            {
                'title': 'Весенний освободитель',
                'description': 'Сломайте 25 кроватей весной',
                'unlock_condition': json.dumps({"beds_broken": 25}),
                'rarity': 'rare',
                'reward_xp': 800,
                'reward_title': 'Весенний разрушитель',
                'icon': 'fas fa-leaf',
                'is_hidden': False
            },
            {
                'title': 'Осенний стратег',
                'description': 'Достигните 70% процента побед',
                'unlock_condition': json.dumps({"win_rate": 70.0}),
                'rarity': 'legendary',
                'reward_xp': 1500,
                'reward_title': 'Мастер стратегии',
                'icon': 'fas fa-chess',
                'is_hidden': True
            }
        ]

        # Check if achievements already exist to avoid duplicates
        created_count = 0
        for achievement_data in seasonal_achievements:
            existing = Achievement.query.filter_by(title=achievement_data['title']).first()
            if not existing:
                achievement = Achievement(**achievement_data)
                db.session.add(achievement)
                created_count += 1

        db.session.commit()

        if created_count > 0:
            return jsonify({'success': True, 'message': f'Создано {created_count} сезонных достижений!'})
        else:
            return jsonify({'success': True, 'message': 'Все сезонные достижения уже существуют!'})

    except Exception as e:
        app.logger.error(f"Error generating achievements: {e}")
        return jsonify({'error': f'Ошибка при создании достижений: {str(e)}'}), 500

@app.route('/admin/assign_achievement', methods=['POST'])
def assign_achievement():
    """Assign achievement to player (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        player_id = request.form.get('player_id', type=int)
        achievement_id = request.form.get('achievement_id', type=int)

        if not player_id or not achievement_id:
            flash('Выберите игрока и достижение!', 'error')
            return redirect(url_for('admin_achievements'))

        player = Player.query.get_or_404(player_id)
        achievement = Achievement.query.get_or_404(achievement_id)

        # Check if player already has this achievement
        existing = PlayerAchievement.query.filter_by(
            player_id=player_id,
            achievement_id=achievement_id
        ).first()

        if existing:
            flash(f'Игрок {player.nickname} уже имеет достижение "{achievement.title}"!', 'warning')
        else:
            # Add achievement
            player_achievement = PlayerAchievement(
                player_id=player_id,
                achievement_id=achievement_id
            )
            db.session.add(player_achievement)

            # Award XP
            player.experience += achievement.reward_xp

            db.session.commit()
            # Очистка кэша статистики
            Player.clear_statistics_cache()
            flash(f'Достижение "{achievement.title}" присвоено игроку {player.nickname}!', 'success')

    except Exception as e:
        app.logger.error(f"Error assigning achievement: {e}")
        flash('Ошибка при присвоении достижения!', 'error')

    return redirect(url_for('admin_achievements'))

@app.route('/admin/remove_achievement/<int:player_id>/<int:achievement_id>', methods=['POST'])
def remove_achievement(player_id, achievement_id):
    """Remove achievement from player (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        player_achievement = PlayerAchievement.query.filter_by(
            player_id=player_id,
            achievement_id=achievement_id
        ).first()

        if player_achievement:
            # Get achievement for XP removal
            achievement = Achievement.query.get(achievement_id)
            player = Player.query.get(player_id)

            # Remove XP (but don't go below 0)
            if player and achievement:
                player.experience = max(0, player.experience - achievement.reward_xp)

            db.session.delete(player_achievement)
            db.session.commit()
            # Очистка кэша статистики
            Player.clear_statistics_cache()

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error removing achievement: {e}")
        return jsonify({'error': 'Failed to remove achievement'}), 500

@app.route('/admin/themes')
def admin_themes():
    """Admin themes management page"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    # Initialize default themes if none exist
    if SiteTheme.query.count() == 0:
        SiteTheme.create_default_themes()

    themes = SiteTheme.query.all()

    return render_template('admin_themes.html',
                         themes=themes)

@app.route('/admin/create_theme', methods=['POST'])
def admin_create_theme():
    """Create new site theme (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        name = request.form.get('name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        primary_color = request.form.get('primary_color', '#ffc107')
        secondary_color = request.form.get('secondary_color', '#17a2b8')
        background_color = request.form.get('background_color', '#121212')
        card_background = request.form.get('card_background', '#1e1e1e')
        text_color = request.form.get('text_color', '#ffffff')
        accent_color = request.form.get('accent_color', '#28a745')
        is_default = request.form.get('is_default') == 'on'

        if not name or not display_name:
            flash('Название и отображаемое имя обязательны!', 'error')
            return redirect(url_for('admin_themes'))

        # Check if theme already exists
        existing = SiteTheme.query.filter_by(name=name).first()
        if existing:
            flash('Тема с таким названием уже существует!', 'error')
            return redirect(url_for('admin_themes'))

        # If setting as default, remove default from others
        if is_default:
            SiteTheme.query.update({'is_default': False})

        theme = SiteTheme(
            name=name,
            display_name=display_name,
            primary_color=primary_color,
            secondary_color=secondary_color,
            background_color=background_color,
            card_background=card_background,
            text_color=text_color,
            accent_color=accent_color,
            is_default=is_default
        )

        db.session.add(theme)
        db.session.commit()

        flash(f'Тема "{display_name}" успешно создана!', 'success')

    except Exception as e:
        app.logger.error(f"Error creating theme: {e}")
        flash('Ошибка при создании темы!', 'error')

    return redirect(url_for('admin_themes'))

@app.route('/admin/delete_theme/<int:theme_id>', methods=['DELETE'])
def admin_delete_theme(theme_id):
    """Delete theme (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        theme = SiteTheme.query.get_or_404(theme_id)

        if theme.is_default:
            return jsonify({'error': 'Cannot delete default theme'}), 400

        db.session.delete(theme)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error deleting theme: {e}")
        return jsonify({'error': 'Failed to delete theme'}), 500

@app.route('/admin/badges')
def admin_badges():
    """Admin badges management page"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    # Initialize default badges if none exist
    if Badge.query.count() == 0:
        Badge.create_default_badges()

    badges = Badge.query.order_by(Badge.created_at.desc()).all()
    players = Player.query.order_by(Player.nickname).all()

    # Create badge statistics
    badge_stats = []
    for badge in badges:
        assigned_count = PlayerBadge.query.filter_by(badge_id=badge.id).count()
        badge_stats.append({
            'badge': badge,
            'assigned_count': assigned_count
        })

    return render_template('admin_badges.html',
                         badge_stats=badge_stats,
                         badges=badges,
                         players=players)

@app.route('/admin/create_badge', methods=['POST'])
def create_badge():
    """Create new badge (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        name = request.form.get('name', '').strip()
        display_name = request.form.get('display_name', '').strip()
        description = request.form.get('description', '').strip()
        icon = request.form.get('icon', 'fas fa-medal').strip()
        emoji = request.form.get('emoji', '').strip()
        emoji_url = request.form.get('emoji_url', '').strip()
        color = request.form.get('color', '#ffffff')
        background_color = request.form.get('background_color', '#343a40')
        border_color = request.form.get('border_color', '#ffd700')
        rarity = request.form.get('rarity', 'common')
        has_gradient = request.form.get('has_gradient') == 'on'
        gradient_start = request.form.get('gradient_start', '#ffd700') if has_gradient else None
        gradient_end = request.form.get('gradient_end', '#ffaa00') if has_gradient else None
        is_animated = request.form.get('is_animated') == 'on'

        if not name or not display_name:
            flash('Название и отображаемое имя обязательны!', 'error')
            return redirect(url_for('admin_badges'))

        # Check if badge already exists
        existing = Badge.query.filter_by(name=name).first()
        if existing:
            flash('Бейдж с таким названием уже существует!', 'error')
            return redirect(url_for('admin_badges'))

        badge = Badge(
            name=name,
            display_name=display_name,
            description=description,
            icon=icon,
            emoji=emoji,
            emoji_url=emoji_url,
            color=color,
            background_color=background_color,
            border_color=border_color,
            has_gradient=has_gradient,
            gradient_start=gradient_start,
            gradient_end=gradient_end,
            rarity=rarity,
            is_animated=is_animated
        )

        db.session.add(badge)
        db.session.commit()

        flash(f'Бейдж "{display_name}" успешно создан!', 'success')

    except Exception as e:
        app.logger.error(f"Error creating badge: {e}")
        flash('Ошибка при создании бейджа!', 'error')

    return redirect(url_for('admin_badges'))

@app.route('/admin/assign_badge', methods=['POST'])
def assign_badge():
    """Assign badge to player (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        player_id = request.form.get('player_id', type=int)
        badge_id = request.form.get('badge_id', type=int)

        if not player_id or not badge_id:
            flash('Выберите игрока и бейдж!', 'error')
            return redirect(url_for('admin_badges'))

        player = Player.query.get_or_404(player_id)
        badge = Badge.query.get_or_404(badge_id)

        # Check if player already has this badge
        existing = PlayerBadge.query.filter_by(
            player_id=player_id,
            badge_id=badge_id
        ).first()

        if existing:
            flash(f'Игрок {player.nickname} уже имеет бейдж "{badge.display_name}"!', 'warning')
        else:
            # Add badge
            player_badge = PlayerBadge(
                player_id=player_id,
                badge_id=badge_id
            )
            db.session.add(player_badge)
            db.session.commit()

            flash(f'Бейдж "{badge.display_name}" присвоен игроку {player.nickname}!', 'success')

    except Exception as e:
        app.logger.error(f"Error assigning badge: {e}")
        flash('Ошибка при присвоении бейджа!', 'error')

    return redirect(url_for('admin_badges'))

@app.route('/admin/remove_badge/<int:player_id>/<int:badge_id>', methods=['POST'])
def remove_badge(player_id, badge_id):
    """Remove badge from player (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        player_badge = PlayerBadge.query.filter_by(
            player_id=player_id,
            badge_id=badge_id
        ).first()

        if player_badge:
            db.session.delete(player_badge)
            db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error removing badge: {e}")
        return jsonify({'error': 'Failed to remove badge'}), 500

@app.route('/admin/toggle_badge_visibility', methods=['POST'])
def toggle_badge_visibility():
    """Toggle badge visibility for player (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        player_id = request.json.get('player_id')
        badge_id = request.json.get('badge_id')

        player_badge = PlayerBadge.query.filter_by(
            player_id=player_id,
            badge_id=badge_id
        ).first()

        if player_badge:
            player_badge.is_visible = not player_badge.is_visible
            db.session.commit()
            return jsonify({'success': True, 'is_visible': player_badge.is_visible})

        return jsonify({'error': 'Badge not found'}), 404

    except Exception as e:
        app.logger.error(f"Error toggling badge visibility: {e}")
        return jsonify({'error': 'Failed to toggle visibility'}), 500

@app.route('/update-badge-visibility', methods=['POST'])
def update_badge_visibility():
    """Update badge visibility settings (player)"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    try:
        for key, value in request.form.items():
            if key.startswith('badge_visible_'):
                badge_id = int(key.replace('badge_visible_', ''))
                is_visible = value == 'on'

                player_badge = PlayerBadge.query.filter_by(
                    player_id=player.id,
                    badge_id=badge_id
                ).first()

                if player_badge:
                    player_badge.is_visible = is_visible

        db.session.commit()
        flash('Настройки видимости бейджей обновлены!', 'success')

    except Exception as e:
        app.logger.error(f"Error updating badge visibility: {e}")
        flash('Ошибка при обновлении настроек!', 'error')

    return redirect(url_for('my_profile'))

@app.route('/admin/roles')
def admin_roles():
    """Admin roles management page"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    # Initialize default roles if none exist
    if AdminCustomRole.query.count() == 0:
        AdminCustomRole.create_default_roles()

    custom_roles = AdminCustomRole.query.filter_by(is_active=True).all()
    players = Player.query.order_by(Player.nickname).all()
    players_with_roles = PlayerAdminRole.query.filter_by(is_active=True).all()

    return render_template('admin_roles.html',
                         custom_roles=custom_roles,
                         players=players,
                         players_with_roles=players_with_roles)

@app.route('/admin/create_role', methods=['POST'])
def admin_create_custom_role():
    """Create new custom role (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        name = request.form.get('name', '').strip()
        color = request.form.get('color', '#ffc107')
        emoji = request.form.get('emoji', '').strip()
        emoji_class = request.form.get('emoji_class', '').strip()
        emoji_file = request.files.get('emoji_file')
        has_gradient = request.form.get('has_gradient') == 'on'
        gradient_end_color = request.form.get('gradient_end_color', '').strip() if has_gradient else None
        is_visible = request.form.get('is_visible') == 'on'

        if not name:
            flash('Название роли обязательно!', 'error')
            return redirect(url_for('admin_roles'))

        # Check if role already exists
        existing = AdminCustomRole.query.filter_by(name=name).first()
        if existing:
            flash('Роль с таким названием уже существует!', 'error')
            return redirect(url_for('admin_roles'))

        # Handle emoji file upload
        emoji_filename = None
        emoji_is_animated = False

        if 'emoji_file' in request.files:
            emoji_file = request.files['emoji_file']
            if emoji_file.filename and emoji_file.filename != '':
                # Validate file
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif'}
                file_ext = emoji_file.filename.rsplit('.', 1)[1].lower() if '.' in emoji_file.filename else ''

                if file_ext not in allowed_extensions:
                    flash('Неподдерживаемый формат файла! Разрешены: PNG, JPG, GIF, WEBP, AVIF', 'error')
                    return redirect(url_for('admin_roles'))

                # Check file size (256KB max)
                emoji_file.seek(0, os.SEEK_END)
                file_size = emoji_file.tell()
                emoji_file.seek(0)

                if file_size > 256 * 1024:  # 256KB
                    flash('Файл слишком большой! Максимум 256KB', 'error')
                    return redirect(url_for('admin_roles'))

                # Check if animated (GIF)
                emoji_is_animated = file_ext == 'gif'

                # Generate unique filename
                import uuid
                unique_id = str(uuid.uuid4()).replace('-', '')
                emoji_filename = f"{unique_id}.{file_ext}"

                # Save file
                upload_dir = os.path.join('static', 'emojis')
                os.makedirs(upload_dir, exist_ok=True)
                emoji_file.save(os.path.join(upload_dir, emoji_filename))

        role = AdminCustomRole(
            name=name,
            color=color,
            emoji=emoji if emoji else None,
            emoji_class=emoji_class if emoji_class else None,
            emoji_filename=emoji_filename,
            emoji_is_animated=emoji_is_animated,
            has_gradient=has_gradient,
            gradient_end_color=gradient_end_color,
            is_visible=is_visible
        )

        db.session.add(role)
        db.session.commit()

        flash(f'Роль "{name}" успешно создана!', 'success')

    except Exception as e:
        app.logger.error(f"Error creating custom role: {e}")
        flash('Ошибка при создании роли!', 'error')

    return redirect(url_for('admin_roles'))

@app.route('/admin/assign_role', methods=['POST'])
def admin_assign_custom_role():
    """Assign custom role to player (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        player_id = request.form.get('player_id', type=int)
        role_id = request.form.get('role_id', type=int)

        if not player_id or not role_id:
            flash('Выберите игрока и роль!', 'error')
            return redirect(url_for('admin_roles'))

        player = Player.query.get_or_404(player_id)
        role = AdminCustomRole.query.get_or_404(role_id)

        # Remove existing active admin role for this player
        PlayerAdminRole.query.filter_by(
            player_id=player_id,
            is_active=True
        ).update({'is_active': False})

        # Create new role assignment
        player_admin_role = PlayerAdminRole(
            player_id=player_id,
            role_id=role_id,
            is_active=True,
            assigned_at=datetime.utcnow()
        )

        # Deactivate other admin roles for this player
        PlayerAdminRole.query.filter_by(player_id=player_id, is_active=True).update({'is_active': False})

        # Activate the new role
        player_admin_role.is_active = True

        db.session.add(player_admin_role)
        db.session.commit()

        flash(f'Роль "{role.name}" назначена и активирована для игрока {player.nickname}!', 'success')

    except Exception as e:
        app.logger.error(f"Error assigning role: {e}")
        flash('Ошибка при назначении роли!', 'error')

    return redirect(url_for('admin_roles'))

@app.route('/admin/delete_role/<int:role_id>', methods=['DELETE'])
def admin_delete_custom_role(role_id):
    """Delete custom role (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        role = AdminCustomRole.query.get_or_404(role_id)

        # Remove emoji file if exists
        if role.emoji_filename:
            try:
                emoji_path = os.path.join('static', 'emojis', role.emoji_filename)
                if os.path.exists(emoji_path):
                    os.remove(emoji_path)
            except Exception as e:
                app.logger.warning(f"Failed to delete emoji file {role.emoji_filename}: {e}")

        # Remove role from all players first
        PlayerAdminRole.query.filter_by(role_id=role_id).delete()

        db.session.delete(role)
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error deleting role: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete role'}), 500

@app.route('/admin/remove_player_role/<int:player_id>', methods=['POST'])
def admin_remove_player_role(player_id):
    """Remove role from player (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        player = Player.query.get_or_404(player_id)

        # Remove role assignment
        PlayerAdminRole.query.filter_by(player_id=player_id).delete()
        db.session.commit()

        flash(f'Роль снята с игрока {player.nickname}!', 'success')

    except Exception as e:
        app.logger.error(f"Error removing player role: {e}")
        flash('Ошибка при снятии роли!', 'error')

    return redirect(url_for('admin_roles'))

@app.route('/inventory')
def inventory():
    """Display player inventory"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        return render_template('inventory.html', current_player=None)

    current_player = Player.query.filter_by(nickname=player_nickname).first()
    return render_template('inventory.html', current_player=current_player)

@app.route('/admin/give_coins', methods=['POST'])
def admin_give_coins():
    """Give coins to player (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('login'))

    try:
        target_player = request.form.get('target_player', '').strip()
        coins_amount = int(request.form.get('coins_amount', '0'))
        reason = request.form.get('reason', '').strip()

        if not target_player or coins_amount == 0:
            flash('Все поля обязательны и сумма койнов должна быть не равна нулю!', 'error')
            return redirect(url_for('admin_reputation'))

        player = Player.query.filter_by(nickname=target_player).first()
        if not player:
            flash('Игрок не найден!', 'error')
            return redirect(url_for('admin_reputation'))

        # Give coins
        old_coins = player.coins
        player.coins += coins_amount
        db.session.commit()

        # Очистка кэша статистики
        Player.clear_statistics_cache()

        flash(f'Игроку {target_player} выдано {coins_amount} койнов! (Было: {old_coins}, Стало: {player.coins})', 'success')

    except Exception as e:
        app.logger.error(f"Error giving coins: {e}")
        flash('Ошибка при выдаче койнов!', 'error')

    return redirect(url_for('admin_reputation'))



# Clan system routes
@app.route('/clans')
def clans():
    """Display clans page"""
    current_player = None
    player_nickname = session.get('player_nickname')
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()

    # Get filter parameters
    sort_by = request.args.get('sort', 'rating')
    search = request.args.get('search', '').strip()

    if search:
        clans = Clan.search_clans(search)
    else:
        if sort_by == 'rating':
            clans = Clan.query.filter_by(is_active=True).order_by(Clan.rating.desc()).all()
        elif sort_by == 'level':
            clans = sorted(Clan.query.filter_by(is_active=True).all(), key=lambda c: c.level, reverse=True)
        elif sort_by == 'members':
            clans = sorted(Clan.query.filter_by(is_active=True).all(), key=lambda c: c.member_count, reverse=True)
        elif sort_by == 'created':
            clans = Clan.query.filter_by(is_active=True).order_by(Clan.created_at.desc()).all()
        else:
            clans = Clan.query.filter_by(is_active=True).order_by(Clan.rating.desc()).all()

    # Get player's clan if logged in
    player_clan = None
    if current_player:
        clan_member = ClanMember.query.filter_by(player_id=current_player.id, is_active=True).first()
        if clan_member:
            player_clan = clan_member.clan

    return render_template('clans.html',
                         clans=clans,
                         current_player=current_player,
                         player_clan=player_clan,
                         current_sort=sort_by,
                         search_query=search,
                         is_admin=session.get('is_admin', False))

@app.route('/clan/<int:clan_id>')
def clan_detail(clan_id):
    """Display clan details"""
    clan = Clan.query.get_or_404(clan_id)
    current_player = None
    player_nickname = session.get('player_nickname')
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()

    # Get clan members
    members = ClanMember.query.filter_by(clan_id=clan_id, is_active=True).all()

    # Check if current player is member
    is_member = False
    player_role = None
    if current_player:
        player_membership = ClanMember.query.filter_by(
            clan_id=clan_id,
            player_id=current_player.id,
            is_active=True
        ).first()
        if player_membership:
            is_member = True
            player_role = player_membership.role

    return render_template('clan_detail.html',
                         clan=clan,
                         members=members,
                         current_player=current_player,
                         is_member=is_member,
                         player_role=player_role,
                         is_admin=session.get('is_admin', False))

@app.route('/create_clan', methods=['GET', 'POST'])
def create_clan():
    """Create new clan"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему для создания клана!', 'error')
        return redirect(url_for('player_login'))

    current_player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    # Check level requirement
    if current_player.level < 100:
        flash('Для создания клана требуется минимум 100 уровень!', 'error')
        return redirect(url_for('clans'))

    # Check if player has enough coins
    clan_cost = 50000
    if current_player.coins < clan_cost:
        flash(f'Для создания клана требуется {clan_cost} койнов!', 'error')
        return redirect(url_for('clans'))

    # Check if player is already in a clan
    existing_membership = ClanMember.query.filter_by(player_id=current_player.id, is_active=True).first()
    if existing_membership:
        flash('Вы уже состоите в клане!', 'error')
        return redirect(url_for('clans'))

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            tag = request.form.get('tag', '').strip().upper()
            description = request.form.get('description', '').strip()
            clan_type = request.form.get('clan_type', 'open')
            max_members = int(request.form.get('max_members', 50))

            # Validation
            if not name or len(name) < 3:
                flash('Название клана должно содержать минимум 3 символа!', 'error')
                return redirect(url_for('create_clan'))

            if not tag or len(tag) < 2 or len(tag) > 10:
                flash('Тег клана должен содержать от 2 до 10 символов!', 'error')
                return redirect(url_for('create_clan'))

            if max_members < 5 or max_members > 100:
                flash('Максимум участников должен быть от 5 до 100!', 'error')
                return redirect(url_for('create_clan'))

            # Check uniqueness
            if Clan.query.filter_by(name=name).first():
                flash('Клан с таким названием уже существует!', 'error')
                return redirect(url_for('create_clan'))

            if Clan.query.filter_by(tag=tag).first():
                flash('Клан с таким тегом уже существует!', 'error')
                return redirect(url_for('create_clan'))

            # Deduct coins for clan creation
            current_player.coins -= 50000

            # Create clan
            clan = Clan(
                name=name,
                tag=tag,
                description=description,
                clan_type=clan_type,
                max_members=max_members,
                leader_id=current_player.id
            )
            db.session.add(clan)
            db.session.flush()

            # Add leader as member
            clan_member = ClanMember(
                clan_id=clan.id,
                player_id=current_player.id,
                role='leader'
            )
            db.session.add(clan_member)
            db.session.commit()

            # Очистка кэша статистики
            Player.clear_statistics_cache()

            flash(f'Клан "{name}" [{tag}] успешно создан!', 'success')
            return redirect(url_for('clan_detail', clan_id=clan.id))

        except Exception as e:
            app.logger.error(f"Error creating clan: {e}")
            flash('Ошибка при создании клана!', 'error')

    return render_template('create_clan.html', current_player=current_player)

@app.route('/join_clan/<int:clan_id>', methods=['POST'])
def join_clan(clan_id):
    """Join a clan"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему для создания клана!', 'error')
        return redirect(url_for('player_login'))

    current_player = Player.query.filter_by(nickname=player_nickname).first_or_404()
    clan = Clan.query.get_or_404(clan_id)

    try:
        # Check if player is already in a clan
        existing_membership = ClanMember.query.filter_by(player_id=current_player.id, is_active=True).first()
        if existing_membership:
            flash('Вы уже состоите в клане!', 'error')
            return redirect(url_for('clan_detail', clan_id=clan_id))

        # Check if clan can accept new members
        if not clan.can_join:
            flash('Клан не принимает новых участников!', 'error')
            return redirect(url_for('clan_detail', clan_id=clan_id))

        # Join clan
        clan_member = ClanMember(
            clan_id=clan_id,
            player_id=current_player.id,
            role='member'
        )
        db.session.add(clan_member)
        db.session.commit()

        flash(f'Вы успешно вступили в клан "{clan.name}"!', 'success')

    except Exception as e:
        app.logger.error(f"Error joining clan: {e}")
        flash('Ошибка при вступлении в клан!', 'error')

    return redirect(url_for('clan_detail', clan_id=clan_id))

@app.route('/leave_clan/<int:clan_id>', methods=['POST'])
def leave_clan(clan_id):
    """Leave a clan"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    current_player = Player.query.filter_by(nickname=player_nickname).first_or_404()
    clan = Clan.query.get_or_404(clan_id)

    try:
        membership = ClanMember.query.filter_by(
            clan_id=clan_id,
            player_id=current_player.id,
            is_active=True
        ).first()

        if not membership:
            flash('Вы не состоите в этом клане!', 'error')
            return redirect(url_for('clan_detail', clan_id=clan_id))

        # Leaders cannot leave (must transfer leadership first)
        if membership.role == 'leader':
            flash('Лидер не может покинуть клан! Передайте лидерство другому участнику.', 'error')
            return redirect(url_for('clan_detail', clan_id=clan_id))

        # Leave clan
        membership.is_active = False
        db.session.commit()

        flash(f'Вы покинули клан "{clan.name}"!', 'success')
        return redirect(url_for('clans'))

    except Exception as e:
        app.logger.error(f"Error leaving clan: {e}")
        flash('Ошибка при выходе из клана!', 'error')

    return redirect(url_for('clan_detail', clan_id=clan_id))

# Tournament system routes
@app.route('/tournaments')
def tournaments():
    """Display tournaments page"""
    current_player = None
    player_nickname = session.get('player_nickname')
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()

    # Get filter parameters
    status_filter = request.args.get('status', 'all')

    if status_filter == 'upcoming':
        tournaments = Tournament.get_upcoming()
    elif status_filter == 'active':
        tournaments = Tournament.get_active()
    elif status_filter == 'completed':
        tournaments = Tournament.get_completed()
    else:
        tournaments = Tournament.query.filter_by(is_active=True).order_by(Tournament.start_date.desc()).all()

    return render_template('tournaments.html',
                         tournaments=tournaments,
                         current_player=current_player,
                         current_status=status_filter,
                         is_admin=session.get('is_admin', False))

@app.route('/tournament/<int:tournament_id>')
def tournament_detail(tournament_id):
    """Display tournament details"""
    tournament = Tournament.query.get_or_404(tournament_id)
    current_player = None
    player_nickname = session.get('player_nickname')
    if player_nickname:
        current_player = Player.query.filter_by(nickname=player_nickname).first()

    # Get tournament participants
    participants = TournamentParticipant.query.filter_by(tournament_id=tournament_id, is_active=True).all()

    # Check if current player is participant
    is_participant = False
    if current_player:
        is_participant = TournamentParticipant.query.filter_by(
            tournament_id=tournament_id,
            player_id=current_player.id,
            is_active=True
        ).first() is not None

    return render_template('tournament_detail.html',
                         tournament=tournament,
                         participants=participants,
                         current_player=current_player,
                         is_participant=is_participant,
                         is_admin=session.get('is_admin', False))

@app.route('/create_tournament', methods=['GET', 'POST'])
def create_tournament():
    """Create new tournament"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему для создания турниров!', 'error')
        return redirect(url_for('player_login'))

    current_player = Player.query.filter_by(nickname=player_nickname).first_or_404()

    # Check level requirement and special roles
    allowed_roles = ['Организатор', 'Клан-лидер', 'admin']
    has_special_role = any(role in current_player.role for role in allowed_roles)

    if current_player.level < 15 and not has_special_role and not session.get('is_admin', False):
        flash('Для создания турниров требуется минимум 15 уровень или специальная роль!', 'error')
        return redirect(url_for('tournaments'))

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            tournament_type = request.form.get('tournament_type', 'singles')
            start_date_str = request.form.get('start_date', '')
            entry_fee = int(request.form.get('entry_fee', 0))
            prize_pool = int(request.form.get('prize_pool', 0))
            max_participants = int(request.form.get('max_participants', 100))

            # Validation
            if not name or len(name) < 3:
                flash('Название турнира должно содержать минимум 3 символа!', 'error')
                return redirect(url_for('create_tournament'))

            if not start_date_str:
                flash('Укажите дату начала турнира!', 'error')
                return redirect(url_for('create_tournament'))

            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            if start_date <= datetime.utcnow():
                flash('Дата начала должна быть в будущем!', 'error')
                return redirect(url_for('create_tournament'))

            # Check minimum prize pool
            min_prize = 1500 if tournament_type == 'clans' else 500
            if prize_pool < min_prize:
                flash(f'Минимальный призовой фонд: {min_prize} койнов!', 'error')
                return redirect(url_for('create_tournament'))

            # Check if player has enough coins
            organizer_type = 'player'
            organizer_clan_id = None

            if tournament_type == 'clans':
                # For clan tournaments, check if player is clan leader
                clan_membership = ClanMember.query.filter_by(
                    player_id=current_player.id,
                    role='leader',
                    is_active=True
                ).first()

                if not clan_membership:
                    flash('Только лидеры кланов могут создавать клановые турниры!', 'error')
                    return redirect(url_for('create_tournament'))

                if clan_membership.clan.clan_coins < prize_pool:
                    flash('У клана недостаточно койнов для призового фонда!', 'error')
                    return redirect(url_for('create_tournament'))

                organizer_type = 'clan'
                organizer_clan_id = clan_membership.clan_id
                # Lock clan funds
                clan_membership.clan.clan_coins -= prize_pool
            else:
                if current_player.coins < prize_pool:
                    flash('У вас недостаточно койнов для призового фонда!', 'error')
                    return redirect(url_for('create_tournament'))

                # Lock player funds
                current_player.coins -= prize_pool

            # Create tournament
            tournament = Tournament(
                name=name,
                description=description,
                tournament_type=tournament_type,
                start_date=start_date,
                entry_fee=entry_fee,
                prize_pool=prize_pool,
                max_participants=max_participants,
                organizer_id=current_player.id,
                organizer_type=organizer_type,
                organizer_clan_id=organizer_clan_id,
                funds_locked=True
            )
            db.session.add(tournament)
            db.session.commit()

            # Очистка кэша статистики
            Player.clear_statistics_cache()

            flash(f'Турнир "{name}" успешно создан!', 'success')
            return redirect(url_for('tournament_detail', tournament_id=tournament.id))

        except Exception as e:
            app.logger.error(f"Error creating tournament: {e}")
            flash('Ошибка при создании турнира!', 'error')

    return render_template('create_tournament.html')

@app.route('/join_tournament/<int:tournament_id>', methods=['POST'])
def join_tournament(tournament_id):
    """Join a tournament"""
    player_nickname = session.get('player_nickname')
    if not player_nickname:
        flash('Необходимо войти в систему!', 'error')
        return redirect(url_for('player_login'))

    current_player = Player.query.filter_by(nickname=player_nickname).first_or_404()
    tournament = Tournament.query.get_or_404(tournament_id)

    try:
        # Check if player is already participating
        existing_participation = TournamentParticipant.query.filter_by(
            tournament_id=tournament_id,
            player_id=current_player.id,
            is_active=True
        ).first()
        if existing_participation:
            flash('Вы уже участвуете в этом турнире!', 'error')
            return redirect(url_for('tournament_detail', tournament_id=tournament_id))

        # Check if tournament can accept new participants
        if not tournament.can_join:
            flash('Турнир не принимает новых участников!', 'error')
            return redirect(url_for('tournament_detail', tournament_id=tournament_id))

        # Check entry fee
        if tournament.entry_fee > current_player.coins:
            flash('Недостаточно койнов для участия!', 'error')
            return redirect(url_for('tournament_detail', tournament_id=tournament_id))

        # Join tournament
        participant = TournamentParticipant(
            tournament_id=tournament_id,
            player_id=current_player.id
        )
        db.session.add(participant)

        # Deduct entry fee
        current_player.coins -= tournament.entry_fee
        db.session.commit()

        flash(f'Вы успешно зарегистрировались в турнире "{tournament.name}"!', 'success')

    except Exception as e:
        app.logger.error(f"Error joining tournament: {e}")
        flash('Ошибка при регистрации в турнире!', 'error')

    return redirect(url_for('tournament_detail', tournament_id=tournament_id))

@app.route('/admin/complete_tournament/<int:tournament_id>', methods=['POST'])
def admin_complete_tournament(tournament_id):
    """Complete tournament and distribute prizes (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('tournaments'))

    try:
        tournament = Tournament.query.get_or_404(tournament_id)

        if tournament.status != 'active':
            flash('Турнир не активен!', 'error')
            return redirect(url_for('tournament_detail', tournament_id=tournament_id))

        # Get winners data from form
        winners_data = []
        participants = TournamentParticipant.query.filter_by(tournament_id=tournament_id, is_active=True).all()

        # Simple distribution: 1st place gets 50%, 2nd gets 30%, 3rd gets 20%
        if participants:
            total_prize = tournament.prize_pool
            if len(participants) >= 3:
                winners_data = [
                    {'participant_id': participants[0].id, 'placement': 1, 'prize_amount': int(total_prize * 0.5)},
                    {'participant_id': participants[1].id, 'placement': 2, 'prize_amount': int(total_prize * 0.3)},
                    {'participant_id': participants[2].id, 'placement': 3, 'prize_amount': int(total_prize * 0.2)}
                ]
            elif len(participants) == 2:
                winners_data = [
                    {'participant_id': participants[0].id, 'placement': 1, 'prize_amount': int(total_prize * 0.7)},
                    {'participant_id': participants[1].id, 'placement': 2, 'prize_amount': int(total_prize * 0.3)}
                ]
            elif len(participants) == 1:
                winners_data = [
                    {'participant_id': participants[0].id, 'placement': 1, 'prize_amount': total_prize}
                ]

        if tournament.complete_tournament(winners_data):
            db.session.commit()
            # Очистка кэша статистики
            Player.clear_statistics_cache()
            flash('Турнир успешно завершён и призы распределены!', 'success')
        else:
            flash('Ошибка при завершении турнира!', 'error')

    except Exception as e:
        app.logger.error(f"Error completing tournament: {e}")
        flash('Ошибка при завершении турнира!', 'error')

    return redirect(url_for('tournament_detail', tournament_id=tournament_id))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('base.html', error_message="Страница не найдена"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('base.html', error_message="Внутренняя ошибка сервера"), 500

# Helper functions for boosters
def get_current_player():
    return Player.query.get(session.get('player_id')) if session.get('player_id') else None

def apply_coins_with_booster(player, amount):
    """Apply coins with active booster multiplier"""
    multiplier = PlayerActiveBooster.get_coins_multiplier(player.id)
    final_amount = int(amount * multiplier)
    player.coins += final_amount
    return final_amount, multiplier

def apply_reputation_with_booster(player, amount):
    """Apply reputation with active booster multiplier"""
    multiplier = PlayerActiveBooster.get_reputation_multiplier(player.id)
    final_amount = int(amount * multiplier)
    player.reputation += final_amount
    return final_amount, multiplier

# ASCEND System API Routes
@app.route('/api/player/<int:player_id>/ascend-data')
def get_ascend_data(player_id):
    """Get ASCEND data for a player"""
    try:
        # Check if player exists
        player = Player.query.get_or_404(player_id)

        # Get or create ASCEND data
        ascend_data = ASCENDData.get_or_create(player_id)

        return jsonify({
            'success': True,
            'ascend': ascend_data.to_dict()
        })
    except Exception as e:
        app.logger.error(f"Error getting ASCEND data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ascend/update', methods=['POST'])
def update_ascend_data():
    """Update ASCEND data for a player (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({
            'success': False,
            'error': 'Доступ запрещен! Только администратор может обновлять ASCEND данные.'
        }), 403

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Данные не получены'
            }), 400

        player_id = data.get('player_id')
        if not player_id:
            return jsonify({
                'success': False,
                'error': 'ID игрока не указан'
            }), 400

        # Check if player exists
        player = Player.query.get_or_404(player_id)

        # Get or create ASCEND data
        ascend_data = ASCENDData.get_or_create(player_id)

        # Store previous overall tier for history
        previous_tier = ascend_data.overall_tier

        # Update ASCEND data
        ascend_data.pvp_tier = data.get('pvp_tier', 'D')
        ascend_data.clutching_tier = data.get('clutching_tier', 'D')
        ascend_data.block_placement_tier = data.get('block_placement_tier', 'D')
        ascend_data.gamesense_tier = data.get('gamesense_tier', 'D')
        ascend_data.overall_tier = data.get('overall_tier', 'D')

        # Update scores
        ascend_data.pvp_score = max(0, min(100, data.get('pvp_score', 25)))
        ascend_data.clutching_score = max(0, min(100, data.get('clutching_score', 25)))
        ascend_data.block_placement_score = max(0, min(100, data.get('block_placement_score', 25)))
        ascend_data.gamesense_score = max(0, min(100, data.get('gamesense_score', 25)))

        # Update other fields
        ascend_data.comment = data.get('comment', '')
        ascend_data.evaluator_name = data.get('evaluator_name', 'Elite Squad')
        ascend_data.previous_tier = previous_tier

        # Set evaluator info
        if session.get('player_id'):
            ascend_data.evaluator_id = session.get('player_id')

        # Update timestamp
        ascend_data.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update
        app.logger.info(f"ASCEND data updated for player {player.nickname} by admin {session.get('player_nickname', 'Unknown')}")

        return jsonify({
            'success': True,
            'message': 'ASCEND данные успешно обновлены',
            'ascend': ascend_data.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating ASCEND data: {e}")
        return jsonify({
            'success': False,
            'error': f'Ошибка при обновлении данных: {str(e)}'
        }), 500

@app.route('/api/ascend/reset/<int:player_id>', methods=['POST'])
def reset_ascend_data(player_id):
    """Reset ASCEND data to defaults (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({
            'success': False,
            'error': 'Доступ запрещен!'
        }), 403

    try:
        player = Player.query.get_or_404(player_id)
        ascend_data = ASCENDData.query.filter_by(player_id=player_id).first()

        if ascend_data:
            # Store current tier as previous
            ascend_data.previous_tier = ascend_data.overall_tier

            # Reset to defaults
            ascend_data.pvp_tier = 'D'
            ascend_data.clutching_tier = 'D'
            ascend_data.block_placement_tier = 'D'
            ascend_data.gamesense_tier = 'D'
            ascend_data.overall_tier = 'D'

            ascend_data.pvp_score = 25
            ascend_data.clutching_score = 25
            ascend_data.block_placement_score = 25
            ascend_data.gamesense_score = 25

            ascend_data.comment = 'Оценка сброшена'
            ascend_data.updated_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'ASCEND данные сброшены к значениям по умолчанию'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'ASCEND данные не найдены'
            }), 404

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error resetting ASCEND data: {e}")
        return jsonify({
            'success': False,
            'error': f'Ошибка при сбросе данных: {str(e)}'
        }), 500

@app.route('/api/ascend/bulk-update', methods=['POST'])
def bulk_update_ascend():
    """Bulk update ASCEND data for multiple players (admin only)"""
    if not session.get('is_admin', False):
        return jsonify({
            'success': False,
            'error': 'Доступ запрещен!'
        }), 403

    try:
        data = request.get_json()
        updates = data.get('updates', [])

        if not updates:
            return jsonify({
                'success': False,
                'error': 'Список обновлений пуст'
            }), 400

        updated_count = 0
        errors = []

        for update in updates:
            try:
                player_id = update.get('player_id')
                if not player_id:
                    continue

                player = Player.query.get(player_id)
                if not player:
                    errors.append(f"Игрок с ID {player_id} не найден")
                    continue

                ascend_data = ASCENDData.get_or_create(player_id)

                # Update fields
                for field in ['pvp_tier', 'clutching_tier', 'block_placement_tier', 'gamesense_tier', 'overall_tier']:
                    if field in update:
                        setattr(ascend_data, field, update[field])

                for field in ['pvp_score', 'clutching_score', 'block_placement_score', 'gamesense_score']:
                    if field in update:
                        score = max(0, min(100, update[field]))
                        setattr(ascend_data, field, score)

                if 'comment' in update:
                    ascend_data.comment = update['comment']

                if 'evaluator_name' in update:
                    ascend_data.evaluator_name = update['evaluator_name']

                ascend_data.updated_at = datetime.utcnow()
                updated_count += 1

            except Exception as e:
                errors.append(f"Ошибка обновления игрока {player_id}: {str(e)}")

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Обновлено {updated_count} игроков',
            'updated_count': updated_count,
            'errors': errors
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in bulk ASCEND update: {e}")
        return jsonify({
            'success': False,
            'error': f'Ошибка при массовом обновлении: {str(e)}'
        }), 500
@app.route('/admin/create_booster_items', methods=['POST'])
def create_booster_items():
    """Create booster shop items (admin only)"""
    if not session.get('is_admin', False):
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('index'))

    try:
        # Coin boosters
        coin_boosters = [
            {
                'name': 'coin_booster_small',
                'display_name': '🪙 Малый бустер койнов',
                'description': '+50% к получаемым койнам на 1 час',
                'category': 'booster',
                'price_coins': 100,
                'price_reputation': 0,
                'rarity': 'common',
                'icon': 'fas fa-coins',
                'item_data': json.dumps({
                    'type': 'coin_multiplier',
                    'multiplier': 1.5,
                    'duration_hours': 1
                })
            },
            {
                'name': 'coin_booster_medium',
                'display_name': '💰 Средний бустер койнов',
                'description': '+100% к получаемым койнам на 2 часа',
                'category': 'booster',
                'price_coins': 300,
                'price_reputation': 5,
                'rarity': 'uncommon',
                'icon': 'fas fa-hand-holding-usd',
                'item_data': json.dumps({
                    'type': 'coin_multiplier',
                    'multiplier': 2.0,
                    'duration_hours': 2
                })
            },
            {
                'name': 'coin_booster_large',
                'display_name': '💎 Большой бустер койнов',
                'description': '+200% к получаемым койнам на 3 часа',
                'category': 'booster',
                'price_coins': 800,
                'price_reputation': 15,
                'rarity': 'rare',
                'icon': 'fas fa-gem',
                'item_data': json.dumps({
                    'type': 'coin_multiplier',
                    'multiplier': 3.0,
                    'duration_hours': 3
                })
            }
        ]

        # Reputation boosters
        rep_boosters = [
            {
                'name': 'rep_booster_small',
                'display_name': '⭐ Малый бустер репутации',
                'description': '+50% к получаемой репутации на 1 час',
                'category': 'booster',
                'price_coins': 150,
                'price_reputation': 0,
                'rarity': 'common',
                'icon': 'fas fa-star',
                'item_data': json.dumps({
                    'type': 'reputation_multiplier',
                    'multiplier': 1.5,
                    'duration_hours': 1
                })
            },
            {
                'name': 'rep_booster_medium',
                'display_name': '🌟 Средний бустер репутации',
                'description': '+100% к получаемой репутации на 2 часа',
                'category': 'booster',
                'price_coins': 400,
                'price_reputation': 8,
                'rarity': 'uncommon',
                'icon': 'fas fa-star-half-alt',
                'item_data': json.dumps({
                    'type': 'reputation_multiplier',
                    'multiplier': 2.0,
                    'duration_hours': 2
                })
            }
        ]

        all_boosters = coin_boosters + rep_boosters

        for booster_data in all_boosters:
            existing = ShopItem.query.filter_by(name=booster_data['name']).first()
            if not existing:
                booster = ShopItem(**booster_data)
                db.session.add(booster)

        db.session.commit()
        flash('Бустеры успешно добавлены в магазин!', 'success')

    except Exception as e:
        app.logger.error(f"Error creating boosters: {e}")
        flash('Ошибка при создании бустеров!', 'error')

    return redirect(url_for('admin'))

# Function to initialize shop items, including boosters
def initialize_shop_items():
    """Initialize default shop items if they don't exist"""
    try:
        # Create boosters if they don't exist
        if ShopItem.query.filter_by(category='booster').count() == 0:

            # Import json at the top if not already imported
            import json

            boosters = [
                {
                    'name': 'coin_booster_1h',
                    'display_name': '🪙 Бустер койнов (1ч)',
                    'description': '+50% к получаемым койнам на 1 час',
                    'category': 'booster',
                    'price_coins': 100,
                    'price_reputation': 0,
                    'unlock_level': 1,
                    'rarity': 'common',
                    'icon': 'fas fa-coins',
                    'item_data': json.dumps({
                        'type': 'coin_multiplier',
                        'multiplier': 1.5,
                        'duration_hours': 1
                    }),
                    'is_active': True
                },
                {
                    'name': 'rep_booster_1h',
                    'display_name': '⭐ Бустер репутации (1ч)',
                    'description': '+50% к получаемой репутации на 1 час',
                    'category': 'booster',
                    'price_coins': 150,
                    'price_reputation': 0,
                    'unlock_level': 1,
                    'rarity': 'common',
                    'icon': 'fas fa-star',
                    'item_data': json.dumps({
                        'type': 'reputation_multiplier',
                        'multiplier': 1.5,
                        'duration_hours': 1
                    }),
                    'is_active': True
                }
            ]

            for booster_data in boosters:
                booster = ShopItem(**booster_data)
                db.session.add(booster)

            db.session.commit()
            app.logger.info("Default boosters created")

    except Exception as e:
        app.logger.error(f"Error initializing shop items: {e}")

# Call this function after app initialization
with app.app_context():
    initialize_shop_items()