# 🎓 Course Enrollment Analytics System

A modern, full-stack platform designed to streamline academic course management through data-driven insights. Built with a focus on automation, real-time analytics, and a premium user experience.

---

## 🚀 Key Features

- **📊 Real-time Analytics Dashboard**: Visualize enrollment trends, department distributions, and course popularity using interactive charts (powered by Recharts).
- **⚙️ Automated Seat Expansion**: Intelligent logic that automatically expands course capacity (+10 seats) when limits are reached, ensuring seamless registration.
- **👥 Multi-Role Architecture**: Specialized dashboards for **Administrators**, **Faculty**, and **Students**, each tailored with specific tools and permissions.
- **🔍 Smart Search & Discovery**: Find courses quickly with advanced filtering by department, code, or name.
- **🔔 Notifications System**: Stay updated with real-time alerts for enrollment changes, seat expansions, and administrative actions.
- **🖼️ Profile Customization**: Integrated user profiles with support for personalized photo uploads.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18+
- **Styling**: Tailwind CSS & Vanilla CSS
- **Animations**: Framer Motion
- **Visualization**: Recharts
- **Icons**: Lucide React
- **Routing**: React Router DOM

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MySQL with SQLAlchemy (Asynchronous)
- **Authentication**: JWT-based Secure Login
- **Logging**: Integrated error and activity tracking

---

## 📂 Project Structure

```bash
course-enrollment-analytics/
├── backend/            # FastAPI Server
│   ├── routes/         # API Endpoint Handlers
│   ├── models/         # Database Models (SQLAlchemy)
│   ├── schemas/        # Pydantic Data Schemas
│   ├── database/       # DB Connection & Migrations
│   └── main.py         # Application Entry Point
├── frontend/           # React Application
│   ├── src/
│   │   ├── pages/      # Dashboard & Manage Views
│   │   ├── components/ # Reusable UI Components
│   │   └── assets/     # Static Styles & Images
├── database/           # SQLite/Data Scripts (Legacy/Reference)
└── update_course.py    # Utility Scripts
```

---

## ⚙️ Getting Started

### Prerequisites
- Python 3.9+
- Node.js & npm
- MySQL Server

### Backend Setup
1. Navigate to `backend/`
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # venv\Scripts\activate on Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your MySQL connection in `database.py` or `.env`.
5. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to `frontend/`
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

---

## 💡 About This Project

This project was developed to solve the logistical challenges of manual course administration. By leveraging real-time data and automated logic, it reduces administrative overhead while providing students with a transparent and efficient enrollment experience.

---
*Created with ❤️ by [Preethika Sudhagar](https://github.com/preethikasudhagar)*