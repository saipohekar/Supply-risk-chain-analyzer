import os
from google import genai
from dotenv import load_dotenv

load_dotenv('e:/k/supply_chain_risk_analyzer/.env')
client = genai.Client()
candidates = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-flash-latest']

for c in candidates:
    try:
        r = client.models.generate_content(model=c, contents='hello')
        print(f'{c}: SUCCESS')
    except Exception as e:
        print(f'{c}: FAILED - {str(e)}')
