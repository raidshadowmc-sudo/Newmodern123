from app import db
from datetime import datetime
from sqlalchemy import func
from functools import lru_cache
import json

class ASCENDHistory(db.Model):
    """Model for storing ASCEND evaluation history"""
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    gamemode = db.Column(db.String(50), default='bedwars', nullable=False)
    
    # Previous values
    old_overall_tier = db.Column(db.String(3), nullable=True)
    new_overall_tier = db.Column(db.String(3), nullable=False)
    
    # Score changes
    old_scores = db.Column(db.Text, nullable=True)  # JSON
    new_scores = db.Column(db.Text, nullable=False)  # JSON
    
    # Change details
    change_type = db.Column(db.String(20), default='update', nullable=False)  # update, upgrade, downgrade
    evaluator_name = db.Column(db.String(100), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    player = db.relationship('Player', backref='ascend_history')
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        import json
        return {
            'id': self.id,
            'player_id': self.player_id,
            'gamemode': self.gamemode,
            'old_overall_tier': self.old_overall_tier,
            'new_overall_tier': self.new_overall_tier,
            'old_scores': json.loads(self.old_scores) if self.old_scores else None,
            'new_scores': json.loads(self.new_scores) if self.new_scores else None,
            'change_type': self.change_type,
            'evaluator_name': self.evaluator_name,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ASCENDData(db.Model):
    """Model for storing ASCEND performance card data"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    gamemode = db.Column(db.String(50), default='bedwars', nullable=False)
    
    # Skill categories - varies by gamemode
    skill1_name = db.Column(db.String(50), default='PVP', nullable=False)
    skill1_tier = db.Column(db.String(3), default='D', nullable=False)
    skill1_score = db.Column(db.Integer, default=25, nullable=False)
    
    skill2_name = db.Column(db.String(50), default='Clutching', nullable=False)
    skill2_tier = db.Column(db.String(3), default='D', nullable=False)
    skill2_score = db.Column(db.Integer, default=25, nullable=False)
    
    skill3_name = db.Column(db.String(50), default='Block Placement', nullable=False)
    skill3_tier = db.Column(db.String(3), default='D', nullable=False)
    skill3_score = db.Column(db.Integer, default=25, nullable=False)
    
    skill4_name = db.Column(db.String(50), default='Gamesense', nullable=False)
    skill4_tier = db.Column(db.String(3), default='D', nullable=False)
    skill4_score = db.Column(db.Integer, default=25, nullable=False)
    
    # Legacy fields for backwards compatibility
    pvp_tier = db.Column(db.String(3), default='D', nullable=False)
    clutching_tier = db.Column(db.String(3), default='D', nullable=False)
    block_placement_tier = db.Column(db.String(3), default='D', nullable=False)
    gamesense_tier = db.Column(db.String(3), default='D', nullable=False)
    overall_tier = db.Column(db.String(3), default='D', nullable=False)

    pvp_score = db.Column(db.Integer, default=25, nullable=False)
    clutching_score = db.Column(db.Integer, default=25, nullable=False)
    block_placement_score = db.Column(db.Integer, default=25, nullable=False)
    gamesense_score = db.Column(db.Integer, default=25, nullable=False)

    # Custom comment
    comment = db.Column(db.Text, nullable=True)

    # Evaluator info
    evaluator_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    evaluator_name = db.Column(db.String(100), default='Elite Squad', nullable=False)

    # Previous tier for history
    previous_tier = db.Column(db.String(3), nullable=True)
    
    # Global ranking
    global_rank = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = db.relationship('Player', foreign_keys=[player_id], backref='ascend_data')
    evaluator = db.relationship('Player', foreign_keys=[evaluator_id])

    @classmethod
    def get_or_create(cls, player_id):
        """Get existing ASCEND data or create new with defaults"""
        ascend_data = cls.query.filter_by(player_id=player_id).first()
        if not ascend_data:
            ascend_data = cls(player_id=player_id)
            db.session.add(ascend_data)
            db.session.commit()
        return ascend_data

    def save_to_history(self):
        """Save current state to history before making changes"""
        import json
        
        # Get old data if exists
        old_data = ASCENDData.query.filter_by(player_id=self.player_id, gamemode=self.gamemode).first()
        
        if old_data and old_data.id != self.id:
            # Determine change type
            change_type = 'update'
            if old_data.overall_tier != self.overall_tier:
                tier_values = {'D': 1, 'C': 2, 'C+': 3, 'B': 4, 'B+': 5, 'A': 6, 'A+': 7, 'S': 8, 'S+': 9}
                if tier_values.get(self.overall_tier, 1) > tier_values.get(old_data.overall_tier, 1):
                    change_type = 'upgrade'
                else:
                    change_type = 'downgrade'
            
            # Create history entry
            history = ASCENDHistory(
                player_id=self.player_id,
                gamemode=self.gamemode,
                old_overall_tier=old_data.overall_tier,
                new_overall_tier=self.overall_tier,
                old_scores=json.dumps({
                    'skill1': old_data.skill1_score,
                    'skill2': old_data.skill2_score,
                    'skill3': old_data.skill3_score,
                    'skill4': old_data.skill4_score
                }),
                new_scores=json.dumps({
                    'skill1': self.skill1_score,
                    'skill2': self.skill2_score,
                    'skill3': self.skill3_score,
                    'skill4': self.skill4_score
                }),
                change_type=change_type,
                evaluator_name=self.evaluator_name,
                comment=self.comment
            )
            db.session.add(history)

    def update_global_rank(self):
        """Update global rank based on overall performance"""
        # Calculate average score
        avg_score = (self.skill1_score + self.skill2_score + self.skill3_score + self.skill4_score) / 4
        
        # Count players with higher scores in same gamemode
        higher_count = db.session.query(ASCENDData).filter(
            ASCENDData.gamemode == self.gamemode,
            ((ASCENDData.skill1_score + ASCENDData.skill2_score + ASCENDData.skill3_score + ASCENDData.skill4_score) / 4) > avg_score
        ).count()
        
        self.global_rank = higher_count + 1

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'gamemode': self.gamemode,
            'skill1_name': self.skill1_name,
            'skill1_tier': self.skill1_tier,
            'skill1_score': self.skill1_score,
            'skill2_name': self.skill2_name,
            'skill2_tier': self.skill2_tier,
            'skill2_score': self.skill2_score,
            'skill3_name': self.skill3_name,
            'skill3_tier': self.skill3_tier,
            'skill3_score': self.skill3_score,
            'skill4_name': self.skill4_name,
            'skill4_tier': self.skill4_tier,
            'skill4_score': self.skill4_score,
            'overall_tier': self.overall_tier,
            'global_rank': self.global_rank,
            'comment': self.comment,
            'evaluator_name': self.evaluator_name,
            'previous_tier': self.previous_tier,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Legacy compatibility
            'pvp_tier': self.pvp_tier,
            'clutching_tier': self.clutching_tier,
            'block_placement_tier': self.block_placement_tier,
            'gamesense_tier': self.gamesense_tier,
            'pvp_score': self.pvp_score,
            'clutching_score': self.clutching_score,
            'block_placement_score': self.block_placement_score,
            'gamesense_score': self.gamesense_score
        }


class GameMode(db.Model):
    """Model for different game modes with their skill categories"""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), default='fas fa-gamepad')
    color = db.Column(db.String(7), default='#ffc107')
    
    # Skill categories for this gamemode
    skill1_name = db.Column(db.String(50), nullable=False)
    skill1_description = db.Column(db.String(200), nullable=True)
    skill1_icon = db.Column(db.String(50), default='fas fa-star')
    
    skill2_name = db.Column(db.String(50), nullable=False)
    skill2_description = db.Column(db.String(200), nullable=True)
    skill2_icon = db.Column(db.String(50), default='fas fa-star')
    
    skill3_name = db.Column(db.String(50), nullable=False)
    skill3_description = db.Column(db.String(200), nullable=True)
    skill3_icon = db.Column(db.String(50), default='fas fa-star')
    
    skill4_name = db.Column(db.String(50), nullable=False)
    skill4_description = db.Column(db.String(200), nullable=True)
    skill4_icon = db.Column(db.String(50), default='fas fa-star')
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'skills': [
                {
                    'name': self.skill1_name,
                    'description': self.skill1_description,
                    'icon': self.skill1_icon
                },
                {
                    'name': self.skill2_name,
                    'description': self.skill2_description,
                    'icon': self.skill2_icon
                },
                {
                    'name': self.skill3_name,
                    'description': self.skill3_description,
                    'icon': self.skill3_icon
                },
                {
                    'name': self.skill4_name,
                    'description': self.skill4_description,
                    'icon': self.skill4_icon
                }
            ],
            'is_active': self.is_active
        }
    
    @classmethod
    def create_default_modes(cls):
        """Create default game modes with their skill categories"""
        default_modes = [
            {
                'name': 'bedwars',
                'display_name': 'Bedwars',
                'description': 'Classic Bedwars gameplay',
                'icon': 'fas fa-bed',
                'color': '#e74c3c',
                'skill1_name': 'PVP',
                'skill1_description': 'Combat effectiveness and dueling skills',
                'skill1_icon': 'fas fa-sword',
                'skill2_name': 'Clutching',
                'skill2_description': 'Performance under pressure situations',
                'skill2_icon': 'fas fa-fire',
                'skill3_name': 'Block Placement',
                'skill3_description': 'Strategic building and defensive positioning',
                'skill3_icon': 'fas fa-cube',
                'skill4_name': 'Gamesense',
                'skill4_description': 'Game awareness and tactical decision making',
                'skill4_icon': 'fas fa-brain'
            },
            {
                'name': 'kitpvp',
                'display_name': 'KitPVP',
                'description': 'Kit-based PvP combat',
                'icon': 'fas fa-sword',
                'color': '#f39c12',
                'skill1_name': 'Aiming',
                'skill1_description': 'Accuracy and target acquisition',
                'skill1_icon': 'fas fa-crosshairs',
                'skill2_name': 'Healing (soups/pots)',
                'skill2_description': 'Health management and healing efficiency',
                'skill2_icon': 'fas fa-heart',
                'skill3_name': 'Movement',
                'skill3_description': 'Mobility and positioning',
                'skill3_icon': 'fas fa-running',
                'skill4_name': 'Spacing',
                'skill4_description': 'Distance control and positioning',
                'skill4_icon': 'fas fa-expand-arrows-alt'
            },
            {
                'name': 'skywars',
                'display_name': 'SkyWars',
                'description': 'Sky-based survival combat',
                'icon': 'fas fa-cloud',
                'color': '#3498db',
                'skill1_name': 'Looting',
                'skill1_description': 'Efficient resource gathering',
                'skill1_icon': 'fas fa-search',
                'skill2_name': 'Potting',
                'skill2_description': 'Potion usage and timing',
                'skill2_icon': 'fas fa-flask',
                'skill3_name': 'Pearling',
                'skill3_description': 'Ender pearl mechanics and timing',
                'skill3_icon': 'fas fa-circle',
                'skill4_name': 'Melee',
                'skill4_description': 'Close combat effectiveness',
                'skill4_icon': 'fas fa-fist-raised'
            },
            {
                'name': 'bridgefight',
                'display_name': 'BridgeFight',
                'description': 'Bridge-based combat scenarios',
                'icon': 'fas fa-bridge',
                'color': '#9b59b6',
                'skill1_name': 'Block Edits',
                'skill1_description': 'Building and editing proficiency',
                'skill1_icon': 'fas fa-edit',
                'skill2_name': 'Bridge Fights',
                'skill2_description': 'Combat on narrow bridges',
                'skill2_icon': 'fas fa-bridge',
                'skill3_name': 'Gamesense',
                'skill3_description': 'Strategic awareness',
                'skill3_icon': 'fas fa-brain',
                'skill4_name': 'PvP',
                'skill4_description': 'Combat effectiveness',
                'skill4_icon': 'fas fa-sword'
            },
            {
                'name': 'sumo',
                'display_name': 'Sumo',
                'description': 'Knockback-based combat',
                'icon': 'fas fa-hand-rock',
                'color': '#e67e22',
                'skill1_name': 'Gamesense',
                'skill1_description': 'Strategic thinking and positioning',
                'skill1_icon': 'fas fa-brain',
                'skill2_name': 'KB control',
                'skill2_description': 'Knockback manipulation and resistance',
                'skill2_icon': 'fas fa-hand-paper',
                'skill3_name': 'Mechanics',
                'skill3_description': 'Technical execution and timing',
                'skill3_icon': 'fas fa-cogs',
                'skill4_name': 'Movement',
                'skill4_description': 'Positioning and mobility',
                'skill4_icon': 'fas fa-running'
            },
            {
                'name': 'fireball_fight',
                'display_name': 'Fireball Fight',
                'description': 'Projectile-based combat',
                'icon': 'fas fa-fire-alt',
                'color': '#e74c3c',
                'skill1_name': 'Attack/Defense',
                'skill1_description': 'Offensive and defensive strategies',
                'skill1_icon': 'fas fa-shield-alt',
                'skill2_name': 'Fireball usage',
                'skill2_description': 'Projectile accuracy and timing',
                'skill2_icon': 'fas fa-fire-alt',
                'skill3_name': 'Gamesense',
                'skill3_description': 'Strategic awareness',
                'skill3_icon': 'fas fa-brain',
                'skill4_name': 'PvP',
                'skill4_description': 'Combat effectiveness',
                'skill4_icon': 'fas fa-sword'
            },
            {
                'name': 'bridge',
                'display_name': 'Bridge',
                'description': 'Classic bridge building and combat',
                'icon': 'fas fa-bridge',
                'color': '#27ae60',
                'skill1_name': 'Bypassing',
                'skill1_description': 'Efficient bridging techniques',
                'skill1_icon': 'fas fa-forward',
                'skill2_name': 'Defense',
                'skill2_description': 'Defensive positioning and blocking',
                'skill2_icon': 'fas fa-shield',
                'skill3_name': 'Gamesense',
                'skill3_description': 'Strategic awareness',
                'skill3_icon': 'fas fa-brain',
                'skill4_name': 'PvP',
                'skill4_description': 'Combat effectiveness',
                'skill4_icon': 'fas fa-sword'
            }
        ]
        
        for mode_data in default_modes:
            existing = cls.query.filter_by(name=mode_data['name']).first()
            if not existing:
                mode = cls(**mode_data)
                db.session.add(mode)
        
        db.session.commit()

class Player(db.Model):
    """Enhanced model for storing detailed player Bedwars statistics"""

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(100), nullable=False, unique=True)
    kills = db.Column(db.Integer, default=0, nullable=False)
    final_kills = db.Column(db.Integer, default=0, nullable=False)
    deaths = db.Column(db.Integer, default=0, nullable=False)
    final_deaths = db.Column(db.Integer, default=0, nullable=False)
    beds_broken = db.Column(db.Integer, default=0, nullable=False)
    games_played = db.Column(db.Integer, default=0, nullable=False)
    wins = db.Column(db.Integer, default=0, nullable=False)
    experience = db.Column(db.Integer, default=0, nullable=False)
    role = db.Column(db.String(50), default='Игрок', nullable=False)
    server_ip = db.Column(db.String(100), default='', nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # New fields for enhanced statistics
    iron_collected = db.Column(db.Integer, default=0, nullable=False)
    gold_collected = db.Column(db.Integer, default=0, nullable=False)
    diamond_collected = db.Column(db.Integer, default=0, nullable=False)
    emerald_collected = db.Column(db.Integer, default=0, nullable=False)
    items_purchased = db.Column(db.Integer, default=0, nullable=False)

    # Minecraft skin system
    skin_url = db.Column(db.String(255), nullable=True)  # Custom skin URL from NameMC
    skin_type = db.Column(db.String(10), default='auto', nullable=False)  # auto, steve, alex, custom
    is_premium = db.Column(db.Boolean, default=False, nullable=False)  # Licensed Minecraft account

    # Personal profile information
    real_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    discord_tag = db.Column(db.String(50), nullable=True)
    youtube_channel = db.Column(db.String(100), nullable=True)
    twitch_channel = db.Column(db.String(100), nullable=True)
    favorite_server = db.Column(db.String(100), nullable=True)
    favorite_map = db.Column(db.String(100), nullable=True)
    preferred_gamemode = db.Column(db.String(50), nullable=True)
    profile_banner_color = db.Column(db.String(7), default='#3498db', nullable=True)
    profile_is_public = db.Column(db.Boolean, default=True, nullable=False)
    custom_status = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    birthday = db.Column(db.Date, nullable=True)

    # Custom profile customization
    custom_avatar_url = db.Column(db.String(255), nullable=True)
    custom_banner_url = db.Column(db.String(255), nullable=True)
    banner_is_animated = db.Column(db.Boolean, default=False, nullable=False)

    # Extended social networks
    social_networks = db.Column(db.Text, nullable=True)  # JSON array of social networks

    # Profile section backgrounds
    stats_section_color = db.Column(db.String(7), default='#343a40', nullable=True)
    info_section_color = db.Column(db.String(7), default='#343a40', nullable=True)
    social_section_color = db.Column(db.String(7), default='#343a40', nullable=True)
    prefs_section_color = db.Column(db.String(7), default='#343a40', nullable=True)

    # Password system
    password_hash = db.Column(db.String(255), nullable=True)
    has_password = db.Column(db.Boolean, default=False, nullable=False)

    # Theme system
    selected_theme_id = db.Column(db.Integer, db.ForeignKey('site_theme.id'), nullable=True)
    selected_theme = db.relationship('SiteTheme', backref='users')

    # Leaderboard customization
    leaderboard_name_color = db.Column(db.String(7), default='#ffffff', nullable=True)
    leaderboard_stats_color = db.Column(db.String(7), default='#ffffff', nullable=True)
    leaderboard_use_gradient = db.Column(db.Boolean, default=False, nullable=False)
    leaderboard_gradient_start = db.Column(db.String(7), default='#ff6b35', nullable=True)
    leaderboard_gradient_end = db.Column(db.String(7), default='#f7931e', nullable=True)
    leaderboard_gradient_animated = db.Column(db.Boolean, default=False, nullable=False)

    # Inventory system
    inventory_data = db.Column(db.Text, nullable=True)  # JSON data for player inventory

    # Relationships for quest system
    player_quests = db.relationship('PlayerQuest', backref='player', lazy=True, cascade='all, delete-orphan')
    player_achievements = db.relationship('PlayerAchievement', backref='player', lazy=True, cascade='all, delete-orphan')

    # Economy system fields
    coins = db.Column(db.Integer, default=0, nullable=False)
    reputation = db.Column(db.Integer, default=0, nullable=False)

    # Karma system fields (NEW)
    karma = db.Column(db.Integer, default=0, nullable=False)

    # Custom role system
    custom_role = db.Column(db.String(100), nullable=True)
    custom_role_color = db.Column(db.String(7), nullable=True)
    custom_role_gradient = db.Column(db.Text, nullable=True)
    custom_role_emoji = db.Column(db.String(10), nullable=True)
    custom_role_animated = db.Column(db.Boolean, default=False, nullable=False)
    custom_role_purchased = db.Column(db.Boolean, default=False, nullable=False)
    custom_emoji_slots = db.Column(db.Integer, default=0, nullable=False) # Added for custom emoji slots

    # Cursor customization removed for stability

    @property
    def active_custom_title(self):
        """Get player's active custom title"""
        player_title = PlayerTitle.query.filter_by(
            player_id=self.id,
            is_active=True
        ).first()
        return player_title.title if player_title else None

    def get_gradient_for_element(self, element_type):
        """Get gradient setting for specific element type"""
        setting = PlayerGradientSetting.query.filter_by(
            player_id=self.id,
            element_type=element_type,
            is_enabled=True
        ).first()
        return setting.css_gradient if setting else None

    @property
    def nickname_gradient(self):
        """Get nickname gradient CSS"""
        return self.get_gradient_for_element('nickname')

    @property
    def stats_gradient(self):
        """Get stats gradient CSS"""
        return self.get_gradient_for_element('stats')

    @property
    def title_gradient(self):
        """Get title gradient CSS"""
        return self.get_gradient_for_element('title')

    @property
    def kills_gradient(self):
        """Get kills gradient CSS"""
        return self.get_gradient_for_element('kills')

    @property
    def deaths_gradient(self):
        """Get deaths gradient CSS"""
        return self.get_gradient_for_element('deaths')

    @property
    def wins_gradient(self):
        """Get wins gradient CSS"""
        return self.get_gradient_for_element('wins')

    @property
    def beds_gradient(self):
        """Get beds gradient CSS"""
        return self.get_gradient_for_element('beds')

    @property
    def status_gradient(self):
        """Get status gradient CSS"""
        return self.get_gradient_for_element('status')

    @property
    def bio_gradient(self):
        """Get bio gradient CSS"""
        return self.get_gradient_for_element('bio')

    @property
    def role_gradient(self):
        """Get role gradient CSS"""
        return self.get_gradient_for_element('role')

    @property
    def can_use_static_gradients(self):
        """Check if player can use static gradients (level 80+)"""
        return self.level >= 80

    @property
    def can_use_animated_gradients(self):
        """Check if player can use animated gradients (level 150+)"""
        return self.level >= 150

    @property
    def can_customize_colors(self):
        """Check if player can customize interface colors (level 40+)"""
        return self.level >= 40

    @property
    def can_use_custom_avatars(self):
        """Check if player can use custom avatars (level 20+)"""
        return self.level >= 20

    @property
    def can_use_animated_avatars(self):
        """Check if player can use animated avatars (level 70+)"""
        return self.level >= 70

    @property
    def can_use_custom_banners(self):
        """Check if player can use custom banners (level 30+)"""
        return self.level >= 30

    @property
    def can_use_animated_banners(self):
        """Check if player can use animated banners (level 135+)"""
        return self.level >= 135

    @property
    def can_use_leaderboard_gradients(self):
        """Check if player can use gradients in leaderboard (level 50+)"""
        return self.level >= 50

    @property
    def can_use_leaderboard_animated_gradients(self):
        """Check if player can use animated gradients in leaderboard (level 75+)"""
        return self.level >= 75

    @property
    def can_buy_basic_custom_role(self):
        """Check if player can buy basic custom role (level 10+)"""
        return self.level >= 10

    @property
    def can_buy_gradient_custom_role(self):
        """Check if player can buy gradient custom role (level 40+)"""
        return self.level >= 40

    @property
    def can_set_free_custom_role(self):
        """Check if player can set free custom role (level 500+)"""
        return self.level >= 500

    @property
    def active_admin_role(self):
        """Get player's active admin custom role"""
        try:
            from models import PlayerAdminRole
            admin_role = PlayerAdminRole.query.filter_by(
                player_id=self.id,
                is_active=True
            ).first()
            return admin_role if admin_role else None
        except Exception:
            return None

    @property
    def all_admin_roles(self):
        """Get all admin roles assigned to player"""
        return PlayerAdminRole.query.filter_by(player_id=self.id).all()



    @property
    def visible_badges(self):
        """Get all visible badges assigned to player"""
        try:
            from models import PlayerBadge, Badge
            return PlayerBadge.query.filter_by(
                player_id=self.id,
                is_visible=True
            ).join(Badge).filter(Badge.is_active == True).all()
        except Exception:
            return []

    @property
    def display_role(self):
        """Get the role to display - simplified logic"""
        # Priority 1: Admin role if assigned
        if hasattr(self, 'active_admin_role') and self.active_admin_role:
            return self.active_admin_role.role.name
        # Priority 2: Regular role
        return self.role

    @property
    def effective_role_data(self):
        """Get complete role data for display - simplified"""
        # Check for admin role first
        if hasattr(self, 'active_admin_role') and self.active_admin_role:
            admin_role = self.active_admin_role
            return {
                'type': 'admin',
                'name': admin_role.role.name,
                'color': admin_role.role.color,
                'emoji': getattr(admin_role.role, 'emoji', ''),
                'has_gradient': getattr(admin_role.role, 'has_gradient', False),
                'gradient_end_color': getattr(admin_role.role, 'gradient_end_color', None)
            }
        # Default role
        else:
            return {
                'type': 'default',
                'name': self.role,
                'color': '#ffc107',
                'has_gradient': False
            }

    @property
    def role_display_html(self):
        """Get HTML for role display with gradients and styling"""
        role_name = self.display_role

        # Check for active admin role styling
        if hasattr(self, 'active_admin_role') and self.active_admin_role:
            admin_role = self.active_admin_role
            style_parts = []
            fallback_color = admin_role.role_color if admin_role.role_color else "#ffc107"

            if admin_role.role_gradient and admin_role.role_gradient_start and admin_role.role_gradient_end:
                gradient = f"linear-gradient(45deg, {admin_role.role_gradient_start}, {admin_role.role_gradient_end})"
                style_parts.extend([
                    f"background: {gradient}",
                    "background-size: 200% 200%" if admin_role.role_gradient_animated else "background-size: 100% 100%",
                    "-webkit-background-clip: text",
                    "-webkit-text-fill-color: transparent",
                    "background-clip: text"
                ])
                if admin_role.role_gradient_animated:
                    style_parts.append("animation: gradientShift 3s ease-in-out infinite")

                style_attr = f'style="{"; ".join(style_parts)}"'
                emoji_part = f"{admin_role.role_emoji} " if admin_role.role_emoji else ""
                return f'<span class="role-display admin-role gradient-role" {style_attr} data-fallback-color="{fallback_color}">{emoji_part}{role_name}</span>'
            elif admin_role.role_color:
                style_parts.append(f"color: {admin_role.role_color}")
                style_attr = f'style="{"; ".join(style_parts)}"'
                emoji_part = f"{admin_role.role_emoji} " if admin_role.role_emoji else ""
                return f'<span class="role-display admin-role" {style_attr}>{emoji_part}{role_name}</span>'
            else:
                emoji_part = f"{admin_role.role_emoji} " if admin_role.role_emoji else ""
                return f'<span class="role-display admin-role">{emoji_part}{role_name}</span>'

        # Check for custom role styling
        elif hasattr(self, 'custom_role_purchased') and self.custom_role_purchased:
            style_parts = []
            fallback_color = self.custom_role_color if self.custom_role_color else "#ffc107"

            if self.custom_role_gradient:
                style_parts.extend([
                    f"background: {self.custom_role_gradient}",
                    "background-size: 200% 200%" if self.custom_role_animated else "background-size: 100% 100%",
                    "-webkit-background-clip: text",
                    "-webkit-text-fill-color: transparent",
                    "background-clip: text"
                ])
                if self.custom_role_animated:
                    style_parts.append("animation: gradientShift 3s ease-in-out infinite")

                style_attr = f'style="{"; ".join(style_parts)}"'
                emoji_part = f"{self.custom_role_emoji} " if self.custom_role_emoji else ""
                return f'<span class="role-display custom-role gradient-role" {style_attr} data-fallback-color="{fallback_color}">{emoji_part}{role_name}</span>'
            elif self.custom_role_color:
                style_parts.append(f"color: {self.custom_role_color}")
                style_attr = f'style="{"; ".join(style_parts)}"'
                emoji_part = f"{self.custom_role_emoji} " if self.custom_role_emoji else ""
                return f'<span class="role-display custom-role" {style_attr}>{emoji_part}{role_name}</span>'
            else:
                emoji_part = f"{self.custom_role_emoji} " if self.custom_role_emoji else ""
                return f'<span class="role-display custom-role">{emoji_part}{role_name}</span>'

        # Check for role gradient (from gradient system)
        elif self.role_gradient:
            style_parts = [
                f"background: {self.role_gradient}",
                "background-size: 200% 200%",
                "-webkit-background-clip: text",
                "-webkit-text-fill-color: transparent",
                "background-clip: text"
            ]
            if hasattr(self, 'can_use_animated_gradients') and self.can_use_animated_gradients:
                style_parts.append("animation: gradientShift 3s ease-in-out infinite")

            style_attr = f'style="{"; ".join(style_parts)}"'
            return f'<span class="role-display default_gradient-role gradient-role" {style_attr} data-fallback-color="#ffc107">{role_name}</span>'

        # Default role display
        return f'<span class="role-display default-role">{role_name}</span>'

    @property
    def nickname_display_html(self):
        """Get HTML for nickname display with gradients"""
        nickname = self.nickname
        gradient = self.nickname_gradient

        if gradient:
            style_parts = [
                f"background: {gradient}",
                "background-size: 200% 200%",
                "-webkit-background-clip: text",
                "-webkit-text-fill-color: transparent",
                "background-clip: text"
            ]

            # Check if gradient should be animated (level 150+)
            if self.can_use_animated_gradients:
                style_parts.append("animation: gradientShift 3s ease-in-out infinite")

            style_attr = f'style="{"; ".join(style_parts)}"'
            return f'<span class="nickname-display gradient-nickname" {style_attr}>{nickname}</span>'

        return f'<span class="nickname-display">{nickname}</span>'

    @property
    def can_set_free_custom_role_progress(self):
        """Get progress towards free custom role unlock (level 500)"""
        if self.level >= 500:
            return 100
        return round((self.level / 500) * 100, 1)

    def get_social_networks_list(self):
        """Get parsed social networks list"""
        if not self.social_networks:
            return []
        try:
            import json
            return json.loads(self.social_networks)
        except:
            return []

    def set_social_networks_list(self, networks_list):
        """Set social networks list"""
        import json
        self.social_networks = json.dumps(networks_list) if networks_list else None

    def get_inventory(self):
        """Get parsed inventory data"""
        if not self.inventory_data:
            return {}
        try:
            import json
            return json.loads(self.inventory_data)
        except:
            return {}

    def set_inventory(self, inventory_dict):
        """Set inventory data"""
        import json
        self.inventory_data = json.dumps(inventory_dict) if inventory_dict else None

    def add_inventory_item(self, item_type, item_id, quantity=1):
        """Add item to player inventory"""
        inventory = self.get_inventory()
        if item_type not in inventory:
            inventory[item_type] = {}

        if item_id in inventory[item_type]:
            inventory[item_type][item_id] += quantity
        else:
            inventory[item_type][item_id] = quantity

        self.set_inventory(inventory)

    def remove_inventory_item(self, item_type, item_id, quantity=1):
        """Remove item from player inventory"""
        inventory = self.get_inventory()
        if item_type in inventory and item_id in inventory[item_type]:
            inventory[item_type][item_id] -= quantity
            if inventory[item_type][item_id] <= 0:
                del inventory[item_type][item_id]
            if not inventory[item_type]:
                del inventory[item_type]
            self.set_inventory(inventory)
            return True
        return False

    def get_inventory_item_count(self, item_type, item_id):
        """Get count of specific item in inventory"""
        inventory = self.get_inventory()
        return inventory.get(item_type, {}).get(item_id, 0)

    def get_badges(self):
        """Get all badges assigned to player (for template compatibility)"""
        try:
            return PlayerBadge.query.filter_by(player_id=self.id).all()
        except Exception:
            return []

    def __repr__(self):
        return f'<Player {self.nickname}: Level {self.level} ({self.experience} XP)>'

    @property
    def kd_ratio(self):
        """Calculate kill/death ratio"""
        if self.deaths == 0:
            return self.kills if self.kills > 0 else 0
        return round(self.kills / self.deaths, 2)

    @property
    def fkd_ratio(self):
        """Calculate final kill/death ratio"""
        if self.final_deaths == 0:
            return self.final_kills if self.final_kills > 0 else 0
        return round(self.final_kills / self.final_deaths, 2)

    @property
    def win_rate(self):
        """Calculate win rate percentage"""
        if self.games_played == 0:
            return 0
        return round((self.wins / self.games_played) * 100, 1)

    @property
    def level(self):
        """Calculate player level based on Hypixel experience system"""
        # Hypixel level thresholds
        level_thresholds = [
            0, 10000, 22500, 37500, 55000, 75000, 97500, 122500, 150000, 180000,
            212500, 247500, 285000, 325000, 367500, 412500, 460000, 510000, 562500, 617500,
            675000, 735000, 797500, 862500, 930000, 1000000, 1072500, 1147500, 1225000, 1305000,
            1387500, 1472500, 1560000, 1650000, 1742500, 1837500, 1935000, 2035000, 2137500, 2242500,
            2350000, 2460000, 2572500, 2687500, 2805000, 2925000, 3047500, 3172500, 3300000, 3430000,
            3562500, 3697500, 3835000, 3975000, 4117500, 4262500, 4410000, 4560000, 4712500, 4867500,
            5025000, 5185000, 5347500, 5512500, 5680000, 5850000, 6022500, 6197500, 6375000, 6555000,
            6737500, 6922500, 7110000, 7300000, 7492500, 7687500, 7885000, 8085000, 8287500, 8492500,
            8700000, 8910000, 9122500, 9337500, 9555000, 9775000, 9997500, 10222500, 10450000, 10680000,
            10912500, 11147500, 11385000, 11625000, 11867500, 12112500, 12360000, 12610000, 12862500, 13117500
        ]

        for level, threshold in enumerate(level_thresholds, 1):
            if self.experience < threshold:
                return max(1, level - 1)

        # For levels 100+, each level requires 2500 more XP than the previous
        if self.experience >= 13117500:
            additional_levels = (self.experience - 13117500) // 2500
            return min(1000, 100 + additional_levels)

        return 100

    @property
    def level_progress(self):
        """Calculate progress to next level as percentage"""
        current_level = self.level
        if current_level >= 1000:
            return 100

        # Hypixel level thresholds
        level_thresholds = [
            0, 10000, 22500, 37500, 55000, 75000, 97500, 122500, 150000, 180000,
            212500, 247500, 285000, 325000, 367500, 412500, 460000, 510000, 562500, 617500,
            675000, 735000, 797500, 862500, 930000, 1000000, 1072500, 1147500, 1225000, 1305000,
            1387500, 1472500, 1560000, 1650000, 1742500, 1837500, 1935000, 2035000, 2137500, 2242500,
            2350000, 2460000, 2572500, 2687500, 2805000, 2925000, 3047500, 3172500, 3300000, 3430000,
            3562500, 3697500, 3835000, 3975000, 4117500, 4262500, 4410000, 4560000, 4712500, 4867500,
            5025000, 5185000, 5347500, 5512500, 5680000, 5850000, 6022500, 6197500, 6375000, 6555000,
            6737500, 6922500, 7110000, 7300000, 7492500, 7687500, 7885000, 8085000, 8287500, 8492500,
            8700000, 8910000, 9122500, 9337500, 9555000, 9775000, 9997500, 10222500, 10450000, 10680000,
            10912500, 11147500, 11385000, 11625000, 11867500, 12112500, 12360000, 12610000, 12862500, 13117500
        ]

        if current_level <= 100:
            current_threshold = level_thresholds[current_level - 1] if current_level > 0 else 0
            next_threshold = level_thresholds[current_level] if current_level < len(level_thresholds) else level_thresholds[-1] + 2500
        else:
            # For levels 100+
            current_threshold = 13117500 + (current_level - 100) * 2500
            next_threshold = 13117500 + (current_level - 99) * 2500

        if next_threshold == current_threshold:
            return 100

        progress = ((self.experience - current_threshold) / (next_threshold - current_threshold)) * 100
        return min(100, max(0, round(progress, 1)))

    @property
    def total_resources(self):
        """Calculate total resources collected"""
        return self.iron_collected + self.gold_collected + self.diamond_collected + self.emerald_collected

    @property
    def star_rating(self):
        """Calculate star rating based on overall performance"""
        # Complex formula considering multiple factors
        base_score = 0

        # Level contribution (0-20 points)
        base_score += min(20, self.level * 0.5)

        # K/D ratio contribution (0-15 points)
        base_score += min(15, self.kd_ratio * 3)

        # Win rate contribution (0-15 points)
        base_score += min(15, self.win_rate * 0.15)

        # Bed breaking contribution (0-10 points)
        base_score += min(10, self.beds_broken * 0.1)

        # Final kills contribution (0-10 points)
        base_score += min(10, self.final_kills * 0.05)

        # Games played bonus (0-5 points for activity)
        base_score += min(5, self.games_played * 0.01)

        # Convert to 1-5 star rating
        return min(5, max(1, round(base_score / 13)))

    @property
    def minecraft_skin_url(self):
        """Get Minecraft skin URL based on skin type and settings"""
        # Use custom avatar if set
        if self.custom_avatar_url:
            return self.custom_avatar_url

        if self.skin_type == 'custom' and self.skin_url:
            return self.skin_url
        elif self.skin_type == 'steve':
            return 'https://mc-heads.net/avatar/steve/128'
        elif self.skin_type == 'alex':
            return 'https://mc-heads.net/avatar/alex/128'
        elif self.is_premium and self.nickname:
            # Try to get premium skin by nickname
            return f'https://mc-heads.net/avatar/{self.nickname}/128'
        else:
            # Default to steve/alex randomly based on nickname hash
            import hashlib
            hash_val = int(hashlib.md5(self.nickname.encode()).hexdigest(), 16)
            default_skin = 'alex' if hash_val % 2 else 'steve'
            return f'https://mc-heads.net/avatar/{default_skin}/128'

    def set_custom_skin(self, namemc_url):
        """Set custom skin from NameMC URL"""
        if namemc_url and 'namemc.com' in namemc_url:
            # Extract UUID or username from NameMC URL
            try:
                import re
                # Extract username from NameMC URL
                match = re.search(r'namemc\.com/profile/([^/]+)', namemc_url)
                if match:
                    username = match.group(1)
                    # Use Crafatar to get skin
                    self.skin_url = f'https://crafatar.com/avatars/{username}?size=128'
                    self.skin_type = 'custom'
                    return True
            except:
                pass
        return False

    @classmethod
    def get_leaderboard(cls, sort_by='experience', limit=50, offset=0):
        """Get top players ordered by specified field with error handling"""
        try:
            limit = min(max(1, limit), 100)  # Ensure reasonable limits
            offset = max(0, offset)

            if sort_by == 'experience':
                return cls.query.order_by(cls.experience.desc()).offset(offset).limit(limit).all()
            elif sort_by == 'kills':
                return cls.query.order_by(cls.kills.desc()).offset(offset).limit(limit).all()
            elif sort_by == 'final_kills':
                return cls.query.order_by(cls.final_kills.desc()).offset(offset).limit(limit).all()
            elif sort_by == 'beds_broken':
                return cls.query.order_by(cls.beds_broken.desc()).offset(offset).limit(limit).all()
            elif sort_by == 'wins':
                return cls.query.order_by(cls.wins.desc()).offset(offset).limit(limit).all()
            elif sort_by == 'level':
                all_players = cls.query.order_by(cls.experience.desc()).offset(offset).limit(limit * 2).all()
                return sorted(all_players, key=lambda p: p.level, reverse=True)[:limit]
            elif sort_by == 'kd_ratio':
                all_players = cls.query.order_by(cls.kills.desc()).offset(offset).limit(limit * 2).all()
                return sorted(all_players, key=lambda p: p.kd_ratio, reverse=True)[:limit]
            elif sort_by == 'win_rate':
                all_players = cls.query.filter(cls.games_played > 0).order_by(cls.wins.desc()).offset(offset).limit(limit * 2).all()
                return sorted(all_players, key=lambda p: p.win_rate, reverse=True)[:limit]
            elif sort_by == 'karma': # Added karma sorting
                return cls.query.order_by(cls.karma.desc()).offset(offset).limit(limit).all()
            else:
                return cls.query.order_by(cls.experience.desc()).offset(offset).limit(limit).all()
        except Exception as e:
            from app import app
            if "no such column" in str(e).lower():
                app.logger.error(f"Database schema error in leaderboard: {e}")
                app.logger.info("Database schema needs to be updated. Please restart the application.")
            else:
                app.logger.error(f"Error getting leaderboard: {e}")
            return []

    @classmethod
    def search_players(cls, query, limit=50, offset=0):
        """Search players by nickname with error handling"""
        try:
            if not query or len(query.strip()) < 1:
                return []

            limit = min(max(1, limit), 100)
            offset = max(0, offset)
            query = query.strip()[:50]  # Limit query length

            return cls.query.filter(cls.nickname.ilike(f'%{query}%')).offset(offset).limit(limit).all()
        except Exception as e:
            from app import app
            app.logger.error(f"Error searching players: {e}")
            return []

    @classmethod
    @lru_cache(maxsize=1)
    def _get_cached_statistics(cls):
        """Get cached statistics (internal method)"""
        try:
            total_players = cls.query.count()
        except Exception as e:
            from app import app
            if "no such column" in str(e).lower():
                app.logger.error(f"Database schema error in statistics: {e}")
                app.logger.info("Database schema needs to be updated. Please restart the application.")
            else:
                app.logger.error(f"Error getting statistics: {e}")
            # Return empty statistics if there's an error
            return {
                'total_players': 0,
                'total_kills': 0,
                'total_deaths': 0,
                'total_games': 0,
                'total_wins': 0,
                'total_beds_broken': 0,
                'average_level': 0,
                'total_coins': 0,
                'total_reputation': 0,
                'total_karma': 0, # Added karma
                'average_coins': 0,
                'average_reputation': 0,
                'average_karma': 0, # Added karma
                'top_player': None,
                'richest_player': None,
                'most_reputable_player': None,
                'most_karma_player': None # Added karma
            }

        if total_players == 0:
            return {
                'total_players': 0,
                'total_kills': 0,
                'total_deaths': 0,
                'total_games': 0,
                'total_wins': 0,
                'total_beds_broken': 0,
                'average_level': 0,
                'total_coins': 0,
                'total_reputation': 0,
                'total_karma': 0, # Added karma
                'average_coins': 0,
                'average_reputation': 0,
                'average_karma': 0, # Added karma
                'top_player': None,
                'richest_player': None,
                'most_reputable_player': None,
                'most_karma_player': None # Added karma
            }

        stats = db.session.query(
            func.sum(cls.kills).label('total_kills'),
            func.sum(cls.deaths).label('total_deaths'),
            func.sum(cls.games_played).label('total_games'),
            func.sum(cls.wins).label('total_wins'),
            func.sum(cls.beds_broken).label('total_beds_broken'),
            func.sum(cls.coins).label('total_coins'),
            func.sum(cls.reputation).label('total_reputation'),
            func.sum(cls.karma).label('total_karma'), # Added karma sum
            func.avg(cls.experience).label('average_experience'),
            func.avg(cls.coins).label('average_coins'),
            func.avg(cls.reputation).label('average_reputation'),
            func.avg(cls.karma).label('average_karma') # Added karma average
        ).first()

        top_player = cls.query.order_by(cls.experience.desc()).first()
        richest_player = cls.query.order_by(cls.coins.desc()).first()
        most_reputable_player = cls.query.order_by(cls.reputation.desc()).first()
        most_karma_player = cls.query.order_by(cls.karma.desc()).first() # Added karma player

        return {
            'total_players': total_players,
            'total_kills': int(stats.total_kills) if stats and stats.total_kills else 0,
            'total_deaths': int(stats.total_deaths) if stats and stats.total_deaths else 0,
            'total_games': int(stats.total_games) if stats and stats.total_games else 0,
            'total_wins': int(stats.total_wins) if stats and stats.total_wins else 0,
            'total_beds_broken': int(stats.total_beds_broken) if stats and stats.total_beds_broken else 0,
            'total_coins': int(stats.total_coins) if stats and stats.total_coins else 0,
            'total_reputation': int(stats.total_reputation) if stats and stats.total_reputation else 0,
            'total_karma': int(stats.total_karma) if stats and stats.total_karma else 0, # Added karma
            'average_level': round(stats.average_experience / 1000) if stats and stats.average_experience else 0,
            'average_coins': round(stats.average_coins) if stats and stats.average_coins else 0,
            'average_reputation': round(stats.average_reputation) if stats and stats.average_reputation else 0,
            'average_karma': round(stats.average_karma) if stats and stats.average_karma else 0, # Added karma
            'top_player': top_player,
            'richest_player': richest_player,
            'most_reputable_player': most_reputable_player,
            'most_karma_player': most_karma_player # Added karma
        }

    @classmethod
    def get_statistics(cls):
        """Get overall leaderboard statistics with caching"""
        return cls._get_cached_statistics()

    @classmethod
    def clear_statistics_cache(cls):
        """Clear statistics cache when data changes"""
        cls._get_cached_statistics.cache_clear()

    def calculate_auto_experience(self):
        """Calculate experience based on player statistics (improved formula)"""
        base_xp = 0

        # XP from kills (15 XP per kill - increased)
        base_xp += self.kills * 15

        # XP from final kills (75 XP per final kill - increased)
        base_xp += self.final_kills * 75

        # XP from beds broken (150 XP per bed - increased)
        base_xp += self.beds_broken * 150

        # XP from wins (300 XP per win - increased)
        base_xp += self.wins * 300

        # XP from games played (40 XP per game - increased)
        base_xp += self.games_played * 40

        # XP from resources collected (1 XP per 8 resources - improved ratio)
        base_xp += self.total_resources // 8

        # Bonus XP for good performance
        if self.kd_ratio >= 3.0:
            base_xp = int(base_xp * 1.4)  # 40% bonus for excellent K/D
        elif self.kd_ratio >= 2.0:
            base_xp = int(base_xp * 1.25)  # 25% bonus
        elif self.kd_ratio >= 1.5:
            base_xp = int(base_xp * 1.15)  # 15% bonus

        if self.win_rate >= 85:
            base_xp = int(base_xp * 1.5)  # 50% bonus for high win rate
        elif self.win_rate >= 75:
            base_xp = int(base_xp * 1.35)  # 35% bonus
        elif self.win_rate >= 50:
            base_xp = int(base_xp * 1.2)  # 20% bonus

        # Bonus for high bed destruction rate
        if self.games_played > 0:
            bed_rate = self.beds_broken / self.games_played
            if bed_rate >= 1.0:
                base_xp = int(base_xp * 1.2)  # 20% bonus for bed breaking

        return base_xp

    def update_stats(self, **kwargs):
        """Update player statistics and auto-calculate experience"""
        old_stats = {
            'kills': self.kills,
            'final_kills': self.final_kills,
            'beds_broken': self.beds_broken,
            'wins': self.wins,
            'games_played': self.games_played
        }

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # Only auto-update XP if stats changed significantly
        if any(getattr(self, key) != old_stats.get(key, 0) for key in old_stats):
            # Don't override manually set experience, just set a baseline
            calculated_xp = self.calculate_auto_experience()
            if self.experience < calculated_xp:
                self.experience = calculated_xp

        self.last_updated = datetime.utcnow()
        db.session.commit()
        return True

    @classmethod
    def add_player(cls, nickname, kills=0, final_kills=0, deaths=0, final_deaths=0, beds_broken=0,
                   games_played=0, wins=0, experience=0, role='Игрок', server_ip='',
                   iron_collected=0, gold_collected=0, diamond_collected=0,
                   emerald_collected=0, items_purchased=0, coins=0, reputation=0, karma=0): # Added karma
        """Add a new player to the leaderboard"""
        player = cls(
            nickname=nickname,
            kills=kills,
            final_kills=final_kills,
            deaths=deaths,
            final_deaths=final_deaths,
            beds_broken=beds_broken,
            games_played=games_played,
            wins=wins,
            experience=experience,
            role=role,
            server_ip=server_ip,
            iron_collected=iron_collected,
            gold_collected=gold_collected,
            diamond_collected=diamond_collected,
            emerald_collected=emerald_collected,
            items_purchased=items_purchased,
            coins=coins,
            reputation=reputation,
            karma=karma # Added karma
        )
        db.session.add(player)
        db.session.commit()
        return player


class Quest(db.Model):
    """Quest system for gamification"""

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # kills, beds, wins, etc.
    target_value = db.Column(db.Integer, nullable=False)
    reward_xp = db.Column(db.Integer, default=0)
    reward_coins = db.Column(db.Integer, default=0)
    reward_reputation = db.Column(db.Integer, default=0)
    reward_title = db.Column(db.String(100), nullable=True)
    icon = db.Column(db.String(50), default='fas fa-trophy')
    difficulty = db.Column(db.String(20), default='medium', nullable=False)  # easy, medium, hard, epic
    quest_category = db.Column(db.String(20), default='permanent', nullable=False)  # daily, weekly, monthly, thematic, mythic, permanent
    is_active = db.Column(db.Boolean, default=True)
    is_repeatable = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_refresh = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with player quest progress
    player_quests = db.relationship('PlayerQuest', backref='quest', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Quest {self.title}>'

    @property
    def completion_rate(self):
        """Calculate overall completion rate"""
        total_attempts = PlayerQuest.query.filter_by(quest_id=self.id).count()
        if total_attempts == 0:
            return 0
        completed = PlayerQuest.query.filter_by(quest_id=self.id, is_completed=True).count()
        return round((completed / total_attempts) * 100, 1)

    @classmethod
    def get_active_quests(cls):
        """Get all active quests"""
        return cls.query.filter_by(is_active=True).all()

    @classmethod
    def refresh_timed_quests(cls):
        """Refresh daily, weekly, and monthly quests"""
        from datetime import datetime, timedelta, date

        current_time = datetime.utcnow()
        current_date = current_time.date()

        # Check and refresh daily quests (check if it's a new day)
        daily_quests = cls.query.filter_by(quest_category='daily', is_active=True).all()
        for quest in daily_quests:
            if not quest.last_refresh or quest.last_refresh.date() < current_date:
                quest.last_refresh = current_time
                # Reset all player progress for this quest
                PlayerQuest.query.filter_by(quest_id=quest.id).update({
                    'is_completed': False,
                    'is_accepted': False,
                    'current_progress': 0,
                    'baseline_value': 0
                })

        # Check and refresh weekly quests (check if it's a new week - Monday)
        weekly_quests = cls.query.filter_by(quest_category='weekly', is_active=True).all()
        for quest in weekly_quests:
            if not quest.last_refresh:
                quest.last_refresh = current_time
                continue

            last_monday = current_date - timedelta(days=current_date.weekday())
            quest_monday = quest.last_refresh.date() - timedelta(days=quest.last_refresh.date().weekday())

            if quest_monday < last_monday:
                quest.last_refresh = current_time
                PlayerQuest.query.filter_by(quest_id=quest.id).update({
                    'is_completed': False,
                    'is_accepted': False,
                    'current_progress': 0,
                    'baseline_value': 0
                })

        # Check and refresh monthly quests (check if it's a new month)
        monthly_quests = cls.query.filter_by(quest_category='monthly', is_active=True).all()
        for quest in monthly_quests:
            if not quest.last_refresh:
                quest.last_refresh = current_time
                continue

            if (quest.last_refresh.year < current_time.year or
                (quest.last_refresh.year == current_time.year and quest.last_refresh.month < current_time.month)):
                quest.last_refresh = current_time
                PlayerQuest.query.filter_by(quest_id=quest.id).update({
                    'is_completed': False,
                    'is_accepted': False,
                    'current_progress': 0,
                    'baseline_value': 0
                })

        db.session.commit()

    @classmethod
    def create_default_quests(cls):
        """Create default quests for the game"""
        # Permanent quests
        permanent_quests = [
            {
                'title': 'Первая кровь',
                'description': 'Убейте 10 игроков в режиме Bedwars',
                'type': 'kills',
                'target_value': 10,
                'reward_xp': 1000,
                'reward_coins': 250,
                'reward_reputation': 10,
                'reward_title': 'Воин',
                'icon': 'fas fa-sword',
                'difficulty': 'easy',
                'quest_category': 'permanent',
                'is_repeatable': False
            },
            {
                'title': 'Разрушитель кроватей',
                'description': 'Сломайте 5 кроватей противников',
                'type': 'beds_broken',
                'target_value': 5,
                'reward_xp': 1500,
                'reward_coins': 300,
                'reward_reputation': 15,
                'reward_title': 'Разрушитель',
                'icon': 'fas fa-bed',
                'difficulty': 'easy',
                'quest_category': 'permanent',
                'is_repeatable': False
            },
        ]

        # Daily quests
        daily_quests = [
            {
                'title': 'Ежедневный воин',
                'description': 'Убейте 15 игроков сегодня',
                'type': 'kills',
                'target_value': 15,
                'reward_xp': 500,
                'reward_coins': 100,
                'reward_reputation': 5,
                'icon': 'fas fa-sword',
                'difficulty': 'easy',
                'quest_category': 'daily'
            },
            {
                'title': 'Ежедневная охота',
                'description': 'Совершите 5 финальных убийств',
                'type': 'final_kills',
                'target_value': 5,
                'reward_xp': 800,
                'reward_coins': 150,
                'reward_reputation': 8,
                'icon': 'fas fa-crosshairs',
                'difficulty': 'medium',
                'quest_category': 'daily'
            },
            {
                'title': 'Ежедневный разрушитель',
                'description': 'Сломайте 3 кровати',
                'type': 'beds_broken',
                'target_value': 3,
                'reward_xp': 600,
                'reward_coins': 120,
                'reward_reputation': 6,
                'icon': 'fas fa-bed',
                'difficulty': 'easy',
                'quest_category': 'daily'
            },
            {
                'title': 'Ежедневный победитель',
                'description': 'Выиграйте 2 игры',
                'type': 'wins',
                'target_value': 2,
                'reward_xp': 1000,
                'reward_coins': 200,
                'reward_reputation': 10,
                'icon': 'fas fa-trophy',
                'difficulty': 'medium',
                'quest_category': 'daily'
            },
            {
                'title': 'Ежедневный майнер',
                'description': 'Соберите 500 единиц железа',
                'type': 'iron_collected',
                'target_value': 500,
                'reward_xp': 400,
                'reward_coins': 80,
                'reward_reputation': 4,
                'icon': 'fas fa-hammer',
                'difficulty': 'easy',
                'quest_category': 'daily'
            }
        ]

        # Weekly quests
        weekly_quests = [
            {
                'title': 'Еженедельный воин',
                'description': 'Убейте 100 игроков за неделю',
                'type': 'kills',
                'target_value': 100,
                'reward_xp': 3000,
                'reward_coins': 750,
                'reward_reputation': 30,
                'icon': 'fas fa-sword',
                'difficulty': 'hard',
                'quest_category': 'weekly'
            },
            {
                'title': 'Мастер финальных убийств',
                'description': 'Совершите 25 финальных убийств',
                'type': 'final_kills',
                'target_value': 25,
                'reward_xp': 4000,
                'reward_coins': 1000,
                'reward_reputation': 40,
                'icon': 'fas fa-skull',
                'difficulty': 'hard',
                'quest_category': 'weekly'
            },
            {
                'title': 'Недельный чемпион',
                'description': 'Выиграйте 15 игр за неделю',
                'type': 'wins',
                'target_value': 15,
                'reward_xp': 5000,
                'reward_coins': 1250,
                'reward_reputation': 50,
                'icon': 'fas fa-crown',
                'difficulty': 'epic',
                'quest_category': 'weekly'
            }
        ]

        # Monthly quests
        monthly_quests = [
            {
                'title': 'Легенда месяца',
                'description': 'Убейте 500 игроков за месяц',
                'type': 'kills',
                'target_value': 500,
                'reward_xp': 15000,
                'reward_coins': 3000,
                'reward_reputation': 150,
                'icon': 'fas fa-fire',
                'difficulty': 'epic',
                'quest_category': 'monthly'
            },
            {
                'title': 'Разрушитель империй',
                'description': 'Сломайте 100 кроватей за месяц',
                'type': 'beds_broken',
                'target_value': 100,
                'reward_xp': 12000,
                'reward_coins': 2500,
                'reward_reputation': 120,
                'icon': 'fas fa-meteor',
                'difficulty': 'epic',
                'quest_category': 'monthly'
            },
            {
                'title': 'Непобедимый',
                'description': 'Выиграйте 50 игр за месяц',
                'type': 'wins',
                'target_value': 50,
                'reward_xp': 20000,
                'reward_coins': 4000,
                'reward_reputation': 200,
                'reward_title': 'Непобедимый',
                'icon': 'fas fa-crown',
                'difficulty': 'epic',
                'quest_category': 'monthly'
            }
        ]

        # Thematic quests (one-time only)
        thematic_quests = [
            {
                'title': 'Рождественское чудо',
                'description': 'Выиграйте 25 игр в рождественский сезон',
                'type': 'wins',
                'target_value': 25,
                'reward_xp': 10000,
                'reward_coins': 2000,
                'reward_reputation': 100,
                'reward_role': 'Рождественский герой',
                'icon': 'fas fa-gifts',
                'difficulty': 'epic',
                'quest_category': 'thematic',
                'is_repeatable': False
            },
            {
                'title': 'Хэллоуинский кошмар',
                'description': 'Совершите 100 финальных убийств в октябре',
                'type': 'final_kills',
                'target_value': 100,
                'reward_xp': 12000,
                'reward_coins': 2500,
                'reward_reputation': 120,
                'reward_role': 'Призрак Хэллоуина',
                'icon': 'fas fa-ghost',
                'difficulty': 'epic',
                'quest_category': 'thematic',
                'is_repeatable': False
            }
        ]

        # Mythic quests (ultra rare, one-time only)
        mythic_quests = [
            {
                'title': 'Властелин Bedwars',
                'description': 'Достигните 1000 побед и K/D 5.0',
                'type': 'wins',
                'target_value': 1000,
                'reward_xp': 50000,
                'reward_coins': 10000,
                'reward_reputation': 500,
                'reward_role': 'Властелин Bedwars',
                'reward_title': 'Властелин',
                'icon': 'fas fa-dragon',
                'difficulty': 'mythic',
                'quest_category': 'mythic',
                'is_repeatable': False
            },
            {
                'title': 'Божество разрушения',
                'description': 'Сломайте 2000 кроватей',
                'type': 'beds_broken',
                'target_value': 2000,
                'reward_xp': 75000,
                'reward_coins': 15000,
                'reward_reputation': 750,
                'reward_role': 'Божество разрушения',
                'reward_title': 'Разрушитель миров',
                'icon': 'fas fa-meteor',
                'difficulty': 'mythic',
                'quest_category': 'mythic',
                'is_repeatable': False
            }
        ]

        all_quests = permanent_quests + daily_quests + weekly_quests + monthly_quests + thematic_quests + mythic_quests

        for quest_data in all_quests:
            existing = cls.query.filter_by(title=quest_data['title']).first()
            if not existing:
                quest = cls(**quest_data)
                db.session.add(quest)

        db.session.commit()


class PlayerQuest(db.Model):
    """Player progress on quests"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False)
    current_progress = db.Column(db.Integer, default=0)
    baseline_value = db.Column(db.Integer, default=0)  # Starting value when quest was accepted
    is_completed = db.Column(db.Boolean, default=False)
    is_accepted = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    accepted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<PlayerQuest {self.player_id}:{self.quest_id}>'

    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        quest_obj = Quest.query.get(self.quest_id)
        if not quest_obj or quest_obj.target_value == 0:
            return 100
        return min(100, round((self.current_progress / quest_obj.target_value) * 100))

    def check_completion(self, player_stat_value):
        """Check if quest should be completed"""
        # Calculate progress from baseline
        progress_from_baseline = max(0, player_stat_value - self.baseline_value)
        self.current_progress = progress_from_baseline
        quest_obj = Quest.query.get(self.quest_id)

        if not self.is_completed and quest_obj and self.current_progress >= quest_obj.target_value:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
            return True
        return False

    @classmethod
    def update_player_quest_progress(cls, player):
        """Update quest progress only for accepted quests"""
        completed_quests = []

        # Only update progress for accepted quests
        accepted_quests = cls.query.filter_by(
            player_id=player.id,
            is_accepted=True,
            is_completed=False
        ).all()

        for player_quest in accepted_quests:
            quest = player_quest.quest

            # Get current stat value
            current_stat_value = getattr(player, quest.type, 0)

            # Check completion based on progress from baseline
            if player_quest.check_completion(current_stat_value):
                completed_quests.append(quest)

                # Award XP only, don't auto-assign title or role
                player.experience += quest.reward_xp

        if completed_quests:
            db.session.commit()

        return completed_quests


class ShopItem(db.Model):
    """Shop items for purchase"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # title, theme, gradient, avatar, cursor
    price_coins = db.Column(db.Integer, default=0, nullable=False)
    price_reputation = db.Column(db.Integer, default=0, nullable=False)
    unlock_level = db.Column(db.Integer, default=1, nullable=False)
    rarity = db.Column(db.String(20), default='common', nullable=False)
    icon = db.Column(db.String(50), default='fas fa-star', nullable=False)
    image_url = db.Column(db.String(500), nullable=True)  # URL for item image
    item_data = db.Column(db.Text, nullable=True)  # JSON data for item effects
    is_limited_time = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    purchases = db.relationship('ShopPurchase', backref='item', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ShopItem {self.display_name}>'

    def can_purchase(self, player):
        """Check if player can purchase this item"""
        # Check level requirement
        if player.level < self.unlock_level:
            return False, f"Требуется {self.unlock_level} уровень"

        # Check if player has enough resources
        if player.coins < self.price_coins:
            return False, "Недостаточно койнов"

        if player.reputation < self.price_reputation:
            return False, "Недостаточно репутации"

        # Check if already purchased (for non-consumable items)
        if self.category in ['title', 'theme', 'cursor', 'avatar']:
            existing = ShopPurchase.query.filter_by(
                player_id=player.id,
                item_id=self.id
            ).first()
            if existing:
                return False, "Уже приобретено"

        return True, "OK"

    def apply_item_effect(self, player):
        """Apply item effect to player"""
        try:
            import json
            data = json.loads(self.item_data) if self.item_data else {}

            if self.category == 'custom_role':
                # Enable custom role for player
                role_type = data.get('role_type', 'basic')
                player.custom_role_purchased = True
                # Set default role if not set
                if not player.custom_role:
                    player.custom_role = f"Кастомная роль"

            elif self.category == 'emoji_slot':
                # Add emoji slots to player
                emoji_slots = data.get('emoji_slots', 1)
                if not hasattr(player, 'custom_emoji_slots'):
                    player.custom_emoji_slots = 0
                player.custom_emoji_slots += emoji_slots

            elif self.category == 'title':
                # Create or find existing custom title
                title_text = data.get('title_text', self.display_name)
                existing_title = CustomTitle.query.filter_by(name=title_text.lower().replace(' ', '_')).first()

                if not existing_title:
                    title = CustomTitle(
                        name=title_text.lower().replace(' ', '_'),
                        display_name=title_text,
                        color=data.get('title_color', '#ffd700'),
                        glow_color=data.get('title_color', '#ffd700')
                    )
                    db.session.add(title)
                    db.session.flush()
                    title_id = title.id
                else:
                    title_id = existing_title.id

                # Check if player already has this title
                existing_player_title = PlayerTitle.query.filter_by(
                    player_id=player.id,
                    title_id=title_id
                ).first()

                if not existing_player_title:
                    # Deactivate other titles first
                    PlayerTitle.query.filter_by(player_id=player.id, is_active=True).update({'is_active': False})

                    # Assign to player
                    player_title = PlayerTitle(
                        player_id=player.id,
                        title_id=title_id,
                        is_active=True
                    )
                    db.session.add(player_title)

            elif self.category == 'booster':
                # Apply immediate booster effects
                booster_type = data.get('booster_type', 'xp')

                if booster_type == 'xp':
                    bonus_xp = data.get('bonus_amount', 1000)
                    player.experience += bonus_xp
                elif booster_type == 'coins':
                    bonus_coins = data.get('bonus_amount', 500)
                    player.coins += bonus_coins
                elif booster_type == 'reputation':
                    bonus_rep = data.get('bonus_amount', 100)
                    player.reputation += bonus_rep

            elif self.category == 'theme':
                # Apply theme to player (would need theme system implementation)
                theme_data = data.get('theme_colors', {})
                # For now, just add experience as reward
                player.experience += 500

            elif self.category == 'gradient':
                # Apply gradient theme to player
                gradient_css = data.get('gradient_css')
                is_animated = data.get('is_animated', False)
                if gradient_css:
                    # Find or create a GradientTheme entry
                    gradient_name = self.name # Use the item name as a unique identifier for the gradient
                    existing_gradient = GradientTheme.query.filter_by(name=gradient_name).first()

                    if not existing_gradient:
                        # Attempt to parse gradient CSS to extract colors and direction
                        # This is a simplified approach; a robust parser would be better
                        import re
                        match = re.search(r'linear-gradient\(([^,]+,\s*[^,]+,\s*[^)]+)\)', gradient_css)
                        if match:
                            gradient_parts = match.group(1).split(',')
                            gradient_direction = '45deg' # Default direction
                            colors = []
                            if len(gradient_parts) >= 2:
                                first_part = gradient_parts[0].strip()
                                if 'deg' in first_part or 'rad' in first_part or 'turn' in first_part:
                                    gradient_direction = first_part
                                    colors = [p.strip() for p in gradient_parts[1:]]
                                else:
                                    colors = [p.strip() for p in gradient_parts]

                                if len(colors) >= 2:
                                    existing_gradient = GradientTheme.query.filter_by(
                                        name=gradient_name,
                                        element_type='custom', # Assign a generic type for player-created gradients
                                        color1=colors[0],
                                        color2=colors[1],
                                        gradient_direction=gradient_direction,
                                        animation_enabled=is_animated
                                    ).first()

                                    if not existing_gradient:
                                        existing_gradient = GradientTheme(
                                            name=gradient_name,
                                            display_name=self.display_name,
                                            element_type='custom',
                                            color1=colors[0],
                                            color2=colors[1] if len(colors) > 1 else colors[0],
                                            color3=colors[2] if len(colors) > 2 else None,
                                            gradient_direction=gradient_direction,
                                            animation_enabled=is_animated,
                                            is_active=True
                                        )
                                        db.session.add(existing_gradient)
                                        db.session.flush()

                    if existing_gradient:
                        # Assign the gradient to the player for a specific element type (e.g., nickname, stats)
                        # This requires a more dynamic way to handle which element the gradient applies to.
                        # For now, we'll assume a default or that the player chooses later.
                        # Let's add a setting for 'nickname' as an example.
                        player_gradient_setting = PlayerGradientSetting.query.filter_by(
                            player_id=player.id,
                            element_type='nickname' # Default to nickname, or could be chosen by player
                        ).first()

                        if not player_gradient_setting:
                            player_gradient_setting = PlayerGradientSetting(
                                player_id=player.id,
                                element_type='nickname',
                                gradient_theme_id=existing_gradient.id,
                                is_enabled=True
                            )
                            db.session.add(player_gradient_setting)
                        else:
                            player_gradient_setting.gradient_theme_id = existing_gradient.id
                            player_gradient_setting.is_enabled = True

                        # Add experience as a reward for purchasing the gradient item
                        player.experience += 300


        except Exception as e:
            from app import app
            app.logger.error(f"Error applying item effect: {e}")
            # Continue execution even if there's an error

    @classmethod
    def create_default_items(cls):
        """Create default shop items"""
        # Titles
        default_items = [
            {
                'name': 'pro_gamer_title',
                'display_name': 'Про-Геймер',
                'description': 'Эксклюзивный титул для настоящих профессионалов',
                'category': 'title',
                'price_coins': 5000,
                'price_reputation': 100,
                'unlock_level': 25,
                'rarity': 'epic',
                'icon': 'fas fa-crown',
                'item_data': '{"title_text": "Про-Геймер", "title_color": "#6f42c1"}'
            },
            {
                'name': 'legend_title',
                'display_name': 'Легенда',
                'description': 'Титул для истинных легенд Bedwars',
                'category': 'title',
                'price_coins': 15000,
                'price_reputation': 500,
                'unlock_level': 50,
                'rarity': 'legendary',
                'icon': 'fas fa-dragon',
                'item_data': '{"title_text": "Легенда", "title_color": "#ff9800", "is_gradient": true, "gradient_colors": "linear-gradient(45deg, #ff9800, #ffc107)"}'
            },
            {
                'name': 'mythic_warrior_title',
                'display_name': 'Мифический Воин',
                'description': 'Сверхредкий титул для избранных',
                'category': 'title',
                'price_coins': 50000,
                'price_reputation': 2000,
                'unlock_level': 75,
                'rarity': 'mythic',
                'icon': 'fas fa-bolt',
                'item_data': '{"title_text": "Мифический Воин", "title_color": "#9400d3", "is_gradient": true, "gradient_colors": "linear-gradient(45deg, #9400d3, #4b0082, #0000ff)"}'
            },

            # Boosters
            {
                'name': 'xp_booster_small',
                'display_name': 'Малый бустер опыта',
                'description': 'Получите +1000 опыта мгновенно',
                'category': 'booster',
                'price_coins': 1000,
                'price_reputation': 0,
                'unlock_level': 1,
                'rarity': 'common',
                'item_data': '{"booster_type": "xp", "bonus_amount": 1000}'
            },
            {
                'name': 'xp_booster_large',
                'display_name': 'Большой бустер опыта',
                'description': 'Получите +10000 опыта мгновенно',
                'category': 'booster',
                'price_coins': 8000,
                'price_reputation': 0,
                'unlock_level': 10,
                'rarity': 'epic',
                'item_data': '{"booster_type": "xp", "bonus_amount": 10000}'
            },
            {
                'name': 'coin_booster',
                'display_name': 'Бустер койнов',
                'description': 'Получите +2500 койнов мгновенно',
                'category': 'booster',
                'price_coins': 3000,
                'price_reputation': 50,
                'unlock_level': 15,
                'rarity': 'uncommon',
                'item_data': '{"booster_type": "coins", "bonus_amount": 2500}'
            },
            {
                'name': 'reputation_booster',
                'display_name': 'Бустер репутации',
                'description': 'Получите +200 репутации мгновенно',
                'category': 'booster',
                'price_coins': 5000,
                'price_reputation': 0,
                'unlock_level': 20,
                'rarity': 'rare',
                'item_data': '{"booster_type": "reputation", "bonus_amount": 200}'
            },

            # Custom Roles
            {
                'name': 'basic_custom_role',
                'display_name': 'Обычная кастомная роль',
                'description': 'Создайте свою роль со статичным цветом',
                'category': 'custom_role',
                'price_coins': 5000,
                'price_reputation': 0,
                'unlock_level': 10,
                'rarity': 'common',
                'item_data': '{"role_type": "basic", "allows_color": true, "allows_gradient": false, "allows_animation": false, "allows_emoji": false}'
            },
            {
                'name': 'gradient_custom_role',
                'display_name': 'Особая роль с градиентом',
                'description': 'Роль с красивым градиентом',
                'category': 'custom_role',
                'price_coins': 50000,
                'price_reputation': 0,
                'unlock_level': 40,
                'rarity': 'epic',
                'item_data': '{"role_type": "gradient", "allows_color": true, "allows_gradient": true, "allows_animation": false, "allows_emoji": false}'
            },
            {
                'name': 'animated_custom_role',
                'display_name': 'Особая анимированная роль',
                'description': 'Роль с анимированным градиентом и эмодзи',
                'category': 'custom_role',
                'price_coins': 75000,
                'price_reputation': 0,
                'unlock_level': 40,
                'rarity': 'legendary',
                'item_data': '{"role_type": "animated", "allows_color": true, "allows_gradient": true, "allows_animation": true, "allows_emoji": true}'
            },
            {
                'name': 'premium_animated_custom_role',
                'display_name': 'Премиум анимированная роль',
                'description': 'Топовая роль с максимальными возможностями',
                'category': 'custom_role',
                'price_coins': 100000,
                'price_reputation': 0,
                'unlock_level': 40,
                'rarity': 'mythic',
                'item_data': '{"role_type": "premium", "allows_color": true, "allows_gradient": true, "allows_animation": true, "allows_emoji": true}'
            },
             {
                'name': 'emoji_slot_basic',
                'display_name': 'Слот для эмодзи (базовый)',
                'description': 'Добавляет 1 слот для кастомного эмодзи к роли',
                'category': 'emoji_slot',
                'price_coins': 10000,
                'price_reputation': 200,
                'unlock_level': 10,
                'rarity': 'uncommon',
                'item_data': '{"emoji_slots": 1}'
            },
            {
                'name': 'emoji_slot_premium',
                'display_name': 'Слот для эмодзи (премиум)',
                'description': 'Добавляет 2 слота для кастомного эмодзи к роли',
                'category': 'emoji_slot',
                'price_coins': 25000,
                'price_reputation': 500,
                'unlock_level': 30,
                'rarity': 'rare',
                'item_data': '{"emoji_slots": 2}'
            },
            {
                'name': 'emoji_slot_legendary',
                'display_name': 'Слот для эмодзи (легендарный)',
                'description': 'Добавляет 3 слота для кастомного эмодзи к роли',
                'category': 'emoji_slot',
                'price_coins': 50000,
                'price_reputation': 1000,
                'unlock_level': 50,
                'rarity': 'legendary',
                'item_data': '{"emoji_slots": 3}'
            },

            # Themes
            {
                'name': 'neon_theme',
                'display_name': 'Неоновая тема',
                'description': 'Яркая неоновая тема оформления',
                'category': 'theme',
                'price_coins': 12000,
                'price_reputation': 300,
                'unlock_level': 30,
                'rarity': 'epic',
                'item_data': '{"theme_colors": {"primary": "#00ffff", "secondary": "#ff00ff"}}'
            },
            {
                'name': 'galaxy_theme',
                'display_name': 'Галактическая тема',
                'description': 'Космическая тема с эффектами галактики',
                'category': 'theme',
                'price_coins': 25000,
                'price_reputation': 800,
                'unlock_level': 60,
                'rarity': 'legendary',
                'item_data': '{"theme_colors": {"primary": "#483d8b", "secondary": "#9400d3"}}'
            },

            # Gradients for customization
            {
                'name': 'fire_gradient',
                'display_name': 'Огненный градиент',
                'description': 'Яркий огненный градиент для любого элемента',
                'category': 'gradient',
                'price_coins': 2500,
                'price_reputation': 50,
                'unlock_level': 15,
                'rarity': 'uncommon',
                'icon': 'fas fa-fire',
                'item_data': '{"gradient_css": "linear-gradient(45deg, #ff6b35, #f7931e, #ffaa00)", "is_animated": true}'
            },
            {
                'name': 'ocean_gradient',
                'display_name': 'Морской градиент',
                'description': 'Прохладный морской градиент',
                'category': 'gradient',
                'price_coins': 2000,
                'price_reputation': 30,
                'unlock_level': 10,
                'rarity': 'common',
                'icon': 'fas fa-water',
                'item_data': '{"gradient_css": "linear-gradient(45deg, #1e3c72, #3a7bd5)", "is_animated": false}'
            },
            {
                'name': 'rainbow_gradient',
                'display_name': 'Радужный градиент',
                'description': 'Яркий радужный градиент с анимацией',
                'category': 'gradient',
                'price_coins': 5000,
                'price_reputation': 100,
                'unlock_level': 25,
                'rarity': 'epic',
                'icon': 'fas fa-rainbow',
                'item_data': '{"gradient_css": "linear-gradient(45deg, #ff0000, #ffff00, #00ff00, #0000ff, #8b00ff)", "is_animated": true}'
            },
            {
                'name': 'galaxy_gradient',
                'display_name': 'Галактический градиент',
                'description': 'Космический градиент для избранных',
                'category': 'gradient',
                'price_coins': 15000,
                'price_reputation': 300,
                'unlock_level': 50,
                'rarity': 'legendary',
                'icon': 'fas fa-star',
                'item_data': '{"gradient_css": "linear-gradient(45deg, #2c3e50, #4a6741, #9b59b6, #e74c3c)", "is_animated": true}'
            },
            # Custom Roles
            {
                'name': 'gradient_custom_role',
                'display_name': 'Особая роль с градиентом',
                'description': 'Роль с красивым градиентом',
                'category': 'custom_role',
                'price_coins': 50000,
                'price_reputation': 0,
                'unlock_level': 40,
                'rarity': 'epic',
                'item_data': '{"role_type": "gradient", "allows_color": true, "allows_gradient": true, "allows_animation": false, "allows_emoji": false}'
            },
        ]

        for item_data in default_items:
            existing = cls.query.filter_by(name=item_data['name']).first()
            if not existing:
                item = cls(**item_data)
                db.session.add(item)

        db.session.commit()


class ShopPurchase(db.Model):
    """Shop purchase history"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_item.id'), nullable=False)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_used = db.Column(db.Boolean, default=False, nullable=False)  # For consumable items
    quantity = db.Column(db.Integer, default=1, nullable=False)

    # Price tracking fields
    price_paid_coins = db.Column(db.Integer, default=0, nullable=False)
    price_paid_reputation = db.Column(db.Integer, default=0, nullable=False)

    # Relationships
    player = db.relationship('Player', backref='shop_purchases')

    def __repr__(self):
        return f'<ShopPurchase {self.player_id}:{self.item_id}>'


class Achievement(db.Model):
    """Achievement system for special accomplishments"""

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default='fas fa-medal')
    rarity = db.Column(db.String(20), default='common')  # common, uncommon, epic, legendary, mythic
    unlock_condition = db.Column(db.Text, nullable=False)  # JSON condition
    reward_xp = db.Column(db.Integer, default=0)
    reward_coins = db.Column(db.Integer, default=0)
    reward_reputation = db.Column(db.Integer, default=0)
    reward_title = db.Column(db.String(100), nullable=True)
    is_hidden = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with player achievements
    player_achievements = db.relationship('PlayerAchievement', backref='achievement', lazy=True)

    def __repr__(self):
        return f'<Achievement {self.title}>'

    def check_unlock_condition(self, player):
        """Check if player meets achievement unlock condition"""
        try:
            import json
            condition = json.loads(self.unlock_condition)

            for key, required_value in condition.items():
                if key == 'kd_ratio':
                    if float(player.kd_ratio) < float(required_value):
                        return False
                elif key == 'win_rate':
                    if float(player.win_rate) < float(required_value):
                        return False
                elif key == 'total_resources':
                    if player.total_resources < required_value:
                        return False
                else:
                    player_value = getattr(player, key, 0)
                    if player_value < required_value:
                        return False

            return True
        except Exception as e:
            print(f"Error checking achievement condition: {e}")
            return False

    @classmethod
    def check_player_achievements(cls, player):
        """Check and award new achievements for player"""
        new_achievements = []

        # Get all achievements not yet earned by player
        earned_achievement_ids = [pa.achievement_id for pa in player.player_achievements]
        unearned_achievements = cls.query.filter(~cls.id.in_(earned_achievement_ids)).all()

        for achievement in unearned_achievements:
            if achievement.check_unlock_condition(player):
                # Award achievement
                player_achievement = PlayerAchievement(
                    player_id=player.id,
                    achievement_id=achievement.id
                )
                db.session.add(player_achievement)

                # Award all rewards
                player.experience += achievement.reward_xp
                player.coins += achievement.reward_coins
                player.reputation += achievement.reward_reputation

                new_achievements.append(achievement)

        if new_achievements:
            db.session.commit()

        return new_achievements

    @classmethod
    def create_default_achievements(cls):
        """Create default achievements with enhanced reward system"""
        default_achievements = [
            # Common achievements (basic rewards)
            {
                'title': 'Новичок',
                'description': 'Сыграйте первую игру',
                'icon': 'fas fa-baby',
                'rarity': 'common',
                'unlock_condition': '{"games_played": 1}',
                'reward_xp': 500,
                'reward_coins': 100,
                'reward_reputation': 5
            },
            {
                'title': 'Первые шаги',
                'description': 'Убейте 10 игроков',
                'icon': 'fas fa-sword',
                'rarity': 'common',
                'unlock_condition': '{"kills": 10}',
                'reward_xp': 750,
                'reward_coins': 150,
                'reward_reputation': 8
            },
            {
                'title': 'Разрушитель',
                'description': 'Сломайте 5 кроватей',
                'icon': 'fas fa-bed',
                'rarity': 'common',
                'unlock_condition': '{"beds_broken": 5}',
                'reward_xp': 800,
                'reward_coins': 200,
                'reward_reputation': 10
            },

            # Uncommon achievements (moderate rewards)
            {
                'title': 'Боец',
                'description': 'Убейте 50 игроков',
                'icon': 'fas fa-fist-raised',
                'rarity': 'uncommon',
                'unlock_condition': '{"kills": 50}',
                'reward_xp': 1500,
                'reward_coins': 300,
                'reward_reputation': 15
            },
            {
                'title': 'Коллекционер',
                'description': 'Соберите 1000 единиц ресурсов',
                'icon': 'fas fa-gem',
                'rarity': 'uncommon',
                'unlock_condition': '{"total_resources": 1000}',
                'reward_xp': 1200,
                'reward_coins': 250,
                'reward_reputation': 12
            },
            {
                'title': 'Победитель',
                'description': 'Выиграйте 10 игр',
                'icon': 'fas fa-trophy',
                'rarity': 'uncommon',
                'unlock_condition': '{"wins": 10}',
                'reward_xp': 2000,
                'reward_coins': 400,
                'reward_reputation': 20
            },

            # Epic achievements (high rewards) - Made more challenging
            {
                'title': 'Неудержимый',
                'description': 'Убейте 500 игроков с K/D > 2.0',
                'icon': 'fas fa-fire',
                'rarity': 'epic',
                'unlock_condition': '{"kills": 500, "kd_ratio": 2.0}',
                'reward_xp': 8000,
                'reward_coins': 1500,
                'reward_reputation': 75,
                'is_hidden': True
            },
            {
                'title': 'Мастер ресурсов',
                'description': 'Соберите 25000 единиц ресурсов и выиграйте 75 игр',
                'icon': 'fas fa-coins',
                'rarity': 'epic',
                'unlock_condition': '{"total_resources": 25000, "wins": 75}',
                'reward_xp': 10000,
                'reward_coins': 2000,
                'reward_reputation': 100,
                'is_hidden': True
            },
            {
                'title': 'Чемпион арены',
                'description': 'Выиграйте 150 игр с 75%+ винрейтом',
                'icon': 'fas fa-crown',
                'rarity': 'epic',
                'unlock_condition': '{"wins": 150, "win_rate": 75.0}',
                'reward_xp': 12000,
                'reward_coins': 2500,
                'reward_reputation': 125
            },
            {
                'title': 'Разрушитель империй',
                'description': 'Сломайте 200 кроватей с 60%+ винрейтом',
                'icon': 'fas fa-hammer',
                'rarity': 'epic',
                'unlock_condition': '{"beds_broken": 200, "win_rate": 60.0}',
                'reward_xp': 9000,
                'reward_coins': 1800,
                'reward_reputation': 90,
                'is_hidden': True
            },

            # Legendary achievements (very high rewards) - Significantly more challenging
            {
                'title': 'Мастер Bedwars',
                'description': 'Достигните K/D 4.0+ при 200+ играх',
                'icon': 'fas fa-star',
                'rarity': 'legendary',
                'unlock_condition': '{"kd_ratio": 4.0, "games_played": 200}',
                'reward_xp': 20000,
                'reward_coins': 4000,
                'reward_reputation': 200,
                'reward_title': 'Мастер'
            },
            {
                'title': 'Великий воин',
                'description': 'Убейте 1500 игроков с 80%+ винрейтом',
                'icon': 'fas fa-shield',
                'rarity': 'legendary',
                'unlock_condition': '{"kills": 1500, "win_rate": 80.0}',
                'reward_xp': 25000,
                'reward_coins': 5000,
                'reward_reputation': 250,
                'reward_title': 'Великий воин'
            },
            {
                'title': 'Легенда арены',
                'description': 'Выиграйте 300 игр с 90%+ винрейтом',
                'icon': 'fas fa-medal',
                'rarity': 'legendary',
                'unlock_condition': '{"wins": 300, "win_rate": 90.0}',
                'reward_xp': 30000,
                'reward_coins': 6000,
                'reward_reputation': 300,
                'reward_title': 'Легенда арены'
            },
            {
                'title': 'Безжалостный убийца',
                'description': 'Совершите 750 финальных убийств с K/D > 3.5',
                'icon': 'fas fa-skull-crossbones',
                'rarity': 'legendary',
                'unlock_condition': '{"final_kills": 750, "kd_ratio": 3.5}',
                'reward_xp': 22000,
                'reward_coins': 4500,
                'reward_reputation': 220,
                'reward_title': 'Безжалостный',
                'is_hidden': True
            },

            # Mythic achievements (maximum rewards)
            {
                'title': 'Божество PVP',
                'description': 'Достигните K/D соотношения 5.0 и совершите 1000+ убийств',
                'icon': 'fas fa-bolt',
                'rarity': 'mythic',
                'unlock_condition': '{"kd_ratio": 5.0, "kills": 1000, "experience": 450000}',
                'reward_xp': 25000,
                'reward_coins': 5000,
                'reward_reputation': 250,
                'reward_title': 'Божество PVP',
                'is_hidden': True
            },
            {
                'title': 'Разрушитель миров',
                'description': 'Сломайте 500 кроватей противников',
                'icon': 'fas fa-meteor',
                'rarity': 'mythic',
                'unlock_condition': '{"beds_broken": 500}',
                'reward_xp': 30000,
                'reward_coins': 6000,
                'reward_reputation': 300,
                'reward_title': 'Разрушитель миров',
                'is_hidden': True
            },
            {
                'title': 'Легенда сервера',
                'description': 'Достигните 95% процента побед при 100+ играх',
                'icon': 'fas fa-dragon',
                'rarity': 'mythic',
                'unlock_condition': '{"win_rate": 95.0, "games_played": 100}',
                'reward_xp': 40000,
                'reward_coins': 8000,
                'reward_reputation': 400,
                'reward_title': 'Легенда сервера',
                'is_hidden': True
            },
            {
                'title': 'Повелитель ресурсов',
                'description': 'Соберите 100,000 единиц ресурсов',
                'icon': 'fas fa-gem',
                'rarity': 'mythic',
                'unlock_condition': '{"total_resources": 100000}',
                'reward_xp': 35000,
                'reward_coins': 7000,
                'reward_reputation': 350,
                'reward_title': 'Повелитель ресурсов',
                'is_hidden': True
            },
            {
                'title': 'Абсолютный чемпион',
                'description': 'Выиграйте 1000 игр и достигните 98% побед',
                'icon': 'fas fa-infinity',
                'rarity': 'mythic',
                'unlock_condition': '{"wins": 1000, "win_rate": 98.0}',
                'reward_xp': 50000,
                'reward_coins': 10000,
                'reward_reputation': 500,
                'reward_title': 'Абсолютный чемпион',
                'is_hidden': True
            },
            {
                'title': 'Всевидящее око',
                'description': 'Совершите 2000 финальных убийств',
                'icon': 'fas fa-eye',
                'rarity': 'mythic',
                'unlock_condition': '{"final_kills": 2000}',
                'reward_xp': 45000,
                'reward_coins': 9000,
                'reward_reputation': 450,
                'reward_title': 'Всевидящее око',
                'is_hidden': True
            },
            {
                'title': 'Архитектор разрушения',
                'description': 'Сломайте 1000 кроватей',
                'icon': 'fas fa-hammer',
                'rarity': 'mythic',
                'unlock_condition': '{"beds_broken": 1000}',
                'reward_xp': 55000,
                'reward_coins': 11000,
                'reward_reputation': 550,
                'reward_title': 'Архитектор разрушения',
                'is_hidden': True
            },
            {
                'title': 'Неуязвимый',
                'description': 'Достигните уровня 200 с K/D > 4.0',
                'icon': 'fas fa-shield-alt',
                'rarity': 'mythic',
                'unlock_condition': '{"experience": 1500000, "kd_ratio": 4.0}',
                'reward_xp': 60000,
                'reward_coins': 12000,
                'reward_reputation': 600,
                'reward_title': 'Неуязвимый',
                'is_hidden': True
            }
        ]

        for achievement_data in default_achievements:
            existing = cls.query.filter_by(title=achievement_data['title']).first()
            if not existing:
                achievement = cls(**achievement_data)
                db.session.add(achievement)

        db.session.commit()


class PlayerAchievement(db.Model):
    """Player progress on achievements with baseline tracking"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    current_progress = db.Column(db.Integer, default=0)
    baseline_values = db.Column(db.Text, nullable=True)  # JSON data for baseline stats when achievement was tracked
    is_earned = db.Column(db.Boolean, default=False)
    earned_at = db.Column(db.DateTime, nullable=True)
    started_tracking_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PlayerAchievement {self.player_id}:{self.achievement_id}>'


class AdminCustomRole(db.Model):
    """Admin-created custom roles for players"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    color = db.Column(db.String(7), default='#ffd700')  # Hex color
    emoji = db.Column(db.String(10), nullable=True)  # Legacy emoji field
    emoji_url = db.Column(db.String(256), nullable=True)  # Custom emoji file path
    emoji_filename = db.Column(db.String(256), nullable=True)  # Filename for uploaded emoji
    emoji_is_animated = db.Column(db.Boolean, default=False) # Flag for animated emoji
    emoji_class = db.Column(db.String(64), nullable=True)  # Font Awesome class
    has_gradient = db.Column(db.Boolean, default=False)
    gradient_end_color = db.Column(db.String(7), nullable=True)  # Second gradient color
    is_visible = db.Column(db.Boolean, default=True)  # Show in profile
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100), default='admin')
    is_active = db.Column(db.Boolean, default=True)

    # Relationship with player roles
    player_roles = db.relationship('PlayerAdminRole', backref='role', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<AdminCustomRole {self.name}>'

    @property
    def gradient_css(self):
        """Get CSS gradient if enabled"""
        if self.has_gradient and self.gradient_end_color:
            return f"linear-gradient(45deg, {self.color}, {self.gradient_end_color})"
        return None

    @property
    def players_count(self):
        """Get count of players with this role"""
        return PlayerAdminRole.query.filter_by(role_id=self.id, is_active=True).count()

    @property
    def display_emoji(self):
        """Get emoji display HTML"""
        if self.emoji_filename:
            # Use uploaded file
            emoji_path = f"/static/emojis/{self.emoji_filename}"
            css_class = "emoji animated-emoji" if self.emoji_is_animated else "emoji"
            return f'<img src="{emoji_path}" class="{css_class}" alt="custom emoji">'
        elif self.emoji_url:
            return f'<img src="{self.emoji_url}" class="emoji" alt="custom emoji">'
        elif self.emoji_class:
            return f'<i class="{self.emoji_class}"></i>'
        elif self.emoji:
            return self.emoji
        return ''


    @classmethod
    def create_default_roles(cls):
        """Create default admin roles"""
        default_roles = [
            {
                'name': 'VIP',
                'color': '#ffd700',
                'emoji_class': 'fas fa-star',
                'has_gradient': False,
                'is_visible': True
            },
            {
                'name': 'Premium',
                'color': '#ff6b35',
                'emoji_class': 'fas fa-crown',
                'has_gradient': True,
                'gradient_end_color': '#f7931e',
                'is_visible': True
            },
            {
                'name': 'Модератор',
                'color': '#28a745',
                'emoji_class': 'fas fa-shield',
                'has_gradient': False,
                'is_visible': True
            },
            {
                'name': 'Администратор',
                'color': '#dc3545',
                'emoji_class': 'fas fa-hammer',
                'has_gradient': True,
                'gradient_end_color': '#c82333',
                'is_visible': True
            }
        ]

        for role_data in default_roles:
            existing = cls.query.filter_by(name=role_data['name']).first()
            if not existing:
                role = cls(**role_data)
                db.session.add(role)

        db.session.commit()


class PlayerAdminRole(db.Model):
    """Players assigned admin custom roles"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('admin_custom_role.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.String(100), default='admin')
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    player = db.relationship('Player', backref='admin_roles')

    def __repr__(self):
        return f'<PlayerAdminRole {self.player_id}:{self.role_id}>'


class Badge(db.Model):
    """Admin-created badges for players"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), default='fas fa-medal')  # Font Awesome class
    emoji = db.Column(db.String(10), nullable=True)  # Text emoji
    emoji_url = db.Column(db.String(256), nullable=True)  # Custom emoji file path
    emoji_class = db.Column(db.String(64), nullable=True)  # Font Awesome class for emoji
    color = db.Column(db.String(7), default='#ffd700')  # Hex color
    background_color = db.Column(db.String(7), default='#343a40')  # Background color
    border_color = db.Column(db.String(7), default='#ffd700')  # Border color
    has_gradient = db.Column(db.Boolean, default=False)
    gradient_start = db.Column(db.String(7), nullable=True)
    gradient_end = db.Column(db.String(7), nullable=True)
    rarity = db.Column(db.String(20), default='common', nullable=False)  # common, rare, epic, legendary, mythic
    is_animated = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100), default='admin')

    # Relationships
    player_badges = db.relationship('PlayerBadge', backref='badge', lazy=True, cascade='all, delete-orphan')

    @property
    def players_count(self):
        """Get count of players with this badge"""
        return PlayerBadge.query.filter_by(badge_id=self.id).count()

    @property
    def css_style(self):
        """Get CSS style for badge"""
        if self.has_gradient and self.gradient_start and self.gradient_end:
            background = f"linear-gradient(45deg, {self.gradient_start}, {self.gradient_end})"
        else:
            background = self.background_color

        return {
            'background': background,
            'color': self.color,
            'border-color': self.border_color
        }

    @property
    def display_emoji(self):
        """Get emoji display HTML"""
        if self.emoji_url:
            return f'<img src="{self.emoji_url}" class="emoji" alt="custom emoji">'
        elif self.emoji_class:
            return f'<i class="{self.emoji_class}"></i>'
        elif self.emoji:
            return self.emoji
        return ''

    @classmethod
    def create_default_badges(cls):
        """Create default badges"""
        default_badges = [
            {
                'name': 'first_steps',
                'display_name': 'Первые шаги',
                'description': 'Добро пожаловать в Bedwars!',
                'icon': 'fas fa-baby',
                'color': '#ffffff',
                'background_color': '#28a745',
                'border_color': '#20c997',
                'rarity': 'common'
            },
            {
                'name': 'veteran',
                'display_name': 'Ветеран',
                'description': 'Опытный игрок сервера',
                'icon': 'fas fa-shield',
                'color': '#ffffff',
                'background_color': '#6f42c1',
                'border_color': '#8e44ad',
                'rarity': 'rare'
            },
            {
                'name': 'champion',
                'display_name': 'Чемпион',
                'description': 'Элитный игрок',
                'icon': 'fas fa-crown',
                'color': '#212529',
                'has_gradient': True,
                'gradient_start': '#ffd700',
                'gradient_end': '#ffaa00',
                'border_color': '#ffd700',
                'rarity': 'epic',
                'is_animated': True
            },
            {
                'name': 'legend',
                'display_name': 'Легенда',
                'description': 'Легендарный игрок сервера',
                'icon': 'fas fa-dragon',
                'color': '#ffffff',
                'has_gradient': True,
                'gradient_start': '#ff6b35',
                'gradient_end': '#f7931e',
                'border_color': '#ff6b35',
                'rarity': 'legendary',
                'is_animated': True
            },
            {
                'name': 'mythic_warrior',
                'display_name': 'Мифический воин',
                'description': 'Достигнил невозможного',
                'icon': 'fas fa-bolt',
                'color': '#ffffff',
                'has_gradient': True,
                'gradient_start': '#9400d3',
                'gradient_end': '#4b0082',
                'border_color': '#9400d3',
                'rarity': 'mythic',
                'is_animated': True
            }
        ]

        for badge_data in default_badges:
            existing = cls.query.filter_by(name=badge_data['name']).first()
            if not existing:
                badge = cls(**badge_data)
                db.session.add(badge)

        db.session.commit()


class PlayerBadge(db.Model):
    """Badges assigned to players"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.String(100), default='admin')
    is_visible = db.Column(db.Boolean, default=True)  # Player can hide/show badges

    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('player_id', 'badge_id', name='unique_player_badge'),)

    # Relationships
    player = db.relationship('Player', backref='player_badges')

    def __repr__(self):
        return f'<PlayerBadge {self.player_id}:{self.badge_id}>'


class PlayerSkillRating(db.Model):
    """Simple skill rating system for players"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)

    # Simple rating system (1-100)
    pvp_skill = db.Column(db.Integer, default=50)  # PvP skill rating
    strategy_skill = db.Column(db.Integer, default=50)  # Strategic gameplay
    teamwork_skill = db.Column(db.Integer, default=50)  # Team coordination
    overall_skill = db.Column(db.Integer, default=50)  # Overall rating

    # Admin notes
    admin_notes = db.Column(db.Text, nullable=True)
    last_updated_by = db.Column(db.String(100), nullable=True)
    last_updated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    player = db.relationship('Player', backref='skill_rating')

    def __repr__(self):
        return f'<PlayerSkillRating {self.player_id}: {self.overall_skill}/100>'

    @property
    def skill_tier(self):
        """Get skill tier based on overall rating"""
        if self.overall_skill >= 90:
            return {'name': 'Grandmaster', 'color': '#ff1493', 'icon': 'fas fa-crown'}
        elif self.overall_skill >= 80:
            return {'name': 'Master', 'color': '#9400d3', 'icon': 'fas fa-star'}
        elif self.overall_skill >= 70:
            return {'name': 'Diamond', 'color': '#00bfff', 'icon': 'fas fa-gem'}
        elif self.overall_skill >= 60:
            return {'name': 'Gold', 'color': '#ffd700', 'icon': 'fas fa-medal'}
        elif self.overall_skill >= 50:
            return {'name': 'Silver', 'color': '#c0c0c0', 'icon': 'fas fa-shield'}
        elif self.overall_skill >= 40:
            return {'name': 'Bronze', 'color': '#cd7f32', 'icon': 'fas fa-trophy'}
        else:
            return {'name': 'Unranked', 'color': '#6c757d', 'icon': 'fas fa-question'}

    def calculate_overall_rating(self):
        """Calculate overall rating based on individual skills"""
        self.overall_skill = round((self.pvp_skill + self.strategy_skill + self.teamwork_skill) / 3)

    @classmethod
    def get_or_create_rating(cls, player_id):
        """Get existing rating or create new one"""
        rating = cls.query.filter_by(player_id=player_id).first()
        if not rating:
            rating = cls(player_id=player_id)
            db.session.add(rating)
            db.session.commit()
        return rating


class CustomTitle(db.Model):
    """Custom titles that admins can assign to players"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), default='#ffd700')  # Hex color
    glow_color = db.Column(db.String(7), default='#ffd700')  # Glow effect color
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100), default='admin')

    def __repr__(self):
        return f'<CustomTitle {self.name}>'

    @classmethod
    def create_default_titles(cls):
        """Create default custom titles"""
        default_titles = [
            {
                'name': 'legend',
                'display_name': '🏆 Легенда',
                'color': '#ffd700',
                'glow_color': '#ffaa00'
            },
            {
                'name': 'champion',
                'display_name': '👑 Чемпион',
                'color': '#ff6b35',
                'glow_color': '#ff4444'
            },
            {
                'name': 'elite',
                'display_name': '⭐ Элита',
                'color': '#9b59b6',
                'glow_color': '#8e44ad'
            },
            {
                'name': 'destroyer',
                'display_name': '💥 Разрушитель',
                'color': '#e74c3c',
                'glow_color': '#c0392b'
            },
            {
                'name': 'master',
                'display_name': '🎯 Мастер',
                'color': '#3498db',
                'glow_color': '#2980b9'
            }
        ]

        for title_data in default_titles:
            existing = cls.query.filter_by(name=title_data['name']).first()
            if not existing:
                title = cls(**title_data)
                db.session.add(title)

        db.session.commit()


class PlayerTitle(db.Model):
    """Custom titles assigned to players by admins"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    title_id = db.Column(db.Integer, db.ForeignKey('custom_title.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.String(100), default='admin')
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    player = db.relationship('Player', backref='custom_titles')
    title = db.relationship('CustomTitle', backref='assigned_players')

    def __repr__(self):
        return f'<PlayerTitle {self.player_id}:{self.title_id}>'


class PlayerActiveBooster(db.Model):
    """Active boosters that players currently have"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    booster_type = db.Column(db.String(50), nullable=False)  # active_coins_booster, active_reputation_booster, etc.
    multiplier = db.Column(db.Float, nullable=False, default=1.0)  # 1.5, 2.0, 3.0 etc.
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship
    player = db.relationship('Player', backref='active_boosters')

    def __repr__(self):
        return f'<PlayerActiveBooster {self.player_id}:{self.booster_type}>'

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    @property
    def time_remaining(self):
        if self.is_expired:
            return 0
        return int((self.expires_at - datetime.utcnow()).total_seconds())

    @classmethod
    def get_active_boosters(cls, player_id):
        """Get all active boosters for a player"""
        return cls.query.filter_by(
            player_id=player_id,
            is_active=True
        ).filter(cls.expires_at > datetime.utcnow()).all()

    @classmethod
    def get_coins_multiplier(cls, player_id):
        """Get current coins multiplier for a player"""
        boosters = cls.query.filter_by(
            player_id=player_id,
            is_active=True
        ).filter(
            cls.expires_at > datetime.utcnow(),
            cls.booster_type.in_(['active_coins_booster', 'active_mega_booster'])
        ).all()

        multiplier = 1.0
        for booster in boosters:
            multiplier *= booster.multiplier
        return multiplier

    @classmethod
    def get_reputation_multiplier(cls, player_id):
        """Get current reputation multiplier for a player"""
        boosters = cls.query.filter_by(
            player_id=player_id,
            is_active=True
        ).filter(
            cls.expires_at > datetime.utcnow(),
            cls.booster_type.in_(['active_reputation_booster', 'active_mega_booster'])
        ).all()

        multiplier = 1.0
        for booster in boosters:
            multiplier *= booster.multiplier
        return multiplier


class GradientTheme(db.Model):
    """Gradient themes for various UI elements"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    element_type = db.Column(db.String(50), nullable=False)  # nickname, stats, kills, etc.
    color1 = db.Column(db.String(7), nullable=False)  # First gradient color
    color2 = db.Column(db.String(7), nullable=False)  # Second gradient color
    color3 = db.Column(db.String(7), nullable=True)   # Optional third color
    gradient_direction = db.Column(db.String(20), default='45deg')  # Gradient direction
    animation_enabled = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GradientTheme {self.name}>'

    @property
    def css_gradient(self):
        """Generate CSS gradient string"""
        if self.color3:
            return f"linear-gradient({self.gradient_direction}, {self.color1}, {self.color2}, {self.color3})"
        return f"linear-gradient({self.gradient_direction}, {self.color1}, {self.color2})"

    @classmethod
    def create_default_themes(cls):
        """Create default gradient themes"""
        default_themes = [
            # Nickname gradients
            {
                'name': 'fire_nickname',
                'display_name': '🔥 Огненный',
                'element_type': 'nickname',
                'color1': '#ff6b35',
                'color2': '#f7931e',
                'color3': '#ffaa00',
                'gradient_direction': '45deg',
                'animation_enabled': True
            },
            {
                'name': 'ocean_nickname',
                'display_name': '🌊 Океанский',
                'element_type': 'nickname',
                'color1': '#00d2ff',
                'color2': '#3a7bd5',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },
            {
                'name': 'purple_nickname',
                'display_name': '🔮 Фиолетовый',
                'element_type': 'nickname',
                'color1': '#667eea',
                'color2': '#764ba2',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },
            {
                'name': 'rainbow_nickname',
                'display_name': '🌈 Радужный',
                'element_type': 'nickname',
                'color1': '#ff0000',
                'color2': '#ffff00',
                'color3': '#00ff00',
                'gradient_direction': '90deg',
                'animation_enabled': True
            },

            # Stats gradients
            {
                'name': 'gold_stats',
                'display_name': '🥇 Золотая статистика',
                'element_type': 'stats',
                'color1': '#ffd700',
                'color2': '#ffed4e',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },
            {
                'name': 'emerald_stats',
                'display_name': '💎 Изумрудная статистика',
                'element_type': 'stats',
                'color1': '#50c878',
                'color2': '#00ff7f',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },
            {
                'name': 'blood_stats',
                'display_name': '🩸 Кровавая статистика',
                'element_type': 'stats',
                'color1': '#dc143c',
                'color2': '#ff1744',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },

            # Individual stat gradients
            {
                'name': 'fire_kills',
                'display_name': '🔥 Огненные киллы',
                'element_type': 'kills',
                'color1': '#ff6b35',
                'color2': '#f7931e',
                'gradient_direction': '45deg',
                'animation_enabled': True
            },
            {
                'name': 'ice_deaths',
                'display_name': '❄️ Ледяные смерти',
                'element_type': 'deaths',
                'color1': '#74b9ff',
                'color2': '#0984e3',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },
            {
                'name': 'golden_wins',
                'display_name': '🏆 Золотые победы',
                'element_type': 'wins',
                'color1': '#ffd700',
                'color2': '#ffaa00',
                'gradient_direction': '45deg',
                'animation_enabled': True
            },
            {
                'name': 'diamond_beds',
                'display_name': '💎 Алмазные кровати',
                'element_type': 'beds',
                'color1': '#74b9ff',
                'color2': '#0984e3',
                'color3': '#6c5ce7',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },

            # Title gradients
            {
                'name': 'legendary_title',
                'display_name': '👑 Легендарный титул',
                'element_type': 'title',
                'color1': '#ffd700',
                'color2': '#ff6b35',
                'color3': '#8e44ad',
                'gradient_direction': '45deg',
                'animation_enabled': True
            },
            {
                'name': 'crystal_title',
                'display_name': '💎 Кристальный титул',
                'element_type': 'title',
                'color1': '#74b9ff',
                'color2': '#0984e3',
                'color3': '#6c5ce7',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },

            # Status gradients (level 20+)
            {
                'name': 'sunset_status',
                'display_name': '🌅 Закатный статус',
                'element_type': 'status',
                'color1': '#ff6b35',
                'color2': '#f7931e',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },
            {
                'name': 'ocean_status',
                'display_name': '🌊 Океанский статус',
                'element_type': 'status',
                'color1': '#00d2ff',
                'color2': '#3a7bd5',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },
            {
                'name': 'mystic_status',
                'display_name': '🔮 Мистический статус',
                'element_type': 'status',
                'color1': '#667eea',
                'color2': '#764ba2',
                'gradient_direction': '45deg',
                'animation_enabled': True
            },

            # Bio gradients (level 20+)
            {
                'name': 'elegant_bio',
                'display_name': '✨ Элегантное био',
                'element_type': 'bio',
                'color1': '#ffd700',
                'color2': '#ffed4e',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },
            {
                'name': 'royal_bio',
                'display_name': '👑 Королевское био',
                'element_type': 'bio',
                'color1': '#8e44ad',
                'color2': '#3498db',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },
            {
                'name': 'cosmic_bio',
                'display_name': '🌌 Космическое био',
                'element_type': 'bio',
                'color1': '#667eea',
                'color2': '#764ba2',
                'color3': '#f093fb',
                'gradient_direction': '45deg',
                'animation_enabled': True
            },

            # Role gradients
            {
                'name': 'admin_role',
                'display_name': '👑 Администраторская роль',
                'element_type': 'role',
                'color1': '#ff6b35',
                'color2': '#f7931e',
                'gradient_direction': '45deg',
                'animation_enabled': True
            },
            {
                'name': 'vip_role',
                'display_name': '💎 VIP роль',
                'element_type': 'role',
                'color1': '#8e44ad',
                'color2': '#3498db',
                'gradient_direction': '45deg',
                'animation_enabled': False
            },
            {
                'name': 'pro_role',
                'display_name': '⭐ Профессиональная роль',
                'element_type': 'role',
                'color1': '#28a745',
                'color2': '#20c997',
                'gradient_direction': '45deg',
                'animation_enabled': False
            }
        ]

        for theme_data in default_themes:
            existing = cls.query.filter_by(name=theme_data['name']).first()
            if not existing:
                theme = cls(**theme_data)
                db.session.add(theme)

        db.session.commit()


class PlayerGradientSetting(db.Model):
    """Player's gradient settings"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    element_type = db.Column(db.String(50), nullable=False)  # nickname, stats, etc.
    gradient_theme_id = db.Column(db.Integer, db.ForeignKey('gradient_theme.id'), nullable=True)
    custom_color1 = db.Column(db.String(7), nullable=True)
    custom_color2 = db.Column(db.String(7), nullable=True)
    custom_color3 = db.Column(db.String(7), nullable=True)
    is_enabled = db.Column(db.Boolean, default=True)
    assigned_by = db.Column(db.String(100), default='admin')
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    player = db.relationship('Player', backref='gradient_settings')
    gradient_theme = db.relationship('GradientTheme', backref='player_settings')

    def __repr__(self):
        return f'<PlayerGradientSetting {self.player_id}:{self.element_type}>'

    @property
    def css_gradient(self):
        """Get CSS gradient for this setting"""
        if self.gradient_theme_id and self.gradient_theme:
            return self.gradient_theme.css_gradient
        elif self.custom_color1 and self.custom_color2:
            if self.custom_color3:
                return f"linear-gradient(45deg, {self.custom_color1}, {self.custom_color2}, {self.custom_color3})"
            return f"linear-gradient(45deg, {self.custom_color1}, {self.custom_color2})"
        return None


class SiteTheme(db.Model):
    """Site themes for different visual styles"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    primary_color = db.Column(db.String(7), default='#ffc107')
    secondary_color = db.Column(db.String(7), default='#6c757d')
    background_color = db.Column(db.String(7), default='#1a1a1a')
    card_background = db.Column(db.String(7), default='#2d2d2d')
    text_color = db.Column(db.String(7), default='#ffffff')
    accent_color = db.Column(db.String(7), default='#ffaa00')
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SiteTheme {self.name}>'

    @property
    def css_variables(self):
        """Generate CSS variables for the theme"""
        return {
            '--primary-color': self.primary_color,
            '--secondary-color': self.secondary_color,
            '--bg-primary': f'linear-gradient(135deg, {self.background_color} 0%, {self.card_background} 100%)',
            '--bg-secondary': f'linear-gradient(135deg, {self.card_background} 0%, {self.background_color} 100%)',
            '--text-color': self.text_color,
            '--accent-color': self.accent_color
        }

    @classmethod
    def create_default_themes(cls):
        """Create default site themes"""
        default_themes = [
            {
                'name': 'default_dark',
                'display_name': 'Классическая тёмная',
                'description': 'Элегантная тёмная тема с золотыми акцентами',
                'primary_color': '#ffc107',
                'secondary_color': '#6c757d',
                'background_color': '#0d1117',
                'card_background': '#161b22',
                'text_color': '#f0f6fc',
                'accent_color': '#28a745',
                'is_default': True
            },
            {
                'name': 'cyber_matrix',
                'display_name': 'Киберматрица',
                'description': 'Футуристическая тема в стиле "Матрицы"',
                'primary_color': '#00ff41',
                'secondary_color': '#008f11',
                'background_color': '#000000',
                'card_background': '#001100',
                'text_color': '#00ff41',
                'accent_color': '#39ff14'
            },
            {
                'name': 'royal_purple',
                'display_name': 'Королевский пурпур',
                'description': 'Роскошная тёмно-фиолетовая тема',
                'primary_color': '#9146ff',
                'secondary_color': '#772ce8',
                'background_color': '#0e0a20',
                'card_background': '#1f0a3e',
                'text_color': '#ffffff',
                'accent_color': '#bf94ff'
            },
            {
                'name': 'ocean_depths',
                'display_name': 'Морские глубины',
                'description': 'Глубокая синяя тема океана',
                'primary_color': '#00b4d8',
                'secondary_color': '#0077b6',
                'background_color': '#03045e',
                'card_background': '#023e8a',
                'text_color': '#caf0f8',
                'accent_color': '#90e0ef'
            },
            {
                'name': 'volcano_fire',
                'display_name': 'Огонь вулкана',
                'description': 'Страстная красно-оранжевая тема',
                'primary_color': '#ff4500',
                'secondary_color': '#dc2626',
                'background_color': '#1a0000',
                'card_background': '#330000',
                'text_color': '#fef2f2',
                'accent_color': '#fb923c'
            },
            {
                'name': 'midnight_blue',
                'display_name': 'Полуночный синий',
                'description': 'Элегантная тёмно-синяя тема',
                'primary_color': '#60a5fa',
                'secondary_color': '#3b82f6',
                'background_color': '#0f172a',
                'card_background': '#1e293b',
                'text_color': '#f1f5f9',
                'accent_color': '#38bdf8'
            },
            {
                'name': 'emerald_forest',
                'display_name': 'Изумрудный лес',
                'description': 'Природная зелёная тема',
                'primary_color': '#10b981',
                'secondary_color': '#059669',
                'background_color': '#064e3b',
                'card_background': '#065f46',
                'text_color': '#ecfdf5',
                'accent_color': '#34d399'
            },
            {
                'name': 'sunset_orange',
                'display_name': 'Закатный оранжевый',
                'description': 'Тёплая оранжево-красная тема',
                'primary_color': '#f97316',
                'secondary_color': '#ea580c',
                'background_color': '#431407',
                'card_background': '#7c2d12',
                'text_color': '#fff7ed',
                'accent_color': '#fb923c'
            },
            {
                'name': 'pink_neon',
                'display_name': 'Неоновый розовый',
                'description': 'Яркая розово-фиолетовая тема',
                'primary_color': '#ec4899',
                'secondary_color': '#db2777',
                'background_color': '#500724',
                'card_background': '#831843',
                'text_color': '#fdf2f8',
                'accent_color': '#f472b6'
            },
            {
                'name': 'golden_luxury',
                'display_name': 'Золотая роскошь',
                'description': 'Роскошная золотисто-чёрная тема',
                'primary_color': '#fbbf24',
                'secondary_color': '#f59e0b',
                'background_color': '#1c1917',
                'card_background': '#292524',
                'text_color': '#fef3c7',
                'accent_color': '#fcd34d'
            },
            {
                'name': 'ice_crystal',
                'display_name': 'Ледяной кристалл',
                'description': 'Холодная голубо-белая тема',
                'primary_color': '#0ea5e9',
                'secondary_color': '#0284c7',
                'background_color': '#0c4a6e',
                'card_background': '#075985',
                'text_color': '#e0f2fe',
                'accent_color': '#38bdf8'
            }
        ]

        for theme_data in default_themes:
            existing = cls.query.filter_by(name=theme_data['name']).first()
            if not existing:
                theme = cls(**theme_data)
                db.session.add(theme)

        db.session.commit()


class CursorTheme(db.Model):
    """Cursor themes for customization"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color1 = db.Column(db.String(7), default='#ffc107')
    color2 = db.Column(db.String(7), default='#ffaa00')
    animation = db.Column(db.String(50), default='glow')  # glow, pulse, rotate, rainbow
    size = db.Column(db.String(10), default='normal')  # small, normal, large
    shape = db.Column(db.String(20), default='circle')  # circle, square, diamond, star
    is_premium = db.Column(db.Boolean, default=False)
    price_coins = db.Column(db.Integer, default=0)
    unlock_level = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CursorTheme {self.name}>'

    @classmethod
    def create_default_cursors(cls):
        """Create default cursor themes"""
        default_cursors = [
            {
                'name': 'classic',
                'display_name': '🎯 Классический',
                'description': 'Стандартный игровой курсор',
                'color1': '#ffc107',
                'color2': '#ffaa00',
                'animation': 'glow',
                'price_coins': 0
            },
            {
                'name': 'fire',
                'display_name': '🔥 Огненный',
                'description': 'Пылающий курсор для настоящих воинов',
                'color1': '#ff6b35',
                'color2': '#f7931e',
                'animation': 'pulse',
                'price_coins': 50,
                'unlock_level': 5
            },
            {
                'name': 'ice',
                'display_name': '❄️ Ледяной',
                'description': 'Холодный как лед курсор',
                'color1': '#74b9ff',
                'color2': '#0984e3',
                'animation': 'glow',
                'price_coins': 75,
                'unlock_level': 10
            },
            {
                'name': 'lightning',
                'display_name': '⚡ Молния',
                'description': 'Быстрый как молния курсор',
                'color1': '#fdcb6e',
                'color2': '#e17055',
                'animation': 'pulse',
                'shape': 'diamond',
                'price_coins': 100,
                'unlock_level': 15,
                'is_premium': True
            },
            {
                'name': 'rainbow',
                'display_name': '🌈 Радужный',
                'description': 'Переливающийся всеми цветами курсор',
                'color1': '#ff0000',
                'color2': '#00ff00',
                'animation': 'rainbow',
                'price_coins': 200,
                'unlock_level': 25,
                'is_premium': True
            },
            {
                'name': 'galaxy',
                'display_name': '🌌 Галактический',
                'description': 'Космический курсор для покорителей вселенной',
                'color1': '#6c5ce7',
                'color2': '#a29bfe',
                'animation': 'rotate',
                'shape': 'star',
                'price_coins': 500,
                'unlock_level': 50,
                'is_premium': True
            }
        ]

        for cursor_data in default_cursors:
            existing = cls.query.filter_by(name=cursor_data['name']).first()
            if not existing:
                cursor = cls(**cursor_data)
                db.session.add(cursor)

        db.session.commit()

    @classmethod
    def create_default_items(cls):
        """Create default shop items"""
        # Этот метод можно оставить пустым или добавить базовые предметы
        pass


class ShopCategory(db.Model):
    """Shop categories for organizing items"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), default='fas fa-shopping-bag')
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<ShopCategory {self.name}>'


class PlayerPurchase(db.Model):
    """Player purchases from the shop"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_item.id'), nullable=False)
    purchase_price_coins = db.Column(db.Integer, nullable=False)
    purchase_price_reputation = db.Column(db.Integer, default=0)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    player = db.relationship('Player')


class PlayerBooster(db.Model):
    """Active boosters for players"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    booster_type = db.Column(db.String(20), nullable=False)  # experience, reputation, coins
    multiplier = db.Column(db.Float, default=1.5)  # 1.5x, 2.0x, etc.
    duration_minutes = db.Column(db.Integer, nullable=False)
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    given_by_admin = db.Column(db.String(100), nullable=True)

    # Relationships
    player = db.relationship('Player', backref='player_boosters')

    def __repr__(self):
        return f'<PlayerBooster {self.player_id}:{self.booster_type}>'

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    @property
    def time_remaining(self):
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return int(delta.total_seconds() / 60)  # minutes

    @classmethod
    def get_active_booster(cls, player_id, booster_type):
        """Get active booster for player"""
        return cls.query.filter_by(
            player_id=player_id,
            booster_type=booster_type,
            is_active=True
        ).filter(cls.expires_at > datetime.utcnow()).first()

    @classmethod
    def cleanup_expired(cls):
        """Remove expired boosters"""
        expired = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for booster in expired:
            booster.is_active = False


class ReputationLog(db.Model):
    """Log of reputation changes"""

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    change_amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    given_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    player = db.relationship('Player', backref='reputation_logs')

    def __repr__(self):
        return f'<ReputationLog {self.player_id}:{self.change_amount}>'


class Clan(db.Model):
    """Clan system for players"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    tag = db.Column(db.String(10), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    clan_type = db.Column(db.String(20), default='open', nullable=False)  # open, invite_only, closed
    max_members = db.Column(db.Integer, default=50, nullable=False)
    experience = db.Column(db.Integer, default=0, nullable=False)
    rating = db.Column(db.Integer, default=1000, nullable=False)
    leader_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    leader = db.relationship('Player', foreign_keys=[leader_id], backref='led_clans')
    members = db.relationship('ClanMember', backref='clan', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Clan {self.name} [{self.tag}]>'

    @property
    def level(self):
        """Calculate clan level based on experience"""
        # Simple level calculation: level = experience // 10000 + 1
        return min(100, max(1, self.experience // 10000 + 1))

    @property
    def member_count(self):
        """Get current member count"""
        return ClanMember.query.filter_by(clan_id=self.id, is_active=True).count()

    @property
    def can_join(self):
        """Check if clan can accept new members"""
        return self.clan_type == 'open' and self.member_count < self.max_members

    def get_members_by_role(self, role):
        """Get clan members by role"""
        return ClanMember.query.filter_by(clan_id=self.id, role=role, is_active=True).all()

    @classmethod
    def get_top_clans(cls, limit=10):
        """Get top clans by rating"""
        return cls.query.filter_by(is_active=True).order_by(cls.rating.desc()).limit(limit).all()

    @classmethod
    def search_clans(cls, query):
        """Search clans by name or tag"""
        return cls.query.filter(
            db.or_(
                cls.name.ilike(f'%{query}%'),
                cls.tag.ilike(f'%{query}%')
            ),
            cls.is_active == True
        ).all()


class ClanMember(db.Model):
    """Clan membership"""

    id = db.Column(db.Integer, primary_key=True)
    clan_id = db.Column(db.Integer, db.ForeignKey('clan.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    role = db.Column(db.String(20), default='member', nullable=False)  # leader, officer, member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    contribution = db.Column(db.Integer, default=0, nullable=False)

    # Relationships
    player = db.relationship('Player', backref='clan_memberships')

    def __repr__(self):
        return f'<ClanMember {self.player_id}:{self.clan_id}>'

    @property
    def role_display(self):
        """Get display name for role"""
        role_names = {
            'leader': '👑 Лидер',
            'officer': '⭐ Офицер',
            'member': '👤 Участник'
        }
        return role_names.get(self.role, '👤 Участник')


class Tournament(db.Model):
    """Tournament system"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    tournament_type = db.Column(db.String(50), default='singles', nullable=False)  # singles, teams, clans
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    entry_fee = db.Column(db.Integer, default=0, nullable=False)
    prize_pool = db.Column(db.Integer, default=0, nullable=False)
    max_participants = db.Column(db.Integer, default=100, nullable=False)
    status = db.Column(db.String(20), default='upcoming', nullable=False)  # upcoming, active, completed
    organizer_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    organizer = db.relationship('Player', backref='organized_tournaments')
    participants = db.relationship('TournamentParticipant', backref='tournament', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Tournament {self.name}>'

    @property
    def participant_count(self):
        """Get current participant count"""
        return TournamentParticipant.query.filter_by(tournament_id=self.id, is_active=True).count()

    @property
    def can_join(self):
        """Check if tournament can accept new participants"""
        return (self.status == 'upcoming' and
                self.participant_count < self.max_participants and
                datetime.utcnow() < self.start_date)

    @property
    def status_display(self):
        """Get display name for status"""
        status_names = {
            'upcoming': '📅 Предстоящий',
            'active': '🔥 Активный',
            'completed': '🏆 Завершённый'
        }
        return status_names.get(self.status, '📅 Предстоящий')

    @property
    def type_display(self):
        """Get display name for tournament type"""
        type_names = {
            'singles': '👤 Одиночный',
            'teams': '👥 Командный',
            'clans': '🏰 Кланы'
        }
        return type_names.get(self.tournament_type, '👤 Одиночный')

    @classmethod
    def get_by_status(cls, status):
        """Get tournaments by status"""
        return cls.query.filter_by(status=status, is_active=True).order_by(cls.start_date.desc()).all()

    @classmethod
    def get_upcoming(cls):
        """Get upcoming tournaments"""
        return cls.query.filter_by(status='upcoming', is_active=True).order_by(cls.start_date.asc()).all()

    @classmethod
    def get_active(cls):
        """Get active tournaments"""
        return cls.query.filter_by(status='active', is_active=True).order_by(cls.start_date.desc()).all()

    @classmethod
    def get_completed(cls):
        """Get completed tournaments"""
        return cls.query.filter_by(status='completed', is_active=True).order_by(cls.end_date.desc()).all()


class TournamentParticipant(db.Model):
    """Tournament participation"""

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    clan_id = db.Column(db.Integer, db.ForeignKey('clan.id'), nullable=True)  # For clan tournaments
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    placement = db.Column(db.Integer, nullable=True)  # Final placement (1st, 2nd, etc.)
    prize_won = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    player = db.relationship('Player', backref='tournament_participations')
    clan = db.relationship('Clan', backref='tournament_participations')

    def __repr__(self):
        return f'<TournamentParticipant {self.player_id}:{self.tournament_id}>'