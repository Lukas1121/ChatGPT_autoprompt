import os
import json
import re
from datetime import datetime
from chatgpt_autoprompt.jobsearch import JobSearch, read_search_data
from chatgpt_autoprompt.AutoPrompt import CoverLetterGenerator
from chatgpt_autoprompt.email_sender import EmailSender
import openai

current_directory = os.path.dirname(os.path.abspath(__file__))
keywords_path = os.path.join(current_directory, 'keywords.json')
processed_links_path = os.path.join(current_directory, 'jobs.json')

# Load credentials
with open('configs\credentials.json', 'r', encoding='utf-8') as file:
    credentials = json.load(file)

api_key = credentials['openai']['api_key']
client = openai.OpenAI(api_key=api_key)

config_paths = {
    'cv': os.path.join(current_directory, 'configs', 'my_cv.txt'),
    'cover_letter_template': os.path.join(current_directory, 'configs', 'cover_letter.txt'),
    'considerations': os.path.join(current_directory, 'configs', 'considerations.txt'),
    'email': os.path.join(current_directory, 'configs', 'email.txt'),
    'output_folder': 'output'
}

def validate_gmail_token():
    """Validates and refreshes the Gmail token if necessary."""
    email_sender = EmailSender()
    if not email_sender.creds or not email_sender.creds.valid:
        print("Gmail token is invalid or expired. Refreshing token...")
        email_sender.authenticate_gmail()  # Refresh the token
        print("Token refreshed successfully.")

def append_job_link_json(file_path, job_link, company, job_title, contact_person, email, danish, relevant=True):
    if relevant:
        date_applied = datetime.now().strftime('%Y-%m-%d')
    else:
        date_applied = f"Job irrelevant, not applied: date = {datetime.now().strftime('%Y-%m-%d')}"

    entry = {
        "job_link": job_link.strip(),
        "company": company,
        "job_title": job_title, 
        "contact_person": contact_person,
        "email": email,
        "date_applied": date_applied,
        "danish": danish
    }

    data = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = []

    if any(existing_entry['job_link'].strip().lower() == job_link.strip().lower() for existing_entry in data):
        print(f"Job link {job_link} already exists in the JSON file. Skipping.")
        return
    
    if any(existing_entry['company'].strip().lower() == company.strip().lower() and existing_entry['job_title'].strip().lower() == job_title.strip().lower() for existing_entry in data):
        print(f"Job with company '{company}' and title '{job_title}' already exists in the JSON file. Skipping.")
        return

    data.append(entry)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def read_existing_job_links(file_path):
    existing_links = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                existing_links = {entry['job_link'].strip().lower() for entry in data}
            except json.JSONDecodeError:
                pass
    return existing_links

def read_existing_job_entries(file_path):
    existing_entries = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                existing_entries = json.load(file)
            except json.JSONDecodeError:
                pass
    return existing_entries

def is_job_relevant(job_description, client): 
    with open(config_paths['cv'], 'r', encoding='utf-8') as file:
        cv_text = file.read()

    key_skills = [
        "Adaptability",
        "New Technologies",
        "Python Programming",
        "Versatile Skillset",
        "Consultancy",
        "Data Analysis",
        "Data Conversion",
        "Data Analyst",
        "Data Treatment",
        "Software Development",
        "Industry-specific Software",
        "X-ray Data Analysis",
        "Python Scripts",
        "Data Processing",
        "Raman Microscopy Analysis",
        "Neutron Moderation",
        "Density Functional Theory",
        "AI Engineering"
    ]

    prompt = (
        "You are an assistant who determines the relevance of job descriptions based on specific keywords. "
        "Consider the job description relevant if it contains IT or science aspects or anything related to the following key skills:\n\n"
        f"{', '.join(key_skills)}\n\n"
        "It does not need to contain all aspects, only one or more. "
        "Additionally, if the job title contains keywords like 'senior', 'sr', 'lead', 'professor', 'post-doc', or 'PhD', it should be considered not relevant. "
        "Please analyze the following job description  and then return 'false' if it is not relevant, and 'true' if it is relevant. "
        "Provide a short explanation for your decision.\n\n"
        "Job Description:\n"
        f"{job_description}\n\n"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant who helps with text analysis."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,  # Increase token limit to allow for a short explanation
        n=1,
        stop=None,
        temperature=0.4  # Increase temperature slightly to allow for more nuanced interpretation
    )
 
    relevance_result = response.choices[0].message.content.strip().lower()
    return "true" in relevance_result

def process_job(search, existing_job_links, cover_letter_generator, processed_links_path, client):
    keyword = search['keyword']
    location = search['location']
    platforms = search.get('platforms', ['jobindex', 'linkedin'])  # Default to both if not specified
    print(f"Searching for keyword: {keyword} in location: {location} on platforms: {platforms}")
    
    job_search = JobSearch(keyword, location, client)
    job_count = 0

    if 'jobindex' in platforms:
        job_count += job_search.search_jobindex()
    if 'linkedin' in platforms:
        job_count += job_search.search_linkedin()

    print(f"Total job results found: {job_count}")
    
    job_html_pages = job_search.fetch_job_html_pages()

    existing_job_entries = read_existing_job_entries(processed_links_path)  # Load existing job entries

    for job_link, html_content in zip(job_search.job_links, job_html_pages):
        job_link = job_link.strip().lower()
        print(f"Processing job link: {job_link}")

        if job_link in existing_job_links:
            print(f"Job link {job_link} already processed. Skipping.")
            continue  # Skip to the next job link

        job_description = job_search.generate_job_description_with_gpt(html_content, job_link)

        extracted_info = cover_letter_generator.extract_company_position_email_and_contact_with_gpt(job_description)
        print(extracted_info)

        company = extracted_info.get('company', 'Unknown').strip()
        job_title = extracted_info.get('position', 'Unknown').strip()
        contact_person = extracted_info.get('contact', 'Unknown').strip()
        email = extracted_info.get('email', 'Unknown').strip()
        danish = extracted_info.get('danish', 'false').strip().lower() == 'true'

        if not company or company.lower() == 'unknown':
            print(f"Job link {job_link} does not have a valid company name. Skipping.")
            append_job_link_json(processed_links_path, job_link, company, job_title, contact_person, email, danish, relevant=False)
            continue

        if any(entry['company'].strip().lower() == company.lower() and entry['job_title'].strip().lower() == job_title.lower() for entry in existing_job_entries):
            print(f"Job with company {company} and title {job_title} already exists. Skipping.")
            continue

        if not is_job_relevant(job_description, client):
            print(f"Job link {job_link} is not relevant. Skipping.")
            append_job_link_json(processed_links_path, job_link, company, job_title, contact_person, email, danish, relevant=False)
            continue

        if not email or email.lower() == 'unknown':
            email = 'Lukieminator@gmail.com'

        append_job_link_json(processed_links_path, job_link, company, job_title, contact_person, email, danish)

        existing_job_links.add(job_link)

        cover_letter_generator.process_job_ads(job_description, job_link)


def main():
    validate_gmail_token()

    search_data = read_search_data(keywords_path)
    cover_letter_generator = CoverLetterGenerator(client, config_paths)
    existing_job_links = read_existing_job_links(processed_links_path)

    for search in search_data:
        process_job(search, existing_job_links, cover_letter_generator, processed_links_path, client)

if __name__ == "__main__":
    main()