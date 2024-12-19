from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QTextBrowser,
    QPushButton, QComboBox, QLabel, QSplitter, QDialog
)
from PyQt5.QtCore import Qt, QUrl
from datetime import time
import os
import re, math
import pickle

class DocumentViewer(QDialog):
    def __init__(self, file_path, content_index):
        super().__init__()
        self.file_path = file_path
        self.content_index = content_index
        self.setWindowTitle(os.path.basename(file_path))
        self.resize(800, 600)

        layout = QVBoxLayout()
        self.content_display = QTextBrowser(self)
        self.content_display.anchorClicked.connect(self.handle_link_click)
        layout.addWidget(self.content_display)

        self.load_document()
        self.setLayout(layout)

    def load_document(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            linked_content = self.add_hyperlinks(content)
            self.content_display.setHtml(linked_content)
        except Exception as e:
            self.content_display.setText(f"Could not open file: {str(e)}")

    def add_hyperlinks(self, content):
        linked_content = ""
        for line in content.splitlines():
            for word in re.findall(r'\w+', line):
                word_lower = word.lower()
                if word_lower in self.content_index:
                    linked_docs = {doc for doc in self.content_index[word_lower]}
                    # Only link if the word appears in exactly two documents (current + one other)
                    if len(linked_docs) == 2 and self.file_path in linked_docs:
                        linked_file = next(doc for doc in linked_docs if doc != self.file_path)
                        linked_content += f"<a href='{linked_file}'>{word}</a> "
                    else:
                        linked_content += f"{word} "
                else:
                    linked_content += f"{word} "
            linked_content += "<br>"
        return linked_content

    def handle_link_click(self, url):
        new_file_path = url.toLocalFile()
        if os.path.exists(new_file_path):
            self.file_path = new_file_path
            self.setWindowTitle(os.path.basename(new_file_path))
            self.load_document()

class UnifiedIRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unified Information Retrieval System")
        self.resize(1200, 800)

        # Initialize documents and indexing structures
        self.documents = self.load_documents('data')
        self.content_index = self.load_content_index('content_index.pkl')
        self.recent_searches = []

        # UI Components
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Search input and dropdown
        self.query_input = QLineEdit(self)
        self.query_input.setPlaceholderText("Enter your query here")
        layout.addWidget(QLabel("Search Query:"))
        layout.addWidget(self.query_input)

        # Model selector
        self.model_selector = QComboBox(self)
        self.model_selector.addItems([
            "Binary Independence Model",
            "Proximal Nodes Model",
            "Set-Theoretic Model",
            "Neural Network Model",
            "Probabilistic Model"
        ])
        layout.addWidget(QLabel("Select Retrieval Model:"))
        layout.addWidget(self.model_selector)

        # Recent searches dropdown
        self.recent_search_dropdown = QComboBox(self)
        self.recent_search_dropdown.addItem("Select a recent search")
        self.recent_search_dropdown.currentIndexChanged.connect(self.load_recent_search)
        layout.addWidget(QLabel("Recent Searches:"))
        layout.addWidget(self.recent_search_dropdown)

        # Search button
        self.search_button = QPushButton("Search", self)
        self.search_button.clicked.connect(self.perform_search)
        layout.addWidget(self.search_button)

        # Results display
        self.results_browser = QTextBrowser(self)
        self.results_browser.setOpenLinks(False)
        self.results_browser.anchorClicked.connect(self.open_document_viewer)
        layout.addWidget(QLabel("Search Results:"))
        layout.addWidget(self.results_browser)

        self.setCentralWidget(main_widget)

    def load_documents(self, directory):
        documents = {}
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        documents[file_path] = f.read()
        return documents

    def load_content_index(self, index_file):
        if os.path.exists(index_file):
            with open(index_file, 'rb') as f:
                return pickle.load(f)
        return {}

    def perform_search(self):
        query = self.query_input.text()
        if not query:
            self.results_browser.setText("Please enter a query.")
            return

        # Update recent searches
        if query not in self.recent_searches:
            self.recent_searches.insert(0, query)
            self.recent_search_dropdown.insertItem(1, query)

        # Preprocess query
        query_terms = re.findall(r'\w+', query.lower())

        # Select model
        model = self.model_selector.currentText()
        if model == "Binary Independence Model":
            results = self.bim_retrieve(query_terms)
        elif model == "Proximal Nodes Model":
            results = self.proximal_nodes_retrieve(query_terms)
        elif model == "Set-Theoretic Model":
            results = self.set_theoretic_retrieve(query_terms)
        elif model == "Neural Network Model":
            results = self.neural_network_retrieve(query_terms)
        elif model == "Probabilistic Model":
            results = self.probabilistic_retrieve(query_terms)
        else:
            results = []

        # Display results
        if results:
            results_html = "<b>Search Results:</b><br><br>"
            for doc, score in results:
                url = QUrl.fromLocalFile(doc).toString()
                snippet = self.documents[doc][:200].replace('\n', ' ') + '...'
                results_html += f"<a href='{url}'><b>{os.path.basename(doc)}</b></a> (Score: {score:.4f})<br>{snippet}<br><br>"
            self.results_browser.setHtml(results_html)
        else:
            self.results_browser.setText("No relevant documents found.")

    def bim_retrieve(self, query_terms):
        scores = {}
        for doc, content in self.documents.items():
            doc_terms = set(re.findall(r'\w+', content.lower()))
            common_terms = set(query_terms) & doc_terms
            scores[doc] = len(common_terms) / len(query_terms)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def generate_proximal_nodes(self, documents):
        """Generate a proximity graph based on term co-occurrence."""
        co_occurrence = {}
        for content in documents.values():
            unique_terms = set(content)
            for term in unique_terms:
                if term not in co_occurrence:
                    co_occurrence[term] = set()
                co_occurrence[term].update(unique_terms - {term})
        return co_occurrence
    
    # Proximal Nodes Model
    def proximal_nodes_retrieve_dynamic(self, query, documents, proximity_graph):
        """Retrieve documents based on dynamically generated proximal nodes."""
        related_terms = set()
        for term in query:
            if term in proximity_graph:
                related_terms.update(proximity_graph[term])
        related_docs = set()
        for term in related_terms:
            for doc_path, content in documents.items():
                if term in content:
                    related_docs.add(doc_path)
        return list(related_docs)

    def set_theoretic_retrieve(self, query_terms):
        start_time = time.time()
        query = self.search_bar.text()
        if not query:
            self.results_browser.setText("Please enter a search query.")
            return

        # Add to recent searches
        if query not in self.recent_searches:
            self.recent_searches.insert(0, query)
            self.search_dropdown.insertItem(0, query)

        tokens = self.tokenize(query)
        query_vector = {}
        num_documents = len(self.documents)

        # Build query vector
        for token in tokens:
            if token in self.term_document_matrix:
                idf = math.log(num_documents / len(self.term_document_matrix[token]))
                query_vector[token] = idf

        # Normalize query vector
        norm = math.sqrt(sum(value ** 2 for value in query_vector.values()))
        for token in query_vector:
            query_vector[token] /= norm

        # Calculate cosine similarity
        scores = {}
        for doc, doc_vector in self.document_vectors.items():
            score = 0
            for term, weight in query_vector.items():
                score += weight * doc_vector.get(term, 0)
            if score > 0:
                scores[doc] = score

        # Rank results
        ranked_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Display results
        elapsed_time = time.time() - start_time
        max_score = ranked_results[0][1] if ranked_results else 0
        min_score = ranked_results[-1][1] if ranked_results else 0
        score_range = max_score - min_score if max_score != min_score else 1

        results_html = f"<b>Search Results:</b> ({len(ranked_results)} results found in {elapsed_time:.4f} seconds)<br><br>"
        for rank, (doc, score) in enumerate(ranked_results):
            doc_name = os.path.basename(doc)
            snippet = self.documents[doc][:200].replace('\n', ' ') + '...'
            # Generate relative color gradient from red to green
            relative_score = (score - min_score) / score_range
            color = self.score_to_color(relative_score)
            results_html += (
                f"<a href='{doc}' style='color:black; text-decoration:none;'><b>{doc_name}</b></a> "
                f"<span style='color:{color};'>Score: {score:.4f}</span><br>{snippet}<br><br>"
            )
        return results_html

    def neural_network_retrieve(self, query_terms):
        query = self.search_bar.text()
        if not query:
            self.results_browser.setText("Please enter a query.")
            return

        # Tokenize and expand query
        query_terms = self.tokenize(query)
        expanded_query = self.semantic_expand(query_terms)

        # Rank articles
        scores = {}
        for title, content in self.articles.items():
            document_terms = self.tokenize(content)
            similarity_score = self.calculate_similarity(expanded_query, document_terms)
            if similarity_score > 0:
                scores[title] = similarity_score

        # Sort results
        ranked_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Display results
        if not ranked_results:
            self.results_browser.setText("No relevant articles found for your query.")
            return

        results_html = f"<b>Search Results for '{query}':</b><br><br>"
        for title, score in ranked_results:
            snippet = self.articles[title][:100] + '...'
            results_html += f"<a href='{title}'><b>{title}</b></a> (Score: {score:.4f})<br>{snippet}<br><br>"

        return results_html

    def probabilistic_retrieve(self, query_terms):
        """Perform a search and display results."""
        query = self.search_bar.text()
        if not query or query not in self.queries:
            self.results_browser.setText("Invalid or empty query. Try 'cat', 'dog', or other predefined queries.")
            return

        model = self.model_selector.currentText()
        if model == "Interference Model":
            ranked_results = self.interference_model_rank(query)
        elif model == "Belief Network":
            ranked_results = self.belief_network_rank(query)
        else:
            self.results_browser.setText("Invalid model selected.")
            return

        results_html = f"<b>Search Results for '{query}' using {model}:</b><br><br>"
        for doc_id, score in ranked_results:
            snippet = self.documents[doc_id][:100] + '...'
            results_html += f"<a href='{doc_id}'><b>{doc_id}</b></a> (Score: {score:.4f})<br>{snippet}<br><br>"

        return results_html

    def load_recent_search(self):
        query = self.recent_search_dropdown.currentText()
        if query != "Select a recent search":
            self.query_input.setText(query)
            self.perform_search()

    def open_document_viewer(self, url):
        file_path = url.toLocalFile()
        if os.path.exists(file_path):
            viewer = DocumentViewer(file_path, self.content_index)
            viewer.exec_()

if __name__ == "__main__":
    app = QApplication([])
    window = UnifiedIRApp()
    window.show()
    app.exec_()
