import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.WARNING)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-replit-2024")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database for Railway
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# Ensure instance directory exists for SQLite
instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_dir, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or f'sqlite:///{os.path.join(instance_dir, "bedwars_leaderboard.db")}'
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 3,
    "max_overflow": 0,
    "pool_timeout": 10,
    "pool_recycle": 280,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Custom Jinja2 filters
@app.template_filter('unique')
def unique_filter(lst):
    """Remove duplicates from list while preserving order"""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

@app.template_filter('hex_to_rgb')
def hex_to_rgb_filter(hex_color):
    """Convert hex color to RGB values"""
    if not hex_color or not hex_color.startswith('#'):
        return "0, 0, 0"

    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return "0, 0, 0"

    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"
    except ValueError:
        return "0, 0, 0"

# Initialize the app with the extension
db.init_app(app)

# Register translation filter
from translations import register_translation_filter
register_translation_filter(app)

# Import routes first
import routes
try:
    import api_routes
except ImportError:
    pass  # API routes are optional

with app.app_context():
    # Import models to ensure tables are created
    from models import Player, Quest, PlayerQuest, Achievement, PlayerAchievement, CustomTitle, PlayerTitle, GradientTheme, PlayerGradientSetting, SiteTheme, ShopItem, ShopPurchase, CursorTheme, Clan, ClanMember, Tournament, TournamentParticipant, PlayerActiveBooster, AdminCustomRole, PlayerAdminRole, Badge, PlayerBadge

    try:
        # Always recreate tables to ensure schema is up to date
        app.logger.info("Updating database schema...")
        db.drop_all()
        db.create_all()

        # Test database connection
        db.session.execute(db.text('SELECT 1')).fetchone()

        # Initialize default data
        try:
            if SiteTheme.query.count() == 0:
                SiteTheme.create_default_themes()
        except:
            pass

        try:
            if Quest.query.count() == 0:
                Quest.create_default_quests()
        except:
            pass

        try:
            if Achievement.query.count() == 0:
                Achievement.create_default_achievements()
        except:
            pass

        try:
            if CustomTitle.query.count() == 0:
                CustomTitle.create_default_titles()
        except:
            pass

        try:
            if GradientTheme.query.count() == 0:
                GradientTheme.create_default_themes()
        except:
            pass

        try:
            if CursorTheme.query.count() == 0:
                CursorTheme.create_default_cursors()
        except:
            pass

        try:
            if ShopItem.query.count() == 0:
                ShopItem.create_default_items()
        except:
            pass

        try:
            if Badge.query.count() == 0:
                Badge.create_default_badges()
        except:
            pass

        app.logger.info("Database initialized successfully!")

    except Exception as e:
        app.logger.error(f"Database initialization error: {e}")
        # Continue anyway - errors will be handled in routes

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("🏗️ Database initialized successfully!")

    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)