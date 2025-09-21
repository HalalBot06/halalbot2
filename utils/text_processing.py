import re
import unicodedata
from typing import Optional, Dict, List


def clean_text(text: str, source_type: Optional[str] = None) -> str:
    """
    Main text cleaning function that handles all Islamic text sources
    
    Args:
        text: Raw text to clean
        source_type: Optional source type for specialized cleaning
    
    Returns:
        Cleaned and formatted text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Apply general cleaning first
    cleaned = _apply_general_cleaning(text)
    
    # Apply source-specific cleaning if specified
    if source_type:
        cleaned = _apply_source_specific_cleaning(cleaned, source_type.lower())
    
    # Final polishing
    cleaned = _apply_final_polish(cleaned)
    
    return cleaned.strip()


def _apply_general_cleaning(text: str) -> str:
    """Apply general text cleaning rules"""
    
    # Normalize Unicode characters
    text = unicodedata.normalize('NFKC', text)
    
    # Remove common artifacts
    text = _remove_web_artifacts(text)
    
    # Clean up whitespace and line breaks
    text = _normalize_whitespace(text)
    
    # Standardize punctuation
    text = _normalize_punctuation(text)
    
    return text


def _remove_web_artifacts(text: str) -> str:
    """Remove web artifacts and unwanted elements"""
    
    # Remove "Share:" links and related artifacts
    text = re.sub(r'\bShare:\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bShare\s+on\s+\w+\s*', '', text, flags=re.IGNORECASE)
    
    # Remove social media artifacts
    text = re.sub(r'\btweet\b|\bfacebook\b|\blinkedin\b', '', text, flags=re.IGNORECASE)
    
    # Remove HTML-like artifacts
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&\w+;', '', text)
    
    # Remove URL artifacts
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    
    # Remove navigation elements
    text = re.sub(r'\b(Home|About|Contact|Menu|Navigation)\b', '', text, flags=re.IGNORECASE)
    
    return text


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace and line breaks"""
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Clean up spaces around punctuation
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    text = re.sub(r'([,.!?;:])\s+', r'\1 ', text)
    
    # Remove trailing whitespace from lines
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    
    return text


def _normalize_punctuation(text: str) -> str:
    """Standardize punctuation marks"""
    
    # Standardize quotes - using Unicode escape sequences to avoid syntax errors
    text = re.sub(r'[\u201c\u201d\u201e]', '"', text)  # Smart double quotes
    text = re.sub(r'[\u2018\u2019\u201a]', "'", text)  # Smart single quotes
    
    # Standardize dashes
    text = re.sub(r'[\u2014\u2013]', '-', text)  # Em dash and en dash
    
    # Fix ellipsis
    text = re.sub(r'\.{3,}', '...', text)
    
    return text


def _apply_source_specific_cleaning(text: str, source_type: str) -> str:
    """Apply cleaning rules specific to Islamic text sources"""
    
    cleaners = {
        'quran': clean_quran_text,
        'hadith': clean_hadith_text,
        'fatwa': clean_fatwa_text,
        'zakat': clean_zakat_text,
        'misc': clean_misc_text
    }
    
    cleaner = cleaners.get(source_type, lambda x: x)
    return cleaner(text)


