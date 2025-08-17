
from app import app, db
from models import Badge

def create_example_badges():
    """Создать примеры бейджей"""
    
    example_badges = [
        {
            'name': 'first_blood',
            'display_name': 'Первая кровь',
            'description': 'Совершил свое первое убийство',
            'icon': 'fas fa-sword',
            'emoji': '⚔️',
            'color': '#ffffff',
            'background_color': '#dc3545',
            'border_color': '#ff6b6b',
            'rarity': 'common'
        },
        {
            'name': 'bed_destroyer',
            'display_name': 'Разрушитель кроватей',
            'description': 'Сломал 10 кроватей',
            'icon': 'fas fa-bed',
            'emoji': '🛏️',
            'color': '#ffffff',
            'background_color': '#e74c3c',
            'border_color': '#f39c12',
            'rarity': 'rare'
        },
        {
            'name': 'speed_demon',
            'display_name': 'Демон скорости',
            'description': 'Выиграл игру менее чем за 5 минут',
            'icon': 'fas fa-bolt',
            'emoji': '⚡',
            'color': '#212529',
            'has_gradient': True,
            'gradient_start': '#f1c40f',
            'gradient_end': '#e67e22',
            'border_color': '#f39c12',
            'rarity': 'epic',
            'is_animated': True
        },
        {
            'name': 'untouchable',
            'display_name': 'Неприкасаемый',
            'description': 'Выиграл игру без единой смерти',
            'icon': 'fas fa-shield-alt',
            'emoji': '🛡️',
            'color': '#ffffff',
            'has_gradient': True,
            'gradient_start': '#3498db',
            'gradient_end': '#8e44ad',
            'border_color': '#9b59b6',
            'rarity': 'legendary',
            'is_animated': True
        },
        {
            'name': 'godlike',
            'display_name': 'Божественный',
            'description': 'Достиг невероятных высот мастерства',
            'icon': 'fas fa-crown',
            'emoji': '👑',
            'color': '#ffffff',
            'has_gradient': True,
            'gradient_start': '#ff6b35',
            'gradient_end': '#f7931e',
            'border_color': '#ff6b35',
            'rarity': 'mythic',
            'is_animated': True
        }
    ]
    
    with app.app_context():
        for badge_data in example_badges:
            # Проверяем, существует ли уже такой бейдж
            existing = Badge.query.filter_by(name=badge_data['name']).first()
            if not existing:
                badge = Badge(**badge_data)
                db.session.add(badge)
                print(f"Создан бейдж: {badge_data['display_name']}")
            else:
                print(f"Бейдж {badge_data['display_name']} уже существует")
        
        db.session.commit()
        print("Примеры бейджей созданы успешно!")

if __name__ == '__main__':
    create_example_badges()
