# CRM360 Application

CRM360 is a full-stack, enterprise-grade Customer Relationship Management (CRM) system built specifically with Windows Server & Microsoft SQL Server in mind. 

## Tech Stack
- **Database:** Microsoft SQL Server (ODBC Driver 18)
- **Backend:** Python FastAPI, SQLAlchemy, Alembic, Pydantic, Pytest
- **Frontend:** React 19, Vite, Tailwind CSS v4, React Router, Recharts, React-Leaflet

## Prerequisites
1. **Python 3.10+** (Added to PATH)
2. **Node.js 18+**
3. **Microsoft SQL Server** (Running locally via Windows Authentication)
4. **ODBC Driver 18 for SQL Server** installed.

## 1. Database Setup
The application is pre-configured to automatically connect to a local SQL Server instance using Windows Authentication (`Trusted_Connection=yes`) and will utilize a database named `CRM360`.

1. Open **SQL Server Management Studio (SSMS)**.
2. Connect to your local SQL Server instance using Windows Authentication.
3. Ensure the `CRM360` database exists (if not, create it manually via `CREATE DATABASE CRM360;`).
4. The backend uses Alembic to manage schemas, so you do not need to manually create any tables.

## 2. Backend Installation & Running

Open a PowerShell terminal and run the following commands:

```powershell
# Navigate to backend
cd backend

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run database migrations to construct tables
alembic upgrade head

# Start the FastAPI backend server
uvicorn main:app --port 8000 --host 0.0.0.0 --reload
```
The API is now running at: `http://localhost:8000/docs`

## 3. Frontend Installation & Running

Open a *new* PowerShell terminal and run:

```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start the React Vite dev server
npm run dev
```
The Frontend is now running at: `http://localhost:5173/`

## Production Build

To build the optimized frontend for production deployment:
```powershell
cd frontend
npm run build
```
This outputs compiled assets into the `frontend/dist` directory, optimized with Tailwind tree-shaking and LightningCSS.

## Initial Login
An administrative user must be created (or seeded) directly in the database, or you can use the test credential configured natively if you've executed the automated tests at least once:
- **Email:** `admin@crm360.com`
- **Password:** `Admin123!`
