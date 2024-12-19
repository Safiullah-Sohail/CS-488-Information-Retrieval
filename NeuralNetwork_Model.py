import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QSplitter, QLineEdit, QTextBrowser, QWidget, QPushButton, QLabel, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt

class ArticleViewer(QDialog):
    def __init__(self, title, content):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(800, 600)

        layout = QVBoxLayout()
        content_display = QTextEdit(self)
        content_display.setReadOnly(True)
        content_display.setText(content)
        layout.addWidget(content_display)
        self.setLayout(layout)

class NeuralNetworkIRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neural Network for IR")
        self.resize(1200, 800)

        # Dataset: Articles
        self.articles = {
            "Article 1": "Exercise improves physical fitness and promotes well-being.",
            "Article 2": "Benefits of regular workouts include better health and increased energy levels.",
            "Article 3": "Staying active through exercise contributes to overall wellness and prevents diseases.",
            "Article 4": "Workouts and physical activities can reduce stress and improve mental health.",
            "Article 5": "Health and fitness go hand in hand with regular physical activity."
        }

        # Vocabulary for basic semantic understanding
        self.vocabulary = {
            "benefits": ["advantages", "gains", "improvements"],
            "exercise": ["workouts", "physical activity", "training"],
            "health": ["wellness", "well-being", "fitness"]
        }

        # UI Elements
        splitter = QSplitter(Qt.Vertical)

        # Search bar
        search_widget = QWidget()
        search_layout = QVBoxLayout()
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Enter your query, e.g., 'benefits of exercise for health'")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(QLabel("Query:"))
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.search_button)
        search_widget.setLayout(search_layout)
        splitter.addWidget(search_widget)

        # Results display
        self.results_browser = QTextBrowser()
        self.results_browser.setOpenLinks(False)
        self.results_browser.anchorClicked.connect(self.show_article)
        splitter.addWidget(self.results_browser)

        splitter.setStretchFactor(0, 1)  # Search bar takes less space
        splitter.setStretchFactor(1, 4)  # Results browser takes more space

        # Set central widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

    def tokenize(self, text):
        """Simple tokenizer."""
        return text.lower().split()

    def semantic_expand(self, query_terms):
        """Expand the query with related terms using predefined vocabulary."""
        expanded_query = set(query_terms)
        for term in query_terms:
            if term in self.vocabulary:
                expanded_query.update(self.vocabulary[term])
        return expanded_query

    def calculate_similarity(self, query_terms, document_terms):
        """Calculate similarity between query and document based on term overlap."""
        common_terms = set(query_terms) & set(document_terms)
        return len(common_terms) / (math.sqrt(len(query_terms)) * math.sqrt(len(document_terms)))

    def perform_search(self):
        """Perform a search and display results."""
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

        self.results_browser.setHtml(results_html)

    def show_article(self, url):
        """Show the full content of the clicked article."""
        title = url.toString()
        if title in self.articles:
            viewer = ArticleViewer(title, self.articles[title])
            viewer.exec_()

if __name__ == "__main__":
    app = QApplication([])
    window = NeuralNetworkIRApp()
    window.show()
    app.exec_()
