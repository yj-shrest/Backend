from atoma_sdk import AtomaSDK
import os
API_KEY = "pQDhafMOzpQAQAe2tQFLbYDFbpbeAh"

with AtomaSDK(
    bearer_auth=API_KEY,
) as atoma_sdk:
    
    completion = atoma_sdk.chat.create(
      model="Infermatic/Llama-3.3-70B-Instruct-FP8-Dynamic",
      messages=[
        {"role": "developer", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
      ]
    )

    print(completion.choices[0].message)