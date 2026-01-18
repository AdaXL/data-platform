import os

from pyspark.sql import SparkSession


def clean_and_convert_to_parquet(input_path="data/raw", output_path="data/processed"):
    """
    Reads CSV files from input_path, cleans them, and saves as Parquet to output_path.
    """
    # Initialize SparkSession
    # If SPARK_MASTER env var is set, use it. Otherwise, default to local[*] for dev/testing.
    # In production (e.g., EMR, Databricks), the master is usually set by the spark-submit command,
    # so we can omit .master() if we want to respect the submission context.

    builder = SparkSession.builder.appName("KaggleMetaCleaner")

    # Only set master explicitly if provided or if running as a standalone script (not via spark-submit)
    # A common pattern is to check an env var or default to local if not present.
    master_url = os.getenv("SPARK_MASTER", "local[*]")
    builder = builder.master(master_url)

    spark = builder.getOrCreate()

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Define schemas or transformations for specific tables
    tables = {
        # 'Users.csv': 'users',
        # 'Competitions.csv': 'competitions',
        # 'UserAchievements.csv': 'user_achievements',
        # 'ForumMessages.csv': 'forum_messages',
        "UserFollowers.csv": "user_followers"
    }

    for file_name, table_name in tables.items():
        file_path = os.path.join(input_path, file_name)
        if os.path.exists(file_path):
            print(f"Processing {file_name}...")
            try:
                df = spark.read.csv(file_path, header=True, inferSchema=True)

                # Basic cleaning example: Remove rows with null IDs if applicable
                # This is generic; specific logic can be added per table
                if "Id" in df.columns:
                    # Use string expression for filter to avoid column object issues in some contexts
                    df = df.filter("Id IS NOT NULL")

                # Save as Parquet
                output_file = os.path.join(output_path, table_name)
                df.write.mode("overwrite").parquet(output_file)
                print(f"Saved {table_name} to {output_file}")
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
        else:
            print(f"File {file_name} not found in {input_path}")

    spark.stop()


if __name__ == "__main__":
    clean_and_convert_to_parquet()
