import os
import sys
import unittest
from unittest.mock import patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from ingestion.kaggle_downloader import download_meta_kaggle_dataset


class TestKaggleDownloader(unittest.TestCase):

    @patch("ingestion.kaggle_downloader.kaggle")
    @patch("ingestion.kaggle_downloader.os")
    @patch("ingestion.kaggle_downloader.zipfile")
    def test_download_meta_kaggle_dataset(self, mock_zipfile, mock_os, mock_kaggle):
        # Setup mocks
        mock_os.path.exists.return_value = False

        # Run function
        download_meta_kaggle_dataset(download_path="data/test_raw")

        # Assertions
        mock_os.makedirs.assert_called_with("data/test_raw")
        mock_kaggle.api.authenticate.assert_called_once()

        # Check that specific files were requested
        expected_files = [
            # 'Users.csv',
            # 'Competitions.csv',
            # 'UserAchievements.csv',
            # 'ForumMessages.csv',
            "UserFollowers.csv"
        ]

        # Verify dataset_download_file was called for each expected file
        self.assertEqual(
            mock_kaggle.api.dataset_download_file.call_count, len(expected_files)
        )

        # Verify calls
        calls = [
            unittest.mock.call("kaggle/meta-kaggle", f, path="data/test_raw")
            for f in expected_files
        ]
        mock_kaggle.api.dataset_download_file.assert_has_calls(calls, any_order=True)


if __name__ == "__main__":
    unittest.main()
