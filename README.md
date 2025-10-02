## INVENTORY MANAGEMENT SYSTEM

A Django powered inventory management system used to track, manage and optimize inventory levels. The system enebales for monitoring stock levels, automation of inventory tracking, generate reports, manage expenses, track sales perfomance and also process sales through a POS System.

## DEFAULTS
superuser creds:
    username: super
    password: dashboard12345

admin creds:
    username: admin
    password: admin

Also check the preview folder, it contains some of the images of the system in use

## SYSTEM COMPONENTS:
==================
- a_core: Main application framework and settings
- b_auth: Custom user authentication system
- dashboard: Administrative interface and reporting
- pos: Point of Sale system for transactions
- reports: Reports and analytics for you business
- settings: System configuration management

## FEATURES:
=========
- Complete inventory tracking and management
- Point of sale system with transaction processing
- Administrative dashboard with analytics
- Multi-user support with custom authentication
- Configurable system settings
- Automatic backup capabilities

## Quick Start
**Environment Variables**
Create a `.env` file:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Database Setup**
```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

**Run the Server**
```
python manage.py runserver
```

Visit http://localhost:8000