import os
import re
from openai import OpenAI

# Initialize the client with the API key
client = OpenAI(
    api_key="sk-proj-TWN2zc55FpVW6WjNKGmET3BlbkFJ9upgXSTJq9YPkgKxEj3n"
)

job_add_path = 'configs/job_add.txt'
cv_path = 'configs/my_cv.txt'
cover_letter_template_path = 'configs/cover_letter.txt'
considerations_path = 'configs/considerations.txt'
output_folder = 'configs/generated_cover_letters'

def extract_company_or_position_with_gpt(job_add_text):
    prompt = (
        "Extract the company name and the position title from the following job advertisement text. "
        "If the company name or position title is not clearly specified, return 'Unknown'. "
        "Format the output as 'Company: [company name], Position: [position title]'.\n\n"
        f"Job Ad:\n{job_add_text}\n"
    )

    response = client.chat.completions.create(
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

def construct_prompt(job_add, cv, cover_letter_template, considerations):
    prompt = (
        "I want you to produce a cover letter using the provided text template. "
        "The cover letter should be targeted to the job advertisement and should draw inspiration from my CV, but the cover letter template may also be used as inspiration "
        "When constructing the cover letter, please consider the following points:\n\n"
        f"Job Ad:\n{job_add}\n\n"
        f"My CV:\n{cv}\n\n"
        f"Considerations:\n{considerations}\n\n"
        f"Cover Letter Template:\n{cover_letter_template}\n\n"
        "Please edit the text within the \\lettercontent{} tags accordingly without exaggerating my skills or claiming experience I do not have. "
        "For any requirements in the job ad that I do not meet, emphasize my broad skill range in IT and advanced sciences such as physics, chemistry, and biophysics. Make sure to write the cover letter in the same language as the job ad"
    )
    return prompt

def save_cover_letter(output_path, content):
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(content)

# Read the contents of the files with UTF-8 encoding
with open(job_add_path, 'r', encoding='utf-8') as file:
    job_add_text = file.read()

with open(cv_path, 'r', encoding='utf-8') as file:
    cv_text = file.read()

with open(cover_letter_template_path, 'r', encoding='utf-8') as file:
    cover_letter_template = file.read()

with open(considerations_path, 'r', encoding='utf-8') as file:
    considerations_text = file.read()

# Extract company and position using GPT
extracted_info = extract_company_or_position_with_gpt(job_add_text)
print(f"Extracted Info: {extracted_info}")  # Debugging line

# Construct the prompt to send for cover letter generation
prompt = construct_prompt(job_add_text, cv_text, cover_letter_template, considerations_text)

def generate_cover_letter_with_gpt(prompt):
    prompt += "\nPlease make sure that each section is enclosed with the \lettercontent{} tags. Also, the cover letter is not alowed to exceed the template in length. It can be shorter, but no longer."

    response = client.chat.completions.create(
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

# Generate the cover letter using the GPT function
generated_cover_letter = generate_cover_letter_with_gpt(prompt)

# Determine the output filename based on the extracted info
company_name = re.search(r'Company:\s*([^,]+)', extracted_info).group(1).strip().replace(" ", "_")
position_title = re.search(r'Position:\s*([^\s,]+)', extracted_info).group(1).strip().replace(" ", "_")
output_filename = f"{company_name}_{position_title}_cover_letter.txt"
output_path = os.path.join(output_folder, output_filename)

# Save the generated cover letter
save_cover_letter(output_path, generated_cover_letter)

print(f"Cover letter saved to: {output_path}")