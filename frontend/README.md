# 🛡️ BorderGuard AI — Frontend Platform

> **Automated Document Screening & Forensic Inspection System**  
> Built for **Smart India Hackathon (SIH)** • Border Security & Immigration Identity Verification  
> **Author & Frontend Lead**: [Moksha](https://github.com/moksha013)

---

## 📌 Overview

**BorderGuard AI** is an intelligent border checkpoint screening platform designed to detect fraudulent identity travel documents, verify passenger biometric matches, and compute an **Explainable Risk Score** in real time. 

The frontend provides border security officers with an intuitive workstation interface to inspect documents, analyze multi-module computer vision results, export formal PDF custody reports, and monitor terminal throughput.

---

## 🚀 Key Features

### 1. 🔍 Dual-Input Checkpoint Screening (`/screening`)
- **Document Verification Box**: Drag-and-drop or file browser supporting passports, visas, and national identity cards.
- **Live Identity Capture**: Real-time HTML5 webcam stream capture for passenger facial matching and liveness verification.

### 2. 🧠 Explainable Risk Score Breakdown (`/result`)
- Replaces black-box AI scores with a **transparent mathematical breakdown** explaining *why* a traveler was cleared or flagged:
  - **Module 1**: OCR extraction integrity.
  - **Module 2**: ICAO Doc 9303 checksum validation (7-3-1 weight check digits).
  - **Module 3**: AI Tampering & Error Level Analysis (ELA) anomalies.
  - **Module 4**: Biometric facial similarity cosine score.
  - **Watchlist Check**: Cross-checkpoint duplicate identity check.

### 3. 📄 One-Click Official PDF Report Export
- Generates and downloads an official **BorderGuard Screening & Inspection Report** (`.pdf`) using `jsPDF`.
- Fully offline client-side generation containing case reference IDs, passenger OCR details, multi-module verdicts, risk breakdown, and officer signature sign-off.

### 4. 📊 Interactive Dashboard with Outcome Donut Chart (`/`)
- Replaced basic static cards with an **interactive SVG Donut/Pie Chart**:
  - 🟢 **Passed** (Clearance approved)
  - 🟡 **Needs Review** (Secondary physical inspection)
  - 🔴 **Rejected** (Fraud or tampering detected)
- Features interactive slice hover, dynamic pass-rate calculations, and categorized progress bars.

### 5. 📈 Analytics & Weekly Anomaly Trends (`/analytics`)
- **Weekly Volume & Anomaly Chart**: Visualizes daily passenger throughput and flagged security cases (Mon–Sun) with hover tooltips.
- **Common Detection Flags Breakdown**: Tracks the most frequent triggers (Expired documents, MRZ mismatches, ELA noise, face discrepancies).

### 6. 📋 Screening History & Audit Trail (`/history`)
- Real-time **Search Bar** (by ID, passenger name, or document number).
- **Status Filter Pills** (`All Records`, `PASS`, `REVIEW`, `REJECT`).
- Color-coded verdict badges and chronological inspection timestamps.

### 7. 🌓 Dark / Light Mode Workstation Theme
- Top-right theme toggle tailored for border security stations (daytime glare reduction vs. low-light nighttime eye strain).
- Automatically persists the officer's theme preference in `localStorage`.

---

## 🛠️ Tech Stack

- **Framework**: [React 19](https://react.dev/)
- **Build Tool**: [Vite 8](https://vitejs.dev/)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/)
- **Routing**: [React Router v7](https://reactrouter.com/)
- **PDF Generation**: [jsPDF](https://github.com/parallax/jsPDF)
- **Icons & Graphics**: Custom Accessible SVG Visualization Components

---

## 📂 Project Structure

```text
BorderGuard-AI-Frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── AnalyticsTrendChart.jsx  # Weekly volume & flagged trend chart
│   │   ├── CameraPanel.jsx          # Live camera feed & snapshot capture
│   │   ├── DocumentUpload.jsx       # Document file upload & image preview
│   │   ├── Header.jsx               # Top-bar status & Dark/Light mode toggle
│   │   ├── RiskScore.jsx            # Composite risk percentage badge
│   │   ├── ScreeningPieChart.jsx    # Interactive SVG Donut/Pie chart
│   │   ├── Sidebar.jsx              # Navigation sidebar with active indicators
│   │   └── StatCard.jsx             # Metric stat card component
│   ├── context/
│   │   └── ThemeContext.jsx         # Global Dark/Light theme state & storage
│   ├── pages/
│   │   ├── Analytics.jsx            # Checkpoint metrics & trends page
│   │   ├── Dashboard.jsx            # Main overview & distribution chart
│   │   ├── History.jsx              # Searchable audit trail table
│   │   ├── Result.jsx               # Explainable risk & forensic report page
│   │   └── Screening.jsx            # Checkpoint upload & camera screening page
│   ├── utils/
│   │   └── generatePdfReport.js     # jsPDF official border report generator
│   ├── App.jsx                      # Router & layout provider
│   ├── index.css                    # Tailwind CSS entry
│   └── main.jsx                     # Application bootstrap
├── package.json
└── README.md
```

---

## ⚙️ Getting Started

### Prerequisites
- Node.js (v18 or higher recommended)
- npm or yarn

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/moksha013/BorderGuard-AI-Frontend.git
   cd BorderGuard-AI-Frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the local development server:**
   ```bash
   npm run dev
   ```
   Open your browser at `http://localhost:5173`.

4. **Build for production:**
   ```bash
   npm run build
   ```

---

## 🔗 Repositories

- **Personal Standalone Frontend**: [github.com/moksha013/BorderGuard-AI-Frontend](https://github.com/moksha013/BorderGuard-AI-Frontend)
- **Team Monorepo**: `Phaneendrao0627/SIH-Border-AI` (branch: `frontend-module`)
