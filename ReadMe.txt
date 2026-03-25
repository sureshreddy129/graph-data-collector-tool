# Microsoft Graph & Teams Data Collector Tool

## 📌 Project Overview

The **Microsoft Graph & Teams Data Collector Tool** is an enterprise desktop automation utility built using **Python (Tkinter)** to simplify the process of fetching Microsoft Graph and Microsoft Teams configuration data across multiple tenants.

In traditional support workflows, engineers were required to manually:

* Connect to SQL databases to retrieve tenant refresh tokens
* Configure separate Postman environments for each customer
* Generate Graph access tokens manually
* Handle refresh token expiry scenarios
* Retry API calls using different user tokens due to permission limitations
* Execute PowerShell scripts separately to fetch Teams Call Queue and Auto Attendant data

This tool automates the **entire workflow end-to-end** within a single user interface.

---

## 🎯 Key Objectives

* Reduce manual operational effort
* Eliminate dependency on Postman token management
* Automatically handle token expiry and permission fallback
* Provide unified UI for Graph and Teams data extraction
* Improve reliability and speed of support activities

---

## 🚀 Features

### ✅ Multi-Platform Database Connectivity

* Supports multiple environments (UK / US / AU)
* Dynamic platform selection
* Tenant search and selection interface

### ✅ Automated Refresh Token Handling

* Fetches **all active refresh tokens** for selected tenant
* Automatically retries API execution using next token if:

  * Token expired
  * API permission denied
  * Teams configuration access restricted

### ✅ Access Token Lifecycle Management

* Generates Microsoft Graph access tokens internally
* Tracks token expiry time
* Prompts user to regenerate token when required

### ✅ Microsoft Graph API Data Extraction

Supports APIs such as:

* Users
* Groups
* PSTN Calls
* Call Records
* Call Sessions
* User lookup APIs

Capabilities:

* Pagination handling
* Date-range filtering
* Function-style and collection APIs
* Structured JSON output

### ✅ Microsoft Teams Configuration Extraction

* Generates delegated Graph and Teams tokens automatically
* Executes MicrosoftTeams PowerShell module internally
* Fetches:

  * Call Queues
  * Auto Attendants

### ✅ Intelligent Token Fallback Logic

If one user refresh token lacks required permissions:

* Tool automatically switches to next available token
* Continues execution until success or tokens exhausted

### ✅ Responsive Execution with Progress Tracking

* Background threaded execution
* Real-time progress updates
* Cancel operation support
* Clear user feedback

### ✅ Logging and Output Management

* Detailed logs for troubleshooting
* Tenant-wise structured output folders
* JSON formatted data storage

---

## 🧠 Workflow Automation (Before vs After)

### ❌ Previous Manual Process

1. Connect to database manually
2. Retrieve refresh token
3. Create Postman environment per tenant
4. Generate access token
5. Run Graph API manually
6. Handle pagination manually
7. Retry with another token if permissions fail
8. Run PowerShell separately for Teams data

### ✅ Automated Using This Tool

1. Select platform and tenant
2. Tool fetches refresh tokens automatically
3. Access token generated internally
4. User selects required APIs
5. Tool fetches Graph and Teams data
6. Automatically handles pagination and retries
7. Falls back to next token if required
8. Saves structured output

---

## 🏗️ Architecture

```
User
  ↓
Tkinter UI (app.py)
  ↓
Data Fetch Executor (core/executor.py)
  ↓
Token Manager
  ↓
 ┌───────────────┬────────────────┐
 ↓               ↓                ↓
DB Manager     Graph Client     Teams Client
 ↓               ↓                ↓
SQL Server     Microsoft Graph   PowerShell Module
                                   ↓
                           Microsoft Teams APIs
```

### Architecture Highlights

* Modular layered design
* Separation of UI, execution, API clients and token logic
* Thread-safe progress communication
* Retry and fallback orchestration
* External PowerShell integration

---

## ⚙️ Installation

### Run from Source

```bash
pip install -r requirements.txt
python main.py
```

---

## 🔧 Configuration

Before running the tool:

1. Copy template config files:

```
Config/client_secrets.template.json → client_secrets.json
Config/db_connection.template.json → db_connection.json
```

2. Update credentials accordingly.

---

## 📂 Project Structure

```
API/
UI/
core/
DB/
utils/
Config/
PowerShell/
```

---

## 🔮 Future Enhancements

* Retry with exponential backoff
* Excel / CSV export support
* API scheduling capability
* Role-based authentication
* Web-based dashboard version
* Docker container deployment

---

## 👨‍💻 Author

Suresh Kumar Reddy
Product Support Engineer | Python Developer | DevOps Enthusiast

---

## ⭐ Contribution

Suggestions and improvements are welcome.
Please raise issues or submit pull requests.
