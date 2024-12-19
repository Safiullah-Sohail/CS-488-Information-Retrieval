import os
import re
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QDialog, QLineEdit, QTextBrowser, QPushButton, QWidget
from PyQt5.QtCore import QUrl
import math

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

# Preprocessing to extract nouns
def preprocess_text(text):
    words = re.findall(r'\w+', text)
    nouns = [
        word.lower() for word in words
        if word.lower() not in NON_NOUNS and (word[0].isupper() or word.lower().endswith(NOUN_SUFFIXES))
    ]
    return ' '.join(nouns)

# Load documents from a directory
def load_documents(directory):
    documents = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    documents[file_path] = preprocess_text(f.read())
    return documents

# TF-IDF and cosine similarity ranking
def compute_tf(doc_terms):
    term_counts = {}
    total_terms = len(doc_terms)
    for term in doc_terms:
        term_counts[term] = term_counts.get(term, 0) + 1
    return {term: count / total_terms for term, count in term_counts.items()}
def compute_idf(documents):
    num_docs = len(documents)
    term_document_counts = {}
    for doc_terms in documents:
        for term in set(doc_terms):
            term_document_counts[term] = term_document_counts.get(term, 0) + 1
    return {term: math.log(num_docs / (1 + count)) for term, count in term_document_counts.items()}
def compute_tf_idf_matrix(documents, idf):
    return [
        {term: tf.get(term, 0) * idf.get(term, 0) for term in idf}
        for tf in (compute_tf(doc) for doc in documents)
    ]
def cosine_similarity(vec1, vec2):
    dot_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in vec1)
    magnitude1 = sum(weight ** 2 for weight in vec1.values()) ** 0.5
    magnitude2 = sum(weight ** 2 for weight in vec2.values()) ** 0.5
    return dot_product / (magnitude1 * magnitude2) if magnitude1 and magnitude2 else 0.0

# Search function
def search(query, documents):
    query_terms = query.lower().split()
    doc_tokens = [doc.split() for doc in documents.values()]
    idf = compute_idf(doc_tokens)
    tf_idf_matrix = compute_tf_idf_matrix(doc_tokens, idf)
    query_tf_idf = {term: compute_tf(query_terms).get(term, 0) * idf.get(term, 0) for term in idf}
    return sorted(
        [(doc, cosine_similarity(query_tf_idf, tf_idf)) for doc, tf_idf in zip(documents.keys(), tf_idf_matrix)],
        key=lambda x: x[1],
        reverse=True
    )

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

# GUI Application
class DocumentRankingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Ranking System")
        self.resize(500, 300)
        # Layout
        layout = QVBoxLayout()

        # Query input
        self.query_input = QLineEdit(self)
        self.query_input.setPlaceholderText("Enter your query here")
        layout.addWidget(self.query_input)

        # Search button
        self.search_button = QPushButton("Search", self)
        self.search_button.clicked.connect(self.perform_search)
        layout.addWidget(self.search_button)

        # Results display
        self.result_display = QTextBrowser(self)
        self.result_display.setOpenLinks(False)  # Prevent default behavior
        self.result_display.anchorClicked.connect(self.handle_anchor_clicked)
        layout.addWidget(self.result_display)

        # Central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Load documents
        self.documents = load_documents('data')

    def handle_anchor_clicked(self, url):
        """Intercept anchor clicks and open the document viewer."""
        self.show_document(url)

    def show_document(self, url):
        """Opens the clicked document in a new window."""
        file_path = url.toLocalFile()
        if os.path.exists(file_path):
            viewer = DocumentViewer(file_path)
            viewer.exec_()  # Open the viewer as a modal dialog
        else:
            # Show an error message in a popup instead of modifying the main results
            error_dialog = QDialog(self)
            error_dialog.setWindowTitle("Error")
            error_layout = QVBoxLayout()
            error_label = QTextBrowser()
            error_label.setText(f"File not found: {file_path}")
            error_layout.addWidget(error_label)
            error_dialog.setLayout(error_layout)
            error_dialog.exec_()

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
        results = search(query, self.documents)
        elapsed_time = time.time() - start_time

        # Handle results
        if results:
            top_results = results[:10]  # Limit to top 10 results
            summary = f"<b>Showing {len(top_results)}/{len(results)} documents, retrieved in {elapsed_time:.2f} seconds.</b><br><br>"

            # Calculate relative color gradient
            scores = [score for _, score in top_results]
            max_score = max(scores) if scores else 0
            min_score = min(scores) if scores else 0

            results_text = summary
            for i, (doc, score) in enumerate(top_results, 1):
                color = self.score_to_color(score, min_score, max_score)
                url = QUrl.fromLocalFile(doc).toString()
                results_text += f"<b><a href='{url}'>{doc}</a></b> " \
                                f"<span style='color:{color}'>({score:.4f})</span><br>"
                with open(doc, 'r', encoding='utf-8') as f:
                    snippet = f.read(200).strip().replace('\n', ' ')
                    results_text += f"Snippet: {snippet}...<br><br>"
            self.result_display.setHtml(results_text)
        else:
            self.result_display.setText("No relevant documents found.")

        # Re-enable the search button
        self.search_button.setEnabled(True)
        self.search_button.setText("Search")

    @staticmethod
    def score_to_color(score, min_score, max_score):
        # Map score to a relative color gradient (green -> yellow -> red)
        if max_score == min_score:  # Handle case where all scores are identical
            return "rgb(255,255,0)"
        relative_score = (score - min_score) / (max_score - min_score)
        red = int(255 * (1 - relative_score))
        green = int(200 * relative_score)
        return f"rgb({red},{green},0)"

# Run Application
app = QApplication([])
window = DocumentRankingApp()
window.show()
app.exec_()
