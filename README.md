# wordpress-rest-enum
A WordPress rest-enumeration script

# Install
- Pro Tip: utilize Python venv

`pip install -r requirements.txt`

# Usage
Enumerate users and media files: `python ./wordpress-rest-enum.py -w https://targetwebsite.com -u -m `

# Recommended
Install JQ lightweight and flexible command-line JSON processor and pipe the results into it.
Enumerate users and media files and parse results into JQ: `python ./wordpress-rest-enum.py -w https://targetwebsite.com -u -m | jq`
