import streamlit as st
import os
from PIL import Image
import io
import google.generativeai as genai
# Try to import elevenlabs with new API structure
try:
    from elevenlabs import Voice, VoiceSettings, generate, voices, set_api_key
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    def generate(*args, **kwargs):
        st.warning("Voice generation is currently unavailable. Please check your ElevenLabs configuration.")
        return None
    def set_api_key(*args, **kwargs):
        pass
    def voices(*args, **kwargs):
        return []
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
    }

    /* Main Container */
    .stApp {
        background-color: var(--background-light);
        color: var(--text-dark);
        font-family: 'Inter', sans-serif;
    }

    /* Header Styling */
    h1 {
        color: var(--primary-green);
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    h2, h3 {
        color: var(--primary-green);
        font-weight: 600;
    }

    /* File Upload Zone */
    .uploadfile {
        border: 2px dashed var(--primary-green);
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: white;
        transition: all 0.3s ease;
    }

    .uploadfile:hover {
        border-color: var(--secondary-green);
        background: #F8FFF8;
    }

    /* Button Styling */
    .stButton > button {
        background-color: var(--primary-green);
        color: white;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: var(--secondary-green);
        transform: translateY(-2px);
        box-shadow: var(--shadow);
    }

    /* Progress Bar */
    .stProgress > div > div {
        background-color: var(--primary-green);
    }

    /* Results Container */
    .results-container {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: var(--shadow);
        margin: 1rem 0;
    }

    /* Collapsible Sections */
    .streamlit-expanderHeader {
        background-color: #F0F7F0;
        border-radius: 5px;
        padding: 0.5rem;
        font-weight: 600;
    }

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .stApp {
            padding: 1rem;
        }
        
        h1 {
            font-size: 2rem;
        }
        
        .uploadfile {
            padding: 1rem;
        }
    }

    /* Loading Animation */
    .stSpinner > div {
        border-top-color: var(--primary-green) !important;
    }

    /* Category Icons */
    .category-icon {
        font-size: 1.5rem;
        margin-right: 0.5rem;
        color: var(--primary-green);
    }

    /* Sponsor Section */
    .sponsor-logos {
        display: flex;
        justify-content: space-around;
        align-items: center;
        padding: 1.5rem;
        background-color: white;
        border-radius: 10px;
        margin: 2rem 0;
        box-shadow: var(--shadow);
    }

    .sponsor-logos img {
        height: 40px;
        margin: 0 1rem;
        transition: all 0.3s ease;
    }

    .sponsor-logos img:hover {
        transform: scale(1.1);
    }

    /* Mode Selector Styling */
    .mode-selector {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
        gap: 1rem;
    }
    
    .mode-button {
        background-color: white;
        color: var(--primary-green);
        padding: 0.5rem 2rem;
        border: 2px solid var(--primary-green);
        border-radius: 25px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .mode-button.active {
        background-color: var(--primary-green);
        color: white;
    }
    
    /* Chat Interface Styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        display: flex;
        align-items: start;
        gap: 1rem;
    }
    
    .user-message {
        background-color: #E8F5E9;
        margin-left: 2rem;
    }
    
    .bot-message {
        background-color: white;
        margin-right: 2rem;
        box-shadow: var(--shadow);
    }
    
    .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: var(--primary-green);
        color: white;
        font-weight: bold;
    }
    
    .message-content {
        flex: 1;
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
    if not ELEVENLABS_AVAILABLE:
        st.warning("Voice guidance is currently unavailable. Please check your ElevenLabs configuration.")
        return None
        
    try:
        # Get ElevenLabs API key from environment
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            st.warning("ElevenLabs API key not found. Voice guidance is unavailable.")
            return None
            
        # Set the API key
        set_api_key(api_key)
        
        # Get available voices
        available_voices = voices()
        if not available_voices:
            st.warning("No voices available. Please check your ElevenLabs API key and subscription.")
            return None
            
        # Find a voice with a more enthusiastic style
        voice_id = None
        voice_name = None
        preferred_voices = ['Bella', 'Antoni', 'Sam']
        
        for voice in available_voices:
            if voice.name in preferred_voices:
                voice_id = voice.voice_id
                voice_name = voice.name
                break
        
        # If no preferred voice found, use the first available voice
        if not voice_id and available_voices:
            voice = available_voices[0]
            voice_id = voice.voice_id
            voice_name = voice.name
            
        if not voice_id:
            st.warning("No suitable voice found.")
            return None
        
        # Generate audio using ElevenLabs
        audio = generate(
            text=text,
            voice=voice_name,
            model="eleven_monolingual_v1"
        )
        
        return audio
    except Exception as e:
        st.warning(f"Voice guidance unavailable: {str(e)}")
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

# Main app
def main():
    # Container for header
    with st.container():
        st.markdown("<h1>♻️ EcoScan - Smart Recycling Guide</h1>", unsafe_allow_html=True)
        
        # Mode selector
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            mode = st.radio(
                "Select Mode",
                ["Simple", "Advanced"],
                horizontal=True,
                label_visibility="collapsed",
                key="mode_selector"
            )
            st.session_state.mode = mode.lower()

    # Main content
    if st.session_state.mode == 'simple':
        st.markdown("""
            <div style='text-align: center; color: #666; margin-bottom: 2rem;'>
                Simple steps to recycle your items
            </div>
        """, unsafe_allow_html=True)
        
        # Simplified file uploader
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)
            
            with st.spinner("🔍 Analyzing..."):
                image_bytes = uploaded_file.getvalue()
                items = analyze_image(image_bytes)
                
                if items:
                    # Get simple instructions
                    instructions = get_recycling_instructions(", ".join(items))
                    if instructions:
                        st.markdown(f"""
                            <div style='background: #E8F5E9; padding: 1.5rem; border-radius: 10px; margin-top: 1rem;'>
                                <h3>♻️ Recycling Instructions</h3>
                                {instructions}
                                <div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #4CAF50; font-style: italic;'>
                                    💡 Tip: Switch to Advanced Mode for detailed analysis and chat support
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

    else:  # Advanced mode
        st.markdown("""
            <div style='text-align: center; color: #666; margin-bottom: 2rem;'>
                Detailed recycling analysis and AI assistance
            </div>
        """, unsafe_allow_html=True)
        
        # Create main section for image analysis
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)

            with st.spinner("🔍 Analyzing your item..."):
                image_bytes = uploaded_file.getvalue()
                items = analyze_image(image_bytes)

            if items:
                st.markdown("""
                    <div class='results-container'>
                        <h2>📋 Analysis Results</h2>
                    </div>
                """, unsafe_allow_html=True)

                # Create tabs for different sections
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
                        # Get recycling instructions using Gemini
                        recycling_advice = get_recycling_instructions(", ".join(items))
                        if recycling_advice:
                            st.markdown(f"""
                                <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: var(--shadow);'>
                                    <h3 style='color: var(--primary-green);'>♻️ Recycling Guide</h3>
                                    {recycling_advice}
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Add voice guidance
                            with st.spinner("Generating voice guidance..."):
                                summary = create_voice_summary(recycling_advice)
                                if summary:
                                    st.markdown("### 🎧 Voice Guidance")
                                    audio = generate_voice_guidance(summary)
                                    if audio:
                                        st.audio(audio, format='audio/mp3')

                with result_tab3:
                    # Get dynamic environmental impact for specific items
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
                        
                        # Display environmental impact with consistent formatting
                        st.markdown("""
                            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: var(--shadow);'>
                                <h3 style='color: var(--primary-green);'>🌍 Environmental Impact Analysis</h3>
                                {}
                            </div>
                        """.format(environmental_impact), unsafe_allow_html=True)
                        
                        # Add chat interface after environmental impact
                        st.markdown("<h3>💬 Chat with EcoBot</h3>", unsafe_allow_html=True)
                        
                        # Initialize message history if not exists
                        if 'messages' not in st.session_state:
                            st.session_state.messages = []

                        # Add clear chat button
                        if st.button("Clear Chat History", key="clear_chat"):
                            st.session_state.messages = []
                            st.session_state.thinking = False
                            st.rerun()

                        # Display chat history
                        for message in st.session_state.messages:
                            display_chat_message(message['text'], message['is_user'])
                        
                        # Chat input
                        if 'thinking' not in st.session_state:
                            st.session_state.thinking = False

                        # Chat input area
                        user_message = st.chat_input(
                            "Ask about recycling and sustainability",
                            key="chat_input",
                            disabled=st.session_state.thinking
                        )
                        
                        if user_message:
                            if not st.session_state.thinking:
                                st.session_state.thinking = True
                                
                                # Add user message to history
                                st.session_state.messages.append({"text": user_message, "is_user": True})
                                
                                # Show thinking indicator
                                with st.spinner("EcoBot is thinking..."):
                                    # Get recent context (last 3 messages)
                                    context = "\n".join([
                                        f"{'User' if m['is_user'] else 'EcoBot'}: {m['text']}" 
                                        for m in st.session_state.messages[-4:-1]
                                    ] if len(st.session_state.messages) > 1 else [])
                                    
                                    # Get bot response with all available context
                                    bot_response = get_chatbot_response(
                                        user_message,
                                        context=context,
                                        items=items,
                                        recycling_advice=recycling_advice,
                                        environmental_impact=environmental_impact
                                    )
                                
                                # Add bot response to history
                                st.session_state.messages.append({"text": bot_response, "is_user": False})
                                
                                # Reset thinking state
                                st.session_state.thinking = False
                                st.rerun()

    # Display sponsor logos
    st.markdown("""
        <div class="sponsor-logos">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Google_Cloud_logo.svg/1280px-Google_Cloud_logo.svg.png" alt="Google Cloud">
            <img src="https://avatars.githubusercontent.com/u/14957082?s=200&v=4" alt="Vercel">
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()