# CRM360 — Enterprise Customer Relationship Management System

CRM360 is a modern, enterprise-grade, full-stack Customer Relationship Management (CRM) platform built with React 19, FastAPI, and Microsoft SQL Server. It features dual authentication (Email/Password & Google OAuth 2.0 OpenID Connect), Role-Based Access Control (RBAC), multi-tenant company support, lead-to-opportunity pipeline management, geotracking, analytics dashboards, and an enterprise landing page.

---

## Tech Stack

- **Frontend:** React 19, Vite (with Rolldown code-splitting & dynamic imports), Tailwind CSS v4, React Router, Recharts, React-Leaflet, Lucide Icons.
- **Backend:** Python FastAPI, SQLAlchemy, Alembic, Pydantic v2, Google Auth (`google-auth`, `requests`), Pytest.
- **Database:** Microsoft SQL Server (via ODBC Driver 18 for SQL Server).
- **Security:** JWT Authentication (HMAC-SHA256), Google OpenID Connect ID token verification, Bcrypt password hashing, Granular RBAC (Data Scopes: Own, Team, Company, All).

---

## Key Modules & Features

1. **Enterprise Public Landing Page & Modal Auth:** Modern SaaS presentation with hero section, live feature tours, client testimonials, and unified Sign In / Get Started modal.
2. **Dual Authentication:**
   - **Email / Password:** Secure JWT issuance with password hashing.
   - **Google Sign In (GIS):** Cryptographic RSA signature verification against Google JWKS certs.
3. **Zero-Trust New User Quarantine:** New Google registrations are placed into `Pending_Approval` status with zero data permissions until an administrator assigns a Company and Role.
4. **Role-Based Access Control (RBAC):** Permissions enforced per module (`View`, `Create`, `Edit`, `Delete`) and scoped per record (`Own`, `Team`, `Company`, `All`).
5. **Dashboard & Analytics:** Real-time summary metrics, deal conversion rate, pipeline stages, revenue charts, and CSV report export.
6. **Core CRM Modules:** Leads, Opportunities (stages with stage-locking rules), Customers, Contacts, Tasks & Engagements, Meetings, Geo-Tracking & Customer Visits.
7. **Organization Administration:** Employees management, Companies, and Custom Roles & Permissions.
8. **Account Settings:** Self-service profile management, security provider detection, password update, and theme mode toggle (Light, Dark, System Default).

---

## Prerequisites

1. **Python 3.10+** (Added to PATH)
2. **Node.js 18+** & **npm**
3. **Microsoft SQL Server** (2019, 2022, or Developer / Express Edition)
4. **ODBC Driver 18 for SQL Server** installed on Windows.
5. *(Optional)* **Google Cloud OAuth 2.0 Web Client ID** (for Google Sign In).

---

## 1. Database Setup

1. Open **SQL Server Management Studio (SSMS)** or `sqlcmd`.
2. Connect to your SQL Server instance (e.g., `localhost` or your machine name).
3. Create the primary database and dedicated test database:
   ```sql
   CREATE DATABASE CRM360;
   CREATE DATABASE CRM360_Test;
   ```

---

## 2. Backend Setup & Configuration

1. Open a PowerShell terminal and navigate to the backend directory:
   ```powershell
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install required Python packages:
   ```powershell
   pip install -r requirements.txt
   ```

4. Create your backend environment configuration:
   ```powershell
   Copy-Item .env.example .env
   ```
   Open `.env` and configure:
   - `DATABASE_URL`: Connection string to your SQL Server instance (e.g., `mssql+pyodbc://username:password@localhost/CRM360?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes` or Windows Authentication `Trusted_Connection=yes`).
   - `SECRET_KEY`: A secure 32+ character random string.
   - `GOOGLE_CLIENT_ID`: (Optional) Your Google OAuth 2.0 Web Client ID.

5. Apply database migrations:
   ```powershell
   alembic upgrade head
   ```

6. Bootstrap the initial Administrator account:
   The backend provides `create_admin.py` to seed the System Administrator role, permissions, company, and initial admin employee.
   
   You can specify your desired administrator email and password via environment variables prior to running the script:
   ```powershell
   # PowerShell
   $env:ADMIN_EMAIL="admin@example.com"
   $env:ADMIN_PASSWORD="YourSecurePassword123!"
   python create_admin.py
   ```
   *(On bash/Linux/macOS, use `export ADMIN_EMAIL="admin@example.com"` and `export ADMIN_PASSWORD="YourSecurePassword123!"`).*

   > [!NOTE]
   > If `ADMIN_PASSWORD` is not set in the environment, `create_admin.py` automatically generates a secure, randomized one-time password and prints it to the terminal console during initialization.

