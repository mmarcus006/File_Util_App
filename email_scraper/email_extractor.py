"""Extracts email addresses from text using regex and basic NLP filtering."""

import re
import logging
import spacy
from typing import List, Set

# Load spacy model once when the module is loaded.
# Using a smaller model for efficiency, adjust if needed.
# Handle potential OSError if the model isn't downloaded.
NLP = None
try:
    NLP = spacy.load("en_core_web_sm")
    logging.info("spaCy model 'en_core_web_sm' loaded successfully.")
except OSError:
    logging.error(
        "spaCy model 'en_core_web_sm' not found. "
        "Please run: python -m spacy download en_core_web_sm"
    )
    # NLP remains None, the find_emails function will skip NLP steps.

# Regex remains the same for initial candidate finding
EMAIL_REGEX = re.compile(
    r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
)

# Domains commonly used in examples that we might want to filter out
EXAMPLE_DOMAINS = {"example.com", "example.org", "example.net", "domain.com", "test.com"}
# Keywords often indicating an example email address
EXAMPLE_KEYWORDS = {"e.g.", "example", "such as", "like"}

def _is_likely_example(email: str, sentence: str) -> bool:
    """Check if the email or its surrounding sentence suggests it's an example."""
    email_lower = email.lower()
    sentence_lower = sentence.lower()

    # Check domain
    try:
        domain = email_lower.split('@')[1]
        if domain in EXAMPLE_DOMAINS:
            logging.debug(f"Filtering example domain: {email}")
            return True
    except IndexError:
        pass # Malformed email, ignore

    # Check keywords in the sentence
    if any(keyword in sentence_lower for keyword in EXAMPLE_KEYWORDS):
        logging.debug(f"Filtering email based on example keyword in sentence: {email} in '{sentence}'")
        return True

    return False

def find_emails(text: str) -> List[str]:
    """Finds potential email addresses using regex and filters them using basic NLP context.

    Args:
        text: The input text potentially containing email addresses.

    Returns:
        A list of unique, cleaned (lowercased, stripped), and filtered email addresses.
    """
    if not text:
        return []

    valid_emails: Set[str] = set()

    try:
        # 1. Find initial candidates with regex
        potential_emails = EMAIL_REGEX.findall(text)
        if not potential_emails:
            logging.debug("No potential emails found via regex.")
            return []

        logging.debug(f"Regex found {len(potential_emails)} potential emails.")

        # 2. Use spaCy for context filtering if model loaded
        if NLP:
            doc = NLP(text)
            # Create a mapping from character index to token/sentence for faster lookup
            char_to_token = {}
            for token in doc:
                for i in range(token.idx, token.idx + len(token.text)):
                    char_to_token[i] = token

            for match in EMAIL_REGEX.finditer(text):
                email_str = match.group(0)
                start_char, end_char = match.span()

                # Find the sentence containing the email
                sentence = "" # Default empty sentence
                token = char_to_token.get(start_char)
                if token and token.sent:
                    sentence = token.sent.text
                else:
                    # Fallback if char not found or no sentence boundary (e.g., email alone)
                    logging.warning(f"Could not determine sentence for email: {email_str}")

                # Apply filtering rules
                if not _is_likely_example(email_str, sentence):
                    cleaned_email = email_str.lower().strip()
                    valid_emails.add(cleaned_email)
                # else: email is filtered out as likely example

        else:
            # spaCy model not loaded, fall back to regex results with basic cleaning
            logging.warning("spaCy model not loaded. Skipping NLP filtering.")
            for email_str in potential_emails:
                cleaned_email = email_str.lower().strip()
                valid_emails.add(cleaned_email)

        # 3. Return unique, sorted list
        final_list = sorted(list(valid_emails))
        logging.info(f"Found {len(final_list)} filtered emails.")
        return final_list

    except Exception as e:
        logging.error(f"Error during email extraction: {e}")
        return [] 