import os
import json
from datetime import datetime

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