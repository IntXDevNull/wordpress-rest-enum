import requests
import json
import argparse
import logging
import urllib3
import re

urllib3.disable_warnings()

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input-file", help="Input file containing list of websites", type=str, required=False)
parser.add_argument("-o", "--output-file", help="Output file to save the results.", type=str, default='wordpress_sites.txt')
parser.add_argument("--log-level", default=logging.INFO, type=lambda x: getattr(logging, x), help="Configure the logging level.")
parser.add_argument("-m", "--media", help="Fetch media", action=argparse.BooleanOptionalAction, required=False)
parser.add_argument("-po", "--posts", help="Fetch posts", action=argparse.BooleanOptionalAction, required=False)
parser.add_argument("-pa", "--pages", help="Fetch pages", action=argparse.BooleanOptionalAction, required=False)
parser.add_argument("-u", "--users", help="Fetch users", action=argparse.BooleanOptionalAction, required=False)
parser.add_argument("-c", "--comments", help="Fetch comments", action=argparse.BooleanOptionalAction, required=False)
parser.add_argument(
    "-im",
    "--ignoreImages",
    help="Filter out extensions commonly associated with images and video",
    action=argparse.BooleanOptionalAction,
    required=False,
)

cliArgs = parser.parse_args()

# Logging
logging.basicConfig(level=cliArgs.log_level)

# Globals
HEADERS = {'User-Agent': 'WordPress Testing'}

def requestRESTAPIComments(website: str, fetchPage: int, timeout=10) -> list:
    perPage = 100
    apiRequest = f'{website}/wp-json/wp/v2/comments?per_page={perPage}&page={str(fetchPage)}'
    results = []
    try:
        with requests.Session() as s:
            download = s.get(apiRequest, headers=HEADERS, verify=False, timeout=timeout)
            if download.status_code == 200:
                content = '[' + '['.join(download.text.split('[')[1:])
                comments = json.loads(content)
                for comment in comments:
                    try:
                        newComment = {"name": comment['author_name'], "date": comment['date'], "link": comment['link']}
                        results.append(newComment)
                    except Exception as err:
                        logging.error(f"Unexpected {err=}, {type(err)=}")
                fetchPage += 1
                if len(comments) > 0:
                    results += requestRESTAPIComments(website, fetchPage)
    except (json.JSONDecodeError, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError) as e:
        logging.error(f"Error in requestRESTAPIComments: {e}")
    return results

def requestRESTAPIUsers(website: str, fetchPage: int, timeout=10) -> list:
    perPage = 100
    apiRequest = f'{website}/wp-json/wp/v2/users?per_page={perPage}&page={str(fetchPage)}'
    results = []
    try:
        with requests.Session() as s:
            download = s.get(apiRequest, headers=HEADERS, verify=False, timeout=timeout)
            if download.status_code == 200:
                content = download.text
                users = json.loads(content)
                for user in users:
                    try:
                        newUser = {"name": user['name'], "username": user['slug']}
                        results.append(newUser)
                    except Exception as err:
                        logging.error(f"Unexpected {err=}, {type(err)=}")
                fetchPage += 1
                if len(users) > 0:
                    results += requestRESTAPIUsers(website, fetchPage)
    except (json.JSONDecodeError, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError) as e:
        logging.error(f"Error in requestRESTAPIUsers: {e}")
    return results

def requestRESTAPI(type: str, website: str, fetchPage: int, timeout=10) -> list:
    perPage = 100
    results = []
    try:
        apiRequest = f'{website}/wp-json/wp/v2/{type}?per_page={perPage}&page={str(fetchPage)}'
        with requests.Session() as s:
            download = s.get(apiRequest, headers=HEADERS, verify=False, timeout=timeout)
            if download.status_code == 200:
                content = download.text
                if content:
                    apiResponse = json.loads(content)
                    for typeReturn in apiResponse:
                        try:
                            results.append(typeReturn['guid']['rendered'])
                        except Exception as err:
                            logging.error(f"Unexpected {err=}, {type(err)=}")
                    fetchPage += 1
                    if len(apiResponse) > 0:
                        results += requestRESTAPI(type, website, fetchPage)
    except (json.JSONDecodeError, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError) as e:
        logging.error(f"Error in requestRESTAPI: {e}")
    return results

def process_website(website):
    result = {}
    fetchPage = 1
    if cliArgs.posts:
        result["posts"] = requestRESTAPI("posts", website, fetchPage)
    if cliArgs.pages:
        result["pages"] = requestRESTAPI("pages", website, fetchPage)
    if cliArgs.comments:
        result["comments"] = requestRESTAPIComments(website, fetchPage)
    if cliArgs.media:
        result["media"] = requestRESTAPI("media", website, fetchPage)
        if cliArgs.ignoreImages:
            newMedia = []
            for url in result.get('media', []):
                if not re.search(r'\.(jpg|gif|jpeg|png|svg|tiff|webm|webp)$', url, flags=re.IGNORECASE):
                    newMedia.append(url)
            result["media"] = newMedia
    if cliArgs.users:
        result["users"] = requestRESTAPIUsers(website, fetchPage)
    return result

def main():
    websites = []
    if cliArgs.input_file:
        try:
            with open(cliArgs.input_file, 'r') as infile:
                websites = [line.strip() for line in infile if line.strip()]
        except Exception as e:
            logging.error(f"Error reading input file: {e}")
            return

    if not websites:
        logging.error("No websites provided. Please specify an input file.")
        return

    all_results = []
    for website in websites:
        logging.info(f"Processing {website}...")
        result = process_website(website)
        all_results.append({website: result})

    output = json.dumps(all_results, indent=4)
    if cliArgs.output_file:
        try:
            with open(cliArgs.output_file, 'w') as outfile:
                outfile.write(output)
            logging.info(f"Results saved to {cliArgs.output_file}")
        except Exception as e:
            logging.error(f"Error writing output file: {e}")
    else:
        print(output)

if __name__ == '__main__':
    main()
