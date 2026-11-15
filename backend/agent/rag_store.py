import os
import chromadb
from sentence_transformers import SentenceTransformer

class LocalEmbeddingFunction:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def __call__(self, input_texts):
        if isinstance(input_texts, str):
            input_texts = [input_texts]
        embeddings = self.model.encode(input_texts, show_progress_bar=False)
        return embeddings.tolist()

def get_policy_collection():
    chroma_path = os.path.join(os.path.dirname(__file__), "../chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    embedding_fn = LocalEmbeddingFunction()
    
    collection = client.get_or_create_collection(
        name="support_policies",
        embedding_function=embedding_fn
    )
    
    if collection.count() == 0:
        docs = [
            "Customers can return eligible items within 30 days of the delivery date for a full refund. Items must be unopened and in original packaging.",
            "Standard refunds are processed back to the original payment method within 3-5 business days. Refunds above 2,000 require manual manager approval via the approval gate.",
            "Standard shipping takes 3-5 business days. If a package is marked as delivered but not received, customers must report it within 7 days for investigation or reshipment.",
            "If an item arrives damaged, the customer is eligible for an immediate free reshipment or a full refund without returning the item, provided photographic proof is supplied."
        ]
        metadatas = [
            {"title": "Return Window Policy", "category": "returns"},
            {"title": "Refund Eligibility Rules", "category": "refunds"},
            {"title": "Shipping and Delivery Terms", "category": "shipping"},
            {"title": "Damaged or Defective Items", "category": "damaged items"}
        ]
        ids = ["pol_1", "pol_2", "pol_3", "pol_4"]
        collection.add(documents=docs, metadatas=metadatas, ids=ids)
        
    return collection