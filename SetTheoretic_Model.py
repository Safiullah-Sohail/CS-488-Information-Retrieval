import os
import re
import time
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLineEdit, QSplitter, QTreeWidget, QTreeWidgetItem, QTextBrowser, QWidget, QPushButton, QLabel, QComboBox, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QUrl

# Document Content Viewer
class DocumentViewer(QDialog):
    def __init__(self, file_path):
        super().__init__()
        self.setWindowTitle(os.path.basename(file_path))
        self.resize(800, 600)

        # Layout for the viewer
        layout = QVBoxLayout()

        # Independent text browser for displaying document content
        content_display = QTextBrowser(self)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content_display.setText(file.read())
        except Exception as e:
            content_display.setText(f"Could not open file: {str(e)}")

        layout.addWidget(content_display)
        self.setLayout(layout)

class SetTheoreticIRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Set-Theoretic IR Models - Generalized Vector Model")
        self.resize(1200, 800)

        # Initialize term-document structures
        self.documents = {}
        self.term_document_matrix = {}
        self.document_vectors = {}
        self.recent_searches = []

        # Load documents
        self.load_documents('data')

        # UI Elements
        splitter = QSplitter(Qt.Vertical)

        # Search bar
        search_widget = QWidget()
        search_layout = QVBoxLayout()
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Enter query, e.g., 'example query'")
        self.search_button = QPushButton("Search")
        self.search_dropdown = QComboBox(self)
        self.search_dropdown.addItems(self.recent_searches)
        self.search_button.clicked.connect(self.perform_search)
        self.search_dropdown.currentIndexChanged.connect(self.populate_search_from_dropdown)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(QLabel("Recent Searches:"))
        search_layout.addWidget(self.search_dropdown)
        search_widget.setLayout(search_layout)
        splitter.addWidget(search_widget)

        # Results display
        self.results_browser = QTextBrowser()
        self.results_browser.setOpenLinks(False)
        self.results_browser.anchorClicked.connect(self.open_document_viewer)
        splitter.addWidget(self.results_browser)

        splitter.setStretchFactor(0, 1)  # Search bar takes less space
        splitter.setStretchFactor(1, 4)  # Results browser takes more space

        # Set central widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

        # Build term-document matrix
        self.build_term_document_matrix()
        self.calculate_document_vectors()

    def load_documents(self, base_dir):
        """Load documents from the data directory."""
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.documents[file_path] = content

    def tokenize(self, text):
        """Tokenize text into words."""
        return re.findall(r'\w+', text.lower())

    def build_term_document_matrix(self):
        """Build term-document matrix."""
        for doc_path, content in self.documents.items():
            tokens = self.tokenize(content)
            for token in tokens:
                if token not in self.term_document_matrix:
                    self.term_document_matrix[token] = {}
                if doc_path not in self.term_document_matrix[token]:
                    self.term_document_matrix[token][doc_path] = 0
                self.term_document_matrix[token][doc_path] += 1

    def calculate_document_vectors(self):
        """Calculate document vectors based on term frequency (TF) and inverse document frequency (IDF)."""
        num_documents = len(self.documents)
        for term, doc_freqs in self.term_document_matrix.items():
            idf = math.log(num_documents / len(doc_freqs))
            for doc, tf in doc_freqs.items():
                if doc not in self.document_vectors:
                    self.document_vectors[doc] = {}
                self.document_vectors[doc][term] = tf * idf

        # Normalize document vectors
        for doc, vector in self.document_vectors.items():
            norm = math.sqrt(sum(value ** 2 for value in vector.values()))
            for term in vector:
                vector[term] /= norm

    def perform_search(self):
        """Perform a search and display results."""
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

        self.results_browser.setHtml(results_html)

    def score_to_color(self, relative_score):
        """Convert a relative score to a color gradient from red to green."""
        red = int((1 - relative_score) * 255)
        green = int(relative_score * 255)
        return f"rgb({red},{green},0)"

    def open_document_viewer(self, url):
        """Open a new window to display the content of the clicked document."""
        file_path = url.toString().replace("%5C", '\\')
        if file_path in self.documents:
            viewer = DocumentViewer(file_path)
            viewer.exec_()

    def populate_search_from_dropdown(self):
        """Populate the search bar from the dropdown."""
        selected_query = self.search_dropdown.currentText()
        self.search_bar.setText(selected_query)

if __name__ == "__main__":
    app = QApplication([])
    window = SetTheoreticIRApp()
    window.show()
    app.exec_()
