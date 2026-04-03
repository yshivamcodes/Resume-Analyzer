"""
AI Resume Analyzer — FastAPI Backend
Vercel Serverless Function Entry Point
"""
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from utils.parser import extract_text_from_pdf
from utils.skills import extract_skills, extract_skills_dynamic
from utils.scoring import compute_final_score, generate_explanations
from utils.ai_module import generate_suggestions, rewrite_bullet_points

app = FastAPI(
    title="AI Resume Analyzer API",
    description="Production-ready Resume Analysis engine",
    version="1.0.0"
)

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

        # 2. Extract Skills (dynamic for JD, curated for resume)
        resume_skills = extract_skills(resume_text)
        jd_skills = extract_skills_dynamic(job_description)

        # 3. Differentiate matched vs missing
        matched_skills = sorted(list(set(resume_skills) & set(jd_skills)))
        missing_skills = sorted(list(set(jd_skills) - set(resume_skills)))

        # 4. Compute scores (new 50/30/20 formula)
        score = compute_final_score(resume_text, job_description, matched_skills, jd_skills)

        # 5. Generate explanations (WHY this score)
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
        return {"error": f"Rewrite failed: {str(e)}"}


# Vercel ASGI handler
handler = Mangum(app)
