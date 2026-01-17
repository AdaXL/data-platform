import chromadb
from chromadb.utils import embedding_functions
import pandas as pd

class SchemaRetriever:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name="kaggle_schema",
            embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )
        self._populate_schema()

    def _populate_schema(self):
        """
        Populates the vector DB with semantic descriptions of the tables.
        In a real scenario, this would load from a schema.yml file.
        """
        if self.collection.count() > 0:
            return

        documents = [
            "Users table: Contains user profiles, including DisplayName, Id, and performance tier (Grandmaster, Master, etc.).",
            "Competitions table: Information about Kaggle competitions, including Title, HostSegment, RewardQuantity, and Deadlines.",
            "UserAchievements table: Tracks user performance in different categories (Competitions, Scripts, Discussions). Contains TotalGold, TotalSilver, TotalBronze medals.",
            "ForumMessages table: Contains individual forum posts, including the Message content, PostDate, and Sentiment.",
            "UserFollowers table: Graph of user connections, showing who follows whom."
        ]
        
        metadatas = [
            {"table": "users"},
            {"table": "competitions"},
            {"table": "user_achievements"},
            {"table": "forum_messages"},
            {"table": "user_followers"}
        ]
        
        ids = ["users", "competitions", "user_achievements", "forum_messages", "user_followers"]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def retrieve_relevant_tables(self, query, n_results=3):
        """
        Returns the names of the tables most relevant to the user's query.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        relevant_tables = [m['table'] for m in results['metadatas'][0]]
        return relevant_tables
