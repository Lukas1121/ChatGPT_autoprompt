import os
import re
from openai import OpenAI
import subprocess

class CoverLetterGenerator:
    def __init__(self, api_key, config_paths):
        self.client = OpenAI(api_key=api_key)
        self.cv_path = config_paths['cv']
        self.cover_letter_template_path = config_paths['cover_letter_template']
        self.considerations_path = config_paths['considerations']
        self.email_template_path = config_paths['email']
        self.output_folder = config_paths['output_folder']
        self.load_configs()
        
    def load_configs(self):
        with open(self.cv_path, 'r', encoding='utf-8') as file:
            self.cv_text = file.read()
        
        with open(self.cover_letter_template_path, 'r', encoding='utf-8') as file:
            self.cover_letter_template = file.read()
        
        with open(self.considerations_path, 'r', encoding='utf-8') as file:
            self.considerations_text = file.read()
        
        with open(self.email_template_path, 'r', encoding='utf-8') as file:
            self.email_template = file.read()

    def extract_company_position_email_and_contact_with_gpt(self, job_add_text):
        prompt = (
            "Extract the company name, the position title, the contact person's name, and the email address from the following job advertisement text. "
            "If any of the information is not clearly specified, return 'Unknown'. "
            "Format the output as 'Company: [company name], Position: [position title], Contact: [contact name], Email: [email address]'.\n\n"
            f"Job Ad:\n{job_add_text}\n"
        )

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant who helps with text extraction."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
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
            "Finally, give no response other than the exact code/cover letter, as I am using a piece of code to convert your prompt directly into a latex project and your response will be captured by this as well causing issues."
        )
        return prompt

    def generate_cover_letter_with_gpt(self, prompt):
        prompt += "\nPlease make sure that each section is enclosed with the \\lettercontent{} tags. Also, the cover letter is not allowed to exceed the template in length. It can be shorter, but no longer."

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
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
    
    def save_cover_letter(self, content, company_name):
        latex_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'LaTeX', 'Cover', 'cover.tex')

        with open(latex_file_path, 'r', encoding='utf-8') as file:
            main_tex_content = file.read()

        company_name_latex = re.escape(company_name)
        main_tex_content = re.sub(r'\\companyname\{[^}]*\}', r'\\companyname{' + company_name_latex + '}', main_tex_content)

        start_placeholder = "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% THIS SECTION HERE"
        end_placeholder = "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% UNTIL HERE"

        before_content = main_tex_content.split(start_placeholder)[0]
        after_content = main_tex_content.split(end_placeholder)[1]

        new_tex_content = before_content + start_placeholder + '\n' + content + '\n' + end_placeholder + after_content

        with open(latex_file_path, 'w', encoding='utf-8') as file:
            file.write(new_tex_content)

    def compile_latex_to_pdf(self, company_name, position_title):
        latex_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'LaTeX', 'Cover', 'cover.tex')
        output_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'LaTeX', 'Cover')
        output_filename = f"{company_name}_{position_title}_cover_letter.pdf"
        output_path = os.path.join(self.output_folder, output_filename)

        xelatex_path = 'xelatex'

        # Remove the existing file if it exists
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"Removed existing file: {output_path}")

        try:
            subprocess.run([xelatex_path, '-output-directory', output_directory, latex_file_path], check=True)
            pdf_output_path = os.path.join(output_directory, 'cover.pdf')
            if os.path.exists(pdf_output_path):
                os.rename(pdf_output_path, output_path)
                print(f"PDF saved to: {output_path}")
            else:
                print("PDF compilation failed. PDF file not found.")
        except subprocess.CalledProcessError as e:
            print(f"Error during PDF compilation: {e}")

    def generate_email_with_gpt(self, job_ad, company_name, position_title, contact_name, email_address):
        email_template = self.email_template
        prompt = (
            "Using the provided email template, generate an email targeting the specified job advertisement. "
            "Replace the placeholders with the relevant information from the job ad and the extracted details. If contact name is unknown then do not mention it. i.e. instead of Hello [contact name], just have Hello, "
            "Maintain the core message of the email while ensuring it is personalized for the job ad.\n\n"
            f"Job Ad:\n{job_ad}\n\n"
            f"Email Template:\n{self.email_template}\n\n"
            "Extracted Information:\n"
            f"Company: {company_name}\n"
            f"Position: {position_title}\n"
            f"Contact: {contact_name}\n"
            f"Email: {email_address}\n"
            "If the job advertisement is in danish, then the email should also be in danish. Make sure to keep popular jargon in its native language web scraping fx don't translate this word it would sound silly"
        )

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.7
        )
        generated_email = response.choices[0].message.content.strip()
        return generated_email

    def process_job_ads(self, job_ads):
        for job_add_text in job_ads:
            extracted_info = self.extract_company_position_email_and_contact_with_gpt(job_add_text)
            print(f"Extracted Info: {extracted_info}")  # Debugging line

            company_name = re.search(r'Company:\s*([^,]+)', extracted_info).group(1).strip().replace(" ", "_")
            position_title = re.search(r'Position:\s*([^\s,]+)', extracted_info).group(1).strip().replace(" ", "_")
            contact_name = re.search(r'Contact:\s*([^,]+)', extracted_info).group(1).strip()
            email_address = re.search(r'Email:\s*([^,]+)', extracted_info).group(1).strip()
            print(f"Company Name: {company_name}, Position Title: {position_title}, Contact Name: {contact_name}, Email Address: {email_address}")


            prompt = self.construct_prompt(job_add_text, self.cv_text, self.cover_letter_template, self.considerations_text)
            generated_cover_letter = self.generate_cover_letter_with_gpt(prompt)

            self.save_cover_letter(generated_cover_letter, company_name)
            self.compile_latex_to_pdf(company_name, position_title)
            generated_email = self.generate_email_with_gpt(job_add_text, company_name, position_title, contact_name, email_address)
            print(f"Generated Email: {generated_email}")

    