# wardrobe-management-system


# Wardrobe Management System

A web-based wardrobe organizer developed using Python, Flask,
Object-Oriented Programming, Data Structures and Algorithms.

## Features
- Add, edit and delete clothing items
- Search and filter clothes
- Sort clothing by name and category
- Track recently worn clothes
- Generate outfit suggestions by occasion
- SQLite database for persistent clothing records
- Responsive interface for desktop and mobile

## Technologies
- Python
- Flask
- HTML and CSS
- SQLite
- OOP: Classes and Objects
- DSA: Lists, Stack, Queue, Searching and Sorting

## Run locally

1. Install Python 3.
2. Install the dependencies:

   pip install -r requirements.txt

3. Start the application:

   python app.py

4. Open http://127.0.0.1:5000 in your browser.

## Deployment

Deploy on a Python-compatible hosting service.
Use `gunicorn app:app` as the start command.

Configure persistent storage for SQLite if the hosting
provider uses an ephemeral filesystem.
