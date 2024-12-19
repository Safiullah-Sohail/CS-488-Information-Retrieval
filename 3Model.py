import os
import re
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLineEdit, QTextBrowser, QPushButton, QComboBox, QWidget, QDialog
from PyQt5.QtCore import QUrl

# Non-nouns and noun suffixes for filtering
NON_NOUNS = {
    'the', 'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'and', 'or', 'but', 'if', 'while', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
    'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
    'both', 'each', 'few', 'more', 'some', 'such', 'no', 'nor', 'too', 'very', 'can', 'will', 'just', 'should',
    'would', 'could', 'might', 'must', 'not', 'he', 'she', 'it'
}
NOUN_SUFFIXES = ('tion', 'ment', 'ness', 'ity', 'ance', 'ence', 'ship', 'age', 'hood', 'ism', 'ist', 'cy', 'dom')

# Preprocessing function
def preprocess_text(text, phrases=None):
    """Tokenize, remove stopwords, and preserve phrases."""
    if phrases is None:
        phrases = []
    text = text.lower()
    for phrase in phrases:
        text = text.replace(phrase, phrase.replace(' ', '_'))  # Replace spaces with underscores for phrases
    words = re.findall(r'\w+', text)
    processed = [word for word in words if word not in NON_NOUNS]
    return [word.replace('_', ' ') for word in processed]  # Restore spaces in phrases

# Load and preprocess documents
def load_documents(directory, phrases=None):
    documents = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    documents[file_path] = preprocess_text(text, phrases)
    return documents

# Non-Overlapped List Model
def non_overlapped_retrieve(query, documents):
    retrieved_docs = set()
    for term in query:
        for doc_path, content in documents.items():
            if term in content:
                retrieved_docs.add(doc_path)
    return list(retrieved_docs)

# Dynamic Proximal Nodes Generation
def generate_proximal_nodes(documents):
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
def proximal_nodes_retrieve_dynamic(query, documents, proximity_graph):
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

# Binary Independence Model (BIM)
def bim_retrieve(query, documents):
    query_terms = set(query)
    rankings = []
    for doc_path, content in documents.items():
        doc_terms = set(content)
        intersection = len(query_terms & doc_terms)
        union = len(query_terms | doc_terms)
        jaccard_score = intersection / union if union != 0 else 0
        rankings.append((doc_path, jaccard_score))
    return sorted(rankings, key=lambda x: x[1], reverse=True)

# Document Viewer
class DocumentViewer(QDialog):
    def __init__(self, file_path):
        super().__init__()
        self.setWindowTitle(os.path.basename(file_path))
        self.resize(800, 600)

        layout = QVBoxLayout()
        content_display = QTextBrowser(self)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content_display.setText(file.read())
        except Exception as e:
            content_display.setText(f"Could not open file: {str(e)}")
        layout.addWidget(content_display)
        self.setLayout(layout)

# Main GUI Application
class DocumentRetrievalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Retrieval System")
        self.resize(700, 400)

        # Main layout
        layout = QVBoxLayout()

        # Query input
        self.query_input = QLineEdit(self)
        self.query_input.setPlaceholderText("Enter your query here")
        layout.addWidget(self.query_input)

        # Model selector
        self.model_selector = QComboBox(self)
        self.model_selector.addItems(["Binary Independence Model", "Non-Overlapped List Model", "Proximal Nodes Model"])
        layout.addWidget(self.model_selector)

        # Search button
        self.search_button = QPushButton("Search", self)
        self.search_button.clicked.connect(self.perform_search)
        layout.addWidget(self.search_button)

        # Results display
        self.result_display = QTextBrowser(self)
        self.result_display.setOpenLinks(False)
        self.result_display.anchorClicked.connect(self.show_document)
        layout.addWidget(self.result_display)

        # Set central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Load documents and generate proximity graph
        self.phrases = ["machine learning", "data visualization"]
        self.documents = load_documents('data', self.phrases)
        self.proximity_graph = generate_proximal_nodes(self.documents)

    def perform_search(self):
        query = self.query_input.text()
        if not query:
            self.result_display.setText("Please enter a query.")
            return

        # Disable the search button and show loading state
        self.search_button.setEnabled(False)
        self.search_button.setText("Loading...")
        QApplication.processEvents()  # Update UI

        start_time = time.time()

        # Preprocess the query
        query_terms = preprocess_text(query, self.phrases)

        # Select the retrieval model
        model = self.model_selector.currentText()
        if model == "Binary Independence Model":
            results = bim_retrieve(query_terms, self.documents)
            results = [doc for doc, _ in results]  # Extract document paths only
        elif model == "Non-Overlapped List Model":
            results = non_overlapped_retrieve(query_terms, self.documents)
        elif model == "Proximal Nodes Model":
            results = proximal_nodes_retrieve_dynamic(query_terms, self.documents, self.proximity_graph)
        else:
            results = []

        elapsed_time = time.time() - start_time

        # Display results
        if results:
            top_results = results[:10]  # Limit to top 10 results
            summary = f"<b>Showing {len(top_results)}/{len(results)} documents, retrieved in {elapsed_time:.2f} seconds.</b><br><br>"
            results_text = summary

            for i, doc_path in enumerate(top_results, 1):
                url = QUrl.fromLocalFile(doc_path).toString()
                results_text += f"<b><a href='{url}'>{doc_path}</a></b><br>"
                with open(doc_path, 'r', encoding='utf-8') as f:
                    snippet = f.read(200).strip().replace('\n', ' ')
                    results_text += f"Snippet: {snippet}...<br><br>"

            self.result_display.setHtml(results_text)
        else:
            self.result_display.setText("No relevant documents found.")

        # Re-enable the search button
        self.search_button.setEnabled(True)
        self.search_button.setText("Search")

    def display_results(self, results):
        if not results:
            self.result_display.setText("No relevant documents found.")
            return
        results_text = "Retrieved Documents:\n\n"
        for i, doc_path in enumerate(results, 1):
            url = QUrl.fromLocalFile(doc_path).toString()
            results_text += f"<a href='{url}'>{doc_path}</a>\n"
        self.result_display.setHtml(results_text)

    def show_document(self, url):
        file_path = url.toLocalFile()
        if os.path.exists(file_path):
            viewer = DocumentViewer(file_path)
            viewer.exec_()

# Run Application
app = QApplication([])
window = DocumentRetrievalApp()
window.show()
app.exec_()
