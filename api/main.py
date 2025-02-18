from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import google.generativeai as genai
from PyPDF2 import PdfReader
import pdfplumber
import os
from dotenv import load_dotenv
import json
from mangum import Mangum

# Load environment variables
load_dotenv()

# Initialize Gemini AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI(title="LectureFlowViz API")
handler = Mangum(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using both PyPDF2 and pdfplumber for better accuracy"""
    text = ""
    
    # First try with PyPDF2
    pdf = PdfReader(pdf_file)
    for page in pdf.pages:
        text += page.extract_text() + "\n"
    
    # If PyPDF2 didn't extract much text, try pdfplumber
    if len(text.strip()) < 100:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    
    return text.strip()

def generate_flowchart(text):
    """Generate flowchart structure using Gemini AI"""
    model = genai.GenerativeModel('gemini-1.0-pro')
    
    prompt = f"""Analyze this lecture text and create a flowchart structure. 
    Return the result as a JSON object with the following structure:
    {{
        "nodes": [
            {{"id": "1", "text": "Main Topic", "level": 1}},
            {{"id": "2", "text": "Subtopic", "level": 2}},
            ...
        ],
        "edges": [
            {{"from": "1", "to": "2"}},
            ...
        ]
    }}
    
    Guidelines:
    1. Break down complex topics into simpler concepts
    2. Maintain logical flow and hierarchy
    3. Keep node text concise (max 50 characters)
    4. Create meaningful connections between related concepts
    5. Maximum 15 nodes for clarity
    
    Text to analyze:
    {text}
    """
    
    try:
        response = model.generate_content(prompt)
        response.resolve()
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating flowchart: {str(e)}")

@app.post("/api/process-pdf")
async def process_pdf(file: UploadFile):
    """Process uploaded PDF and return flowchart data"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    try:
        # Read the PDF content
        contents = await file.read()
        
        # Create a temporary file to handle the PDF
        temp_path = f"temp_{file.filename}"
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        # Extract text from PDF
        text = extract_text_from_pdf(temp_path)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Generate flowchart data
        flowchart_data = generate_flowchart(text)
        
        return JSONResponse(content=flowchart_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"} 