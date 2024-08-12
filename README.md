
# ChatGPT Autoprompt

## Overview

ChatGPT Autoprompt is a Python-based automation tool designed to streamline the job application process. It automates the search for job listings, extracts relevant details, generates customized cover letters, and prepares emails for application submission.

## Features

- **Job Search Automation**: Searches for job ads on Jobindex.
- **HTML Code Manipulation**: Cleans up HTML code to isolate job ads.
- **Data Extraction**: Mines job ads for specific details like job link, company, job title, contact person, contact email, and language.
- **Cover Letter Generation**: Uses ChatGPT to create personalized cover letters.
- **Email Preparation**: Generates application emails, including handling cases where contact information is missing.
- **Job Information Storage**: Saves extracted data into `jobs.json` for further processing.
- **Latex Compilation**: Compiles the generated cover letter using LaTeX.

## Requirements

- Python 3.x
- OpenAI API Key
- Gmail Secret Token/API Key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Lukas1121/ChatGPT_autoprompt.git
   cd ChatGPT_autoprompt
   ```

2. Install the required Python packages:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. Set up your configuration files:
   - Place your OpenAI API key and Gmail secret token in the appropriate configuration files.

## Usage

1. **Job Search**:
   - Run the \`jobsearch.py\` script to search for job ads on Jobindex.
   - The script will clean up the HTML code and send it to ChatGPT to extract the job description.

   \`\`\`bash
   python jobsearch.py
   \`\`\`

2. **Prompt Handling**:
   - Use the \`AutoPrompt.py\` script to handle the main prompts and interactions with ChatGPT.
   - This script mines job details and generates the cover letter.

   \`\`\`bash
   python AutoPrompt.py
   \`\`\`

3. **Email Sending**:
   - Use the \`emailsender.py\` script to send the application email and handle token validation.
   - If no contact email is found, the email is sent to yourself with a link to the job ad for manual input.

   \`\`\`bash
   python emailsender.py
   \`\`\`

## Configuration

- **configs folder**:
  - Contains all the necessary templates and details for generating cover letters and emails.
  - Customize your CV, cover letter template, and other considerations in this folder.

- **jobs.json**:
  - Stores all the mined job details for use in the scripts as well as for loggin.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


