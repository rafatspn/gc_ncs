import os
import re
import sys
import csv
import json
import time
import argparse
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import defaultdict, Counter
import torch.optim as optim
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier 
from sklearn.metrics import accuracy_score
from sklearn.ensemble import StackingClassifier
from xgboost import XGBClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.preprocessing import LabelEncoder

training_time = 0

# def set_seed(seed=42):
#     torch.manual_seed(seed)  # Sets seed for CPU and GPU (if no deterministic ops are used)
#     torch.cuda.manual_seed_all(seed)  # Sets seed for all GPUs
#     torch.backends.cudnn.deterministic = True  # Ensures deterministic behavior
#     torch.backends.cudnn.benchmark = False  # Disables optimization that can introduce randomness

# set_seed(42)

def read_csv(in_path, csv_files):
    dataframes = []
    for file in csv_files:
        df = pd.read_csv(os.path.join(in_path, file))
        dataframes.append(df)
    return pd.concat(dataframes, ignore_index=True)

def load_data(df, ir_path):
    def read_ir(file):
        try:
            with open(file, "r") as f:
                return f.read()
        except FileNotFoundError:
            print("Loading error")
            print(file)
            return None
    df['text'] = df['filename'].apply(
        lambda filename: read_ir(os.path.join(ir_path, f"{filename}.txt"))
    )
    return df.dropna(subset=['text'])

def preprocess_line(line):
    line = re.sub(r';.*$', '', line).strip()
    if not line:
        return None
    line = re.sub(r'([\(\)\[\]\{\}<>=\*:,])', r' \1 ', line)
    line = re.sub(r'\b\d+\.\d+(e[+-]?\d+)?\b', 'FLOAT_CONST', line)
    line = re.sub(r'0x[0-9a-fA-F]+', 'HEX_CONST', line)
    line = re.sub(r'\b\d+\b', 'INT_CONST', line)
    line = re.sub(r'<\d+x[^>]+>', 'VECTOR_PLACEHOLDER', line)
    line = re.sub(r'\[.*?\]', 'ARRAY_PLACEHOLDER', line)
    return line

def postprocess_tokens(tokens):
    processed_tokens = []
    for token in tokens:
        if token.startswith('!') or token.startswith('#'):
            continue
        if token.startswith('%'):
            token = '%ID'
        if token.startswith('@'):
            token = '@ID'
        if any(label in token for label in ['phi', 'pre', 'in', 'preheader', 'loopexit']):
            token = 'SPECIAL_LABEL'
        processed_tokens.append(token)
    return processed_tokens

def tokenize_code(texts):
    dictionary = defaultdict(lambda: len(dictionary) + 1)
    tokenized_sequences = []
    for text in texts:
        lines = text.splitlines()
        token_sequence = []
        for line in lines:
            line = preprocess_line(line)
            if not line:
                continue
            tokens = line.split()
            tokens = postprocess_tokens(tokens)
            token_sequence.extend(dictionary[token] for token in tokens)
        tokenized_sequences.append(token_sequence)
    dictionary['gc_cnn'] = 'gc_cnn'
    return tokenized_sequences, dictionary

class CNNModel(nn.Module):
    def __init__(self, vocab_size, num_classes, embedding_size=64, num_filters=64, kernel_size=32):
        super(CNNModel, self).__init__()
        print(vocab_size)
        self.embedding = nn.Embedding(vocab_size, embedding_size)
        self.conv1d = nn.Conv1d(embedding_size, num_filters, kernel_size)
        self.global_max_pool = nn.AdaptiveMaxPool1d(1)
        self.fc = nn.Linear(num_filters, num_classes)

    def forward(self, x):
        x = self.embedding(x)
        x = x.permute(0, 2, 1)
        x = F.relu(self.conv1d(x))
        x = self.global_max_pool(x).squeeze(-1)
        x = self.fc(x)
        return x 

class FeatureExtractor(nn.Module):
    def __init__(self, pre_trained_cnn, aux_input_size=2):
        super(FeatureExtractor, self).__init__()
        self.embedding = pre_trained_cnn.embedding
        self.conv1d = pre_trained_cnn.conv1d
        self.global_max_pool = nn.AdaptiveMaxPool1d(1)
        self.aux_input_size = aux_input_size

    def forward(self, x, aux_inputs):
        x = self.embedding(x)
        x = x.permute(0, 2, 1)
        x = F.relu(self.conv1d(x))
        x = self.global_max_pool(x).squeeze(-1)
        combined = torch.cat((x, aux_inputs), dim=1)
        return combined

