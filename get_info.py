import requests
import csv
import re

#API
print("please enter your api_key")
api_key = input()
print('please enter your space ID')
space_id = input()
project_prefix = 'R'

# name of csv
csv_filename = 'backlog_comments.csv'

# circul number to normal number
trans_table = {ord(chr(0x2460 + i)): ord(str(i + 1)) for i in range(9)}

def replace_circled_with_translate(text: str) -> str:
    return text.translate(trans_table)

# write on the csv
def write_csv(writer, issue_id_or_key, castomer_number, title, comment_id, created_user, comment_text, created_date):
    comment_text = comment_text.replace('\n', ' ').replace('\r', ' ')
    writer.writerow([
        str(issue_id_or_key),
        str(castomer_number),
        str(title),
        str(comment_id),
        str(created_user),
        str(comment_text),
        str(created_date)
    ])

# create csv
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['issue_key', 'castomer_number', 'Title', 'comment_ID', 'Contributor', 'Text', 'date'])

    issue_number = 1

    while True:
        issue_id_or_key = f"{project_prefix}-{issue_number}"

        # get the info
        issue_url = f'https://{space_id}.backlog.com/api/v2/issues/{issue_id_or_key}'
        issue_response = requests.get(issue_url, params={'apiKey': api_key})

        if issue_response.status_code == 200:
            issue_data = issue_response.json()
            title = issue_data.get('summary', '')
            title = replace_circled_with_translate(title)

            min_id = None 

            while True:
                comment_url = f'https://{space_id}.backlog.com/api/v2/issues/{issue_id_or_key}/comments'
                params = {
                    'apiKey': api_key,
                    'count': 100
                }
                if min_id is not None:
                    params['minId'] = min_id

                comment_response = requests.get(comment_url, params=params)

                if comment_response.status_code == 200:
                    comments = comment_response.json()

                    print(f"{issue_id_or_key} : number of comment {len(comments)}")

                    if not comments:
                        break

                    for comment in comments:
                        comment_id = comment.get('id')
                        created_user = comment.get('createdUser', {}).get('name')
                        comment_text = comment.get('content')
                        created_date = comment.get('created')

                        if not (comment_text and created_user):
                            continue
       
       
    
                        hyphen_match = re.search(r'\d+-\d+', title)

                        if hyphen_match:
                            castomer_number = hyphen_match.group()
                        else:
                            # if there are no '-', find frist number
                            match = re.match(r'\s*(\d+)', title)

                            if match:
                                castomer_number = match.group(1)
                            else:
                                # find firs cala
                                number_only = re.search(r'\d+', title)
                                if number_only:
                                    number_start = number_only.start()
                                    if len(title) > number_start + len(number_only.group()):
                                        next_char = title[number_start + len(number_only.group())]
                                        if next_char == '/':
                                            castomer_number = '' 
                                        else:
                                            castomer_number = number_only.group()
                                    else:
                                        castomer_number = number_only.group()
                                else:
                                    castomer_number = ''

                        # check of -
                        if castomer_number and '-' not in castomer_number:
                            if len(castomer_number) < 3:
                                castomer_number = ''  

                        # castomer_number -> str
                        castomer_number = str(castomer_number)
                        castomer_number = replace_circled_with_translate(castomer_number)
                        castomer_number = f'="{castomer_number}"' if castomer_number else ''




                        # circul number -> normal number
                        castomer_number = replace_circled_with_translate(castomer_number)

                        write_csv(writer, issue_id_or_key, castomer_number, title, comment_id, created_user, comment_text, created_date)

                    # max ID
                    last_comment_id = max(c.get('id') for c in comments)
                    min_id = last_comment_id

                else:
                    print(f"error cannot get info of comments ({comment_response.status_code}): {comment_response.text}")
                    break

            issue_number += 1 

        elif issue_response.status_code == 404:
            #if the spesfic number is none, it will check that there are soome items
            print(f"there are no items, it will be skiped{issue_id_or_key} ")
            issue_number += 1  
            continue

        else:
            print(f"error cannot get issue_response info ({issue_response.status_code}): {issue_response.text}")
            break

    print(f"\n✅ {csv_filename} done")
