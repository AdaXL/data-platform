import chromadb
from chromadb.utils import embedding_functions


class SchemaRetriever:
    def __init__(self, collection_name="schema_store"):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_functions.DefaultEmbeddingFunction(),
        )

    def index_schema(self, tables_info):
        """
        Dynamically indexes schema information.
        tables_info: List of dicts with 'table_name' and 'description' (or 'columns_str')
        """
        # Clear existing for simplicity in this dynamic app context, or manage updates smarter
        if self.collection.count() > 0:
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection.name,
                embedding_function=embedding_functions.DefaultEmbeddingFunction(),
            )

        documents = []
        metadatas = []
        ids = []

        for info in tables_info:
            table_name = info["table_name"]
            # Create a rich description document
            desc = f"Table: {table_name}. "
            if "description" in info:
                desc += f"Description: {info['description']} "
            if "columns" in info:
                desc += f"Columns: {info['columns']}"

            documents.append(desc)
            metadatas.append({"table": table_name})
            ids.append(table_name)

        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def retrieve_relevant_tables(self, query, n_results=5):
        """
        Returns the names of the tables most relevant to the user's query.
        """
        if self.collection.count() == 0:
            return []

        # Adjust n_results if we have fewer tables than requested
        count = self.collection.count()
        k = min(n_results, count)

        results = self.collection.query(query_texts=[query], n_results=k)

        if not results["metadatas"]:
            return []

        relevant_tables = [m["table"] for m in results["metadatas"][0]]
        return relevant_tables
