"""
Web scraper for subject-related content
"""
import json

def scrape_subject_content(subject):
    """Scrape web content related to the subject"""
    # Mock implementation - in real scenario, scrape actual web content
    mock_content = {
        "physics": "Physics is the natural science that studies matter, its motion and behavior through space and time, and the related entities of energy and force.",
        "chemistry": "Chemistry is the scientific discipline involved with elements and compounds composed of atoms, molecules and ions.",
        "biology": "Biology is the natural science that studies life and living organisms, including their physical structure, chemical processes, molecular interactions.",
        "mathematics": "Mathematics includes the study of such topics as quantity, structure, space, and change.",
        "computer science": "Computer science is the study of algorithmic processes, computational systems and the design of computer systems."
    }
    
    return {
        "content": mock_content.get(subject.lower(), "General academic content"),
        "keywords": ["academic", "study", "research", "analysis", "theory"]
    }