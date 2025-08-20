# **AICS Collaboration Analyzer**

The AICS Collaboration Analyzer is a web application designed to help users analyze their chat transcripts with AI models. It provides insights into the user's collaboration patterns based on the SHAPE framework, helping them improve their prompting and interaction skills.

## 🚀 **Evolution: From Python Backend to React Frontend**

This repository showcases the evolution of the AICS app from a Python-based backend system to a modern React application with real-time SHAPE analysis.

---

## 📁 **Version 1.0 - Python Backend (Legacy)**

**Location:** `version-1/` folder

### **Features**
* **Transcript Analysis:** Users can upload a .docx or .txt file, or paste a raw chat transcript for analysis.  
* **"Light" Report (Free):** Instantly receive a high-level analysis, including:  
  * Session statistics (turn ratio, word counts).  
  * A final AI Use Classification (e.g., "Augmentor," "Assistant").  
* **"Full" Report (Email Gated):** By providing an email address, users can unlock a detailed report containing:  
  * A complete SHAPE score breakdown (Structural Vision, Human-Led Meaning, etc.).  
  * Personalized, actionable recommendations to help improve their collaboration skills to the next level.  
* **Upsell Path:** The full report includes a call-to-action to upgrade to "AICS Pro" for formal citation generation.

### **Tech Stack**
* **Backend:** Python with [FastAPI](https://fastapi.tiangolo.com/)  
* **Frontend:** HTML with [Tailwind CSS](https://tailwindcss.com/) (loaded via CDN)  
* **Templating:** [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/)  
* **File Handling:** [python-docx](https://python-docx.readthedocs.io/en/latest/) for .docx files, [chardet](https://chardet.readthedocs.io/en/latest/) for robust encoding detection.

### **Getting Started (v1.0)**
1. **Navigate to version-1 folder:** `cd version-1`
2. **Create and activate a virtual environment:**  
   ```bash
   # For macOS/Linux  
   python3 -m venv venv  
   source venv/bin/activate

   # For Windows  
   py -m venv venv  
   venv\Scripts\activate
   ```
3. **Install dependencies:** `pip install -r requirements.txt`
4. **Run the application:** `uvicorn main:app --reload`
5. **Access at:** http://127.0.0.1:8000

---

## 🎯 **Version 2.1 - React Frontend with SHAPE Analysis (Current)**

**Location:** `version-2/` folder

### **What's New**
* **Real SHAPE Analysis Engine:** 25 heuristics across 5 domains instead of mock data
* **Modern React UI:** Responsive, component-based interface
* **Real-time Pattern Detection:** Live analysis of conversation patterns
* **Enhanced User Experience:** Better file handling, validation, and feedback

### **SHAPE Analysis Domains**
- **S** (Structural Vision): Outlines, organization, flow patterns
- **H** (Human-Led Meaning): Examples, definitions, context sharing
- **A** (Authorial Voice): Tone, style, personalization requests
- **P** (Purpose Framing): Goals, audience, constraints specification
- **E** (Editorial Intervention): Corrections, improvements, refinements

### **Features**
* **File Upload:** Support for .txt and .md files
* **Text Pasting:** Direct input with character limits and validation
* **Real-time Analysis:** Live SHAPE scoring and pattern detection
* **Domain Breakdown:** Individual scores (0-20) and total score (0-100)
* **Pattern Evidence:** Shows exactly which patterns were detected
* **Actionable Insights:** Specific recommendations based on missing patterns
* **Email Reports:** Optional delivery of full analysis reports

### **Tech Stack**
* **Frontend:** React 18 with hooks (useReducer, useRef, useEffect)
* **Styling:** Tailwind CSS via CDN
* **Icons:** Lucide React
* **State Management:** useReducer for complex state
* **File Processing:** Native browser APIs

### **Getting Started (v2.1)**
1. **Navigate to version-2 folder:** `cd version-2`
2. **Install dependencies:** `npm install`
3. **Start development server:** `npm start`
4. **Access at:** http://localhost:3000

---

## 🔍 **What Changed Between Versions**

| Feature | v1.0 (Python) | v2.1 (React) |
|---------|----------------|---------------|
| **Analysis Engine** | Mock data + basic scoring | Real SHAPE analysis with 25 heuristics |
| **Scoring System** | Hardcoded collaboration levels | Pattern-based scoring (0-100) |
| **Pattern Detection** | None | Real-time regex pattern matching |
| **User Interface** | Server-rendered HTML | Interactive React components |
| **File Handling** | Server-side processing | Client-side with validation |
| **Real-time Updates** | Page refreshes | Live state updates |
| **Insights** | Generic recommendations | Pattern-specific insights |
| **Deployment** | Python backend required | Static build deployable anywhere |

---

## 🚀 **Deployment**

### **Version 1.0 (Python)**
The included Procfile is configured for deployment on platforms like Heroku or Render.
* **Build Command:** `pip install -r requirements.txt`  
* **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

### **Version 2.1 (React)**
The React version can be deployed as a static site on any platform.
* **Build Command:** `npm run build`
* **Deploy:** Upload the `build/` folder to your hosting service
* **Render.com:** Connect your GitHub repository and deploy automatically

---

## 📊 **Example Results Comparison**

### **v1.0 (Mock Data)**
```
Collaboration Level: "Strategic Partner"
Level Number: 3
Total Score: 21/25
```

### **v2.1 (Real Analysis)**
```
SHAPE Total Score: 68/100
S (Structural): 16/20 (4/5 patterns detected)
H (Human): 12/20 (3/5 patterns detected)
A (Authorial): 8/20 (2/5 patterns detected)
P (Purpose): 20/20 (5/5 patterns detected)
E (Editorial): 12/20 (3/5 patterns detected)
```

---

## 🔧 **Development**

### **Adding New Patterns**
To add new SHAPE heuristics, edit the `PAT` object in `AICS_App_v21.jsx`:
```javascript
const PAT = {
  S: [
    /\b(outline|table of contents|toc)\b/i,
    // Add your new patterns here
  ],
  // ... other domains
};
```

### **Customizing Analysis**
Modify the `generateInsightsAndRecommendations` function to add domain-specific insights and recommendations.

---

## 📝 **Contributing**

This project demonstrates the evolution of AI conversation analysis tools. Contributions are welcome for both versions!

## 📄 **License**

[Add your license information here]