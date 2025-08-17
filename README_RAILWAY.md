
# Railway Deployment Instructions

## Environment Variables
Set these environment variables in your Railway project:

1. `DATABASE_URL` - PostgreSQL connection string (automatically provided by Railway)
2. `SECRET_KEY` - Flask secret key for sessions
3. `ADMIN_PASSWORD` - Admin panel password
4. `FLASK_ENV` - Set to "production" for production deployment

## Deployment Steps

1. Connect your GitHub repository to Railway
2. Set the environment variables above
3. Railway will automatically detect the Python app and deploy it
4. Your app will be available at the provided Railway URL

## Database Setup

Railway will automatically provision a PostgreSQL database. The `DATABASE_URL` will be set automatically.

## Build Configuration

The app uses:
- `runtime.txt` to specify Python version
- `requirements.txt` for dependencies
- `railway.json` for deployment configuration
- Gunicorn as the production WSGI server
