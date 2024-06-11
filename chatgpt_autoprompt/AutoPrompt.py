import os
import re
from openai import OpenAI

class CoverLetterGenerator:
    def __init__(self, api_key, config_paths):
        self.client = OpenAI(api_key=api_key)
        self.cv_path = config_paths['cv']
        self.cover_letter_template_path = config_paths['cover_letter_template']
        self.considerations_path = config_paths['considerations']
        self.output_folder = config_paths['output_folder']
        self.load_configs()
        
    def load_configs(self):
        with open(self.cv_path, 'r', encoding='utf-8') as file:
            self.cv_text = file.read()
        
        with open(self.cover_letter_template_path, 'r', encoding='utf-8') as file:
            self.cover_letter_template = file.read()
        
        with open(self.considerations_path, 'r', encoding='utf-8') as file:
            self.considerations_text = file.read()

    def extract_company_or_position_with_gpt(self, job_add_text):
        prompt = (
            "Extract the company name and the position title from the following job advertisement text. "
            "If the company name or position title is not clearly specified, return 'Unknown'. "
            "Format the output as 'Company: [company name], Position: [position title]'.\n\n"
            f"Job Ad:\n{job_add_text}\n"
        )

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant who helps with text extraction."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.7
        )
        extracted_text = response.choices[0].message.content.strip()
        return extracted_text

    def construct_prompt(self, job_add, cv, cover_letter_template, considerations):
        prompt = (
            "I want you to produce a cover letter using the provided text template. "
            "The cover letter should be targeted to the job advertisement and should draw inspiration from my CV, but the cover letter template may also be used as inspiration. "
            "When constructing the cover letter, please consider the following points:\n\n"
            f"Job Ad:\n{job_add}\n\n"
            f"My CV:\n{cv}\n\n"
            f"Considerations:\n{considerations}\n\n"
            f"Cover Letter Template:\n{cover_letter_template}\n\n"
            "Please edit the text within the \\lettercontent{} tags accordingly without exaggerating my skills or claiming experience I do not have. "
            "For any requirements in the job ad that I do not meet, emphasize my broad skill range in IT and advanced sciences such as physics, chemistry, and biophysics. Make sure to write the cover letter in the same language as the job ad."
        )
        return prompt

    def generate_cover_letter_with_gpt(self, prompt):
        prompt += "\nPlease make sure that each section is enclosed with the \\lettercontent{} tags. Also, the cover letter is not allowed to exceed the template in length. It can be shorter, but no longer."

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.7
        )
        generated_text = response.choices[0].message.content.strip()
        return generated_text

    def save_cover_letter(self, output_path, content):
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def process_job_ads(self, job_ads):
        for job_add_text in job_ads:
            extracted_info = self.extract_company_or_position_with_gpt(job_add_text)
            print(f"Extracted Info: {extracted_info}")  # Debugging line

            prompt = self.construct_prompt(job_add_text, self.cv_text, self.cover_letter_template, self.considerations_text)
            generated_cover_letter = self.generate_cover_letter_with_gpt(prompt)

            company_name = re.search(r'Company:\s*([^,]+)', extracted_info).group(1).strip().replace(" ", "_")
            position_title = re.search(r'Position:\s*([^\s,]+)', extracted_info).group(1).strip().replace(" ", "_")
            output_filename = f"{company_name}_{position_title}_cover_letter.txt"
            output_path = os.path.join(self.output_folder, output_filename)

            self.save_cover_letter(output_path, generated_cover_letter)
            print(f"Cover letter saved to: {output_path}")
