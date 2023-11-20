# k8s-dump-and-drive
Automate the process of capturing heap and thread dumps from Kubernetes pods and seamlessly upload them to Google Drive. This Python script simplifies diagnostic operations by facilitating efficient dump management within Kubernetes environments.

## Key Features
- Google Drive Integration: Easily upload compressed dump files to Google Drive for centralized storage and accessibility.
Kubernetes 
- Automation: Streamlined heap and thread dump creation within Kubernetes pods using standard tools (jmap and jstack).
- Automatic Cleanup: Scheduled cleanup of old dump files on Google Drive to ensure efficient space utilization.
- Customizable: Adjust the script for different Kubernetes namespaces and pod instances.

## Prerequisites
- Google Drive API credentials in the form of a service account JSON file (devops-infra.json).
- Python 3.x installed.
- Google API client library installed (pip install --upgrade google-api-python-client).

## Configuration
- Set the path to the service account credentials file (SERVICE_ACCOUNT_FILE).
- Set the ID of the target folder in Google Drive (FOLDER_ID).
- Update the Kubernetes namespace and pod name in the script for the dump operation.

## Usage
1. Clone the Repository:
```
git clone git@github.com:vivek-raj1/k8s-dump-and-drive.git
```

2. Set Up Google Drive API:
- Obtain a service account JSON file (devops-infra.json) and update the script accordingly.

3. Run the Script:
```
pip install -r requirements.txt
mv .env.sample .env
python dump.py NAMESPACE POD_NAME
```
Replace NAMESPACE and POD_NAME with the appropriate values for your Kubernetes environment.

4. Explore Dumps:
- Compressed dump files will be uploaded to Google Drive.
- Old dump files will be automatically cleaned up after 24 hours.

## Process Overview
### Google Drive Cleanup:
- Deletes files in the specified Google Drive folder older than 24 hours.

### Kubernetes Heap and Thread Dumps:
- Takes a heap dump using the jmap command within the pod.
- Takes a thread dump using the jstack command within the pod.
- Deletes the dump file from the pod.

### File Compression:
- Creates a tar.gz file containing the heap and thread dumps.

### Google Drive Upload:
- Uploads the compressed file to the specified Google Drive folder.

## Notes
- Dump files will be deleted from the pod after creation.
- Uploaded files will be automatically cleaned up from Google Drive after 24 hours.