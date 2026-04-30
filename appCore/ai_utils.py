"""AI utilities for art analysis, collaboration, and candidate search.

ADAPTED CODE SOURCES:
- CLIP model: Hugging Face Transformers library
  Original Source: https://huggingface.co/openai/clip-vit-base-patch32
- OpenAI API: OpenAI Python SDK
  Original Source: https://platform.openai.com/docs/libraries
- Image processing: Python Pillow library
  Original Source: https://pillow.readthedocs.io/
- Tensor operations: PyTorch library
  Original Source: https://pytorch.org/

All AI integration code is custom implementation using these libraries.
"""
# CLIP (Contrastive Language-Image Pre-Training) model from Hugging Face
# Source: https://huggingface.co/openai/clip-vit-base-patch32
from transformers import CLIPProcessor, CLIPModel
# Pillow for image loading and processing
# Source: https://pillow.readthedocs.io/
from PIL import Image
# PyTorch for tensor operations
# Source: https://pytorch.org/
import torch
# OpenAI Python SDK for GPT API calls
# Source: https://platform.openai.com/docs/libraries/python-lib
import openai
from django.conf import settings
import json
import numpy as np

# Load CLIP model once
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Configure OpenAI
openai.api_key = settings.OPENAI_API_KEY

def generate_embedding(image_path):
    """Generate CLIP embedding for an image"""
    image = Image.open(image_path)
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
    return outputs[0].numpy().tolist()

def get_openai_response(prompt):
    """Helper function to call OpenAI API"""
    try:
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI art expert and curator. Provide detailed, insightful analysis about art, artists, and collaborations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return None

def compare_artists(artist_a_username, artist_b_username, artist_a_bio="", artist_b_bio=""):
    """Compare two artists using their artworks and OpenAI"""
    prompt = f"""
    Compare two artists:
    Artist 1: {artist_a_username} - Bio: {artist_a_bio}
    Artist 2: {artist_b_username} - Bio: {artist_b_bio}
    
    Provide a detailed comparison including:
    1. Similarities in their artistic styles (list 3-4 points)
    2. Differences in techniques or themes (list 3-4 points)
    3. Recommendation for collaboration (2-3 sentences)
    
    Format your response exactly like this:
    SIMILARITIES: point1 | point2 | point3
    DIFFERENCES: point1 | point2 | point3
    RECOMMENDATION: your recommendation text here
    """
    return get_openai_response(prompt)

def suggest_collaboration(primary_artist, goal, collaborator_name="", collaborator_bio=""):
    """Suggest collaboration partners based on style matching"""
    prompt = f"""
    Artist: {primary_artist}
    Goal/Project Description: {goal}
    Potential Collaborator: {collaborator_name}
    Collaborator Bio: {collaborator_bio}
    
    Provide collaboration analysis including:
    1. Why these artists would work well together (2-3 sentences)
    2. Specific collaboration idea or project theme (2-3 sentences)
    3. List of complementary strengths (3 points)
    
    Format your response exactly like this:
    RATIONALE: your rationale text here
    IDEA: your collaboration idea here
    STRENGTHS: strength1 | strength2 | strength3
    """
    return get_openai_response(prompt)

def analyze_style(artwork_titles, artwork_descriptions):
    """Analyze artist's style based on their artworks"""
    prompt = f"""
    Analyze this artist's style based on their artworks:
    
    Artwork Titles: {', '.join(artwork_titles)}
    Descriptions: {artwork_descriptions}
    
    Provide analysis in exactly this format:
    DOMINANT_STYLE: (one sentence about their main style)
    COLOR_TENDENCIES: (one sentence about colors they use)
    MOOD_THEME: (one sentence about emotions/themes)
    TECHNICAL_STRENGTHS: (one sentence about their skills)
    RECOMMENDATIONS: (one sentence for growth)
    """
    return get_openai_response(prompt)

def search_candidates(project_brief, artists_data):
    """Rank artists for a project brief"""
    prompt = f"""
    Project Brief: {project_brief}
    
    Artists Portfolio Summary:
    {artists_data}
    
    Rank these artists for this project on a scale of 1-10.
    Provide analysis in exactly this JSON format:
    {{"results": [
        {{"username": "name1", "score": 8.5, "reason": "why they match"}},
        {{"username": "name2", "score": 7.0, "reason": "why they match"}}
    ]}}
    """
    response = get_openai_response(prompt)
    if response:
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
    return None
