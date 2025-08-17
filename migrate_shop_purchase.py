
from app import app, db
from sqlalchemy import text

def migrate_shop_purchase():
    """Добавить новые поля в таблицу shop_purchase"""
    
    with app.app_context():
        try:
            # Проверяем, существуют ли уже новые поля
            result = db.session.execute(text("PRAGMA table_info(shop_purchase)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'price_paid_coins' not in columns:
                db.session.execute(text("ALTER TABLE shop_purchase ADD COLUMN price_paid_coins INTEGER DEFAULT 0 NOT NULL"))
                print("Добавлено поле price_paid_coins")
            
            if 'price_paid_reputation' not in columns:
                db.session.execute(text("ALTER TABLE shop_purchase ADD COLUMN price_paid_reputation INTEGER DEFAULT 0 NOT NULL"))
                print("Добавлено поле price_paid_reputation")
            
            db.session.commit()
            print("Миграция ShopPurchase завершена успешно!")
            
        except Exception as e:
            print(f"Ошибка миграции: {e}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_shop_purchase()
