import random
import openai
import requests
import ast


openai.api_key = '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'
api_key = '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'


def process_image(image):
    _class = random.choice(range(0, 5))
    _size = random.choice(range(1, 4))
    return _class, _size

    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": "Analyze the extent of the damage and size of the building in this image of a ruined city. Size should be 1 for small, 2 for medium, and 3 for large.\
                The extent of the damage should be 0 for No Damage, 1 for Mild, 2 for Moderate, 3 for Severe, and 4 for Destructed. Respond only tuple in the form (damage, size)."
            },
            {
                "type": "image_url",
                "image_url": {
                "url": f"data:image/jpeg;base64,{image}"
                }
            }
            ]
        }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    val = response.json()['choices'][0]['message']['content']
    return ast.literal_eval(val)
