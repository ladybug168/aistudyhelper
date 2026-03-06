import pdfplumber
import numpy as np
from openai import OpenAI
import os
import base64
from PIL import Image
import io
import json
import logging
import math
from newspaper import Article
from functools import partial
from concurrent.futures import ThreadPoolExecutor

from prompts.summary_prompt import SUMMARY_PROMPTS
from prompts.quiz_prompt import QUIZ_PROMPTS
from prompts.flashcard_prompt import FLASHCARD_PROMPTS
from prompts.solve_question_prompt import SOLVEQUESTION_PROMPTS
from prompts.promptmode import PROMPT_MODES


#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
# main.py

logger = logging.getLogger(__name__)


def extract_web_text(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.text


def summarize_training(text, subject):

    prompt_template = get_prompt(SUMMARY_PROMPTS,subject, prompt_type="summary")

    prompt = prompt_template.format(text=text)
    response = client.chat.completions.create(
		model="gpt-4o-mini",
		messages=[{"role": "user", "content": prompt}],
		temperature=0.1
	)
    #logger.info(f"summarize_training | tokens={response.usage.total_tokens}")
    return response.choices[0].message.content
    
def summarize_chunks(chunks,subject):

    summaries = []
    print(f"summarize_chunks subject {subject}")
    for i, chunk in enumerate(chunks):

        print(f"Summarizing chunk {i+1}")

        summary = summarize_training(chunk[:6000],subject)

        summaries.append(summary)

    return summaries

def summarize_chunks_parallel(chunks,subject):

    summaries = []
    subject_val = subject

    with ThreadPoolExecutor(max_workers=5) as executor:
        func = partial(summarize_chunks, subject=subject_val)
        results = list(executor.map(func, chunks))
        #summaries = list(results)

    return results

def process_chunks(chunks,subject):

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(extract_knowledge, chunks,subject))

    return results
    
def get_dynamic_chunk_size(total_pages):
    logger.info(f"total_pages {total_pages}")
    print(f"total_pages {total_pages}")
    if total_pages <= 10:
        return total_pages          # single chunk

    elif total_pages <= 40:
        target_chunks = 6

    elif total_pages <= 100:
        target_chunks = 8

    else:
        target_chunks = 10

    chunk_size = math.ceil(total_pages / target_chunks)

    return chunk_size

# ------------------------
#  PDF
# ------------------------
def process_pdf(pdf_path,subject):
    logger.info(f"process pdf called with subject {subject}")
    
    pages = extract_pages(pdf_path)
    chunk_size = get_dynamic_chunk_size(len(pages))
   
    chunks = chunk_text(pages, chunk_size)
    print(f"process pdf called with subject {subject} , chunk_size: {chunk_size} .chunks length:{len(chunks)}")
    #chunk_summaries = summarize_chunks_parallel(chunks,subject)
    #chunks = chunk_pages(pages, chunk_size)

    knowledge_chunks = process_chunks_thread(chunks,subject)
    combined = "\n".join(knowledge_chunks)
    return combined

def process_chunks_thread(chunks,subject):

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(extract_knowledge, chunks,subject))

    return results
    
def extract_pages(pdf_path):

    pages = []

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

    return pages
 

def chunk_text(pages, chunk_size):
    return [
        " ".join(pages[i:i+chunk_size])
        for i in range(0, len(pages), chunk_size)
    ]
    
def extract_knowledge(text,subject):
    print(f"extract_knowledge text len :{len(text)}")
    prompt = f"""
You are an expert {subject} tutor.

Extract the most important concepts from the material below.
Focus on definitions, key principles, and relationships.

Material:
{text[:8000]}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    logger.info(f"extract_knowledge | tokens={response.usage.total_tokens}")
    return response.choices[0].message.content
    
 

    
def final_summary(subject,combinedsummaries,mode):

    prompt = build_prompt_mode(SUMMARY_PROMPTS[subject],combinedsummaries,mode)
    print(prompt)
    response = callgpt4omini(prompt)
    logger.info(f"final_summary | tokens={response.usage.total_tokens}")
    return response.choices[0].message.content
    

def final_summary_custom (subject,combinedsummaries,instruction):

    prompt = build_prompt_custom(instruction,combinedsummaries)
    print(f"build_prompt_custom:{prompt}")
    response = callgpt4omini(prompt)
    logger.info(f"final_summary_custom | tokens={response.usage.total_tokens}")
    return response.choices[0].message.content

def callgpt4omini(prompt):
    return client.chat.completions.create(

        model="gpt-4o-mini",

        messages=[{"role":"user","content":prompt}]

    )
    

def chunk_pages(pages, chunk_size=5):

    chunks = []

    for i in range(0, len(pages), chunk_size):

        chunk = pages[i:i+chunk_size]

        text = " ".join(chunk)

        chunks.append(text)

    return chunks
    
 

def get_prompt(myprompt,subject, prompt_type, user_question=None, material_summary=None):
    """
    subject: math, history, finance, art
    prompt_type: summary, quiz, solve
    """
    #print(f"get_prompt myprompt {myprompt}")
    print(f"subject {subject}")
    base_prompt = myprompt[subject]

    if prompt_type == "solve":
        if user_question is None or material_summary is None:
            raise ValueError("solve prompt requires user_question and material_summary")
        return base_prompt.format(
            user_question = user_question,
            material_summary_or_text = material_summary
        )
    return base_prompt

#dynamic prompt    
def build_prompt_mode(baseprompt,text, mode):
    mode_instruction = PROMPT_MODES.get(mode, "").strip()
    prompt = f"""
{baseprompt}

Additional instruction:
{mode_instruction}

Training content:
{text}
"""
    return prompt
    
    
def build_prompt_custom(personalprompt,text):


    prompt = f"""
{personalprompt}


Training content:
{text}
"""

    return prompt    


# -------- QUIZ GENERATION --------

def generate_quiz_json(subject,text):
    prompt_template = get_prompt(QUIZ_PROMPTS,subject, prompt_type="quiz")
    prompt = prompt_template.format(material=text)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    quiz_text = response.choices[0].message.content
    quiz_text = quiz_text.replace("```json", "").replace("```", "").strip()
    try:
        quiz_data = json.loads(quiz_text)
    except json.JSONDecodeError:
        print("JSON parse error")
        print(quiz_text)
        quiz_data = []
    return quiz_data




# -------- QUIZ SOLVER --------

def solve_question(subject,text,question):

    solve_prompt = get_prompt(SOLVEQUESTION_PROMPTS,
    subject = subject,
    prompt_type = "solve",
    user_question = question,
    material_summary = text
)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":solve_prompt}]
    )

    return response.choices[0].message.content

def extract_image_text(image_file):

    image_bytes = image_file.read()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt = """
You are an assistant that reads training slides.

Extract the following from the slide:

1. Slide title
2. Bullet points
3. Key learning concepts
4. Important definitions if present

Return clean structured text.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{base64_image}",
                    },
                ],
            }
        ],
    )
    #logger.info(f"extract_image_text | tokens={response.usage.total_tokens}")
    return response.output_text
        
# ------------------------
# main
# ------------------------
if __name__ == "__main__":

    #text = process_pdf("Code-of-Business-Conduct-PPT-2025.pdf")

    #chunks = split_chunks(text)

    print("Creating embeddings...")
    #embeddings = create_embeddings(chunks)

    quiz = """
Question: What is insider trading?

A. Buying stocks legally
B. Trading using non-public information
C. Selling stocks publicly
D. None
"""

    #answer_quiz(quiz, chunks, embeddings)