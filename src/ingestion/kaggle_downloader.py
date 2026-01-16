import os
import kaggle
import zipfile

def download_meta_kaggle_dataset(download_path='data/raw'):
    """
    Downloads the Meta Kaggle dataset to the specified path.
    Requires Kaggle API credentials to be set up (e.g., ~/.kaggle/kaggle.json).
    """
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    
    print(f"Downloading Meta Kaggle dataset to {download_path}...")
    kaggle.api.authenticate()
    
    # List of specific files to download
    files_to_download = [
        # 'Users.csv',
        # 'Competitions.csv',
        # 'UserAchievements.csv',
        # 'ForumMessages.csv',
        'UserFollowers.csv'
    ]
    
    # Kaggle API doesn't support downloading specific files easily via dataset_download_files with unzip=True for a subset
    # So we download the whole thing or use the API to get specific files if possible.
    # For simplicity in this script, we'll download the zip and extract specific files, 
    # or just download everything as before but we acknowledge the plan focuses on these.
    # Actually, let's try to download specific files if the API allows, otherwise full download.
    # The kaggle api 'dataset_download_file' downloads a single file.
    
    for file_name in files_to_download:
        print(f"Downloading {file_name}...")
        kaggle.api.dataset_download_file('kaggle/meta-kaggle', file_name, path=download_path)
        
        # Unzip if it comes as a zip (Kaggle API often zips individual large files)
        zip_path = os.path.join(download_path, file_name + '.zip')
        if os.path.exists(zip_path):
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(download_path)
            os.remove(zip_path)
            print(f"Extracted {file_name}")
        else:
             print(f"{file_name} downloaded (not zipped or already extracted).")

    print("Download complete.")

if __name__ == "__main__":
    download_meta_kaggle_dataset()
