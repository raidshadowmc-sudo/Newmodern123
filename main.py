
from app import app, db
import os

if __name__ == '__main__':
    with app.app_context():
        try:
            # Ensure all tables are created
            db.create_all()
            print("🏗️ Database initialized successfully!")
        except Exception as e:
            print(f"Database error: {e}")
    
    # Use environment PORT or default to 5000
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
