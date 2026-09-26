import pypandoc
import os
import urllib.request
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

print("Downloading Pandoc (this may take a minute)...")
try:
    pypandoc.download_pandoc()
    print("Pandoc downloaded successfully.")
except Exception as e:
    print(f"Error downloading pandoc: {e}")

try:
    print("Converting Markdown to DOCX...")
    output = pypandoc.convert_file('Final_Project_Report.md', 'docx', outputfile='Final_Project_Report.docx')
    print("Successfully created Final_Project_Report.docx!")
except Exception as e:
    print(f"Error during conversion: {e}")
