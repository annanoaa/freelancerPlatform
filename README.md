# Freelance Marketplace Platform

## Overview
A comprehensive web-based platform that connects freelancers with clients, facilitating project creation, bidding, and collaboration. Built with Django and Django REST Framework, this platform demonstrates advanced features including complex database queries, REST APIs, Celery task processing, and caching mechanisms.

## Features

### User Management
- **Role-based Authentication**
  - Freelancer, Client, and Admin roles
  - Custom user model with email verification
  - JWT-based authentication
  - Profile management with skills and portfolio

- **Profile Features**
  - Detailed user profiles with bio, location, and hourly rates
  - Skill management system
  - Professional links (LinkedIn, GitHub, Portfolio)
  - Rating and review system

### Project Management
- **Project Lifecycle**
  - Project creation with detailed specifications
  - Budget range setting
  - Required skills specification
  - File attachment support
  - Project status tracking (Open, In Progress, Completed, Cancelled)

- **Bidding System**
  - Freelancer bid submission
  - Proposal management
  - Bid status tracking (Pending, Accepted, Rejected, Withdrawn)
  - Budget validation

- **Milestone System**
  - Project milestone creation
  - Progress tracking
  - Payment milestone management
  - Completion verification

### Communication System
- **Messaging**
  - Real-time messaging between clients and freelancers
  - Project-specific conversations
  - File sharing in messages
  - Message read status tracking

- **Notification System**
  - Various notification types (messages, bids, project updates)
  - Email notifications
  - Real-time updates
  - Notification preferences management

## Technical Architecture

### Backend Structure
```
├── users/                 # User management app
├── projects/             # Project management app
├── communications/       # Messaging and notifications app
└── freelancerPlatform/  # Main project directory
```

### Key Components
1. **Django Apps**
   - Users: Handles authentication and user profiles
   - Projects: Manages project lifecycle and bidding
   - Communications: Handles messaging and notifications

2. **Database Models**
   - Custom User model
   - Profile model with skills
   - Project and Bid models
   - Conversation and Message models
   - Notification model

3. **API Endpoints**
   - Authentication endpoints
   - User management endpoints
   - Project management endpoints
   - Communication endpoints
   - File management endpoints

### Technical Features
1. **Advanced Security**
   - JWT Authentication
   - Permission-based access control
   - Email verification
   - Request rate limiting

2. **Performance Optimization**
   - Redis caching implementation
   - Database query optimization
   - Celery task processing
   - Efficient file handling

3. **Real-time Features**
   - Message notifications
   - Project updates
   - Bid alerts

## Installation and Setup

### Prerequisites
- Python 3.8+
- Redis Server
- Virtual Environment

### Environment Variables
```env
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:password@localhost:5432/db_name
REDIS_URL=redis://localhost:6379
EMAIL_HOST=smtp.your-email-host.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
SITE_URL=http://localhost:8000
```

### Installation Steps
1. Clone the repository
```bash
git clone <https://github.com/annanoaa/freelancerPlatform>
cd freelancer-platform
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Apply migrations
```bash
python manage.py migrate
```

5. Create superuser
```bash
python manage.py createsuperuser
```

6. Start Celery worker
```bash
celery -A freelancerPlatform worker -l info
```

7. Run development server
```bash
python manage.py runserver
```

## API Documentation
The API documentation is available through Swagger UI at `/swagger/` endpoint when the server is running.