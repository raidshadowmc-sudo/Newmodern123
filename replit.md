# Overview

This is a comprehensive Minecraft Bedwars leaderboard web application built with Flask. The application tracks and displays detailed player statistics for Bedwars gameplay, including kills, deaths, beds broken, resources collected, and experience points. It features a modern gaming-themed interface with admin functionality for managing player data, plus an advanced quest system and achievements for enhanced gamification.

## Recent Updates (Aug 2025)
- ✅ Fixed admin login system (password changed to 'admin')
- ✅ Added comprehensive quest system with 8 default quests
- ✅ Implemented achievements system with rarity levels
- ✅ Enhanced navigation with quest and achievement pages
- ✅ Added demo data initialization for testing
- ✅ Fixed database query errors in statistics methods
- ✅ Integrated Minecraft skin system with NameMC support
- ✅ Added automatic skin detection for premium accounts
- ✅ Created daily/weekly/monthly quest generation system
- ✅ Built comprehensive admin panel for quest/achievement management
- ✅ Configured render.com deployment with render.yaml
- ✅ Enhanced UI with Minecraft-themed avatars and pixelated rendering
- ✅ Updated branding from "Elite Squad Bedwars" to "Elite Squad" across all templates
- ✅ Updated win rate color thresholds (40%+ yellow, 50%+ green) with theme-independent colors
- ✅ Modified experience guide performance bonuses from ≥85%/75%/50% to ≥50%/40%/25%
- ✅ Removed arbitrary role section from reputation guide benefits
- ✅ Enhanced statistics page with gradient effects and improved visual appeal
- ✅ Added comprehensive shop styling with rarity-based borders and hover effects
- ✅ Optimized JavaScript for better performance with requestAnimationFrame batching
- ✅ Added mobile optimization with reduced animations for better performance
- ✅ Prepared railway.com deployment configuration

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive design
- **Styling**: Custom CSS with gaming theme using CSS variables and modern gradients
- **JavaScript**: Vanilla JavaScript for client-side interactivity and animations
- **UI Framework**: Bootstrap 5 with dark theme and Font Awesome icons
- **Responsive Design**: Mobile-first approach with optimized layouts for different screen sizes

## Backend Architecture
- **Web Framework**: Flask with SQLAlchemy ORM for database operations
- **Database Models**: Single Player model with comprehensive Bedwars statistics tracking
- **Authentication**: Session-based admin authentication with environment variable password
- **Route Structure**: RESTful routes for player profiles, statistics, and admin functions
- **Error Handling**: Flask's built-in error handling with custom templates

## Data Architecture
- **ORM**: SQLAlchemy with DeclarativeBase for modern database modeling
- **Database Schema**: Player table with fields for game statistics, resources, and metadata
- **Data Validation**: Model-level validation and computed properties for ratios and percentages
- **Database Configuration**: Support for both SQLite (development) and PostgreSQL (production)

## Security & Configuration
- **Environment Variables**: Secure configuration for database URLs and admin passwords
- **Session Management**: Flask sessions with configurable secret keys
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxies
- **Database Connection**: Connection pooling and ping checks for reliability

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework
- **SQLAlchemy**: Database ORM and connection management
- **Werkzeug**: WSGI utilities and middleware

## Frontend Dependencies
- **Bootstrap 5**: CSS framework loaded via CDN
- **Font Awesome 6**: Icon library loaded via CDN
- **Custom CSS**: Gaming-themed styling with Minecraft color palette

## Database Support
- **SQLite**: Default development database
- **PostgreSQL**: Production database support with automatic URL conversion
- **Database Drivers**: SQLAlchemy handles driver requirements based on database URL

## Development & Deployment
- **Environment Configuration**: Uses environment variables for sensitive configuration
- **Logging**: Python's built-in logging module for debugging
- **Static File Serving**: Flask's built-in static file handling for CSS/JS assets