def train_model(model, train_loader, num_epochs=30, device="cpu"):
    global training_time
    device="cpu"
    optimizer = optim.Adam(model.parameters())
    criterion = nn.CrossEntropyLoss()  
    model.to(device)
    training_start_time = time.perf_counter()
    for epoch in range(num_epochs):
        model.train()
        epoch_loss = 0.0
        for batch in train_loader:
            inputs, labels = batch
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels.argmax(dim=1)) 
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
        # print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss/len(train_loader):.4f}")
    training_time = training_time + (time.perf_counter() - training_start_time)

def train_and_evaluate_models(data, token_dict, out_path, out_file, device="cpu"):
    labels = ['class_50', 'class_60', 'class_70', 'class_80', 'class_90']  
    num_classes_dict = {label: data[label].nunique() for label in labels} 
    models = {}
    label_encoders = {}
    predictions = {}
    device="cpu"
    for label in labels:
        print(f"Training model for {label}")
        
        # Encode labels
        le = LabelEncoder()
        data[label] = le.fit_transform(data[label])
        label_encoders[label] = le
        
        # Split data
        train_data = data[(data['size'].isin(['S', 'M', 'L']))]
        test_data = data[(data['size'].isin(['SM', 'XL']))]
        # test_data = test_data[test_data[label].isin(train_data[label].unique())]
        
        max_length = 4096

        def pad_sequences(data):
            return pad_sequence(
                [torch.tensor(seq[:max_length], dtype=torch.long) if len(seq) > max_length 
                 else torch.cat((torch.tensor(seq, dtype=torch.long), torch.zeros(max_length - len(seq), dtype=torch.long)))
                 for seq in data],
                batch_first=True
            )
        X_train = pad_sequences(train_data['text'])
        X_test = pad_sequences(test_data['text'])
        y_train = torch.eye(num_classes_dict[label])[train_data[label].values]
        y_test = torch.eye(num_classes_dict[label])[test_data[label].values]
        
        # Create DataLoader
        train_dataset = TensorDataset(X_train, y_train)
        test_dataset = TensorDataset(X_test, y_test)

        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
        # print(len(y_test))

        #Initialization
        model = CNNModel(len(token_dict), num_classes_dict[label]).to(device)
        train_model(model, train_loader, device=device)
        models[label] = model
        
        #Evaluation
        model.eval()
        test_preds = []
        inference_times = []
        with torch.no_grad():
            for inputs, _ in test_loader:
                inputs = inputs.to(device)

                #inference time for batch
                start_time = time.perf_counter()
                outputs = model(inputs)
                end_time = time.perf_counter()

                #per-sample inference time
                batch_time = end_time - start_time
                per_sample_time = batch_time / inputs.shape[0]

                inference_times.extend([per_sample_time] * inputs.shape[0])

                test_preds.extend(outputs.argmax(dim=1).cpu().numpy())
                 
        predictions[label] = test_preds

        average_time = np.mean(inference_times)
        std_dev_time = np.std(inference_times)
        total_inference_time = sum(inference_times)

        print(f"Total Inference Time: {total_inference_time:.6f} sec")
        print(f"Average Inference Time per Sample: {average_time:.6f} sec")
        print(f"Standard Deviation of Inference Time: {std_dev_time:.6f} sec")
    
    #Calculate Score
    test_filenames = test_data['filename'].values
    test_speedup = test_data['speedup'].values

    scores = np.zeros(len(test_filenames))

    print(len(scores))

    for label in labels:
        for index, prediction in enumerate(predictions[label]):
            scores[index] = scores[index] + prediction
    
    results_dict = pd.DataFrame({
        "filename": test_filenames,
        "speedup": test_speedup,
        "score": scores
    })

    for label in labels:
        col_name = f"pred_{label}"
        results_dict[col_name] = predictions[label]

    results = pd.DataFrame(results_dict)

    results.to_csv(os.path.join(out_path, out_file), index=False)

def main():
    global training_time
    parser = argparse.ArgumentParser(description="Training with CNN")
    parser.add_argument("--csv_path", type=str, required=True)
    parser.add_argument("--csv_files", type=str, required=True)
    parser.add_argument("--ir_path", type=str, required=True)
    parser.add_argument("--out_path", type=str, required=True)
    parser.add_argument("--out_file", type=str, required=True)
    args = parser.parse_args()

    csv_files = args.csv_files.split(",")
    print(args.csv_files)
    data = read_csv(args.csv_path, csv_files)
    data = load_data(data, args.ir_path)
    data['text'], token_dict = tokenize_code(data['text'])

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    train_and_evaluate_models(data, token_dict, args.out_path, args.out_file, device=device)
    print(f"Total training Time: {training_time:.6f} sec")
    

if __name__ == "__main__":
    main()