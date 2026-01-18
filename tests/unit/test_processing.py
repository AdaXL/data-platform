import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from processing.data_cleaner import clean_and_convert_to_parquet


class TestDataCleaner(unittest.TestCase):

    @patch("processing.data_cleaner.SparkSession")
    @patch("processing.data_cleaner.os")
    def test_clean_and_convert_to_parquet(self, mock_os, mock_spark_session):
        # Setup mocks
        mock_spark = MagicMock()

        # Mock the builder chain: builder -> appName -> master -> getOrCreate
        # Note: We updated the code to use os.getenv("SPARK_MASTER", "local[*]"), so .master() is called.
        mock_builder = mock_spark_session.builder.appName.return_value
        mock_builder.master.return_value.getOrCreate.return_value = mock_spark

        mock_df = MagicMock()
        mock_spark.read.csv.return_value = mock_df
        mock_df.columns = ["Id", "Name"]  # Mock columns

        # Mock filter return (chaining)
        mock_df.filter.return_value = mock_df

        # Mock file existence
        def side_effect(path):
            if "UserFollowers.csv" in path:
                return True
            if "data/processed" in path:  # output path check
                return False
            return False

        mock_os.path.exists.side_effect = side_effect
        mock_os.path.join.side_effect = os.path.join  # Use real join
        mock_os.getenv.return_value = "local[*]"  # Mock env var default

        # Run function
        clean_and_convert_to_parquet(
            input_path="data/test_raw", output_path="data/test_processed"
        )

        # Assertions
        # Verify the builder chain was called
        mock_spark_session.builder.appName.assert_called_with("KaggleMetaCleaner")
        mock_builder.master.assert_called_with("local[*]")

        # Check that read.csv was called
        self.assertTrue(
            mock_spark.read.csv.called, "Spark read.csv should have been called"
        )

        # Check that write.parquet was called
        self.assertTrue(
            mock_df.write.mode.return_value.parquet.called,
            "DataFrame write.parquet should have been called",
        )


if __name__ == "__main__":
    unittest.main()
