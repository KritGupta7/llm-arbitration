from app.services.openai_client import client

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": "What causes tides?"
        }
    ]
)

print(response.choices[0].message.content)