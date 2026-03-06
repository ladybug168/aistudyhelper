# flashcard_prompt.py

FLASHCARD_PROMPTS = {
    "math": """
Based on the following study material, generate 5 quiz questions.

Return the result ONLY in valid JSON format.

Format:

[
  {{
    "question": "question text",
    "options": [
      "A. option",
      "B. option",
      "C. option",
      "D. option"
    ],
    "answer": "B",
    "explanation": "short explanation"
  }}
]

Material:
{material}
""",
    "history": """
Based on the following study material, generate 5 quiz questions.

Return the result ONLY in valid JSON format.

Format:

[
  {{
    "question": "question text",
    "options": [
      "A. option",
      "B. option",
      "C. option",
      "D. option"
    ],
    "answer": "B",
    "explanation": "short explanation"
   }}
]

Material:
{material}
"""
,
    "finance": """
Based on the following study material, generate 5 quiz questions.

Return the result ONLY in valid JSON format.

Format:

[
  {{
    "question": "question text",
    "options": [
      "A. option",
      "B. option",
      "C. option",
      "D. option"
    ],
    "answer": "B",
    "explanation": "short explanation"
   }}
]

Material:
{material}
"""
,
    "art":  """
Based on the following study material, generate 5 quiz questions.

Return the result ONLY in valid JSON format.

Format:

[
  {{
    "question": "question text",
    "options": [
      "A. option",
      "B. option",
      "C. option",
      "D. option"
    ],
    "answer": "B",
    "explanation": "short explanation"
  }}
]

Material:
{material}
"""

}