# **AICS Collaboration Analyzer**

The AICS Collaboration Analyzer is a web application designed to help users analyze their chat transcripts with AI models. It provides insights into the user's collaboration patterns based on the SHAPE framework, helping them improve their prompting and interaction skills.

The app operates on a freemium model, providing instant value while capturing leads for a premium version.

## **Features**

* **Transcript Analysis:** Users can upload a .docx or .txt file, or paste a raw chat transcript for analysis.  
* **"Light" Report (Free):** Instantly receive a high-level analysis, including:  
  * Session statistics (turn ratio, word counts).  
  * A final AI Use Classification (e.g., "Augmentor," "Assistant").  
* **"Full" Report (Email Gated):** By providing an email address, users can unlock a detailed report containing:  
  * A complete SHAPE score breakdown (Structural Vision, Human-Led Meaning, etc.).  
  * Personalized, actionable recommendations to help improve their collaboration skills to the next level.  
* **Upsell Path:** The full report includes a call-to-action to upgrade to "AICS Pro" for formal citation generation.

## **Tech Stack**

* **Backend:** Python with [FastAPI](https://fastapi.tiangolo.com/)  
* **Frontend:** HTML with [Tailwind CSS](https://tailwindcss.com/) (loaded via CDN)  
* **Templating:** [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/)  
* **File Handling:** [python-docx](https://python-docx.readthedocs.io/en/latest/) for .docx files, [chardet](https://chardet.readthedocs.io/en/latest/) for robust encoding detection.

## **Getting Started**

To run the application locally, follow these steps:

1. **Clone the repository:**  
   git clone \<your-repository-url\>  
   cd \<your-repository-name\>

2. **Create and activate a virtual environment:**  
   \# For macOS/Linux  
   python3 \-m venv venv  
   source venv/bin/activate

   \# For Windows  
   py \-m venv venv  
   venv\\Scripts\\activate

3. Install the dependencies:  
   The requirements.txt file contains all necessary packages.  
   pip install \-r requirements.txt

4. Run the application:  
   The server will start, and you can access the app at http://127.0.0.1:8000.  
   uvicorn main:app \--reload

## **Deployment**

The included Procfile is configured for deployment on platforms like Heroku or Render.

* **Build Command:** pip install \-r requirements.txt  
* **Start Command:** uvicorn main:app \--host 0.0.0.0 \--port $PORT