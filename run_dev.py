"""
Local development server.
Serves both the FastAPI backend and static frontend files.
Run: python run_dev.py
"""
import uvicorn
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.utils.parser import extract_text_from_pdf
from api.utils.skills import extract_skills, extract_skills_dynamic
from api.utils.scoring import compute_final_score, generate_explanations
from api.utils.ai_module import generate_suggestions, rewrite_bullet_points

app = FastAPI(title="AI Resume Analyzer — Dev Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "AI Resume Analyzer API is running"}


@app.post("/api/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        file_bytes = await resume.read()

        # 1. Parse PDF
        resume_text = extract_text_from_pdf(file_bytes)
        if not resume_text.strip():
            return {"error": "Could not extract text from the uploaded PDF. Please ensure it's a text-based PDF, not a scanned image."}

        # 2. Extract Skills
        resume_skills = extract_skills(resume_text)
        jd_skills = extract_skills_dynamic(job_description)

        # 3. Differentiate matched vs missing
        matched_skills = sorted(list(set(resume_skills) & set(jd_skills)))
        missing_skills = sorted(list(set(jd_skills) - set(resume_skills)))

        # 4. Compute scores (50/30/20 formula)
        score = compute_final_score(resume_text, job_description, matched_skills, jd_skills)

        # 5. Generate explanations
        explanations = generate_explanations(score, matched_skills, missing_skills, resume_text, job_description)

        # 6. Generate AI suggestions
        suggestions = generate_suggestions(resume_text, job_description, missing_skills)

        return {
            "score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "explanations": explanations,
            "suggestions": suggestions
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Analysis failed: {str(e)}"}


@app.post("/api/rewrite")
async def rewrite_section(
    section_text: str = Form(...),
    jd_text: str = Form("")
):
    try:
        rewritten = rewrite_bullet_points(section_text, jd_text)
        return {"improved_text": rewritten}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Rewrite failed: {str(e)}"}


# Serve static frontend files
app.mount("/styles", StaticFiles(directory="public/styles"), name="styles")
app.mount("/scripts", StaticFiles(directory="public/scripts"), name="scripts")


@app.get("/")
async def serve_index():
    return FileResponse("public/index.html")


if __name__ == "__main__":
    print("\n>> AI Resume Analyzer - Dev Server")
    print("   Frontend: http://localhost:8000")
    print("   API:      http://localhost:8000/api/health\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
