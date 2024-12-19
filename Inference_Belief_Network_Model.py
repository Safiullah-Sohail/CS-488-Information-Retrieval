from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QSplitter, QLineEdit, QTextBrowser, QWidget, QPushButton, QLabel, QComboBox, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt

class DocumentViewer(QDialog):
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

class ProbabilisticIRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Probabilistic IR Models")
        self.resize(1200, 800)

        # Dataset: Documents, Queries, and Relevance Judgments
        self.documents = {
            "doc1": "The cat sat on the cozy mat in the sunny room, watching the birds outside.",
            "doc2": "Dogs are loyal and friendly animals, often seen playing in parks with children.",
            "doc3": "Cats prefer quiet places to sleep and enjoy warm sunlight on a lazy afternoon.",
            "doc4": "Birds chirp in the morning, creating a soothing melody that starts the day beautifully.",
            "doc5": "The quick brown fox jumps over the lazy dog in the dense green forest.",
            "doc6": "Many people enjoy hiking in the mountains during weekends, exploring nature's beauty.",
            "doc7": "Technology has significantly advanced, bringing groundbreaking innovations every single day.",
            "doc8": "Books are a great source of knowledge and entertainment, offering countless stories and insights.",
            "doc9": "Traveling to new places is a fantastic way to explore different cultures and cuisines.",
            "doc10": "Fitness enthusiasts often focus on strength training, cardio exercises, and healthy diets.",
            "doc11": "The history of ancient civilizations reveals fascinating details about human progress and culture.",
            "doc12": "Space exploration has opened up new possibilities for understanding the universe and its origins.",
            "doc13": "Gardening can be a relaxing hobby that brings you closer to nature and its wonders.",
            "doc14": "Cooking recipes are often passed down through generations, preserving cultural traditions and tastes.",
            "doc15": "The music industry has evolved with the rise of streaming platforms and digital media.",
            "doc16": "Wildlife conservation is essential for maintaining ecological balance and biodiversity.",
            "doc17": "Education is a powerful tool for personal and societal growth, shaping the future of individuals.",
            "doc18": "Health and wellness practices contribute to a better quality of life and overall happiness.",
            "doc19": "Art and creativity have always been integral to human expression and cultural identity.",
            "doc20": "Science fiction often explores futuristic themes, advanced technologies, and imaginative worlds."
        }

        self.queries = [
            "cat",
            "dog",
            "sunlight",
            "technology",
            "hiking",
            "fitness",
            "space exploration",
            "gardening",
            "history",
            "art"
        ]

        self.relevance = {
            ("cat", "doc1"): 1,
            ("cat", "doc3"): 1,
            ("dog", "doc2"): 1,
            ("sunlight", "doc3"): 1,
            ("technology", "doc7"): 1,
            ("hiking", "doc6"): 1,
            ("fitness", "doc10"): 1,
            ("space exploration", "doc12"): 1,
            ("gardening", "doc13"): 1,
            ("history", "doc11"): 1,
            ("art", "doc19"): 1
        }

        # Interference Model Probabilities
        self.query_prob = {}
        self.doc_prob = {}
        self.query_doc_prob = {}

        # UI Elements
        splitter = QSplitter(Qt.Vertical)

        # Search bar
        search_widget = QWidget()
        search_layout = QVBoxLayout()
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Enter query, e.g., 'cat'")
        self.search_button = QPushButton("Search")
        self.model_selector = QComboBox()
        self.model_selector.addItems(["Interference Model", "Belief Network"])
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(QLabel("Query:"))
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(QLabel("Select Model:"))
        search_layout.addWidget(self.model_selector)
        search_layout.addWidget(self.search_button)
        search_widget.setLayout(search_layout)
        splitter.addWidget(search_widget)

        # Results display
        self.results_browser = QTextBrowser()
        self.results_browser.setOpenLinks(False)
        self.results_browser.anchorClicked.connect(self.show_document)
        splitter.addWidget(self.results_browser)

        splitter.setStretchFactor(0, 1)  # Search bar takes less space
        splitter.setStretchFactor(1, 4)  # Results browser takes more space

        # Set central widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

        # Calculate Probabilities for Models
        self.calculate_probabilities()

    def tokenize(self, text):
        """Simple tokenizer."""
        return text.lower().split()

    def calculate_probabilities(self):
        """Calculate probabilities for the Interference Model."""
        total_docs = len(self.documents)
        for query in self.queries:
            query_count = sum(1 for (q, d), rel in self.relevance.items() if q == query and rel == 1)
            self.query_prob[query] = query_count / total_docs

        for doc_id, content in self.documents.items():
            doc_tokens = self.tokenize(content)
            self.doc_prob[doc_id] = len(doc_tokens) / sum(len(self.tokenize(d)) for d in self.documents.values())

        for (query, doc_id), rel in self.relevance.items():
            if rel == 1:
                self.query_doc_prob[(query, doc_id)] = self.query_prob[query] * self.doc_prob[doc_id]

    def interference_model_rank(self, query):
        """Rank documents based on the Interference Model."""
        scores = {}
        for doc_id in self.documents:
            scores[doc_id] = self.query_doc_prob.get((query, doc_id), 0)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def belief_network_rank(self, query):
        """Rank documents based on a simple belief network."""
        scores = {}
        for doc_id in self.documents:
            # Using a simplified Bayes' theorem: P(Relevance | Query) = P(Query | Doc) * P(Doc)
            p_query_given_doc = self.query_doc_prob.get((query, doc_id), 0) / self.doc_prob.get(doc_id, 1e-9)
            scores[doc_id] = p_query_given_doc * self.doc_prob.get(doc_id, 0)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def perform_search(self):
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

        self.results_browser.setHtml(results_html)

    def show_document(self, url):
        """Show the full content of the clicked document."""
        doc_id = url.toString().replace("%5C", '\\')
        if doc_id in self.documents:
            viewer = DocumentViewer(doc_id, self.documents[doc_id])
            viewer.exec_()

if __name__ == "__main__":
    app = QApplication([])
    window = ProbabilisticIRApp()
    window.show()
    app.exec_()
