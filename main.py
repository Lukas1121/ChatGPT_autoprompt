import os
import json
import re
from datetime import datetime
from chatgpt_autoprompt.jobsearch import JobSearch, read_search_data
from chatgpt_autoprompt.AutoPrompt import CoverLetterGenerator
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

def append_job_link_json(file_path, job_link, company, job_title, contact_person, email, danish):
    entry = {
        "job_link": job_link.strip(),
        "company": company,
        "job_title": job_title,
        "contact_person": contact_person,
        "email": email,
        "date_applied": datetime.now().strftime('%Y-%m-%d'),
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

def process_job(search, existing_job_links, cover_letter_generator, processed_links_path, client):
    keyword = search['keyword']
    location = search['location']
    print(f"Searching for keyword: {keyword} in location: {location}")
    
    job_search = JobSearch(keyword, location, client)
    job_count = job_search.search_jobindex()
    
    print(f"Total job results found: {job_count}")
    
    job_html_pages = job_search.fetch_job_html_pages()

    for job_link, html_content in zip(job_search.job_links, job_html_pages):
        job_link = job_link.strip().lower()
        print(f"Processing job link: {job_link}")

        if job_link in existing_job_links:
            print(f"Job link {job_link} already processed. Skipping.")
            continue  # Skip to the next job link

        job_description = job_search.generate_job_description_with_gpt(html_content)

        extracted_info = cover_letter_generator.extract_company_position_email_and_contact_with_gpt(job_description)
        print(extracted_info)

        company = extracted_info.get('company', 'Unknown').strip()
        job_title = extracted_info.get('position', 'Unknown').strip()
        contact_person = extracted_info.get('contact', 'Unknown').strip()
        email = extracted_info.get('email', 'Unknown').strip()
        danish = extracted_info.get('danish', 'false').strip().lower() == 'true'

        append_job_link_json(processed_links_path, job_link, company, job_title, contact_person, email, danish)

        existing_job_links.add(job_link)

        # If no valid email found, set your own email
        if not email or email.lower() == 'unknown':
            email = 'Lukieminator@gmail.com'

        cover_letter_generator.process_job_ads(job_description, job_link)


def main():
    search_data = read_search_data(keywords_path)
    cover_letter_generator = CoverLetterGenerator(client, config_paths)
    existing_job_links = read_existing_job_links(processed_links_path)

    for search in search_data:
        process_job(search, existing_job_links, cover_letter_generator, processed_links_path, client)

if __name__ == "__main__":
    main()