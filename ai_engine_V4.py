import streamlit as st
import os
from PIL import Image
import io
import google.generativeai as genai
# Try to import elevenlabs with new API structure
try:
    from elevenlabs.api import Voice, VoiceSettings
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
    client = ElevenLabs()
    st.info("ElevenLabs package successfully imported")
except ImportError as e:
    ELEVENLABS_AVAILABLE = False
    st.error(f"Failed to import ElevenLabs: {str(e)}")
    st.error("To enable voice guidance, please run: pip install elevenlabs")
    def generate_voice(*args, **kwargs):
        st.warning("Voice generation is currently unavailable. Please install the ElevenLabs package using: pip install elevenlabs")
        return None
    Voice = None
    VoiceSettings = None

import base64
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'mode' not in st.session_state:
    st.session_state.mode = 'simple'

if 'thinking' not in st.session_state:
    st.session_state.thinking = False

# Configure page settings
st.set_page_config(
    page_title="EcoScan - Smart Recycling Guide",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add custom CSS
st.markdown("""
    <style>
    /* Global Styles and Variables */
    :root {
        --primary-green: #2E7D32;
        --secondary-green: #4CAF50;
        --accent-blue: #1565C0;
        --background-light: #F5F9F5;
        --text-dark: #1A1A1A;
        --shadow: 0 2px 4px rgba(0,0,0,0.1);
        --border-radius: 12px;
        --spacing-unit: 1rem;
    }

    /* Main Container */
    .stApp {
        background-color: var(--background-light);
        color: var(--text-dark);
        font-family: 'Inter', sans-serif;
        max-width: 1400px;
        margin: 0 auto;
        padding: calc(var(--spacing-unit) * 2);
    }

    /* Header Styling */
    .header-container {
        background: linear-gradient(135deg, #2E7D32 0%, #388E3C 100%);
        color: white;
        padding: calc(var(--spacing-unit) * 2);
        border-radius: var(--border-radius);
        margin-bottom: calc(var(--spacing-unit) * 2);
        box-shadow: var(--shadow);
        text-align: center;
    }

    .header-container h1 {
        color: white;
        font-size: 2.5rem;
        margin-bottom: var(--spacing-unit);
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    /* Mode Selector */
    .mode-selector {
        background: white;
        padding: calc(var(--spacing-unit) * 0.75);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        margin: var(--spacing-unit) 0;
        display: inline-flex;
        gap: calc(var(--spacing-unit) * 0.5);
    }

    /* File Uploader */
    .uploadfile {
        background: white;
        border: 2px dashed var(--primary-green);
        border-radius: var(--border-radius);
        padding: calc(var(--spacing-unit) * 2);
        margin: calc(var(--spacing-unit) * 2) 0;
        text-align: center;
        transition: all 0.3s ease;
    }

    .uploadfile:hover {
        border-color: var(--secondary-green);
        background: #F8FFF8;
        transform: translateY(-2px);
    }

    /* Results Container */
    .results-container {
        background: white;
        padding: calc(var(--spacing-unit) * 2);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        margin: calc(var(--spacing-unit) * 2) 0;
    }

    /* Tabs Styling */
    .stTabs {
        background: white;
        padding: var(--spacing-unit);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #f8f9fa;
        padding: calc(var(--spacing-unit) * 0.5);
        border-radius: calc(var(--border-radius) * 0.75);
        gap: calc(var(--spacing-unit) * 0.5);
    }

    .stTabs [data-baseweb="tab"] {
        background: white;
        color: var(--primary-green);
        padding: calc(var(--spacing-unit) * 0.75) calc(var(--spacing-unit) * 1.5);
        border-radius: calc(var(--border-radius) * 0.5);
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: var(--primary-green);
        color: white;
        transform: translateY(-2px);
    }

    /* Chat Interface */
    .chat-container {
        background: white;
        padding: calc(var(--spacing-unit) * 2);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        margin: calc(var(--spacing-unit) * 2) 0;
    }

    .chat-message {
        padding: calc(var(--spacing-unit) * 1.5);
        border-radius: calc(var(--border-radius) * 0.75);
        margin-bottom: var(--spacing-unit);
        display: flex;
        align-items: start;
        gap: var(--spacing-unit);
    }

    .user-message {
        background: #E8F5E9;
        margin-left: calc(var(--spacing-unit) * 2);
        border-top-left-radius: calc(var(--border-radius) * 0.25);
    }

    .bot-message {
        background: #F5F9F5;
        margin-right: calc(var(--spacing-unit) * 2);
        border-top-right-radius: calc(var(--border-radius) * 0.25);
    }

    /* Buttons and Interactive Elements */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-green) 0%, var(--secondary-green) 100%);
        color: white;
        padding: calc(var(--spacing-unit) * 0.75) calc(var(--spacing-unit) * 2);
        border-radius: calc(var(--border-radius) * 1.5);
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    /* Image Display */
    .stImage {
        background: white;
        padding: var(--spacing-unit);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
        margin: calc(var(--spacing-unit) * 2) 0;
    }

    .stImage img {
        border-radius: calc(var(--border-radius) * 0.5);
        width: 100%;
        height: auto;
    }

    /* Desktop Layout */
    @media (min-width: 992px) {
        .desktop-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: calc(var(--spacing-unit) * 2);
            align-items: start;
        }

        .full-width {
            grid-column: 1 / -1;
        }
    }

    /* Mobile Adjustments */
    @media (max-width: 991px) {
        :root {
            --spacing-unit: 0.75rem;
        }

        .header-container h1 {
            font-size: 2rem;
        }

        .stApp {
            padding: var(--spacing-unit);
        }
    }

    /* Loading States */
    .stSpinner {
        display: flex;
        justify-content: center;
        margin: calc(var(--spacing-unit) * 2) 0;
    }

    .stSpinner > div {
        border-top-color: var(--primary-green) !important;
    }

    /* Alerts and Messages */
    .stAlert {
        border-radius: var(--border-radius);
        margin: var(--spacing-unit) 0;
        padding: calc(var(--spacing-unit) * 1.25);
    }

    /* Radio Buttons */
    .stRadio > div {
        display: flex;
        gap: calc(var(--spacing-unit) * 0.5);
    }

    .stRadio label {
        background: white;
        padding: calc(var(--spacing-unit) * 0.75) calc(var(--spacing-unit) * 1.5);
        border-radius: calc(var(--border-radius) * 0.75);
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stRadio label:hover {
        background: #f8f9fa;
        transform: translateY(-2px);
    }

    /* Footer and Sponsor Section */
    .footer-section {
        margin-top: calc(var(--spacing-unit) * 3);
        padding: calc(var(--spacing-unit) * 2);
        background: white;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow);
    }

    .footer-content {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: calc(var(--spacing-unit) * 2);
        margin-bottom: calc(var(--spacing-unit) * 2);
    }

    .footer-column {
        text-align: center;
    }

    .footer-column h4 {
        color: var(--primary-green);
        margin-bottom: calc(var(--spacing-unit) * 0.75);
        font-size: 1.2rem;
    }

    .sponsor-logos {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: calc(var(--spacing-unit) * 2);
    }

    .sponsor-logos img {
        height: 40px;
        transition: all 0.3s ease;
    }

    .sponsor-logos img:hover {
        transform: scale(1.1);
    }

    .github-link {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        background: #24292e;
        color: white;
        text-decoration: none;
        border-radius: calc(var(--border-radius) * 0.5);
        font-weight: 600;
        transition: all 0.3s ease;
        margin-top: 1rem;
    }

    .github-link:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        background: #2f363d;
    }

    .github-link img {
        width: 24px;
        height: 24px;
    }
    </style>
    """, unsafe_allow_html=True)

# Add Material Icons for category icons
st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
""", unsafe_allow_html=True)

# Initialize Gemini
def init_gemini():
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            st.error("Google API key not found. Please set the GOOGLE_API_KEY environment variable.")
            return None
            
        genai.configure(api_key=api_key)
        
        # Configure generation parameters
        generation_config = {
            "temperature": 0.1,  # Lower temperature for more focused responses
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 1024,
        }
        
        # Create the model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config
        )
        return model
    except Exception as e:
        st.error(f"Error initializing Gemini: {str(e)}")
        return None

# Image recognition function
def analyze_image(image_bytes):
    model = init_gemini()
    if not model:
        return None
    
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Prepare the image for Gemini
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Generate content about the image
        prompt = """You are a recycling expert analyzing this image. Your task is to:
        1. Identify all visible objects that could be recycled or need special disposal
        2. Focus on materials like plastic, metal, glass, electronics, paper, etc.
        3. Be specific about the materials (e.g., "plastic water bottle" rather than just "bottle")
        4. List each item separately, separated by commas
        
        Format your response as a simple comma-separated list without explanations or bullets.
        Example format: plastic water bottle, aluminum can, glass jar
        
        What recyclable or disposable items do you see in this image?"""
        
        response = model.generate_content([prompt, image])
        response.resolve()  # Ensure the response is complete
        
        # Extract items from response and clean up
        text = response.text.strip()
        if not text:  # If response is empty, try a simpler prompt
            prompt = "List all visible objects in this image that could be recycled or need disposal, separated by commas:"
            response = model.generate_content([prompt, image])
            response.resolve()
            text = response.text.strip()
        
        # Split and clean items
        items = [item.strip() for item in text.split(',')]
        items = [item for item in items if item and not item.lower().startswith('i see') and not item.lower().startswith('there')]
        
        if not items:  # If still empty, try one more time with a very simple prompt
            prompt = "What objects do you see in this image? List them with commas:"
            response = model.generate_content([prompt, image])
            response.resolve()
            items = [item.strip() for item in response.text.strip().split(',')]
        
        return [item for item in items if item]
    except Exception as e:
        st.error(f"Error analyzing image: {str(e)}")
        return None

# Generate recycling advice
def get_recycling_advice(item_description):
    model = init_gemini()
    if not model:
        return None
    
    try:
        prompt = f"""As an expert in recycling and environmental sustainability, provide detailed guidance for recycling these items: {item_description}.
        
        Format your response with these EXACT sections and bullet points:

        1. Preparation Steps:
        • Clean and rinse all items thoroughly
        • Remove any non-recyclable parts
        • Separate different materials
        • Flatten or compress items if applicable

        2. Recycling/Disposal Options:
        • Curbside recycling instructions
        • Local recycling center locations
        • Special handling requirements
        • Alternative disposal methods

        3. Environmental Impact:
        • Material recovery benefits
        • Energy savings
        • Pollution reduction
        • Resource conservation

        4. Additional Tips:
        • Common recycling mistakes to avoid
        • Best practices for sorting
        • Local guidelines and requirements
        • Storage recommendations

        Provide specific, actionable details for each bullet point."""
        
        response = model.generate_content(prompt)
        response.resolve()
        return response.text
    except Exception as e:
        st.error(f"Error generating recycling advice: {str(e)}")
        return None

# Generate a concise summary for voice guidance
def create_voice_summary(advice):
    try:
        model = init_gemini()
        if not model:
            return None
            
        prompt = """Create an enthusiastic and engaging 30-second summary (approximately 75 words) of the following recycling advice. 
        Make it sound exciting and motivational, using an upbeat tone. Include encouraging phrases and positive reinforcement.
        Focus on the most important preparation steps and disposal methods. Start with an energetic greeting and end with a motivational closer.
        
        Example style:
        "Hey there, eco-warrior! Great news about recycling your [items]! Here's what you need to know... Remember, you're making a real difference!"

        Advice to summarize:
        {advice}"""
        
        response = model.generate_content(prompt.format(advice=advice))
        response.resolve()
        return response.text.strip()
    except Exception as e:
        st.error(f"Error creating summary: {str(e)}")
        return None

# Generate voice guidance
def generate_voice_guidance(text):
    try:
        if not ELEVENLABS_AVAILABLE:
            st.error("ElevenLabs package is not installed. Please run: pip install elevenlabs")
            return None
            
        # Get ElevenLabs API key from environment
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            st.error("ElevenLabs API key not found. Please add your API key to .streamlit/secrets.toml")
            st.info("You can get an API key from: https://elevenlabs.io/")
            return None
            
        # Initialize client with API key
        client = ElevenLabs(api_key=api_key)
            
        try:
            # Get available voices
            voices = client.voices.get_all()
            if not voices:
                st.error("No voices available. Please check your API key and subscription.")
                return None
                
            # Use a default voice (Antoni)
            voice = next((v for v in voices if v.name == "Antoni"), voices[0])
            
            # Generate audio using ElevenLabs
            audio = client.generate(
                text=text,
                voice=voice,
                model_id="eleven_monolingual_v1"
            )
            
            if audio:
                return audio
            else:
                st.error("Failed to generate audio. No audio data received.")
                return None
                
        except Exception as voice_error:
            st.error(f"Error with voice generation: {str(voice_error)}")
            return None
            
    except Exception as e:
        st.error(f"Voice guidance error: {str(e)}")
        return None

# Add chat functionality
def get_chatbot_response(user_message, context="", items=None, recycling_advice=None, environmental_impact=None):
    try:
        model = init_gemini()
        if not model:
            return "I'm having trouble connecting to the AI service. Please check your API key and try again."
        
        # Build comprehensive context
        full_context = []
        if items:
            full_context.append(f"Detected items in image: {', '.join(items)}")
        if recycling_advice:
            full_context.append(f"Recycling advice: {recycling_advice}")
        if environmental_impact:
            full_context.append(f"Environmental impact: {environmental_impact}")
        if context:
            full_context.append(f"Previous conversation: {context}")
            
        combined_context = "\n\n".join(full_context)
        
        prompt = f"""You are EcoBot, an expert in recycling and environmental sustainability. Your goal is to provide helpful, practical advice about recycling and environmental topics.

        Available Context:
        {combined_context}
        
        User question: {user_message}
        
        Provide a clear, friendly, and practical response that:
        1. Uses the available context about detected items and environmental impact when relevant
        2. Includes specific, actionable steps when appropriate
        3. Adds interesting environmental facts when appropriate
        4. Maintains a helpful and encouraging tone
        5. References specific items or advice from the context when applicable
        
        Keep your response concise but informative."""
        
        response = model.generate_content(prompt)
        response.resolve()
        return response.text.strip()
    except Exception as e:
        return f"I encountered an error while processing your request: {str(e)}\nPlease try rephrasing your question or try again later."

def display_chat_message(message, is_user=True):
    avatar = "👤" if is_user else "🌱"
    alignment = "user-message" if is_user else "bot-message"
    
    st.markdown(f"""
        <div class='chat-message {alignment}'>
            <div class='message-avatar'>{avatar}</div>
            <div class='message-content'>{message}</div>
        </div>
    """, unsafe_allow_html=True)

def get_recycling_instructions(items):
    try:
        model = init_gemini()
        if not model:
            return None
            
        prompt = f"""Create clear, step-by-step instructions for recycling these items: {items}.
        Format the response as numbered steps with emoji indicators.
        Include:
        1. Basic preparation steps (cleaning, sorting)
        2. Specific disposal instructions for each material
        3. One key environmental fact
        
        Keep it simple and actionable, focusing on what the user needs to do right now.
        Use friendly, encouraging language."""
        
        response = model.generate_content(prompt)
        response.resolve()
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating instructions: {str(e)}")
        return None

def get_environmental_metrics(items):
    try:
        model = init_gemini()
        if not model:
            return None
            
        prompt = f"""Analyze these items and provide environmental impact metrics: {', '.join(items)}
        
        Return the data in this EXACT JSON format:
        {{
            "carbon_footprint": {{
                "manufacturing": float (in kg CO2),
                "transportation": float (in kg CO2),
                "disposal": float (in kg CO2)
            }},
            "water_usage": {{
                "manufacturing": float (in liters),
                "recycling": float (in liters)
            }},
            "energy_savings": {{
                "recycling_vs_new": float (in kWh),
                "percentage_saved": float (0-100)
            }},
            "landfill_impact": {{
                "volume": float (in cubic meters),
                "decomposition_time": float (in years)
            }},
            "recycling_benefits": {{
                "trees_saved": float,
                "water_saved": float (in liters),
                "energy_saved": float (in kWh)
            }}
        }}
        
        Base the numbers on typical industry averages and environmental impact studies.
        Use realistic values that would make sense for these specific items."""
        
        response = model.generate_content(prompt)
        response.resolve()
        
        # Convert the response to a Python dictionary
        import json
        metrics = json.loads(response.text)
        return metrics
    except Exception as e:
        st.error(f"Error generating environmental metrics: {str(e)}")
        return None

# Main app
def main():
    # Configure page layout for better responsiveness
    st.markdown("""
        <style>
        /* Main Container */
        .block-container {
            max-width: 1400px;
            padding: 2rem 3rem;
            margin: 0 auto;
        }
        
        /* Header Styling */
        .header-container {
            text-align: center;
            margin-bottom: 2rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Mode Selector Styling */
        .mode-selector {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin: 1rem 0;
            padding: 0.5rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Improve image display */
        .stImage {
            margin: 1rem 0;
        }
        
        .stImage > img {
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
            background: white;
            padding: 0.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .stTabs [data-baseweb="tab"] {
            height: auto;
            padding: 0.75rem 1.5rem;
            background: #f8f9fa;
            border-radius: 6px;
            border: none;
            color: #2E7D32;
            font-weight: 600;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: #2E7D32;
            color: white;
        }
        
        /* Results container */
        .results-container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        
        /* Desktop specific styles */
        @media (min-width: 992px) {
            .desktop-layout {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 2rem;
                align-items: start;
            }
            
            .full-width {
                grid-column: 1 / -1;
            }
            
            .stRadio > div {
                flex-direction: row !important;
                gap: 2rem;
            }
            
            .stRadio label {
                padding: 1rem 2rem !important;
                background: #f8f9fa;
                border-radius: 8px;
                text-align: center;
                font-weight: 600;
            }
            
            .stRadio label:hover {
                background: #e9ecef;
            }
        }
        
        /* Mobile specific styles */
        @media (max-width: 991px) {
            .block-container {
                padding: 1rem;
            }
            
            .stRadio > div {
                flex-direction: column !important;
            }
            
            .stRadio label {
                margin: 0.5rem 0 !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    # Header section with improved visibility
    st.markdown("""
        <div class="header-container">
            <h1>♻️ EcoScan</h1>
            <p style="font-size: 1.2rem; opacity: 0.9;">Smart Recycling Guide</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Mode selector with improved styling
    st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
    mode = st.radio(
        "Choose Mode",
        ["Simple", "Advanced"],
        horizontal=True,
        key="mode_selector",
        label_visibility="collapsed"
    )
    st.session_state.mode = mode.lower()
    
    # Mode description with enhanced styling
    if st.session_state.mode == 'simple':
        st.markdown("""
            <div style='background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%); padding: 1.5rem; border-radius: 12px; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h3 style='color: #2E7D32; margin-bottom: 0.5rem; font-size: 1.5rem; text-align: center;'>🎯 Quick Recycling Guide</h3>
                <p style='color: #1B5E20; font-size: 1.1rem; text-align: center;'>Simply upload a photo of your items and get instant guidance</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); padding: 1.5rem; border-radius: 12px; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h3 style='color: #1565C0; margin-bottom: 0.5rem; font-size: 1.5rem; text-align: center;'>🔬 Detailed Analysis</h3>
                <p style='color: #0D47A1; font-size: 1.1rem; text-align: center;'>Get comprehensive recycling analysis with environmental impact data</p>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # File uploader with improved styling
    st.markdown("""
        <div style='background: white; padding: 2rem; border-radius: 12px; margin: 2rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <div style='text-align: center;'>
                <h3 style='color: #2E7D32; margin-bottom: 1rem; font-size: 1.3rem;'>📸 Take or Upload a Photo</h3>
                <p style='color: #666; margin-bottom: 1.5rem;'>Snap a picture or choose an image of items you want to recycle</p>
            </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload an image of items to recycle",
        type=["jpg", "jpeg", "png"],
        label_visibility="visible"  # Changed to visible for better clarity
    )

    if uploaded_file:
        if st.session_state.mode == 'simple':
            # Create a container for the image and results
            st.markdown('<div style="background: white; padding: 2rem; border-radius: 12px; box-shadow: var(--shadow);">', unsafe_allow_html=True)
            
            # Display image in a more attractive way
            image = Image.open(uploaded_file)
            st.image(image, use_column_width=True)
            
            with st.spinner("🔍 Analyzing your items..."):
                image_bytes = uploaded_file.getvalue()
                items = analyze_image(image_bytes)
                
                if items:
                    instructions = get_recycling_instructions(", ".join(items))
                    if instructions:
                        # Create a summary for voice guidance
                        summary = create_voice_summary(instructions)
                        
                        # Display results in a more engaging way
                        st.markdown(f"""
                            <div style='background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%); 
                                      padding: 2rem; 
                                      border-radius: 12px; 
                                      margin-top: 1rem; 
                                      box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                                <h3 style='color: #2E7D32; margin-bottom: 1rem; text-align: center;'>♻️ Your Recycling Guide</h3>
                                <div style='background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem;'>
                                    {instructions}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Add voice guidance
                        if summary:
                            st.markdown("""
                                <div style='background: white; padding: 1.5rem; border-radius: 8px; margin-top: 1rem;'>
                                    <h4 style='color: #2E7D32; margin-bottom: 0.5rem;'>🎧 Listen to Instructions</h4>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            audio = generate_voice_guidance(summary)
                            if audio:
                                st.audio(audio, format='audio/mp3')
                        
                        # Add a friendly call-to-action for advanced mode
                        st.markdown("""
                            <div style='margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid #4CAF50; text-align: center;'>
                                <p style='color: #2E7D32; font-style: italic;'>
                                    💡 Want more detailed analysis? Try Advanced Mode for environmental impact data and chat support!
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Advanced mode with grid layout
            st.markdown('<div class="desktop-layout">', unsafe_allow_html=True)
            
            # Image column
            st.markdown('<div>', unsafe_allow_html=True)
            image = Image.open(uploaded_file)
            st.image(image, width=600)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Analysis column
            st.markdown('<div>', unsafe_allow_html=True)
            with st.spinner("🔍 Analyzing your item..."):
                image_bytes = uploaded_file.getvalue()
                items = analyze_image(image_bytes)

            if items:
                st.markdown("""
                    <div class='results-container'>
                        <h2 style='color: #2E7D32;'>📋 Analysis Results</h2>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Full-width tabs section
            if items:
                st.markdown('<div class="full-width">', unsafe_allow_html=True)
                result_tab1, result_tab2, result_tab3 = st.tabs(["Items Detected", "Recycling Guide", "Environmental Impact"])
                
                with result_tab1:
                    for item in items:
                        st.markdown(f"""
                            <div style='display: flex; align-items: center; margin: 0.5rem 0;'>
                                <i class='material-icons category-icon'>eco</i>
                                <span>{item}</span>
                            </div>
                        """, unsafe_allow_html=True)

                with result_tab2:
                    if items:
                        recycling_advice = get_recycling_instructions(", ".join(items))
                        if recycling_advice:
                            st.markdown(f"""
                                <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: var(--shadow);'>
                                    <h3 style='color: var(--primary-green);'>♻️ Recycling Guide</h3>
                                    {recycling_advice}
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Voice guidance section with better error handling and debugging
                            st.markdown("### 🎧 Voice Guidance")
                            st.write("Debug Information:")
                            st.write("- ElevenLabs Available:", ELEVENLABS_AVAILABLE)
                            st.write("- API Key Set:", bool(os.getenv("ELEVENLABS_API_KEY")))
                            
                            if ELEVENLABS_AVAILABLE:
                                with st.spinner("Generating voice guidance..."):
                                    summary = create_voice_summary(recycling_advice)
                                    if summary:
                                        st.write("- Summary created successfully")
                                        st.write("Summary text:", summary)
                                        audio = generate_voice_guidance(summary)
                                        if audio:
                                            st.audio(audio, format='audio/mp3')
                                        else:
                                            st.error("Failed to generate audio")
                                    else:
                                        st.error("Failed to create summary")
                            else:
                                st.error("Voice guidance is currently disabled. ElevenLabs package not available.")

                with result_tab3:
                    # Get environmental metrics
                    metrics = get_environmental_metrics(items)
                    
                    if metrics:
                        # Create columns for the visualizations
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Carbon Footprint Breakdown
                            st.markdown("""
                                <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: var(--shadow); margin-bottom: 1rem;'>
                                    <h4 style='color: var(--primary-green);'>🏭 Carbon Footprint Breakdown</h4>
                            """, unsafe_allow_html=True)
                            
                            # Create a pie chart for carbon footprint
                            import plotly.express as px
                            carbon_data = metrics['carbon_footprint']
                            fig = px.pie(
                                values=list(carbon_data.values()),
                                names=list(carbon_data.keys()),
                                title='CO₂ Emissions by Stage (kg)',
                                color_discrete_sequence=px.colors.sequential.Greens
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            # Water Usage Comparison
                            st.markdown("""
                                <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: var(--shadow);'>
                                    <h4 style='color: var(--primary-green);'>💧 Water Usage Impact</h4>
                            """, unsafe_allow_html=True)
                            
                            water_data = metrics['water_usage']
                            fig = px.bar(
                                x=list(water_data.keys()),
                                y=list(water_data.values()),
                                title='Water Consumption (Liters)',
                                color_discrete_sequence=px.colors.sequential.Blues
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        with col2:
                            # Energy Savings
                            st.markdown("""
                                <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: var(--shadow); margin-bottom: 1rem;'>
                                    <h4 style='color: var(--primary-green);'>⚡ Energy Impact</h4>
                            """, unsafe_allow_html=True)
                            
                            energy_savings = metrics['energy_savings']['recycling_vs_new']
                            percentage_saved = metrics['energy_savings']['percentage_saved']
                            
                            import plotly.graph_objects as go
                            fig = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = percentage_saved,
                                title = {'text': "Energy Savings vs. New Production"},
                                gauge = {
                                    'axis': {'range': [0, 100]},
                                    'bar': {'color': "#2E7D32"},
                                    'steps': [
                                        {'range': [0, 33], 'color': "#E8F5E9"},
                                        {'range': [33, 66], 'color': "#A5D6A7"},
                                        {'range': [66, 100], 'color': "#4CAF50"}
                                    ]
                                }
                            ))
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            # Recycling Benefits
                            st.markdown("""
                                <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: var(--shadow);'>
                                    <h4 style='color: var(--primary-green);'>🌱 Environmental Benefits</h4>
                            """, unsafe_allow_html=True)
                            
                            benefits = metrics['recycling_benefits']
                            fig = px.bar(
                                x=list(benefits.keys()),
                                y=list(benefits.values()),
                                title='Positive Environmental Impact',
                                color_discrete_sequence=px.colors.sequential.Greens
                            )
                            fig.update_layout(showlegend=False)
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Additional metrics display
                        st.markdown("""
                            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: var(--shadow); margin-top: 1rem;'>
                                <h4 style='color: var(--primary-green);'>📊 Additional Impact Metrics</h4>
                                <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;'>
                        """, unsafe_allow_html=True)
                        
                        # Display landfill impact
                        landfill = metrics['landfill_impact']
                        st.markdown(f"""
                            <div style='background: #F1F8E9; padding: 1rem; border-radius: 8px;'>
                                <h5 style='color: #2E7D32; margin-bottom: 0.5rem;'>Landfill Impact</h5>
                                <p>Volume: {landfill['volume']:.2f} m³</p>
                                <p>Decomposition: {landfill['decomposition_time']:.1f} years</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("</div></div>", unsafe_allow_html=True)
                    
                    # Environmental impact text analysis
                    impact_prompt = f"""Analyze the environmental impact of recycling these items: {', '.join(items)}
                    
                    Please provide a clear, engaging analysis covering:
                    1. Immediate material impact (with specific metrics where possible)
                    2. Energy and water savings
                    3. Pollution reduction benefits
                    4. Long-term environmental benefits
                    
                    Format the response in clear, readable paragraphs with bullet points for key metrics.
                    Use an encouraging, positive tone."""
                    
                    model = init_gemini()
                    if model:
                        impact_response = model.generate_content(impact_prompt)
                        impact_response.resolve()
                        environmental_impact = impact_response.text.strip()
                        
                        st.markdown("""
                            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: var(--shadow);'>
                                <h3 style='color: var(--primary-green);'>🌍 Environmental Impact Analysis</h3>
                                {}
                            </div>
                        """.format(environmental_impact), unsafe_allow_html=True)
                        
                        # Chat interface section
                        st.markdown("<h3>💬 Chat with EcoBot</h3>", unsafe_allow_html=True)
                        
                        if 'messages' not in st.session_state:
                            st.session_state.messages = []

                        if st.button("Clear Chat History", key="clear_chat"):
                            st.session_state.messages = []
                            st.session_state.thinking = False
                            st.rerun()

                        for message in st.session_state.messages:
                            display_chat_message(message['text'], message['is_user'])
                        
                        if 'thinking' not in st.session_state:
                            st.session_state.thinking = False

                        user_message = st.chat_input(
                            "Ask about recycling and sustainability",
                            key="chat_input",
                            disabled=st.session_state.thinking
                        )
                        
                        if user_message:
                            if not st.session_state.thinking:
                                st.session_state.thinking = True
                                st.session_state.messages.append({"text": user_message, "is_user": True})
                                
                                with st.spinner("EcoBot is thinking..."):
                                    context = "\n".join([
                                        f"{'User' if m['is_user'] else 'EcoBot'}: {m['text']}" 
                                        for m in st.session_state.messages[-4:-1]
                                    ] if len(st.session_state.messages) > 1 else [])
                                    
                                    bot_response = get_chatbot_response(
                                        user_message,
                                        context=context,
                                        items=items,
                                        recycling_advice=recycling_advice,
                                        environmental_impact=environmental_impact
                                    )
                                
                                st.session_state.messages.append({"text": bot_response, "is_user": False})
                                st.session_state.thinking = False
                                st.rerun()

    # Footer section with GitHub repository
    st.markdown("""
        <div class="footer-section">
            <div class="footer-content">
                <div class="footer-column">
                    <h4>🚀 Powered By</h4>
                    <div class="sponsor-logos">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Google_Cloud_logo.svg/1280px-Google_Cloud_logo.svg.png" alt="Google Cloud">
                        <img src="https://avatars.githubusercontent.com/u/14957082?s=200&v=4" alt="Vercel">
                    </div>
                </div>
                <div class="footer-column">
                    <h4>🌟 Open Source</h4>
                    <p style="color: #666; margin-bottom: 1rem;">Contribute to EcoScan's development</p>
                    <a href="https://github.com/sadir06/Hackathon" target="_blank" class="github-link">
                        <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" alt="GitHub">
                        View on GitHub
                    </a>
                </div>
                <div class="footer-column">
                    <h4>🌍 Our Mission</h4>
                    <p style="color: #666;">Making recycling easier and more accessible through AI technology</p>
                </div>
            </div>
            <div style="text-align: center; margin-top: 2rem; color: #666; font-size: 0.9rem;">
                <p>© 2024 EcoScan. Built with ❤️ for a sustainable future.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    main()