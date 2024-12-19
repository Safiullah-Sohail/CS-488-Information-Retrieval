import os
import re
import pickle
import networkx as nx
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem, QTextBrowser, QWidget, QGraphicsView, QGraphicsScene, QTreeWidgetItemIterator
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

# Load content index
def load_content_index(index_file):
    """
    Load the serialized content index from the file.
    """
    if os.path.exists(index_file):
        with open(index_file, 'rb') as f:
            return pickle.load(f)
    return {}

class DocumentIRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Structure guided and Hypertext model")
        self.resize(1200, 800)

        # Splitter for layout
        splitter = QSplitter(Qt.Horizontal)

        # File browser pane
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("Documents")
        self.file_tree.itemClicked.connect(self.file_selected)
        splitter.addWidget(self.file_tree)

        # Content display pane
        self.result_display = QTextBrowser(self)
        self.result_display.setOpenLinks(True)
        self.result_display.anchorClicked.connect(self.show_linked_document)
        splitter.addWidget(self.result_display)

        # Graph visualization pane
        self.graph_view = QGraphicsView()
        self.graph_scene = QGraphicsScene()
        self.graph_view.setScene(self.graph_scene)
        splitter.addWidget(self.graph_view)
        splitter.setStretchFactor(2, 3)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(0, 1)

        # Set central widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

        # Load documents into tree
        self.load_file_tree('data')

        # Load content index for linking
        self.content_index = load_content_index('content_index.pkl')

    def load_file_tree(self, base_dir):
        """
        Load files and folders into the tree view.
        """
        base_item = QTreeWidgetItem(self.file_tree, [os.path.basename(base_dir)])
        base_item.setData(0, Qt.UserRole, base_dir)

        for root, dirs, files in os.walk(base_dir):
            current_item = base_item
            if root != base_dir:
                relative_path = os.path.relpath(root, base_dir)
                path_parts = relative_path.split(os.sep)
                for part in path_parts:
                    found_item = None
                    for i in range(current_item.childCount()):
                        if current_item.child(i).text(0) == part:
                            found_item = current_item.child(i)
                            break
                    if not found_item:
                        found_item = QTreeWidgetItem(current_item, [part])
                        found_item.setData(0, Qt.UserRole, os.path.join(base_dir, relative_path))
                    current_item = found_item

            for file in files:
                if file.endswith('.txt'):
                    file_item = QTreeWidgetItem(current_item, [file])
                    file_item.setData(0, Qt.UserRole, os.path.join(root, file))

    def file_selected(self, item, column):
        """
        Handle file selection from the tree view.
        """
        print(item)
        file_path = item.data(0, Qt.UserRole)
        if os.path.isfile(file_path):
            self.display_file_content(file_path)

    def display_file_content(self, file_path):
        """
        Display the content of the selected file with links to other files.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            document_name = os.path.basename(file_path)
            linked_content = f"<b>{document_name}</b><br><br>"  # Display document name in bold
            # Add links for terms based on content index
            graph_data = []
            for line in content.splitlines():
                for word in re.findall(r'\w+', line):
                    word_lower = word.lower()
                    if word_lower in self.content_index:
                        # Use a set to ensure unique documents
                        linked_docs = {doc[0] for doc in self.content_index[word_lower] if doc[0] != file_path}
                        if len(linked_docs) == 1:  # Link if the word appears in exactly one other document
                            linked_file_path = next(iter(linked_docs))  # Get the other document's path
                            linked_content += f"<a href='{linked_file_path}'>{word}</a> "
                            graph_data.append((word_lower, linked_docs))
                        else:
                            linked_content += word + " "
                    else:
                        linked_content += word + " "
                linked_content += "<br>"

            self.result_display.setHtml(linked_content)

            # Plot the graph if there are terms to visualize
            if graph_data:
                self.plot_graph(graph_data)

        except Exception as e:
            self.result_display.setText(f"Error displaying file: {str(e)}")

    def show_linked_document(self, url):
        """
        Handle clicks on links to show the linked document.
        """
        linked_file_path = url.toString().replace("%5C", '\\')
        # print(linked_file_path)
        # print(linked_file_path)
        if os.path.isfile(linked_file_path):
            iterator = QTreeWidgetItemIterator(self.file_tree)
            while iterator.value():
                item = iterator.value()
                print(item.data(0, Qt.UserRole))
                if item.data(0, Qt.UserRole) == linked_file_path:
                    print('imitating click')
                    self.file_tree.itemClicked.emit(item, 0)  # Imitate the itemClicked event
                    return
                iterator += 1

    def plot_graph(self, graph_data):
        """
        Plot the graph showing connections between files that share the term.
        """
        # Clear the existing graph
        self.graph_scene.clear()

        # Create a graph object
        G = nx.Graph()

        for term, linked_files in graph_data:
            for file_path in linked_files:
                file_name = os.path.basename(file_path)
                G.add_node(file_name)
                G.add_node(term, color='red')  # Add the term as a separate node
                G.add_edge(term, file_name)

        # Draw the graph using matplotlib
        fig, ax = plt.subplots(figsize=(8, 6))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, ax=ax, node_color=["red" if G.nodes[n].get("color") == "red" else "lightblue" for n in G.nodes], node_size=2000, font_size=10, font_weight="bold")

        # Render the graph in the QGraphicsView
        canvas = FigureCanvas(fig)
        canvas.setGeometry(0, 0, 800, 600)
        self.graph_scene.addWidget(canvas)

if __name__ == "__main__":
    app = QApplication([])
    window = DocumentIRApp()
    window.show()
    app.exec_()
