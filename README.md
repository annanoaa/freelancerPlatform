# Freelance Marketplace Platform

## Project Overview

A comprehensive web-based platform connecting freelancers with clients, facilitating project creation, bidding, and collaboration. The platform leverages modern Django features to provide a robust and scalable solution for freelance work management.

## 🚀 Features

### User Management
- Custom user authentication system
- Role-based access control (Freelancer, Client, Admin)
- Email verification
- Profile management with skills and ratings

### Project Management
- Create and manage projects
- Bidding system
- Project lifecycle tracking
- Milestone management

### Communication
- Messaging system
- Notifications
- Real-time updates

## 🛠 Technical Stack

### Backend
- **Framework**: Django 5.1.4
- **Authentication**: Django REST framework, Simple JWT
- **API Documentation**: DRF-yasg (Swagger)
- **Task Processing**: Celery
- **Caching**: Redis
- **Database**: sqlite3

### Additional Technologies
- Celery for asynchronous tasks
- Redis for caching and task queue
- SMTP for email services

## 🔧 Key Technical Components

### User System
- Custom User model with roles
- JWT-based authentication
- Email verification
- Profile creation with skills

### Project Workflow
- Open bidding
- Bid submission and management
- Project assignment
- Milestone tracking
- Project completion

### Advanced Features
- Complex query optimization
- Caching mechanisms
- Asynchronous email notifications
- Role-based permissions

## 📦 Installation

### Prerequisites
- Python 3.10+
- PostgreSQL
- Redis
- Virtual Environment

### Setup Steps
1. Clone the repository
```bash
git clone https://github.com/yourusername/freelance-marketplace.git
cd freelance-marketplace
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
- Create a `.env` file based on `.env.example`
- Configure database, email, and other settings

5. Run migrations
```bash
python manage.py migrate
```

6. Start services
```bash
# Start Django development server
python manage.py runserver

# Start Celery worker
celery -A freelancerPlatform worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A freelancerPlatform beat --loglevel=info
```

## 🔐 Environment Configuration

Ensure the following environment variables are set:
- `DJANGO_SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
- `SITE_URL`


## 🚢 Deployment Considerations
- Use production-ready database (PostgreSQL)
- Configure Redis for caching and task queue
- Set up SMTP for email services
- Use gunicorn/uwsgi with Nginx
- Set `DEBUG=False` in production
- Implement proper security settings

## 📊 Project Roadmap

### Phase 1 (Completed)
- [x] User authentication
- [x] Profile management
- [x] Basic API structure
- [x] Swagger documentation


## 🤝 Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


