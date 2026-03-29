# Project Name: open city webapp  
**Pillar:** Thriving city hall

---

## 📋 Overview
**User:** The primary users are **City of Richmond Procurement Staff** and **Departmental Contract Managers**. Secondary users include **Vendors/Contractors** seeking to understand compliance and renewal cycles.

**Problem:** Richmond staff must navigate a fragmented landscape of City, state (VITA), and federal (GSA) contracts. Critical details—like expiration dates, renewal windows, and pricing—are buried in PDFs across multiple systems, requiring hours of manual, error-prone review to ensure cost-effectiveness and legal compliance.

**Why It Matters in Richmond:** With Richmond’s budget surpassing $1 billion and recent audits highlighting the need for stronger financial oversight, the City cannot afford manual bottlenecks. This project prevents "leaving money on the table" by identifying cheaper state/federal "piggybacking" options and ensuring no contract expires without a competitive review.

**Alignment:** This aligns with **Contracting Access & Small Business Navigation**. By making contract data transparent and searchable, we lower the barrier for local vendors to compete and ensure the City’s spending is optimized for a thriving local economy.

---

## 🏗️ Proposed Solution
We are building an **Intelligent Procurement Engine** that integrates disparate municipal, state, and federal datasets into a single, searchable repository. 

### **Core User Flow:**
1. **Ingest:** Fetch data from City Socrata APIs, SAM.gov, and unstructured eVA/VITA PDFs.
2. **Process:** Clean and deduplicate data to create a "Single Source of Truth."
3. **Analyze:** Pass documents through an **LLM-powered pipeline** to extract key clauses, pricing, and renewal dates.
4. **Identify:** The system automatically flags "Piggybacking" opportunities (where state prices are lower than current city prices).
5. **Notify:** Automated alerts are sent to staff regarding upcoming expiration and renewal windows.

---

## 📊 Data & Document Sources
* **Source 1:** [City Contracts Socrata (xqn7-jvv2)](https://data.richmondgov.com/resource/xqn7-jvv2.json) - Local contract metadata.
* **Source 2:** [eVA Virginia Procurement](https://data.virginia.gov/) - Statewide contract and purchase order data.

---

## 🚀 MVP Scope (Hackathon Weekend)
* **Functional Dashboard:** A unified view of sample contracts from City and State sources.
* **PDF Intelligence:** A demo of an LLM extracting exact quotes and expiration dates from 5–10 representative procurement PDFs.
* **Early Warning System:** A "Renewal Calendar" visualization showing contracts expiring within the next 30 days.
* **Cost-Comparison:** A basic proof-of-concept showing a City contract price vs. an eVA/GSA benchmark.

### **What this project does NOT do:**
* It does **not** make legal determinations.
* It does **not** automatically award contracts.
* It does **not** replace the official City financial system (ERP).

---

## ⚠️ Risks & Limitations
* **VITA Access:** The VITA portal lacks an API; for the MVP, we are using manual extraction/scraping.
* **Document Variance:** Procurement PDFs vary in format; the LLM may require "prompt tuning" for highly non-standard layouts.
* **Data Refresh:** The prototype relies on static CSV exports for some sources rather than real-time syncing.

---

## 🎙️ Demo & Long-Term Potential
**Demo Plan:** We will show a "Before and After" scenario: A staff member searching for a contract renewal date in a 50-page PDF (the old way) vs. our dashboard instantly flagging that same date and suggesting a cheaper state-contract alternative (the new way).

**Longer-term Potential:** This could evolve into a **Public-Facing Vendor Portal**, allowing local small businesses to see exactly when contracts are coming up for bid, fostering a more competitive and equitable Richmond marketplace.
