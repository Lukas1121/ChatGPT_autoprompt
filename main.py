import os
import json
import re
from datetime import datetime
from chatgpt_autoprompt.jobsearch import JobSearch, read_search_data
from chatgpt_autoprompt.AutoPrompt import CoverLetterGenerator

# Define the correct path to keywords.json and processed links file
current_directory = os.path.dirname(os.path.abspath(__file__))
keywords_path = os.path.join(current_directory, 'keywords.json')
processed_links_path = os.path.join(current_directory, 'jobs.json')

# Load credentials
with open('configs\credentials.json', 'r', encoding='utf-8') as file:
    credentials = json.load(file)

api_key = credentials['openai']['api_key']

config_paths = {
    'cv': os.path.join(current_directory, 'configs', 'my_cv.txt'),
    'cover_letter_template': os.path.join(current_directory, 'configs', 'cover_letter.txt'),
    'considerations': os.path.join(current_directory, 'configs', 'considerations.txt'),
    'email': os.path.join(current_directory, 'configs', 'email.txt'),
    'output_folder': 'generated_cover_letters'
}

def append_job_link_json(file_path, job_link, company, job_title, contact_person, email):
    entry = {
        "job_link": job_link.strip(),
        "company": company,
        "job_title": job_title,
        "contact_person": contact_person,
        "email": email,
        "date_applied": datetime.now().strftime('%Y-%m-%d')
    }

    data = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                # Handle empty or corrupted JSON file
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

def process_job(search, existing_job_links, cover_letter_generator):
    keyword = search['keyword']
    location = search['location']
    print(f"Searching for keyword: {keyword} in location: {location}")
    
    job_search = JobSearch(keyword, location)
    job_count = job_search.search_jobindex()
    
    print(f"Total job results found: {job_count}")
    
    job_descriptions = job_search.fetch_job_descriptions()

    print(f"Total job descriptions found: {len(job_descriptions)}")

    for job_link, description in zip(job_search.job_links, job_descriptions):
        job_link = job_link.strip().lower()
        print(f"Processing job link: {job_link}")

        if job_link in existing_job_links:
            print(f"Job link {job_link} already processed. Skipping.")
            continue  # Skip to the next job link

        extracted_info = cover_letter_generator.extract_company_position_email_and_contact_with_gpt(description)
        company = re.search(r'Company:\s*([^,]+)', extracted_info).group(1).strip()
        job_title = re.search(r'Position:\s*([^\s,]+)', extracted_info).group(1).strip()
        contact_person = re.search(r'Contact:\s*([^,]+)', extracted_info).group(1).strip()
        email = re.search(r'Email:\s*([^,]+)', extracted_info).group(1).strip()

        print(extracted_info)

        append_job_link_json(processed_links_path, job_link, company, job_title, contact_person, email)

        existing_job_links.add(job_link)

        cover_letter_generator.process_job_ads(description, job_link)

def main():
    search_data = read_search_data(keywords_path)
    cover_letter_generator = CoverLetterGenerator(api_key, config_paths)
    existing_job_links = read_existing_job_links(processed_links_path)

    for search in search_data:
        process_job(search, existing_job_links, cover_letter_generator)

if __name__ == "__main__":
    main()
