import streamlit as st
from src.resume_parser import extract_text_from_pdf
from src.ats_scorer import ATSScorer

st.set_page_config(page_title="Resume Parser", layout="wide")
st.title("🚀 Resume Parser & ATS Optimizer")

# Tab 1: Parse Resume
with st.container():
    st.header("📄 Parse Resume")
    uploaded_file = st.file_uploader("Upload PDF Resume", type="pdf")
    
    if uploaded_file:
        try:
            text = extract_text_from_pdf(uploaded_file)
            st.success("✅ PDF extracted!")
            
            # Show preview
            st.subheader("Extracted Text (Preview)")
            st.text(text[:300] + "...")
            
            # ATS Score
            st.subheader("🎯 ATS Compatibility Score")
            scorer = ATSScorer()
            result = scorer.calculate_score(text)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Score", f"{result['total_score']:.0f}/100")
            with col2:
                st.metric("Format", f"{result['format_score']:.0f}")
            with col3:
                st.metric("Length", f"{result['length_score']:.0f}")
            
            if result['issues']:
                st.warning(f"⚠️ Issues: {', '.join(result['issues'])}")
                
        except Exception as e:
            st.error(f"Error: {e}")