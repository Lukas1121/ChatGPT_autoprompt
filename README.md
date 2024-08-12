
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
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your configuration files:
   - Place your OpenAI API key and Gmail secret token in the appropriate configuration files.

## Usage

1. **Run the Main Script**:
   - The full automation process is initiated by running the `main.py` script, which orchestrates all other scripts (`jobsearch.py`, `AutoPrompt.py`, `emailsender.py`).
   - This script handles job search, data extraction, cover letter generation, and email preparation.

   ```bash
   python main.py
   ```

2. **Script Dependencies**:
   - The individual scripts (`jobsearch.py`, `AutoPrompt.py`, `emailsender.py`) are not meant to be run standalone. They are invoked by `main.py` as part of the automation process.

## Configuration

- **configs folder**:
  - Contains all the necessary templates and details for generating cover letters and emails.
  - Customize your CV, cover letter template, and other considerations in this folder.

- **jobs.json**:
  - Stores all the mined job details for use in the scripts as well as for loggin.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