def clean_quran_text(text: str) -> str:
    """Clean Quranic text while preserving sacred content"""
    
    # Remove verse numbering artifacts
    text = re.sub(r'\[\d+:\d+\]', '', text)
    
    # Clean up English translation formatting
    text = re.sub(r'Translation:\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'English:\s*', '', text, flags=re.IGNORECASE)
    
    return text


def clean_hadith_text(text: str) -> str:
    """Clean Hadith text while preserving authenticity chains"""
    
    # Standardize hadith source references
    text = re.sub(r'Bukhari:\s*(\d+)', r'Sahih Bukhari \1:', text)
    text = re.sub(r'Muslim:\s*(\d+)', r'Sahih Muslim \1:', text)
    
    # Clean up narrator chain formatting
    text = re.sub(r'\s+reported\s+that\s+', ' reported that ', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+narrated\s+that\s+', ' narrated that ', text, flags=re.IGNORECASE)
    
    # Preserve honorific phrases
    text = _preserve_islamic_honorifics(text)
    
    return text


def clean_fatwa_text(text: str) -> str:
    """Clean Fatwa text and standardize Q&A formatting"""
    
    # Remove ANSWER: artifacts with optional Share: following
    text = re.sub(r'(ANSWER\s*:?)(\s*Share:)?', r'Answer:', text, flags=re.IGNORECASE)
    
    # Standardize Question/Answer formatting
    text = re.sub(r'Question:\s*', 'Question: ', text, flags=re.IGNORECASE)
    text = re.sub(r'Answer:\s*', '\n\nAnswer: ', text, flags=re.IGNORECASE)
    
    # Remove fatwa reference numbers
    text = re.sub(r'Fatwa\s*#?\s*\d+\s*[:-]?\s*', '', text, flags=re.IGNORECASE)
    
    # Clean up scholarly references
    text = re.sub(r'\(.*?Mufti.*?\)', '', text)
    
    # Preserve Islamic phrases and honorifics
    text = _preserve_islamic_honorifics(text)
    
    return text


def clean_zakat_text(text: str) -> str:
    """Clean Zakat calculation and ruling text"""
    
    # Standardize calculation formatting
    text = re.sub(r'Calculation:\s*', '\n\nCalculation: ', text, flags=re.IGNORECASE)
    text = re.sub(r'Example:\s*', '\n\nExample: ', text, flags=re.IGNORECASE)
    
    # Clean up currency symbols and amounts
    text = re.sub(r'\$\s+', '$', text)
    text = re.sub(r'%\s+', '%', text)
    
    # Preserve nisab and zakat terminology
    zakat_terms = ['nisab', 'hawl', 'zakat', 'sadaqah', 'khums']
    for term in zakat_terms:
        text = re.sub(f'\\b{term}\\b', term.capitalize(), text, flags=re.IGNORECASE)
    
    return text


def clean_misc_text(text: str) -> str:
    """Clean miscellaneous Islamic text"""
    
    # Apply general Q&A formatting
    text = re.sub(r'Question:\s*', 'Question: ', text, flags=re.IGNORECASE)
    text = re.sub(r'Answer:\s*', '\n\nAnswer: ', text, flags=re.IGNORECASE)
    
    # Preserve Islamic honorifics
    text = _preserve_islamic_honorifics(text)
    
    return text


def _preserve_islamic_honorifics(text: str) -> str:
    """Preserve and properly format Islamic honorifics and phrases"""
    
    # Replace common honorifics with standardized forms
    text = re.sub(r'\bSAW\b|\bsaw\b|\(saw\)|\[saw\]', '(ﷺ)', text, flags=re.IGNORECASE)
    text = re.sub(r'\bPBUH\b|\bpbuh\b|\(pbuh\)|\[pbuh\]', '(ﷺ)', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAS\b|\bas\b|\(as\)|\[as\]', '(عليه السلام)', text, flags=re.IGNORECASE)
    text = re.sub(r'\bRA\b|\bra\b|\(ra\)|\[ra\]', '(رضي الله عنه)', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSWT\b|\bswt\b|\(swt\)|\[swt\]', '(سبحانه وتعالى)', text, flags=re.IGNORECASE)
    
    return text


def _apply_final_polish(text: str) -> str:
    """Apply final polishing touches to the text"""
    
    # Ensure proper spacing after sentence endings
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
    
    # Clean up any remaining multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    
    # Ensure paragraphs are properly separated
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()


def format_qa_pair(question: str, answer: str) -> str:
    """Format a question-answer pair with proper Islamic formatting"""
    
    question = clean_text(question.strip())
    answer = clean_text(answer.strip())
    
    if not question or not answer:
        return ""
    
    # Ensure Question: prefix
    if not question.lower().startswith('question:'):
        question = f"Question: {question}"
    
    # Ensure Answer: prefix
    if not answer.lower().startswith('answer:'):
        answer = f"Answer: {answer}"
    
    return f"{question}\n\n{answer}"


def extract_qa_from_text(text: str) -> Dict[str, str]:
    """Extract question and answer from formatted text"""
    
    # Try to find question and answer patterns
    qa_pattern = r'(?:Question:\s*)(.*?)(?:\n.*?Answer:\s*)(.*?)(?:\n\n|$)'
    match = re.search(qa_pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        return {
            'question': clean_text(match.group(1)),
            'answer': clean_text(match.group(2))
        }
    
    # If no clear Q&A pattern, return the whole text as answer
    return {
        'question': '',
        'answer': clean_text(text)
    }


def format_source_reference(source: str, category: str = None) -> str:
    """Format source references for display"""
    
    if not source:
        return "Unknown Source"
    
    # Clean up source name
    source = source.replace('.txt', '').replace('_', ' ')
    
    # Add category prefix if available
    if category:
        category_prefixes = {
            'quran': '📖 Quran',
            'hadith': '📜 Hadith',
            'fatwa': '⚖️ Fatwa',
            'zakat': '💰 Zakat',
            'misc': '📚 Islamic Text'
        }
        prefix = category_prefixes.get(category.lower(), '📚')
        return f"{prefix}: {source.title()}"
    
    return source.title()


def validate_islamic_text(text: str) -> List[str]:
    """Validate Islamic text and return list of potential issues"""
    
    issues = []
    
    if not text or len(text.strip()) < 10:
        issues.append("Text is too short or empty")
    
    # Check for potentially problematic content
    if re.search(r'\b(error|404|not found)\b', text, re.IGNORECASE):
        issues.append("Text may contain error messages")
    
    # Check for proper Islamic formatting
    if 'question:' in text.lower() and 'answer:' not in text.lower():
        issues.append("Question found but no answer")
    
    # Check for excessive formatting artifacts
    if text.count('\n') > len(text) * 0.1:
        issues.append("Excessive line breaks detected")
    
    if len(re.findall(r'[^\w\s\u0600-\u06FF]', text)) > len(text) * 0.2:
        issues.append("Excessive special characters detected")
    
    return issues


def get_text_stats(text: str) -> Dict[str, int]:
    """Get statistics about the text"""
    
    if not text:
        return {}
    
    return {
        'total_chars': len(text),
        'total_words': len(text.split()),
        'total_lines': text.count('\n') + 1,
        'arabic_chars': len(re.findall(r'[\u0600-\u06FF]', text)),
        'questions': len(re.findall(r'question:', text, re.IGNORECASE)),
        'answers': len(re.findall(r'answer:', text, re.IGNORECASE))
    }


def clean_text_batch(texts: List[str], source_types: List[str] = None) -> List[str]:
    """Clean a batch of texts efficiently"""
    
    if source_types is None:
        source_types = [None] * len(texts)
    
    return [
        clean_text(text, source_type)
        for text, source_type in zip(texts, source_types)
    ]


def process_corpus_data(corpus_data: List[Dict], text_field: str = 'text') -> List[Dict]:
    """Process corpus data and clean text fields"""
    
    processed = []
    
    for item in corpus_data:
        if text_field in item:
            # Determine source type from the item
            source_type = item.get('source', item.get('category', None))
            
            # Clean the text
            cleaned_text = clean_text(item[text_field], source_type)
            
            # Update the item
            item = item.copy()
            item[text_field] = cleaned_text
            
            # Add validation info
            issues = validate_islamic_text(cleaned_text)
            if not issues:
                processed.append(item)
    
    return processed


def quick_clean(text: str) -> str:
    """Quick text cleaning for simple use cases"""
    return clean_text(text)


def is_valid_islamic_text(text: str) -> bool:
    """Check if text appears to be valid Islamic content"""
    
    if not text or len(text.strip()) < 5:
        return False
    
    issues = validate_islamic_text(text)
    return len(issues) == 0


def test_cleaning_functions():
    """Test the text cleaning functions with sample data"""
    
    test_cases = [
        {
            'input': 'Question:    What is the ruling on prayer?    ANSWER: Share: Prayer is obligatory...',
            'source': 'fatwa',
            'expected_fixes': ['whitespace', 'answer formatting', 'share removal']
        },
        {
            'input': 'Bukhari: 123 The Prophet SAW said...',
            'source': 'hadith',
            'expected_fixes': ['hadith formatting', 'honorific standardization']
        }
    ]
    
    for i, case in enumerate(test_cases):
        print(f"Test case {i+1}:")
        print(f"Input: {case['input'][:50]}...")
        cleaned = clean_text(case['input'], case['source'])
        print(f"Output: {cleaned[:50]}...")
        print(f"Issues found: {validate_islamic_text(cleaned)}")
        print("-" * 50)


if __name__ == "__main__":
    test_cleaning_functions()
