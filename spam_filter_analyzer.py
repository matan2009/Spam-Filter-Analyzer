import re
import sys
import os
import csv
from email import policy
from email.parser import BytesParser
from multiprocessing import Pool
import asyncio
import aiospamc

# CSV output file headers
HEADERS = ['eml filename', 'subject', 'sender name', 'sender address', 'recipient address', 'spam-assassin score',
           'number of attachments', 'list of attachments file names', 'list of links', 'number of links', 'date']

# Script input
ARGS = sys.argv[1:]
MAILS_FOLDER_PATH = ARGS[0]
THRESHOLD = ARGS[1]
SPAM_SERVICE_ADDRESS = ARGS[2]
PATH_TO_CSV_FOLDER = ARGS[3]


async def check_for_spam(message):
    spam_service_ip = SPAM_SERVICE_ADDRESS[:SPAM_SERVICE_ADDRESS.find(':')]
    response = await aiospamc.check(message, host=spam_service_ip)
    return response


def extract_spam_assassin_score(email_body, eml_metadata):
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(check_for_spam(email_body.as_string().encode('ascii')))
    spam_assassin_score = response.headers['Spam'].score
    if spam_assassin_score >= float(THRESHOLD):
        eml_metadata['spam-assassin score'] = spam_assassin_score
        return True
    return False


def extract_mail_file_name(eml_filename, eml_metadata):
    eml_metadata['eml filename'] = eml_filename


def extract_mail_subject(email_body, eml_metadata):
    eml_metadata['subject'] = email_body['Subject']


def extract_sender_name(email_body, eml_metadata):
    try:
        # trying to extract sender name from email body
        sender_data = email_body['From']
        sender_name = re.search((r'[\w\s\.-]+[^<>@\w\.-]'), sender_data)
        eml_metadata['sender name'] = sender_name.group(0)
    except Exception:
        # Couldn't extract sender name from email body
        pass


def extract_sender_address(email_body, eml_metadata):
    try:
        # trying to extract sender mail address from email body
        sender_data = email_body['From']
        sender_address = re.search(r'[a-zA-Z0-9_.-]+@[a-zA-Z0-9][a-zA-Z0-9-.]+\.([a-zA-Z]{2,6})', sender_data)
        eml_metadata['sender address'] = sender_address.group(0)
    except Exception:
        # Couldn't extract sender mail address from email body
        pass


def extract_recipient_address(email_body, eml_metadata):
    try:
        # trying to extract recipient mail address from email body
        recipient_data = email_body['To']
        recipient_address = re.search(r'[a-zA-Z0-9_.-]+@[a-zA-Z0-9][a-zA-Z0-9-.]+\.([a-zA-Z]{2,6})', recipient_data)
        eml_metadata['recipient address'] = recipient_address.group(0)
    except Exception:
        # Couldn't extract recipient mail address from email body
        pass


def extract_number_of_attachments(email_body, eml_metadata):
    try:
        number_of_attachments = email_body.as_string().count('Content-Disposition: attachment')
        eml_metadata['number of attachments'] = number_of_attachments
    except Exception:
        # Couldn't extract number of attachments from email body
        pass


def extract_metadata_by_keyword(email_body, key_word):
    matches = re.finditer(key_word, email_body.as_string())
    file_names_start_indexes = [match.end() for match in matches]
    file_names_end_indexes = [email_body.as_string().find('"', index + 1) for index in file_names_start_indexes]
    return [email_body.as_string()[start:end] for (start, end) in
                  zip(file_names_start_indexes, file_names_end_indexes)]


def extract_attachments_file_names(email_body, eml_metadata):
    try:
        key_word = 'filename='
        attachments_file_names = extract_metadata_by_keyword(email_body, key_word)
        if attachments_file_names:
            eml_metadata['list of attachments file names'] = attachments_file_names
    except Exception:
        # Couldn't extract attachments file names from email body
        pass


def extract_list_of_links(email_body, eml_metadata):
    try:
        key_word = 'href=3D'
        list_of_links = extract_metadata_by_keyword(email_body, key_word)
        if list_of_links:
            eml_metadata['list of links'] = list_of_links
    except Exception:
        # Couldn't extract list of links from email body
        pass


def extract_number_of_links(email_body, eml_metadata):
    number_of_links = email_body.as_string().count('href=3D')
    eml_metadata['number of links'] = number_of_links


def extract_date_mail_received(email_body, eml_metadata):
    eml_metadata['date'] = email_body['Date']


def extract_metadata_from_mails(eml_filename):
    eml_metadata = {}
    email_full_address = os.path.join(MAILS_FOLDER_PATH, eml_filename)
    with open(email_full_address, 'rb') as fp:
        email_body = BytesParser(policy=policy.default).parse(fp)
        if extract_spam_assassin_score(email_body, eml_metadata):
            extract_mail_file_name(eml_filename, eml_metadata)
            extract_mail_subject(email_body, eml_metadata)
            extract_sender_name(email_body, eml_metadata)
            extract_sender_address(email_body, eml_metadata)
            extract_recipient_address(email_body, eml_metadata)
            extract_number_of_attachments(email_body, eml_metadata)
            extract_attachments_file_names(email_body, eml_metadata)
            extract_list_of_links(email_body, eml_metadata)
            extract_number_of_links(email_body, eml_metadata)
            extract_date_mail_received(email_body, eml_metadata)
        return eml_metadata


def main():
    try:
        csv_file = open(os.path.join(PATH_TO_CSV_FOLDER, 'csv_file.csv'), 'w', encoding='UTF8', newline='')
        writer = csv.DictWriter(csv_file, fieldnames=HEADERS)
        writer.writeheader()
        with Pool() as pool:
            eml_metadata = pool.map(extract_metadata_from_mails, os.listdir(MAILS_FOLDER_PATH))
            filtered_eml_metadata = filter(None, eml_metadata)
            writer.writerows(filtered_eml_metadata)
        csv_file.close()
    except Exception as ex:
        with open('error_file.txt', 'w') as err_file:
            err_file.write(f"The script couldn't run as expected because of the following error: {ex}")


if __name__ == '__main__':
    main()

