import argparse
import os
from app.services.rag_service import RAGService


def main() -> None:
    parser = argparse.ArgumentParser(description="Index Odoo addons into a local ChromaDB vector store")
    parser.add_argument("--path", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "odoo", "addons"), help="Path to the Odoo addons directory")
    parser.add_argument("--reset", action="store_true", help="Reset and re-index the collection")
    parser.add_argument("--persist-dir", default=None, help="Optional ChromaDB persist directory")
    parser.add_argument("--collection", default="odoo_reference", help="ChromaDB collection name")
    args = parser.parse_args()

    rag_service = RAGService(persist_directory=args.persist_dir, collection_name=args.collection, odoo_addons_path=args.path)
    result = rag_service.index_directory(source_path=args.path, reset=args.reset)
    print(result)


if __name__ == "__main__":
    main()
