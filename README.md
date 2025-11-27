# VerzendConnect - Event Ordering Platform

A complete event ordering platform built with Django, Tailwind CSS, and modern web technologies. Perfect for ordering items and services for birthdays, weddings, and private parties.

## Features

### Customer Features
- **Product Browsing**: Browse products by category and event type
- **Search & Filter**: Advanced product search and filtering
- **Shopping Cart**: Session-based cart for guests, persistent cart for users
- **Multi-step Checkout**: Streamlined checkout process
- **User Accounts**: Registration, login, profile management
- **Order Tracking**: View order history and status
- **Payment Integration**: iDEAL, PayPal, Credit Card via Mollie

### Admin Features
- **Dashboard**: Real-time analytics and statistics
- **Product Management**: Full CRUD for products, categories, event types
- **Order Management**: View, update, and manage orders
- **Customer Management**: View and manage customers
- **Email Notifications**: Automated email notifications
- **In-app Notifications**: Real-time admin notifications

## Tech Stack

- **Backend**: Django 5.0
- **Frontend**: Django Templates + Tailwind CSS
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Background Tasks**: Celery + Redis
- **Payments**: Mollie API
- **Email**: Django SMTP (dev) / Resend (prod)
- **Admin Theme**: Django Unfold
- **Containerization**: Docker + Docker Compose

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+ (for Tailwind CSS)
- Redis (for Celery)

### Installation

1. Clone the repository:
```bash
cd verzendconnect
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
npm install
```

4. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your settings
```

5. Build Tailwind CSS:
```bash
npm run build:css
# Or for development with watch mode:
npm run watch:css
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Create a superuser:
```bash
python manage.py createsuperuser
```

8. Run the development server:
```bash
python manage.py runserver
```

9. (Optional) Start Celery worker:
```bash
celery -A config worker -l INFO
```

### Docker Setup

For production-like environment:

```bash
docker-compose up -d
```

For development:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

## Project Structure

```
verzendconnect/
├── apps/
│   ├── core/              # Products, Categories, Event Types
│   ├── accounts/          # User management
│   ├── orders/            # Cart, Orders
│   ├── payments/          # Mollie integration
│   ├── dashboard/         # Admin analytics
│   └── notifications/     # Email, In-app notifications
├── config/                # Django settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── celery.py
├── templates/             # HTML templates
├── static/                # Static files (CSS, JS, images)
├── media/                 # User uploads
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `True` |
| `SECRET_KEY` | Django secret key | - |
| `DATABASE_URL` | Database connection URL | SQLite |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `MOLLIE_API_KEY` | Mollie API key | - |
| `RESEND_API_KEY` | Resend API key (prod) | - |

### Mollie Setup

1. Create an account at [mollie.com](https://mollie.com)
2. Get your API key from the dashboard
3. Add to `.env`: `MOLLIE_API_KEY=your_api_key`
4. Enable desired payment methods in Mollie dashboard

## Development

### Running Tests

```bash
python manage.py test
```

### Code Style

The project uses Python's PEP 8 style guide.

### Tailwind CSS

CSS is built using Tailwind CSS. Run the watcher during development:

```bash
npm run watch:css
```

## Deployment

### Digital Ocean

1. Create a Droplet with Docker installed
2. Clone the repository
3. Set up environment variables
4. Run with Docker Compose:

```bash
docker-compose -f docker-compose.yml up -d
```

### SSL/HTTPS

SSL is handled by Nginx with Let's Encrypt. Update `nginx.conf` with your domain.

## License

Private - All rights reserved.

## Support

For support, email support@verzendconnect.nl

