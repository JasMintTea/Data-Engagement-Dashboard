from datetime import datetime
import re
from App.models import Participant
from App.database import db


def clean_name(text):
    """Convert names to proper case (e.g., JOHN DOE -> John Doe, john doe -> John Doe)"""
    if not text or not isinstance(text, str):
        return text
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text.strip())
    # Capitalize first letter of each word, lowercase the rest
    return ' '.join(word.capitalize() for word in text.split())


def clean_email(email):
    """Convert email to lowercase and strip whitespace"""
    if not email or not isinstance(email, str):
        return email
    return email.strip().lower()


def create_participant(first_name, last_name, email, institution_id, **kwargs):
    """Create a new participant."""

    # Clean the names and email
    first_name = clean_name(first_name)
    last_name = clean_name(last_name)
    email = clean_email(email) if email else None

    # Handle birth_date conversion if it exists
    birth_date = kwargs.get("birth_date")
    if birth_date and isinstance(birth_date, str):
        try:
            # Convert string 'YYYY-MM-DD' to date object
            kwargs["birth_date"] = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except ValueError:
            # If conversion fails, set to None
            kwargs["birth_date"] = None

    participant = Participant(
        first_name=first_name,
        last_name=last_name,
        email=email,
        institution_id=institution_id,
        **kwargs
    )
    db.session.add(participant)
    db.session.commit()
    return participant