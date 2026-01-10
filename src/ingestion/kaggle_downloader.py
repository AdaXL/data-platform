import os
import kaggle

def download_meta_kaggle_dataset(download_path='data/raw'):
    """
    Downloads the Meta Kaggle dataset to the specified path.
    Requires Kaggle API credentials to be set up (e.g., ~/.kaggle/kaggle.json).
    """
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    
    print(f"Downloading Meta Kaggle dataset to {download_path}...")
    kaggle.api.authenticate()
    kaggle.api.dataset_download_files('kaggle/meta-kaggle', path=download_path, unzip=True)
    print("Download complete.")

if __name__ == "__main__":
    download_meta_kaggle_dataset()
