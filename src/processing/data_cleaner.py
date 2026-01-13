from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date
import os

def clean_and_convert_to_parquet(input_path='data/raw', output_path='data/processed'):
    """
    Reads CSV files from input_path, cleans them, and saves as Parquet to output_path.
    """
    spark = SparkSession.builder \
        .appName("KaggleMetaCleaner") \
        .getOrCreate()

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Define schemas or transformations for specific tables
    tables = {
        'Users.csv': 'users',
        'Competitions.csv': 'competitions',
        'UserAchievements.csv': 'user_achievements',
        'ForumMessages.csv': 'forum_messages',
        'UserFollowers.csv': 'user_followers'
    }

    for file_name, table_name in tables.items():
        file_path = os.path.join(input_path, file_name)
        if os.path.exists(file_path):
            print(f"Processing {file_name}...")
            df = spark.read.csv(file_path, header=True, inferSchema=True)
            
            # Basic cleaning example: Remove rows with null IDs if applicable
            # This is generic; specific logic can be added per table
            if "Id" in df.columns:
                df = df.filter(col("Id").isNotNull())
            
            # Save as Parquet
            output_file = os.path.join(output_path, table_name)
            df.write.mode("overwrite").parquet(output_file)
            print(f"Saved {table_name} to {output_file}")
        else:
            print(f"File {file_name} not found in {input_path}")

    spark.stop()

if __name__ == "__main__":
    clean_and_convert_to_parquet()
