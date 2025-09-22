# components/styling.py
"""
Enhanced CSS styling and theme management for HalalBot application
Complete UI redesign with modern, professional Islamic theming
FIXED VERSION: Resolves HTML rendering and CSS timing issues
"""

import streamlit as st
import base64
import os
from pathlib import Path


def get_base64_image(image_path: str) -> str:
    """
    Convert image to base64 string for embedding in CSS
    
    Args:
        image_path: Path to image file
        
    Returns:
        Base64 encoded string of the image
    """
    try:
        # Try multiple possible paths
        possible_paths = [
            image_path,
            f"static/{image_path}",
            f"./{image_path}",
            f"./static/{image_path}"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()
        
        # If file not found, return empty string
        print(f"Warning: Image not found at any of these paths: {possible_paths}")
        return ""
        
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return ""


def apply_custom_css():
    """
    Apply comprehensive modern CSS styling for HalalBot
    FIXED: Ensures HTML rendering works properly
    """
    
    # Get logo as base64 for embedding
    logo_base64 = get_base64_image("halalbot_logo.png")
    logo_data_url = f"data:image/png;base64,{logo_base64}" if logo_base64 else ""
    
    # CRITICAL FIX: Use st.html instead of st.markdown for CSS
    # This ensures better CSS injection and HTML compatibility
    css_content = f"""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Amiri:wght@400;700&display=swap');
    
    /* CRITICAL: Force HTML rendering for Streamlit */
    .stMarkdown {{
        color: inherit !important;
    }}
    
    .stMarkdown > div {{
        color: inherit !important;
    }}
    
    /* Ensure unsafe_allow_html works */
    [data-testid="stMarkdownContainer"] {{
        color: inherit !important;
    }}
    
    /* Root Variables - Enhanced Islamic Color Palette */
    :root {{
        --primary-green: #1B5E3F;
        --primary-green-light: #2E7D4A;
        --secondary-green: #4A9B6B;
        --accent-gold: #D4AF37;
        --accent-gold-light: #E8C547;
        --warm-white: #FDFDF8;
        --off-white: #F9F9F4;
        --soft-gray: #F1F3F4;
        --light-gray: #E8EAF0;
        --text-dark: #1A202C;
        --text-medium: #4A5568;
        --text-light: #718096;
        --border-light: #E2E8F0;
        --border-medium: #CBD5E0;
        --success-green: #38A169;
        --error-red: #E53E3E;
        --warning-orange: #DD6B20;
        --info-blue: #3182CE;
        
        /* Shadows */
        --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        
        /* Gradients */
        --gradient-primary: linear-gradient(135deg, var(--primary-green) 0%, var(--secondary-green) 100%);
        --gradient-gold: linear-gradient(135deg, var(--accent-gold) 0%, var(--accent-gold-light) 100%);
        --gradient-subtle: linear-gradient(135deg, var(--warm-white) 0%, var(--off-white) 100%);
    }}
    
    /* CRITICAL FIX: Global Styles with Higher Specificity */
    .stApp {{
        background: var(--warm-white) !important;
        font-family: 'Inter', sans-serif !important;
        color: var(--text-dark) !important;
        line-height: 1.6 !important;
    }}
    
    /* CRITICAL FIX: Force HTML content to inherit proper styles */
    .stApp * {{
        color: inherit;
    }}
    
    /* Hide Streamlit Branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stDeployButton {{visibility: hidden;}}
    
    /* CRITICAL FIX: Enhanced Form Field Styling with Better Inheritance */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea > div > div > textarea {{
        background-color: white !important;
        color: var(--text-dark) !important;
        border: 2px solid var(--border-medium) !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-sm) !important;
        font-family: 'Inter', sans-serif !important;
    }}
    
    /* Focus states for form fields */
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus-within,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--primary-green) !important;
        box-shadow: 0 0 0 3px rgba(27, 94, 63, 0.1), var(--shadow-md) !important;
        background-color: white !important;
        color: var(--text-dark) !important;
        outline: none !important;
    }}
    
    /* Placeholder text styling */
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {{
        color: var(--text-light) !important;
        opacity: 0.8 !important;
    }}
    
    /* Form Labels */
    .stTextInput > label,
    .stSelectbox > label,
    .stTextArea > label,
    .stSlider > label {{
        color: var(--text-dark) !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
        font-family: 'Inter', sans-serif !important;
    }}
    
    /* CONVERSATIONAL INTERFACE SPECIFIC FIXES */
    
    /* Welcome Container - Fixed HTML Rendering */
    .welcome-container {{
        background: linear-gradient(135deg, #1B5E3F 0%, #2E7D4A 100%) !important;
        color: white !important;
        padding: 2rem !important;
        border-radius: 20px !important;
        margin-bottom: 2rem !important;
        text-align: center !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important;
        position: relative !important;
        overflow: hidden !important;
    }}
    
    .welcome-container * {{
        color: white !important;
    }}
    
    .welcome-container h2 {{
        margin: 0 !important;
        font-family: 'Amiri', serif !important;
        font-size: 2.5rem !important;
        color: white !important;
    }}
    
    .welcome-container p {{
        margin: 1rem 0 !important;
        font-size: 1.1rem !important;
        color: white !important;
        line-height: 1.7 !important;
    }}
    
    .welcome-container em {{
        color: white !important;
        font-style: italic !important;
    }}
    
    /* Chat Messages - Fixed HTML Rendering */
    .user-message {{
        display: flex !important;
        justify-content: flex-end !important;
        margin: 1rem 0 !important;
    }}
    
    .user-message-content {{
        background: linear-gradient(135deg, #E8F5E8 0%, #D4EDDA 100%) !important;
        color: #1B5E3F !important;
        padding: 1rem 1.5rem !important;
        border-radius: 20px 20px 5px 20px !important;
        max-width: 75% !important;
        font-weight: 500 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        border: 1px solid rgba(27, 94, 63, 0.2) !important;
    }}
    
    .ai-message {{
        display: flex !important;
        justify-content: flex-start !important;
        margin: 1rem 0 !important;
    }}
    
    .ai-message-content {{
        background: white !important;
        color: #2D3748 !important;
        padding: 1.5rem !important;
        border-radius: 20px 20px 20px 5px !important;
        max-width: 85% !important;
        border-left: 4px solid #1B5E3F !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1) !important;
        line-height: 1.6 !important;
        border: 1px solid #e2e8f0 !important;
    }}
    
    .ai-message-content * {{
        color: #2D3748 !important;
    }}
    
    .ai-message-header {{
        display: flex !important;
        align-items: center !important;
        margin-bottom: 0.75rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 1px solid #f1f3f4 !important;
    }}
    
    .ai-message-header strong {{
        margin-left: 0.5rem !important;
        color: #1B5E3F !important;
        font-size: 1.1rem !important;
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: var(--off-white);
        padding: 0.5rem;
        border-radius: 12px;
        border: 1px solid var(--border-light);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: var(--text-medium) !important;
        font-weight: 500;
        transition: all 0.3s ease;
        border: none;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: white !important;
        color: var(--primary-green) !important;
        font-weight: 600 !important;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-light) !important;
    }}
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background: var(--gradient-subtle) !important;
        border-right: 1px solid var(--border-light);
    }}
    
    section[data-testid="stSidebar"] * {{
        color: var(--text-dark) !important;
    }}
    
    /* Main Container */
    .main .block-container {{
        padding: 2rem 1rem;
        max-width: 900px;
        margin: 0 auto;
    }}
    
    /* Header Section with Logo */
    .app-header {{
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
    }}
    
    .logo-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: var(--gradient-subtle);
        border-radius: 20px;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-light);
        max-width: 300px;
        margin-left: auto;
        margin-right: auto;
    }}
    
    .logo-placeholder {{
        width: 80px;
        height: 80px;
        background: var(--gradient-primary);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin-right: 1rem;
        box-shadow: var(--shadow-md);
        background-image: url('{logo_data_url}');
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
    }}
    
    .logo-text {{
        color: var(--primary-green);
        font-family: 'Amiri', serif;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    /* Typography */
    h1 {{
        font-family: 'Amiri', serif !important;
        color: var(--primary-green) !important;
        text-align: center !important;
        font-size: 3rem !important;
        font-weight: 700 !important;
        margin: 1rem 0 0.5rem 0 !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .subtitle {{
        text-align: center;
        color: var(--text-medium);
        font-size: 1.1rem;
        font-style: italic;
        margin-bottom: 2rem;
        font-weight: 400;
    }}
    
    /* Enhanced Disclaimer Section */
    .disclaimer-container {{
        background: linear-gradient(135deg, #FFF8E7 0%, #FFFBF0 100%);
        border: 2px solid var(--accent-gold);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
        box-shadow: var(--shadow-md);
    }}
    
    .disclaimer-container::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--gradient-gold);
    }}
    
    .disclaimer-container::after {{
        content: '☪️';
        position: absolute;
        top: 1rem;
        right: 1.5rem;
        font-size: 1.5rem;
        opacity: 0.3;
    }}
    
    .disclaimer-container h3 {{
        color: var(--primary-green) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.3rem !important;
    }}
    
    .disclaimer-container p {{
        color: var(--text-dark) !important;
        line-height: 1.7 !important;
        font-size: 1rem !important;
        margin: 0 !important;
    }}
    
    /* Search Section */
    .search-container {{
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-light);
    }}
    
    .search-label {{
        font-weight: 600;
        color: var(--text-dark);
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
        display: block;
    }}
    
    /* Controls Section */
    .controls-container {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        margin: 1.5rem 0;
    }}
    
    .control-group {{
        background: var(--off-white);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid var(--border-light);
    }}
    
    .control-label {{
        font-weight: 600;
        color: var(--text-dark);
        margin-bottom: 1rem;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* Enhanced Slider Styling */
    .stSlider > div > div > div {{
        background: var(--gradient-primary) !important;
        height: 6px !important;
        border-radius: 3px !important;
    }}
    
    .stSlider > div > div > div > div {{
        background: white !important;
        border: 3px solid var(--primary-green) !important;
        box-shadow: var(--shadow-md) !important;
        width: 20px !important;
        height: 20px !important;
        border-radius: 50% !important;
    }}
    
    .stSlider > div > div > div > div:hover {{
        transform: scale(1.1);
        transition: transform 0.2s ease;
    }}
    
    /* Enhanced Button Styling */
    .stButton > button {{
        background: var(--gradient-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.875rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-md) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        font-family: 'Inter', sans-serif !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-xl) !important;
        background: linear-gradient(135deg, #154A33 0%, #1F5F42 100%) !important;
    }}
    
    .stButton > button:active {{
        transform: translateY(0) !important;
    }}
    
    /* Form Container Styling */
    .stForm {{
        background: white !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        box-shadow: var(--shadow-lg) !important;
        border: 1px solid var(--border-light) !important;
        margin: 1rem 0 !important;
    }}
    
    /* Expandable Content */
    .streamlit-expanderHeader {{
        background: linear-gradient(135deg, var(--off-white) 0%, var(--soft-gray) 100%) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-light) !important;
        color: var(--primary-green) !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        background: linear-gradient(135deg, var(--soft-gray) 0%, var(--light-gray) 100%) !important;
        box-shadow: var(--shadow-sm) !important;
    }}
    
    .streamlit-expanderContent {{
        border: 1px solid var(--border-light) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        background: white !important;
        padding: 1.5rem !important;
    }}
    
    /* Query Display */
    .query-header {{
        background: var(--gradient-primary);
        color: white !important;
        padding: 1.25rem 1.5rem;
        border-radius: 16px;
        margin: 2rem 0 1.5rem 0;
        font-weight: 600;
        box-shadow: var(--shadow-lg);
        position: relative;
        overflow: hidden;
        font-size: 1.1rem;
    }}
    
    .query-header::before {{
        content: '🔍';
        margin-right: 0.75rem;
        font-size: 1.3em;
    }}
    
    /* Results Container */
    .results-container {{
        margin-top: 2rem;
    }}
    
    /* Enhanced Result Cards */
    .result-card {{
        background: white;
        border: 1px solid var(--border-light);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}
    
    .result-card:hover {{
        box-shadow: var(--shadow-xl);
        transform: translateY(-4px);
        border-color: var(--secondary-green);
    }}
    
    .result-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 5px;
        background: var(--gradient-primary);
    }}
    
    /* Alert Messages */
    .stAlert {{
        border-radius: 12px !important;
        border: none !important;
        box-shadow: var(--shadow-md) !important;
        padding: 1rem 1.5rem !important;
    }}
    
    .stSuccess {{
        background: linear-gradient(135deg, #F0FFF4 0%, #E6FFFA 100%) !important;
        border-left: 4px solid var(--success-green) !important;
        color: var(--text-dark) !important;
    }}
    
    .stError {{
        background: linear-gradient(135deg, #FFF5F5 0%, #FFEBEE 100%) !important;
        border-left: 4px solid var(--error-red) !important;
        color: var(--text-dark) !important;
    }}
    
    .stWarning {{
        background: linear-gradient(135deg, #FFFAF0 0%, #FFF8E1 100%) !important;
        border-left: 4px solid var(--warning-orange) !important;
        color: var(--text-dark) !important;
    }}
    
    .stInfo {{
        background: linear-gradient(135deg, #F7FAFC 0%, #EDF2F7 100%) !important;
        border-left: 4px solid var(--info-blue) !important;
        color: var(--text-dark) !important;
    }}
    
    /* Login Container */
    .login-container {{
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 20px;
        box-shadow: var(--shadow-xl);
        border: 1px solid var(--border-light);
    }}
    
    /* CRITICAL: Chat container for better HTML rendering */
    .chat-container {{
        max-height: 70vh;
        overflow-y: auto;
        padding: 1rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
    }}
    
    /* Feedback container */
    .feedback-container {{
        background: linear-gradient(135deg, #F7FAFC 0%, #EDF2F7 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #E2E8F0;
    }}
    
    /* Responsive Design */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding: 1rem 0.5rem;
        }}
        
        .logo-container {{
            max-width: 250px;
            padding: 0.75rem;
        }}
        
        .logo-placeholder {{
            width: 60px;
            height: 60px;
            font-size: 1.5rem;
        }}
        
        .logo-text {{
            font-size: 2rem;
        }}
        
        h1 {{
            font-size: 2.5rem !important;
        }}
        
        .controls-container {{
            grid-template-columns: 1fr;
            gap: 1rem;
        }}
        
        .search-container {{
            padding: 1.5rem;
        }}
        
        .disclaimer-container {{
            padding: 1.5rem;
        }}
        
        .user-message-content,
        .ai-message-content {{
            max-width: 95% !important;
        }}
        
        .welcome-container {{
            padding: 1.5rem !important;
        }}
        
        .welcome-container h2 {{
            font-size: 2rem !important;
        }}
    }}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {{
        width: 10px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--soft-gray);
        border-radius: 5px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--primary-green);
        border-radius: 5px;
        border: 2px solid var(--soft-gray);
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--secondary-green);
    }}
    
    /* Animations */
    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .result-card {{
        animation: fadeInUp 0.5s ease-out;
    }}
    
    .search-container {{
        animation: fadeInUp 0.3s ease-out;
    }}
    
    .disclaimer-container {{
        animation: fadeInUp 0.4s ease-out;
    }}
    
    /* Welcome container animation */
    .welcome-container::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: shimmer 3s linear infinite;
    }}
    
    @keyframes shimmer {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """
    
    # CRITICAL: Use st.html for better CSS injection instead of st.markdown
    st.components.v1.html(css_content, height=0)
    
    # BACKUP: Also inject via markdown as fallback
    st.markdown(css_content, unsafe_allow_html=True)


def create_app_header():
    """Create the enhanced app header with logo and branding"""
    # Try to get logo as base64, fallback to emoji if not available
    logo_base64 = get_base64_image("halalbot_logo.png")
    
    if logo_base64:
        logo_element = f'<img src="data:image/png;base64,{logo_base64}" alt="HalalBot Logo" style="width: 80px; height: 80px; object-fit: contain; margin-right: 1rem;" />'
    else:
        logo_element = '<div class="logo-placeholder">☪️</div>'
    
    return f"""
    <div class="app-header">
        <div class="logo-container">
            {logo_element}
            <h2 class="logo-text">HalalBot</h2>
        </div>
        <h1>HalalBot Alpha</h1>
        <div class="subtitle">Qur'an & Hadith AI Assistant (Local RAG) — Alpha v0.2</div>
    </div>
    """


def create_disclaimer_section():
    """Create the enhanced disclaimer section"""
    return """
    <div class="disclaimer-container">
        <h3>ℹ️ Important Disclaimer</h3>
        <p>🧠 <em>Note: I am an AI assistant trained on the Qur'an, Hadith, and select scholarly sources.</em><br>
        Please consult your local Imam or a qualified scholar for specific religious rulings.</p>
    </div>
    """


def create_search_container():
    """Create the enhanced search container wrapper"""
    return """
    <div class="search-container">
    """


def create_styled_result_card(result: dict, index: int) -> str:
    """Create an enhanced styled result card"""
    source_type = result.get('category', 'other')
    
    # Enhanced icons for different source types
    source_icons = {
        'quran': '📖',
        'hadith': '📜',
        'fatwa': '⚖️',
        'zakat': '💰',
        'other': '📚'
    }
    
    icon = source_icons.get(source_type, '📚')
    source_display = result['source'].replace('.txt', '').replace('_', ' ').title()
    
    return f"""
    <div class="result-card source-{source_type}">
        <div class="result-text">
            <strong>{index}.</strong> {result['text']}
        </div>
        <div class="source-info">
            <span class="source-badge">
                {icon} {source_display}
            </span>
            <span class="score-badge">
                ⭐ Score: {result['score']:.2f}
            </span>
        </div>
    </div>
    """


def create_query_header(query: str) -> str:
    """Create an enhanced query header"""
    return f"""
    <div class="query-header">
        Query: <em>{query}</em>
    </div>
    """


def create_no_results_message() -> str:
    """Create an enhanced no results message"""
    return """
    <div class="no-results">
        <h3>No relevant answers found</h3>
        <p>Try adjusting your search terms or lowering the minimum score.</p>
    </div>
    """


def create_search_tips() -> str:
    """Create helpful search tips content"""
    return """
    **💡 Search Tips:**
    
    - **Be specific**: Instead of "prayer", try "prayer times" or "prayer requirements"
    - **Use Arabic terms**: Try "wudu", "salah", "zakat" for more precise results
    - **Ask questions**: "What is the ruling on..." or "How to perform..."
    - **Lower the score**: Reduce minimum score for broader results
    - **Filter sources**: Use source filters to focus on Quran, Hadith, or Fatwas only
    
    **Popular topics**: Prayer, Fasting, Zakat, Hajj, Marriage, Business Ethics, Halal Food
    """


def apply_page_config():
    """Apply enhanced Streamlit page configuration with favicon"""
    # Try to set favicon
    favicon_base64 = get_base64_image("halalbot_favicon.ico")
    
    page_config = {
        "page_title": "HalalBot - Islamic AI Assistant",
        "page_icon": "☪️",  # Fallback emoji
        "layout": "centered",
        "initial_sidebar_state": "auto"
    }
    
    # If we have favicon data, use it
    if favicon_base64:
        page_config["page_icon"] = f"data:image/x-icon;base64,{favicon_base64}"
    
    st.set_page_config(**page_config)


def load_static_assets():
    """
    Load and prepare static assets for the application
    This function ensures assets are properly loaded and cached
    """
    assets = {}
    
    # Try to load logo
    logo_base64 = get_base64_image("halalbot_logo.png")
    if logo_base64:
        assets['logo'] = f"data:image/png;base64,{logo_base64}"
        print("✅ Logo loaded successfully")
    else:
        print("⚠️ Logo not found, using fallback")
        assets['logo'] = None
    
    # Try to load favicon
    favicon_base64 = get_base64_image("halalbot_favicon.ico")
    if favicon_base64:
        assets['favicon'] = f"data:image/x-icon;base64,{favicon_base64}"
        print("✅ Favicon loaded successfully")
    else:
        print("⚠️ Favicon not found, using fallback")
        assets['favicon'] = None
    
    return assets


def test_static_files():
    """Test function to check if static files are accessible"""
    print("🔍 Testing static file access...")
    
    # Check current working directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    # List files in current directory
    files = os.listdir(".")
    print(f"Files in current directory: {files}")
    
    # Check if static directory exists
    if os.path.exists("static"):
        static_files = os.listdir("static")
        print(f"Files in static directory: {static_files}")
        
        # Check specific files
        logo_exists = os.path.exists("static/halalbot_logo.png")
        favicon_exists = os.path.exists("static/halalbot_favicon.ico")
        
        print(f"Logo exists: {logo_exists}")
        print(f"Favicon exists: {favicon_exists}")
        
        return logo_exists, favicon_exists
    else:
        print("❌ Static directory not found")
        return False, False


def force_html_rendering():
    """
    Force HTML rendering capability in Streamlit
    This function ensures unsafe_allow_html works properly
    """
    
    # Method 1: Inject HTML rendering enabler
    html_enabler = """
    <style>
    /* Force HTML rendering */
    .stMarkdown [data-testid="stMarkdownContainer"] {
        color: inherit !important;
    }
    
    /* Enable HTML content rendering */
    .stMarkdown > div {
        color: inherit !important;
    }
    </style>
    <script>
    // Enable HTML rendering
    if (window.parent) {
        window.parent.postMessage({type: 'enableHTML'}, '*');
    }
    </script>
    """
    
    st.components.v1.html(html_enabler, height=0)


if __name__ == "__main__":
    # Test the static file loading when run directly
    test_static_files()
    assets = load_static_assets()
    print(f"Loaded assets: {list(assets.keys())}")