7. Start the FastAPI development server:
   ```powershell
   uvicorn main:app --port 8000 --host 0.0.0.0 --reload
   ```
   Interactive Swagger documentation is available at: `http://localhost:8000/docs`

---

## 3. Frontend Setup & Configuration

1. Open a second PowerShell terminal and navigate to the frontend directory:
   ```powershell
   cd frontend
   ```

2. Create your frontend environment configuration:
   ```powershell
   Copy-Item .env.example .env
   ```
   In `.env`:
   - `VITE_API_URL=/api`: Relative API path (seamlessly handled by Vite's development reverse proxy to `http://127.0.0.1:8000`).
   - `VITE_GOOGLE_CLIENT_ID`: (Optional) Same Google OAuth Web Client ID configured in the backend.

3. Install Node.js dependencies:
   ```powershell
   npm install
   ```

4. Start the Vite development server:
   ```powershell
   npm run dev
   ```
   Open `http://localhost:5173/` in your browser.

---

## 4. Evaluator Walkthrough: Creating Demo Accounts & RBAC

Once logged into the application using your bootstrapped administrator credentials:

### A. Creating a Demo Employee Account
1. In the sidebar, navigate to **Employees** (`/employees`).
2. Click **Add Employee**.
3. Fill in the demo employee's Name, Email, and initial Password.
4. Select an existing Company (e.g., `CRM360 Internal`) and Role (e.g., `Sales Representative` or custom role).
5. Ensure the Status is set to **Active**.
6. Save the record. You can now open a private/incognito browser window and sign in using the demo employee's email and password.

### B. Configuring Custom Roles and Permissions (RBAC)
1. In the sidebar, navigate to **Roles** (`/roles`).
2. Click **Add Role** or edit an existing role.
3. Define the role name, description, and status.
4. Assign granular CRUD permissions per module:
   - **Modules:** `Lead`, `Opportunity`, `Customer`, `Contact`, `Activity`, `Task`, `Meeting`, `Employee`, `Company`, `Role`.
   - **Actions:** `View`, `Create`, `Edit`, `Delete`.
   - **Data Scopes:**
     - `Own`: Access restricted to records owned/created by the employee.
     - `Team`: Access restricted to records within the employee's department/team.
     - `Company`: Access restricted to records within the employee's assigned company.
     - `All`: Unrestricted cross-company access (System Administrator).

### C. Google Sign In & Zero-Trust Quarantine Workflow
1. If Google OAuth is configured, users can click **Sign in with Google** on the landing page or login screen.
2. When a new user authenticates with Google for the first time:
   - The backend cryptographically validates the token with Google JWKS.
   - The user account is automatically provisioned in a quarantined state: `status = 'Pending_Approval'` with **no Company, Role, or data permissions**.
   - The user is redirected to the `/pending-approval` holding screen and cannot access protected CRM data or endpoints.
3. **Administrator Approval:**
   - The System Administrator logs into CRM360 and navigates to **Employees**.
   - The new user appears in the employee list marked with a `Pending_Approval` badge.
   - The administrator edits the employee, assigns an authorized **Company** and **Role**, sets the status to **Active**, and saves.
   - Upon page refresh or subsequent login, the user's workspace is immediately unlocked with the permissions of their assigned role.

---

## 5. Production Build & Optimization

The frontend uses route-level dynamic code-splitting (`React.lazy` and `Suspense`) and automated chunk isolation in Vite:
```powershell
cd frontend
npm run build
```
- Heavy vendor libraries (`recharts`, `leaflet`) are isolated into dedicated chunks.
- Initial client bundle footprint is reduced by >60% compared to monolithic bundling.
- Compiled production assets are emitted into `frontend/dist`.

---

## 6. Automated Testing

All automated tests run against the isolated test database `CRM360_Test` without altering production records:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest -v
```
**Test Coverage:** 54/54 automated test cases covering:
- Authentication & JWT issuance
- Google ID token verification & quarantine gating
- Inactive user access restrictions
- RBAC scope enforcement & unauthorized access protection
- Complete Lead-to-Customer conversion workflow
- Opportunity pipeline stage transitions and lock validation
- Task, meeting, and geotracking visit lifecycles

---

## License

This project is licensed under the MIT License.
