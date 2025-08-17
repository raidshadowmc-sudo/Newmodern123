
import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Player

@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

@pytest.fixture
def sample_player():
    """Create a sample player for testing"""
    player = Player(
        nickname="TestPlayer",
        kills=100,
        deaths=50,
        wins=25,
        games_played=30,
        experience=5000
    )
    db.session.add(player)
    db.session.commit()
    return player

def test_index_page(client):
    """Test main leaderboard page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Elite Squad' in response.data or b'Bedwars' in response.data

def test_index_page_empty_database(client):
    """Test main page works with empty database"""
    response = client.get('/')
    assert response.status_code == 200
    # Should not crash with empty database

def test_api_leaderboard_empty(client):
    """Test API leaderboard with empty database"""
    response = client.get('/api/leaderboard')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] == True
    assert data['players'] == []
    assert data['total'] == 0

def test_api_leaderboard_with_data(client, sample_player):
    """Test API leaderboard with sample data"""
    response = client.get('/api/leaderboard')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] == True
    assert len(data['players']) > 0
    assert data['total'] > 0
    
    # Check player data structure
    player_data = data['players'][0]
    assert 'nickname' in player_data
    assert 'level' in player_data
    assert 'experience' in player_data

def test_statistics_page(client):
    """Test statistics page loads"""
    response = client.get('/statistics')
    assert response.status_code == 200

def test_quests_page(client):
    """Test quests page loads"""
    response = client.get('/quests')
    assert response.status_code == 200

def test_achievements_page(client):
    """Test achievements page loads"""
    response = client.get('/achievements')
    assert response.status_code == 200

def test_shop_page(client):
    """Test shop page loads"""
    response = client.get('/shop')
    assert response.status_code == 200

def test_themes_page(client):
    """Test themes page loads"""
    response = client.get('/themes')
    assert response.status_code == 200

def test_player_profile_not_found(client):
    """Test player profile with non-existent ID"""
    response = client.get('/player/9999')
    assert response.status_code == 404

def test_player_profile_exists(client, sample_player):
    """Test player profile with existing player"""
    response = client.get(f'/player/{sample_player.id}')
    assert response.status_code == 200
    assert sample_player.nickname.encode() in response.data

def test_login_page(client):
    """Test admin login page loads"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'password' in response.data.lower()

def test_player_login_page(client):
    """Test player login page loads"""
    response = client.get('/player_login')
    assert response.status_code == 200

def test_api_stats(client):
    """Test API stats endpoint"""
    response = client.get('/api/stats')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'stats' in data
    assert 'charts' in data

# Performance test
def test_index_page_performance(client):
    """Test that main page loads reasonably fast"""
    import time
    
    start_time = time.time()
    response = client.get('/')
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 2.0  # Should load in less than 2 seconds

if __name__ == '__main__':
    # Run tests if script is executed directly
    pytest.main([__file__])
