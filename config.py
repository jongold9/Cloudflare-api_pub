import os

# User credentials for login
USERS = {
    "example_user1": "example_password1",
    "example_user2": "example_password2",
}

# API учетные данные
ACCOUNTS = [
    {
        "name": "Example-API-1",
        "API_KEY": os.getenv('FLASK_API_KEY_Example1', 'example_api_key_1'), 
        "EMAIL": os.getenv('FLASK_EMAIL_Example1', 'example_email1@example.com')  
    }, 
    {
        "name": "Example-API-2",
        "API_KEY": os.getenv('FLASK_API_KEY_Example2', 'example_api_key_2'),
        "EMAIL": os.getenv('FLASK_EMAIL_Example2', 'example_email2@example.com')
    },
]
