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

**Preview**

**Cashier View**
<img width="1365" height="664" alt="cashiers" src="https://github.com/user-attachments/assets/66edf225-1d4c-426f-b031-f5f829bb0204" />

**Dashboard**
<img width="1365" height="666" alt="dashboard-sell" src="https://github.com/user-attachments/assets/223cd3de-f049-457d-9813-88758677ce1a" />

**Expense Dashboard**
<img width="1365" height="664" alt="expense" src="https://github.com/user-attachments/assets/3193d7b6-19b6-487a-8895-8dde020d0944" />

**Settings Dashboard**
<img width="1365" height="666" alt="general-settings" src="https://github.com/user-attachments/assets/49b914fe-0e41-4369-86fa-7a6b8172ec6c" />
<img width="1365" height="665" alt="settings" src="https://github.com/user-attachments/assets/51dfbc61-c624-411c-b5b2-c6a8ad8cc120" />

**Products Dashboard**
<img width="1364" height="664" alt="products" src="https://github.com/user-attachments/assets/276b0596-d961-4e23-be9d-18a9588444ac" />

**Receipts Dashboard**
<img width="1365" height="664" alt="receipt" src="https://github.com/user-attachments/assets/ee15b21c-3a35-4808-b767-f9b0701eae3c" />

**POS System**
<img width="1365" height="664" alt="sell" src="https://github.com/user-attachments/assets/9485d2f5-c825-482e-84be-ac30c940433d" />

