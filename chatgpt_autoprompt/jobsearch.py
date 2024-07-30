import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
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

        page_number = 1
        while True:
            encoded_keyword = f"%27{self.keyword.replace(' ', '+')}%27"  # Use '%27' to encode single quotes around the keyword phrase
            url = f"https://www.jobindex.dk/jobsoegning/{self.location}?page={page_number}&q={encoded_keyword}"
            driver.get(url)
            
            try:
                logger.info(f"Navigated to {url}")
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "PaidJob"))
                )
                logger.info("Search results loaded")
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                job_links = self.extract_job_links(soup)
                if not job_links:
                    logger.info("No more job links found, stopping search.")
                    break

                self.job_links.extend(job_links)
                page_number += 1

            except Exception as e:
                logger.error("An error occurred: %s", e)
                break
        
        driver.quit()
        return len(self.job_links)
    
    def search_linkedin(self):
        profile_path = r"C:\Users\Lukas\AppData\Roaming\Mozilla\Firefox\Profiles\4r5zndpw.default-release"  # Replace with your actual profile path
        options = Options()
        options.binary_location = FIREFOX_BINARY_PATH
        profile = FirefoxProfile(profile_path)
        options.profile = profile
        service = Service(GECKODRIVER_PATH)
        driver = webdriver.Firefox(service=service, options=options)

        encoded_keyword = self.keyword.replace(' ', '%20')
        geo_id = "101286674"  # Geo ID for Middle Jutland
        start = 0
        while start < 75:  # Limit to first 50 listings
            url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_keyword}&geoId={geo_id}&start={start}&refresh=true"
            driver.get(url)

            try:
                logger.info(f"Navigated to {url}")
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "jobs-search-results__list-item"))
                )
                logger.info("Search results loaded")

                job_links = self.extract_linkedin_job_links(driver)
                if job_links:
                    self.job_links.extend(job_links)
                else:
                    logger.info("No job links found on LinkedIn.")
                    break

                start += 25  # LinkedIn pagination increases by 25

            except Exception as e:
                logger.error("An error occurred: %s", e)
                break

        driver.quit()
        return len(self.job_links)

    def extract_linkedin_job_links(self, driver):
        job_links = []
        job_cards = driver.find_elements(By.CLASS_NAME, 'jobs-search-results__list-item')

        for card in job_cards:
            try:
                # Retry mechanism for stale elements
                for attempt in range(3):
                    try:
                        # Check for "Easy Apply" button and skip such jobs
                        if len(card.find_elements(By.XPATH, ".//button[contains(@aria-label, 'Easy Apply')]")) > 0:
                            break  # Skip this job card

                        # Extract the job link
                        job_link_element = card.find_element(By.CSS_SELECTOR, "a.job-card-list__title")
                        job_link = job_link_element.get_attribute("href")
                        job_links.append(job_link)
                        break
                    except StaleElementReferenceException:
                        if attempt < 2:
                            time.sleep(1)  # Wait before retrying
                        else:
                            logger.error(f"Stale element reference error after 3 attempts: {card}")
                            raise
                    except NoSuchElementException as e:
                        logger.error(f"NoSuchElementException: {e}")
                        break
            except Exception as e:
                logger.error(f"An error occurred while processing a job card: {e}")
                continue

        return job_links
    
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
    
    def construct_extraction_prompt(self, html_content, html_link):
        soup = BeautifulSoup(html_content, 'html.parser')

        for tag in soup(['script', 'style', 'footer', 'nav', 'header', 'aside']):
            tag.decompose()

        relevant_sections = soup.find_all(['div', 'section', 'article'], class_=lambda x: x and ('job' in x.lower() or 'listing' in x.lower() or 'content' in x.lower()))

        if not relevant_sections:
            relevant_sections = soup.find_all(['div', 'section', 'article'])

        extracted_content = ' '.join(section.get_text(separator=' ', strip=True) for section in relevant_sections)

        max_length = 45000
        truncated_content = extracted_content[:max_length]

        prompt = (
            "You are an assistant who extracts job descriptions from HTML content. "
            "I will provide you with the truncated HTML content of a job ad page, and you need to extract the job description from it. "
            "The job description is usually within meta tags, div tags, or main content sections. "
            "If you find the job description within multiple possible sections, concatenate them appropriately. "
            "If any additional information that clearly belongs to the job description is found, include it as well. "
            "Make especially sure to include company name, position title and any email or contact person who might be related to the job ad. "
            "Here is the HTML content:\n\n"
            f"{truncated_content}\n\n"
            "Here is the HTML link, you don't need to be able to click the link, but the company name or position title might be present in the html string:\n\n"
            f"{html_link}\n\n"
        )
        return prompt


    def generate_job_description_with_gpt(self, html_content, html_link):
        prompt = self.construct_extraction_prompt(html_content, html_link)

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant who helps with text extraction."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2024,
            n=1,
            stop=None,
            temperature=0.5
        )

        job_description = response.choices[0].message.content.strip()

        return job_description

def read_search_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['searches']

