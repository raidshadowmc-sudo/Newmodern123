
#!/usr/bin/env python3
"""
ASCEND database migration script
"""

import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ASCENDData, Player

def migrate_ascend():
    """Create ASCEND table and initialize data for existing players"""
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if ASCENDData table exists and has data
        try:
            existing_count = ASCENDData.query.count()
            print(f"Found {existing_count} existing ASCEND records")
        except Exception as e:
            print(f"ASCEND table doesn't exist or has issues: {e}")
            existing_count = 0
        
        # Initialize ASCEND data for existing players
        players = Player.query.all()
        created_count = 0
        
        for player in players:
            existing_ascend = ASCENDData.query.filter_by(player_id=player.id).first()
            if not existing_ascend:
                # Create default ASCEND data
                ascend_data = ASCENDData(
                    player_id=player.id,
                    comment=get_default_comment(player)
                )
                db.session.add(ascend_data)
                created_count += 1
        
        db.session.commit()
        print(f"✅ ASCEND migration completed!")
        print(f"📊 Total players: {len(players)}")
        print(f"🆕 Created ASCEND records: {created_count}")
        print(f"📈 Existing ASCEND records: {existing_count}")

def get_default_comment(player):
    """Generate default comment based on player level"""
    if player.level >= 200:
        return "Legendary player with exceptional skills across all areas. Master of Bedwars with incredible game sense and clutching ability."
    elif player.level >= 150:
        return "Excellent player with strong fundamentals. Great PVP skills and tactical awareness make them a formidable opponent."
    elif player.level >= 100:
        return "Skilled player showing good understanding of game mechanics. Solid performance in most aspects of gameplay."
    elif player.level >= 75:
        return "Competent player with room for improvement. Focus on enhancing PVP skills and strategic thinking."
    elif player.level >= 50:
        return "Developing player with potential. Work on consistency and game awareness to reach the next level."
    elif player.level >= 25:
        return "Beginner with some experience. Focus on fundamentals like block placement and basic PVP techniques."
    else:
        return "New player still learning the basics. Practice regularly to improve overall gameplay and understanding."

if __name__ == "__main__":
    migrate_ascend()
