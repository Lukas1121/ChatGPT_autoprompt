import os
import json
import re
from openai import OpenAI
import subprocess
from chatgpt_autoprompt.email_sender import EmailSender

class CoverLetterGenerator:
    def __init__(self, client, config_paths):
        self.client = client
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

    def get_job_info_from_json(self, job_link):
        processed_links_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'jobs.json')

        if os.path.exists(processed_links_path):
            with open(processed_links_path, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    print("Error reading JSON file.")
                    return None
            
            for entry in data:
                if entry['job_link'] == job_link:
                    return entry
        
        return None


    def extract_company_position_email_and_contact_with_gpt(self, job_add_text):
        prompt = (
            "Extract the company name, the position title, the contact person's name, and the email address from the following job advertisement text. "
            "If any of the information is not clearly specified, return 'Unknown'. "
            "Also, determine if the job advertisement is in Danish. "
            "Format the output as 'Company: [company name], Position: [position title], Contact: [contact name], Email: [email address], Danish: [true/false]'.\n\n"
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

        print("Extracted Text:", extracted_text)  # Print the extracted text to debug

        result = {}
        for line in extracted_text.split(', '):
            if ': ' in line:
                key, value = line.split(': ', 1)
                result[key.lower()] = value
            else:
                print(f"Skipping line: {line} (unexpected format)")  # Log unexpected lines

        return result


    def construct_prompt(self, job_add, cv, cover_letter_template, considerations):
        prompt = (
            "I want you to produce a cover letter using the provided text template. "
            "The cover letter should be targeted to the job advertisement and should draw inspiration from my CV, but the cover letter template may also be used as inspiration. "
            "When constructing the cover letter, please consider the following points:\n\n"
            f"Cover Letter Template:\n{cover_letter_template}\n\n"
            f"Job Ad:\n{job_add}\n\n"
            f"My CV:\n{cv}\n\n"
            f"Considerations:\n{considerations}\n\n"
            "Please edit the text within the \\lettercontent{} tags accordingly without exaggerating my skills or claiming experience I do not have. "
            "Finally, give no response other than the exact code/cover letter, as I am using a piece of code to convert your prompt directly into a latex project and your response will be captured by this as well causing issues."
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
    
    def save_cover_letter(self, content, company_name):
        latex_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'LaTeX', 'Cover', 'cover.tex')

        with open(latex_file_path, 'r', encoding='utf-8') as file:
            main_tex_content = file.read()

        # Escape underscores for LaTeX
        company_name_latex = company_name.replace('_', '\\_')

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

    def generate_email_with_gpt(self, job_ad, company_name, position_title, contact_name, email_address, danish):
        prompt = (
            "Using the provided email template, generate an email targeting the specified job advertisement. "
            "Replace the placeholders with the relevant information from the job ad and the extracted details. "
            "start the mail with hello regardless of whether the contacts name is known"
            "Maintain the core message of the email while ensuring it is personalized for the job ad.\n\n"
            f"Job Ad:\n{job_ad}\n\n"
            f"Email Template:\n{self.email_template}\n\n"
            "Extracted Information:\n"
            f"Company: {company_name}\n"
            f"Position: {position_title}\n"
            f"Contact: {contact_name}\n"
            f"Email: {email_address}\n"
            "If the job advertisement is in Danish, then the email should also be in Danish. "
            "Make sure to keep popular jargon in its native language (e.g., 'web scraping' should not be translated as it would sound silly).\n"
            "Finally the proper word for cover letter in danish is simply 'ansøgning'"
        )

        response = self.client.chat.completions.create(
            model="gpt-4",
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

        # Split the subject and body
        try:
            subject = re.search(r'Subject:\s*(.*)', generated_email).group(1).strip()
            body = generated_email.split('\n', 1)[1].strip()
        except AttributeError:
            body = generated_email
            if danish:
                subject = f"Ansøgning for {position_title} hos {company_name}"
            else:
                subject = f"Application for {position_title} at {company_name}"

        return subject, body


    def process_job_ads(self, job_add_text, job_link):
        job_info = self.get_job_info_from_json(job_link)
        
        company_name = job_info['company']
        position_title = job_info['job_title']
        contact_name = job_info['contact_person']
        email_address = job_info['email']
        danish = job_info['danish'] 
        job_link = job_info['job_link']

        prompt = self.construct_prompt(job_add_text, self.cv_text, self.cover_letter_template, self.considerations_text)
        generated_cover_letter = self.generate_cover_letter_with_gpt(prompt)
        
        self.save_cover_letter(generated_cover_letter, company_name)
        self.compile_latex_to_pdf(company_name, position_title)

        if email_address.lower() == 'lukieminator@gmail.com':
            subject = f"Manual Application Required for {position_title} at {company_name}"
            body = f"This job needs to be applied to manually. Please find attached the generated cover letter and CV.\n\nJob Link: {job_link}"
        else:
            subject, body = self.generate_email_with_gpt(job_add_text, company_name, position_title, contact_name, email_address, danish=danish)

        email_sender = EmailSender()
        cover_letter_path = os.path.join(self.output_folder, f"{company_name}_{position_title}_cover_letter.pdf")
        cv_path = os.path.join(self.output_folder, 'CV_Dansk_Lukas_Zeppelin.pdf') if danish else os.path.join(self.output_folder, 'CV_English_Lukas_Zeppelin.pdf')
        
        files = [cover_letter_path, cv_path]

        email_sender.send_message('Lukas.zeppelin.ry@gmail.com', email_address, subject, body, files)
