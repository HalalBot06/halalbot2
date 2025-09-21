# components/styling.py
"""
Enhanced CSS styling and theme management for HalalBot application
Complete UI redesign with modern, professional Islamic theming
"""

import streamlit as st


def apply_custom_css():
    """Apply comprehensive modern CSS styling for HalalBot"""
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Amiri:wght@400;700&display=swap');
    
    /* Root Variables - Enhanced Islamic Color Palette */
    :root {
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
    }
    
    /* Global Styles */
    .stApp {
        background: var(--warm-white);
        font-family: 'Inter', sans-serif;
        color: var(--text-dark);
        line-height: 1.6;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: var(--gradient-subtle) !important;
        border-right: 1px solid var(--border-light);
    }
    
    .css-1d391kg .css-1v0mbdj {
        color: var(--text-dark) !important;
    }
    
    /* Main Container */
    .main .block-container {
        padding: 2rem 1rem;
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* Header Section */
    .app-header {
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
    }
    
    .logo-container {
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
    }
    
    .logo-placeholder {
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
    }
    
    .logo-text {
        color: var(--primary-green);
        font-family: 'Amiri', serif;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Typography */
    h1 {
        font-family: 'Amiri', serif !important;
        color: var(--primary-green) !important;
        text-align: center !important;
        font-size: 3rem !important;
        font-weight: 700 !important;
        margin: 1rem 0 0.5rem 0 !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .subtitle {
        text-align: center;
        color: var(--text-medium);
        font-size: 1.1rem;
        font-style: italic;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Enhanced Disclaimer Section */
    .disclaimer-container {
        background: linear-gradient(135deg, #FFF8E7 0%, #FFFBF0 100%);
        border: 2px solid var(--accent-gold);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
        box-shadow: var(--shadow-md);
    }
    
    .disclaimer-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--gradient-gold);
    }
    
    .disclaimer-container::after {
        content: '☪️';
        position: absolute;
        top: 1rem;
        right: 1.5rem;
        font-size: 1.5rem;
        opacity: 0.3;
    }
    
    .disclaimer-container h3 {
        color: var(--primary-green) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.3rem !important;
    }
    
    .disclaimer-container p {
        color: var(--text-dark) !important;
        line-height: 1.7 !important;
        font-size: 1rem !important;
        margin: 0 !important;
    }
    
    /* Search Section */
    .search-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-light);
    }
    
    .search-label {
        font-weight: 600;
        color: var(--text-dark);
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
        display: block;
    }
    
    /* Enhanced Input Styling */
    .stTextInput > div > div > input {
        border: 2px solid var(--border-medium) !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        background: white !important;
        color: var(--text-dark) !important;
        font-weight: 500 !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-green) !important;
        box-shadow: 0 0 0 3px rgba(27, 94, 63, 0.1), var(--shadow-md) !important;
        background: white !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: var(--text-light) !important;
        opacity: 0.8 !important;
    }
    
    /* Controls Section */
    .controls-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        margin: 1.5rem 0;
    }
    
    .control-group {
        background: var(--off-white);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid var(--border-light);
    }
    
    .control-label {
        font-weight: 600;
        color: var(--text-dark);
        margin-bottom: 1rem;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Enhanced Slider Styling */
    .stSlider > div > div > div {
        background: var(--gradient-primary) !important;
        height: 6px !important;
        border-radius: 3px !important;
    }
    
    .stSlider > div > div > div > div {
        background: white !important;
        border: 3px solid var(--primary-green) !important;
        box-shadow: var(--shadow-md) !important;
        width: 20px !important;
        height: 20px !important;
        border-radius: 50% !important;
    }
    
    .stSlider > div > div > div > div:hover {
        transform: scale(1.1);
        transition: transform 0.2s ease;
    }
    
    /* Enhanced Selectbox Styling */
    .stSelectbox > div > div {
        border: 2px solid var(--border-medium) !important;
        border-radius: 12px !important;
        background: white !important;
        box-shadow: var(--shadow-sm) !important;
        transition: all 0.3s ease !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: var(--primary-green) !important;
        box-shadow: 0 0 0 3px rgba(27, 94, 63, 0.1), var(--shadow-md) !important;
    }
    
    .stSelectbox div[data-baseweb="select"] > div {
        color: var(--text-dark) !important;
        font-weight: 500 !important;
    }
    
    /* Expandable Tips Section */
    .tips-section {
        margin: 1.5rem 0;
    }
    
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, var(--off-white) 0%, var(--soft-gray) 100%) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-light) !important;
        color: var(--primary-green) !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, var(--soft-gray) 0%, var(--light-gray) 100%) !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    .streamlit-expanderContent {
        border: 1px solid var(--border-light) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        background: white !important;
        padding: 1.5rem !important;
    }
    
    /* Query Display */
    .query-header {
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
    }
    
    .query-header::before {
        content: '🔍';
        margin-right: 0.75rem;
        font-size: 1.3em;
    }
    
    .query-header::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
        pointer-events: none;
    }
    
    /* Results Container */
    .results-container {
        margin-top: 2rem;
    }
    
    /* Enhanced Result Cards */
    .result-card {
        background: white;
        border: 1px solid var(--border-light);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .result-card:hover {
        box-shadow: var(--shadow-xl);
        transform: translateY(-4px);
        border-color: var(--secondary-green);
    }
    
    .result-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 5px;
        background: var(--gradient-primary);
    }
    
    /* Source-specific styling */
    .source-quran::before {
        background: var(--gradient-primary);
    }
    
    .source-hadith::before {
        background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
    }
    
    .source-fatwa::before {
        background: var(--gradient-gold);
    }
    
    .source-zakat::before {
        background: linear-gradient(135deg, #38A169 0%, #48BB78 100%);
    }
    
    /* Result Text */
    .result-text {
        color: var(--text-dark) !important;
        line-height: 1.8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
        font-family: 'Inter', sans-serif;
    }
    
    .result-text strong {
        color: var(--primary-green);
        font-weight: 600;
    }
    
    /* Source Info */
    .source-info {
        display: flex;
        gap: 1rem;
        align-items: center;
        padding-top: 1.5rem;
        border-top: 1px solid var(--border-light);
        font-size: 0.95rem;
        flex-wrap: wrap;
    }
    
    .source-badge {
        background: var(--gradient-subtle);
        color: var(--primary-green) !important;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        border: 1px solid var(--border-medium);
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
    }
    
    .source-badge:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    
    .score-badge {
        background: var(--gradient-gold);
        color: white !important;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        box-shadow: var(--shadow-md);
        transition: all 0.3s ease;
    }
    
    .score-badge:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-lg);
    }
    
    /* Enhanced Buttons */
    .stButton > button {
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
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-xl) !important;
        background: linear-gradient(135deg, #154A33 0%, #1F5F42 100%) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Feedback Section */
    .feedback-section {
        background: var(--off-white);
        border-radius: 12px;
        padding: 1rem;
        margin-top: 1rem;
        border: 1px solid var(--border-light);
    }
    
    .feedback-buttons {
        display: flex;
        gap: 0.5rem;
        justify-content: center;
    }
    
    .feedback-buttons .stButton > button {
        padding: 0.5rem 1rem !important;
        font-size: 0.9rem !important;
        min-width: 80px !important;
    }
    
    /* Alert Messages */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        box-shadow: var(--shadow-md) !important;
        padding: 1rem 1.5rem !important;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #F0FFF4 0%, #E6FFFA 100%) !important;
        border-left: 4px solid var(--success-green) !important;
        color: var(--text-dark) !important;
    }
    
    .stError {
        background: linear-gradient(135deg, #FFF5F5 0%, #FFEBEE 100%) !important;
        border-left: 4px solid var(--error-red) !important;
        color: var(--text-dark) !important;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #FFFAF0 0%, #FFF8E1 100%) !important;
        border-left: 4px solid var(--warning-orange) !important;
        color: var(--text-dark) !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #F7FAFC 0%, #EDF2F7 100%) !important;
        border-left: 4px solid var(--info-blue) !important;
        color: var(--text-dark) !important;
    }
    
    /* No Results Message */
    .no-results {
        text-align: center;
        padding: 3rem 2rem;
        background: var(--off-white);
        border-radius: 16px;
        border: 2px dashed var(--border-medium);
        margin: 2rem 0;
        color: var(--text-medium);
    }
    
    .no-results::before {
        content: '🔍';
        font-size: 3rem;
        display: block;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    /* Footer/Logout Section */
    .app-footer {
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid var(--border-light);
        text-align: center;
    }
    
    .logout-button .stButton > button {
        background: linear-gradient(135deg, #E53E3E 0%, #C53030 100%) !important;
        padding: 0.75rem 1.5rem !important;
    }
    
    .logout-button .stButton > button:hover {
        background: linear-gradient(135deg, #C53030 0%, #9C2A2A 100%) !important;
    }
    
    /* Admin Section */
    .admin-section {
        background: linear-gradient(135deg, #F7FAFC 0%, #EDF2F7 100%);
        border: 2px solid var(--border-medium);
        border-radius: 16px;
        padding: 2rem;
        margin-top: 3rem;
        box-shadow: var(--shadow-md);
    }
    
    .admin-section h3 {
        color: var(--primary-green) !important;
        margin-bottom: 1rem !important;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 0.5rem;
        }
        
        .logo-container {
            max-width: 250px;
            padding: 0.75rem;
        }
        
        .logo-placeholder {
            width: 60px;
            height: 60px;
            font-size: 1.5rem;
        }
        
        .logo-text {
            font-size: 2rem;
        }
        
        h1 {
            font-size: 2.5rem !important;
        }
        
        .controls-container {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
        
        .result-card {
            padding: 1.5rem;
        }
        
        .source-info {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.75rem;
        }
        
        .search-container {
            padding: 1.5rem;
        }
        
        .disclaimer-container {
            padding: 1.5rem;
        }
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--soft-gray);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-green);
        border-radius: 5px;
        border: 2px solid var(--soft-gray);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-green);
    }
    
    /* Loading States */
    .stSpinner {
        color: var(--primary-green) !important;
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .result-card {
        animation: fadeInUp 0.5s ease-out;
    }
    
    .search-container {
        animation: fadeInUp 0.3s ease-out;
    }
    
    .disclaimer-container {
        animation: fadeInUp 0.4s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)


def create_app_header():
    """Create the enhanced app header with logo and branding"""
    return """
    <div class="app-header">
        <div class="logo-container">
            <div class="logo-placeholder">
                ☪️
            </div>
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
    """Apply enhanced Streamlit page configuration"""
    st.set_page_config(
        page_title="HalalBot - Islamic AI Assistant",
        page_icon="☪️",
        layout="centered",
        initial_sidebar_state="auto"
    )
