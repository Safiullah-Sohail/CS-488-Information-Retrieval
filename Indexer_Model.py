import os
import re
import csv
import time
import threading
import PyPDF2
import pickle
from queue import Queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

# Define paths and constants
CONTENT_INDEX_FILE = "content_index2.pkl"
FILENAME_INDEX_FILE = "filename_index2.pkl"
TESTDATA_DIR = "data"
REFRESH_INTERVAL = 5  # Check interval in seconds for changes

# Load and Save Index Functions
def load_index(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    return {}
def save_index(index, file_path):
    with open(file_path, 'wb') as f:
        pickle.dump(index, f)

def index_file_content(filename, content_index, snippet_radius=5):
    ext = filename.split('.')[-1].lower()

    # Expanded list of common non-nouns (verbs, pronouns, prepositions, adjectives, etc.)
    non_nouns = {
        'the', 'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'and', 'or', 'but', 'if', 'while', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
        'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
        'both', 'each', 'few', 'more', 'some', 'such', 'no', 'nor', 'too', 'very', 'can', 'will', 'just', 'should',
        'would', 'could', 'might', 'must', 'not', 'he', 'she', 'it'
    }

    # Common noun suffixes (helps identify nouns by their endings)
    noun_suffixes = ('tion', 'ment', 'ness', 'ity', 'ance', 'ence', 'ship', 'age', 'hood', 'ism', 'ist', 'cy', 'dom')

    try:
        if ext == 'txt':
            with open(filename, 'r', encoding='utf-8') as file:
                for line in file:
                    words = re.findall(r'\w+', line)
                    for i, word in enumerate(words):
                        word_lower = word.lower()
                        first_letter = word_lower[0]

                        # Filtering logic to determine if the word is likely a noun
                        is_likely_noun = (
                            word_lower not in non_nouns and  # Exclude non-nouns
                            (word[0].isupper() or  # Likely proper noun if capitalized
                             word_lower.endswith(noun_suffixes))  # Common noun suffix
                        )

                        if not is_likely_noun:
                            continue  # Skip non-noun words

                        # Ensure the index structure exists for this letter and word
                        if first_letter not in content_index:
                            content_index[first_letter] = {}
                        if word_lower not in content_index[first_letter]:
                            content_index[first_letter][word_lower] = {}
                        if filename not in content_index[first_letter][word_lower]:
                            content_index[first_letter][word_lower][filename] = set()

                        # Capture context around the word
                        start = max(0, i - snippet_radius)
                        end = min(len(words), i + snippet_radius + 1)
                        snippet = " ".join(words[start:end])
                        content_index[first_letter][word_lower][filename].add(snippet)

        elif ext == 'csv':
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    words = [word for cell in row for word in re.findall(r'\w+', cell)]
                    for i, word in enumerate(words):
                        word_lower = word.lower()
                        first_letter = word_lower[0]

                        # Apply the same noun filtering as above
                        is_likely_noun = (
                            word_lower not in non_nouns and
                            (word[0].isupper() or
                             word_lower.endswith(noun_suffixes))
                        )

                        if not is_likely_noun:
                            continue

                        # Ensure the index structure exists for this letter and word
                        if first_letter not in content_index:
                            content_index[first_letter] = {}
                        if word_lower not in content_index[first_letter]:
                            content_index[first_letter][word_lower] = {}
                        if filename not in content_index[first_letter][word_lower]:
                            content_index[first_letter][word_lower][filename] = set()

                        # Capture context around the word
                        start = max(0, i - snippet_radius)
                        end = min(len(words), i + snippet_radius + 1)
                        snippet = " ".join(words[start:end])
                        content_index[first_letter][word_lower][filename].add(snippet)

        elif ext == 'pdf':
            with open(filename, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        words = re.findall(r'\w+', text)
                        for i, word in enumerate(words):
                            word_lower = word.lower()
                            first_letter = word_lower[0]

                            # Apply the same noun filtering as above
                            is_likely_noun = (
                                word_lower not in non_nouns and
                                (word[0].isupper() or
                                 word_lower.endswith(noun_suffixes))
                            )

                            if not is_likely_noun:
                                continue

                            # Ensure the index structure exists for this letter and word
                            if first_letter not in content_index:
                                content_index[first_letter] = {}
                            if word_lower not in content_index[first_letter]:
                                content_index[first_letter][word_lower] = {}
                            if filename not in content_index[first_letter][word_lower]:
                                content_index[first_letter][word_lower][filename] = set()

                            # Capture context around the word
                            start = max(0, i - snippet_radius)
                            end = min(len(words), i + snippet_radius + 1)
                            snippet = " ".join(words[start:end])
                            content_index[first_letter][word_lower][filename].add(snippet)

    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
    except Exception as e:
        print(f"An error occurred while indexing the file '{filename}': {str(e)}")

# Index filenames in testData directory
def index_filenames(test_data_dir, filename_index):
    for root, _, files in os.walk(test_data_dir):
        for filename in files:
            file_path = os.path.join(root, filename)
            filename_lower = filename.lower()
            last_modified = os.path.getmtime(file_path)

            # Initialize an empty set for the filename if it doesn't exist
            if filename_lower not in filename_index:
                filename_index[filename_lower] = set()

            # Add the (file_path, last_modified) tuple to the set to avoid duplicates
            filename_index[filename_lower].add((file_path, last_modified))

# Check if files have been modified since the last indexing
def needs_reindexing(filename_index):
    modified_files = []
    for root, _, files in os.walk(TESTDATA_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            last_modified = os.path.getmtime(file_path)
            filename_lower = filename.lower()

            # Check if the file is in the filename_index with the same timestamp
            if filename_lower in filename_index:
                indexed_paths = [entry[0] for entry in filename_index[filename_lower]]
                if file_path in indexed_paths:
                    indexed_last_modified = [entry[1] for entry in filename_index[filename_lower] if entry[0] == file_path][0]
                    if last_modified != indexed_last_modified:
                        modified_files.append(file_path)
                        print(file_path + "time update")
                else:
                    modified_files.append(file_path)
                    print(file_path + "not in index")
            else:
                modified_files.append(file_path)
                print(file_path + "new file")

    # Also check if any files in the index no longer exist in the directory
    for filename_lower, entries in filename_index.items():
        for file_path, _ in entries:
            if not os.path.exists(file_path):
                modified_files.append(file_path)
    return modified_files

# Initial indexing function
def perform_initial_indexing(content_index, filename_index, num_threads=4):
    print("Performing initial indexing...")

    # Queue setup for multithreaded subdirectory processing
    queue = Queue()
    for root, dirs, _ in os.walk(TESTDATA_DIR):
        for subdir in dirs:
            queue.put(os.path.join(root, subdir))

    # Calculate total files for progress tracking
    total_files = sum(len(files) for _, _, files in os.walk(TESTDATA_DIR))
    processed_files = [0]

    # Start threads for indexing
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=index_subdir, args=(queue, content_index, filename_index, total_files, processed_files))
        thread.start()
        threads.append(thread)

    # Main thread handles files in the root directory of TESTDATA_DIR
    index_filenames(TESTDATA_DIR, filename_index)
    for root, _, files in os.walk(TESTDATA_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            index_file_content(file_path, content_index)
            processed_files[0] += 1
            show_progress(processed_files[0], total_files)

    # Wait for threads to complete
    for thread in threads:
        thread.join()

    # Save updated indexes
    save_index(content_index, CONTENT_INDEX_FILE)
    save_index(filename_index, FILENAME_INDEX_FILE)
    print("\nInitial indexing complete.")

# Threaded indexing function for subdirectory indexing
def index_subdir(queue, content_index, filename_index, total_files, processed_files):
    while not queue.empty():
        subdir = queue.get()
        for root, _, files in os.walk(subdir):
            for filename in files:
                file_path = os.path.join(root, filename)
                index_file_content(file_path, content_index)
                processed_files[0] += 1
                show_progress(processed_files[0], total_files)
        queue.task_done()

# Show progress percentage for indexing
def show_progress(processed_files, total_files):
    percent = (processed_files / total_files) * 100
    print(f"\rIndexing Progress: [{int(percent)}%]", end="")

# Monitor for file changes using watchdog
class IndexUpdateHandler(FileSystemEventHandler):
    def __init__(self, content_index, filename_index):
        super().__init__()
        self.content_index = content_index
        self.filename_index = filename_index

    def on_modified(self, event):
        if event.is_directory:
            return
        print()
        print(f"File modified: {event.src_path}")
        update_modified_files(self.content_index, self.filename_index)

    def on_created(self, event):
        if event.is_directory:
            return
        print()
        print(f"File created: {event.src_path}")
        update_modified_files(self.content_index, self.filename_index)

    def on_deleted(self, event):
        if event.is_directory:
            return
        print()
        print(f"File deleted: {event.src_path}")
        update_modified_files(self.content_index, self.filename_index)

# Start monitoring
def start_file_monitoring(content_index, filename_index):
    event_handler = IndexUpdateHandler(content_index, filename_index)
    observer = Observer()
    observer.schedule(event_handler, TESTDATA_DIR, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Load subset of content index based on the first letter of query
def load_content_subindex(letter):
    try:
        with open(CONTENT_INDEX_FILE, 'rb') as f:
            full_content_index = pickle.load(f)
            return full_content_index.get(letter, {})
    except FileNotFoundError:
        return {}

# Optimized Search Functions
def search_content(query, current_letter, content_index, exact_match=True):
    print("\n--- Search Results ---")
    query_letter = query[0].lower()

    # Load sub-index only if the first letter of the query changes
    if query_letter != current_letter[0]:
        content_index.clear()
        content_index.update(load_content_subindex(query_letter))
        current_letter[0] = query_letter

    # Perform search on the loaded sub-index
    query_lower = query.lower()
    if exact_match:
        # Retrieve context snippets for exact match
        results = content_index.get(query_lower, {})
        if results:
            print(f"Exact match found for '{query}':")
            for filename, snippets in results.items():
                print(f"\nIn file '{filename}':")
                for snippet in snippets:
                    print(f"  ... {snippet} ...")
        else:
            print(f"No exact matches found for '{query}'")
    else:
        # Pattern match: find all words that match the regex pattern
        pattern = re.compile(query, re.IGNORECASE)
        found = False
        for word, file_data in content_index.items():
            if pattern.search(word):
                found = True
                print(f"\nPattern '{query}' found in word '{word}':")
                for filename, snippets in file_data.items():
                    print(f"\nIn file '{filename}':")
                    for snippet in snippets:
                        print(f"  ... {snippet} ...")

        if not found:
            print(f"No pattern matches found for '{query}'")
def search_filename(query, filename_index, exact_match=True):
    print("\n--- Filename Search Results ---")
    if exact_match:
        results = filename_index.get(query.lower(), [])
        print(results)
        if results:
            for file_path, _ in results:
                print(f"Found file: {file_path}")
        else:
            print(f"No exact matches found for '{query}'")
    else:
        pattern = re.compile(query, re.IGNORECASE)
        found = False
        for filename, entries in filename_index.items():
            if pattern.search(filename):
                found = True
                for file_path, _ in entries:
                    print(f"Found file: {file_path}")
        if not found:
            print(f"No pattern matches found for '{query}'")

# Main Search UI
def main_ui(content_index, filename_index):
    current_letter = ['']  # Track the currently loaded sub-index letter
    cached_content_index = {}  # Cache for the currently loaded sub-index

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=== Search Engine ===")
        print("Choose Search Option:")
        print("1. Search within File Content")
        print("2. Search for File Names")
        print("3. Exit")

        search_choice = input("Enter your choice: ")
        if search_choice == '3':
            # save_index(content_index, CONTENT_INDEX_FILE)
            # save_index(filename_index, FILENAME_INDEX_FILE)
            print("Exiting Search Engine.")
            break
        elif search_choice in ['1', '2']:
            exact_or_pattern = input("Search exact term? (Y for Yes): ")
            query = input("Enter your search query: ")
            exact_match = exact_or_pattern == 'Y'

            if search_choice == '1':
                search_content(query, current_letter, cached_content_index, exact_match)
            elif search_choice == '2':
                search_filename(query, filename_index, exact_match)

            input("\nPress Enter to continue...")
        else:
            print("Invalid choice. Try again.")

def update_modified_files(content_index, filename_index):
    modified_files = needs_reindexing(filename_index)

    # Update each modified file in the index
    for file_path in modified_files:
        filename_lower = os.path.basename(file_path).lower()

        # Remove old entries from both indexes
        content_index = {k: [entry for entry in v if entry[0] != file_path] for k, v in content_index.items()}
        if filename_lower in filename_index:
            filename_index[filename_lower] = [entry for entry in filename_index[filename_lower] if entry[0] != file_path]

        # If the file exists, re-index it
        if os.path.exists(file_path):
            index_file_content(file_path, content_index)
            last_modified = os.path.getmtime(file_path)
            if filename_lower not in filename_index:
                filename_index[filename_lower] = []
            filename_index[filename_lower].append((file_path, last_modified))
        else:
            print(f"File removed from index: {file_path}")

    # Save the updated indexes
    save_index(content_index, CONTENT_INDEX_FILE)
    save_index(filename_index, FILENAME_INDEX_FILE)
    print("Updated indexes for modified files.")

# Main Program Entry Point
if __name__ == "__main__":
    content_index = load_index(CONTENT_INDEX_FILE)
    filename_index = load_index(FILENAME_INDEX_FILE)

    # Perform initial indexing if changes are detected
    if not content_index or not filename_index:
        perform_initial_indexing(content_index, filename_index)
    elif  needs_reindexing(filename_index):
        update_modified_files(content_index, filename_index)

    # Start background file monitoring thread
    threading.Thread(target=start_file_monitoring, args=(content_index, filename_index), daemon=True).start()

    # Start main UI
    main_ui(content_index, filename_index)