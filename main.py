import os
import json
from chatgpt_autoprompt.jobsearch import JobSearch, read_search_data
from chatgpt_autoprompt.AutoPrompt import CoverLetterGenerator

# Define the correct path to keywords.json
current_directory = os.path.dirname(os.path.abspath(__file__))
keywords_path = os.path.join('keywords.json')

# Load search data
search_data = read_search_data(keywords_path)

config_paths = {
    'cv': os.path.join(current_directory, 'configs', 'my_cv.txt'),
    'cover_letter_template': os.path.join(current_directory, 'configs', 'cover_letter.txt'),
    'considerations': os.path.join(current_directory, 'configs', 'considerations.txt'),
    'email': os.path.join(current_directory, 'configs', 'email.txt'),
    'output_folder': 'generated_cover_letters'
}

# API key for OpenAI
api_key = "sk-proj-TWN2zc55FpVW6WjNKGmET3BlbkFJ9upgXSTJq9YPkgKxEj3n"

for search in search_data:
    keyword = search['keyword']
    location = search['location']
    print(f"Searching for keyword: {keyword} in location: {location}")
    
    job_search = JobSearch(keyword, location)
    job_count = job_search.search_jobindex()
    
    print(f"Total job results found: {job_count}")
    for job_link in job_search.job_links:
        print(job_link) 
    
    
    job_descriptions = job_search.fetch_job_descriptions()
    print(len(job_descriptions))
    cover_letter_generator = CoverLetterGenerator(api_key, config_paths)
    
    for description in job_descriptions:
        # print(description)
        cover_letter_generator.process_job_ads([description])
        break

    print("\n")