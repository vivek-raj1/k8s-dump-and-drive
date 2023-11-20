import os
from dotenv import load_dotenv
import subprocess
import tarfile
import datetime
import shutil
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pytz

# Load environment variables from .env file
load_dotenv()

# Set the service account credentials file path
SERVICE_ACCOUNT_FILE = os.environ.get('SERVICE_ACCOUNT_FILE', 'devops-infra.json')

# ID of the target folder in Google Drive
FOLDER_ID = os.environ.get('FOLDER_ID', '1UQIThvghtfhvUdLFn-DAvcKj')

# Authenticate using the service account credentials
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/drive']
)

# Create a Drive API client
drive_service = build('drive', 'v3', credentials=credentials)

# Get a list of all files in the target folder
results = drive_service.files().list(q=f"'{FOLDER_ID}' in parents",
                                     fields="files(id, name, createdTime)").execute()
files = results.get('files', [])

# Calculate the current time in IST (Indian Standard Time)
ist_timezone = pytz.timezone('Asia/Kolkata')
current_time = datetime.datetime.now(ist_timezone)
five_minutes_ago = current_time - datetime.timedelta(minutes=1440)

# Iterate over the files and delete those older than 5 minutes
for file in files:
    file_name = file['name']
    file_id = file['id']
    created_time = file['createdTime']

    # Convert the ISO formatted timestamp to a datetime object in IST
    created_timestamp = datetime.datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC)
    created_timestamp = created_timestamp.astimezone(ist_timezone)

    if created_timestamp < five_minutes_ago:
        # Delete the file
        drive_service.files().delete(fileId=file_id).execute()
        print(f"Deleted file: {file_name}")
    else:
        print(f"File not eligible for deletion: {file_name}")

# Check if the correct number of command-line arguments is provided
if len(sys.argv) != 3:
    print("Usage: python dump.py NAMESPACE POD_NAME")
    sys.exit(1)

# Get the namespace and pod name from the command-line arguments
NAMESPACE = sys.argv[1]
POD_NAME = sys.argv[2]

# Set the output directory for dumps
OUTPUT_DIR = '/tmp'

# Create the output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set the timestamp for the dump file names
timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')

# Take a heap dump using jmap command within the pod
heap_dump_file = os.path.join(OUTPUT_DIR, f'{POD_NAME}_heapdump_{timestamp}.hprof')
subprocess.run(['kubectl', 'exec', '-n', NAMESPACE, POD_NAME, '--', 'jmap', '-dump:format=b,file=/tmp/heapdump', '1'], check=True)
subprocess.run(['kubectl', 'cp', f'{NAMESPACE}/{POD_NAME}:/tmp/heapdump', heap_dump_file], check=True)
print('heap done')
# Take a thread dump using jstack command within the pod
thread_dump_file = os.path.join(OUTPUT_DIR, f'{POD_NAME}_threaddump_{timestamp}.txt')
proc = subprocess.run(['kubectl', 'exec', '-n', NAMESPACE, POD_NAME, '--', 'jstack', '1'], stdout=subprocess.PIPE, check=True, universal_newlines=True)
with open(thread_dump_file, 'w') as file:
    file.write(proc.stdout)

print('thread done')
# Delete the file from the pod
delete_command = f'kubectl exec -n {NAMESPACE} {POD_NAME} -- rm /tmp/heapdump'
subprocess.run(delete_command, shell=True, check=True)
print('File deleted from pod')


# Create a tar.gz file for the dumps
#compressed_file = os.path.join(OUTPUT_DIR, f'{POD_NAME}_dumps_{timestamp}.tar.gz')
#with tarfile.open(compressed_file, 'w:gz') as tar:
#    tar.add(heap_dump_file, arcname=f'{POD_NAME}_heapdump_{timestamp}.hprof')
#    tar.add(thread_dump_file, arcname=f'{POD_NAME}_threaddump_{timestamp}.txt')

compressed_file = os.path.join(OUTPUT_DIR, f'{POD_NAME}_dumps_{timestamp}.tar.gz')
subprocess.run(['tar', '-czf', compressed_file, heap_dump_file, thread_dump_file], check=True)
print('Compression completed.')
print('compress done')
# Upload the compressed file to Google Drive
file_metadata = {'name': os.path.basename(compressed_file), 'parents': [FOLDER_ID]}
media = MediaFileUpload(compressed_file)
file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

print('upload done')
# Print the link to the uploaded file
file_id = file.get('id')
file_link = f"https://drive.google.com/uc?export=download&id={file_id}"
print(f"File uploaded successfully. Link: {file_link}")
print("File will delete after 24 hours")

# Clean up the temporary dump files and compressed file
os.remove(heap_dump_file)
os.remove(thread_dump_file)
os.remove(compressed_file)