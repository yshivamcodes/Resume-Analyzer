import requests, json

with open(r'C:\Users\manis\OneDrive\Desktop\resume analyser\test_resume.pdf', 'rb') as f:
    files = {'resume': ('test.pdf', f, 'application/pdf')}
    data = {'job_description': """
        Looking for a B.Tech Computer Science student with experience in:
        - Python, Pandas, NumPy, Scikit-learn, TensorFlow
        - Machine Learning, Data Science, Data Analysis
        - Streamlit, Flask for web application development
        - HTML, CSS, JavaScript
        - Feature Engineering, Data Preprocessing, EDA, Data Visualization
        - Git, GitHub
        - NLP for chatbot development
        - Prediction models using Random Forest
        - Regression models for forecasting
    """}
    resp = requests.post('http://localhost:8000/api/analyze', files=files, data=data)

result = resp.json()
print("Score breakdown:")
print(json.dumps(result['score'], indent=2))
print("Matched skills:", result['matched_skills'])
print("Missing skills:", result['missing_skills'])
