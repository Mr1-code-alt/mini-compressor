import markdown

with open("Final_Project_Report.md", "r", encoding="utf-8") as f:
    text = f.read()

# Convert markdown to html, enabling tables and fenced code blocks
html = markdown.markdown(text, extensions=['tables', 'fenced_code'])

# Add some basic styling so it looks good when opened in a browser or Word
html_full = f"""
<html>
<head>
<style>
    body {{ font-family: "Times New Roman", Times, serif; font-size: 12pt; line-height: 1.15; color: #000000; margin: 20px; text-align: justify; }}
    p {{ margin-top: 0pt; margin-bottom: 10pt; }}
    h1, h2, h3, h4 {{ font-family: Arial, Helvetica, sans-serif; color: #002060; text-align: left; margin-top: 18pt; margin-bottom: 6pt; line-height: 1.2; }}
    h1 {{ font-size: 16pt; text-transform: uppercase; text-align: center; border-bottom: 2px solid #002060; padding-bottom: 4px; }}
    h2 {{ font-size: 14pt; border-bottom: 1px solid #cccccc; padding-bottom: 2px; }}
    h3 {{ font-size: 12pt; font-weight: bold; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12pt 0; font-size: 11pt; font-family: Arial, sans-serif; page-break-inside: avoid; }}
    th, td {{ border: 1px solid #555555; padding: 6px 10px; text-align: left; vertical-align: top; }}
    th {{ background-color: #e6eef4; color: #002060; font-weight: bold; }}
    img {{ display: block; margin: 12pt auto; max-width: 90%; border: 1px solid #dddddd; padding: 4px; }}
    code, pre {{ font-family: Consolas, monospace; background-color: #f8f9fa; padding: 4px; border-radius: 4px; font-size: 10.5pt; }}
    pre {{ padding: 10px; border: 1px solid #e1e4e8; overflow-x: auto; margin-bottom: 12pt; }}
    blockquote {{ border-left: 4px solid #002060; background-color: #f0f4f8; padding: 8px 15px; margin: 12pt 0; font-style: italic; }}
    hr {{ margin: 15pt 0; border: 0; border-top: 1px solid #cccccc; }}
</style>
</head>
<body>
{html}
</body>
</html>
"""

with open("Final_Project_Report.html", "w", encoding="utf-8") as f:
    f.write(html_full)

print("HTML created successfully!")
