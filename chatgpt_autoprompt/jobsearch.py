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
import openai
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_directory = os.path.dirname(os.path.abspath(__file__))
GECKODRIVER_PATH = os.path.join(current_directory, "geckodriver.exe")

FIREFOX_BINARY_PATH = "C:/Program Files/Mozilla Firefox/firefox.exe"

class JobSearch:
    def __init__(self, keyword, location, client):
        self.keyword = keyword
        self.location = location
        self.job_links = []
        self.client = client
    
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

    def fetch_job_html_pages(self):
        job_html_pages = []
        valid_job_links = []
        
        for job_link in self.job_links:
            response = requests.get(job_link)
            if response.status_code == 200:
                job_html_pages.append(response.text)
                valid_job_links.append(job_link)
        
        self.job_links = valid_job_links
        return job_html_pages
    
    def construct_extraction_prompt(self, html_content):
        prompt = (
            "You are an assistant who extracts job descriptions from HTML content. "
            "I will provide you with the HTML content of a job ad page, and you need to extract the job description from it. "
            "The job description is usually within meta tags, div tags, or main content sections. "
            "If you find the job description within multiple possible sections, concatenate them appropriately. "
            "If any additional information that clearly belongs to the job description is found, include it as well. "
            "Here is the HTML content:\n\n"
            f"{html_content}\n\n"
            "Extracted Job Description:"
        )
        return prompt

    def generate_job_description_with_gpt(self, html_content):
        openai.api_key = self.openai_api_key
        prompt = self.construct_extraction_prompt(html_content)

        response = self.client.chat.completions.create(
            engine="gpt-3.5-turbo",
            prompt=prompt,
            max_tokens=2500,
            n=1,
            stop=None,
            temperature=0.5
        )

        job_description = response.choices[0].text.strip()
        return job_description

def read_search_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['searches']

