import pickle

# Replace 'path_to_your_file.pkl' with the actual path to your pickle file
file_path = 'content_index.pkl'

with open(file_path, 'rb') as file:
    data = pickle.load(file)
    dat = dict()
    print(data)
