import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import requests
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_directory = os.path.dirname(os.path.abspath(__file__))
GECKODRIVER_PATH = os.path.join(current_directory, "geckodriver.exe")

FIREFOX_BINARY_PATH = "C:/Program Files/Mozilla Firefox/firefox.exe"

class JobSearch:
    def __init__(self, keyword, location):
        self.keyword = keyword
        self.location = location
        self.job_links = []
    
    def search_jobindex(self):
        options = Options()
        options.binary_location = FIREFOX_BINARY_PATH
        service = Service(GECKODRIVER_PATH)
        driver = webdriver.Firefox(service=service, options=options)
        encoded_keyword = self.keyword.replace(' ', '+')
        driver.get(f"https://www.jobindex.dk/jobsoegning/{self.location}?q={encoded_keyword}")
        
        try:
            logger.info("Navigated to Jobindex.dk")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "PaidJob"))
            )
            logger.info("Search results loaded")
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            self.job_links = self.extract_job_links(soup)
            job_count = self.extract_job_count(soup)
        except Exception as e:
            logger.error("An error occurred: %s", e)
            job_count = 0
        finally:
            driver.quit()
            
        return job_count
    
    def extract_job_links(self, soup):
        job_links = []
        for job in soup.find_all('div', class_='jobsearch-result'):
            h4_tag = job.find('h4')
            if h4_tag:
                link = h4_tag.find('a', href=True)
                if link:
                    job_links.append(link['href'])
        return job_links

    def extract_job_count(self, soup):
        job_count_elem = soup.find('h1', class_='jobsearch-header')
        if job_count_elem:
            job_count_text = job_count_elem.get_text()
            job_count = int(job_count_text.split()[0])
            return job_count
        return 0

    def fetch_job_descriptions(self):
        job_descriptions = []
        
        for job_link in self.job_links:
            response = requests.get(job_link)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_description = None
            
            # Approach 1: Look for meta tags with property 'og:description' or 'description'
            job_description_meta = soup.find('meta', property='og:description')
            if job_description_meta:
                job_description = job_description_meta['content']
            
            if not job_description:
                job_description_meta = soup.find('meta', attrs={'name': 'description'})
                if job_description_meta:
                    job_description = job_description_meta['content']
            
            # Approach 2: Look for a div with common class names
            if not job_description:
                job_description_div = soup.find('div', class_='job-description')
                if job_description_div:
                    job_description = job_description_div.get_text(strip=True)
            
            if not job_description:
                job_description_div = soup.find('div', class_='jobtext-jobad__body')
                if job_description_div:
                    job_description = job_description_div.get_text(strip=True)
            
            if not job_description:
                job_description_div = soup.find('div', class_='job-content')
                if job_description_div:
                    job_description = job_description_div.get_text(strip=True)
            
            # Approach 3: Look for paragraphs within a main content div
            if not job_description:
                job_description_div = soup.find('div', class_='main-content')
                if job_description_div:
                    paragraphs = job_description_div.find_all('p')
                    job_description = ' '.join([para.get_text(strip=True) for para in paragraphs])
            
            # Approach 4: General approach to find the main content area if other approaches fail
            if not job_description:
                main_content = soup.find('div', role='main')
                if main_content:
                    job_description = main_content.get_text(strip=True)
            
            # Approach 5: Look for specific header and section elements
            if not job_description:
                header = soup.find('header', class_='jobtext-jobad__header')
                if header:
                    body = header.find_next('section', class_='jobtext-jobad__body')
                    if body:
                        job_description = body.get_text(strip=True)
            
            if job_description:
                job_descriptions.append(job_description)
        
        return job_descriptions


def read_search_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['searches']

# Main execution
try:
    search_data = read_search_data('keywords.json')
except json.JSONDecodeError as e:
    logger.error(f"Error reading JSON file: {e}")
    search_data = []

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
    # for description in job_descriptions:
    #     print(description)
        # Here you would integrate the code to handle prompting ChatGPT with the job description
        # e.g., chatgpt_prompt_handler(description)
    
    print("\n")