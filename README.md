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
1. Open **SQL Server Management Studio (SSMS)** or `sqlcmd`.
2. Connect to your local SQL Server instance.
3. Create the production and test databases:
```sql
CREATE DATABASE CRM360;
CREATE DATABASE CRM360_Test;
```

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

# Create your .env file from the example
Copy-Item .env.example .env
```

**Important:** Open `.env` and change `SECRET_KEY` to a securely generated random string. Update `DATABASE_URL` with your SQL Server instance name.

```powershell
# Run database migrations to construct tables
alembic upgrade head

# Create the initial Administrator account
# This reads ADMIN_EMAIL and ADMIN_PASSWORD from your .env
python create_admin.py

# Start the FastAPI backend server
uvicorn main:app --port 8000 --host 0.0.0.0 --reload
```
The API is now running at: `http://localhost:8000/docs`

## 3. Frontend Installation & Running

Open a *new* PowerShell terminal and run:

```powershell
# Navigate to frontend
cd frontend

# Create environment variables
Copy-Item .env.example .env

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
This outputs compiled assets into the `frontend/dist` directory.

## Testing

To run the automated backend test suite safely against the isolated test database (`CRM360_Test`):
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest tests/ -v
```
*(Tests utilize the `conftest.py` isolation layer and will not overwrite production data.)*
