# Python has been installed as /opt/homebrew/bin/python3
# source sklearn-env/bin/activate  # activate
# Module 7 Part 2
from sklearn.model_selection import train_test_split
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, ConfusionMatrixDisplay, confusion_matrix, roc_curve, auc
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
import pickle 
from sklearn import svm
import matplotlib.pyplot as plt

# Function to print the unique label values
def print_unique_values(df):
  print("--Showing Unique Values--")
  # Get unique values in the 'Label' column
  unique_values = df['Label'].unique()

  # Print the unique values
  for value in unique_values:
      print(value)

# List of file paths from the open tab metadata
file_paths = ["fast_gestures.csv", "slow_gestures.csv", "static_gestures.csv"]

# Read CSV data from each file
dfs = []
column_names = ["Value", "Label"]
for file_path in file_paths:
    try:
        df = pd.read_csv(file_path, header=None, names=column_names, skiprows=1)
        dfs.append(df)
        print(f"Read data from {file_path}")
    except Exception as e:
        print(f"Error reading data from {file_path}: {str(e)}")

# Concatenate all dataframes into a single dataframe
combined_df = pd.concat(dfs, axis=0, ignore_index=True)

# Convert all values in the "Label" column to lowercase
combined_df['Label'] = combined_df['Label'].str.lower()

# Remove all spaces from the "Label" column
combined_df['Label'] = combined_df['Label'].str.replace(" ", "")

# Print all label values
print_unique_values(combined_df)

# # Replace "water" with "bottle"
# combined_df['Label'] = combined_df['Label'].replace('waterbottle', 'bottle', regex=True)
# # Replace "waterbottle" with "bottle"
# combined_df['Label'] = combined_df['Label'].replace('water', 'bottle', regex=True)

# # Replace "whitepaper" with "paper"
# combined_df['Label'] = combined_df['Label'].replace('whitepaper', 'paper', regex=True)

# # Replace "foil3" with "foil"
# combined_df['Label'] = combined_df['Label'].replace('foil3', 'foil', regex=True)

# # Replace "V" with blank
# combined_df['Value'] = combined_df['Value'].replace(' V', '', regex=True)

# print_unique_values(combined_df)

# Print the first few rows of the combined dataframe
print(combined_df.head())

# Assuming you have a DataFrame called 'df' with columns 'Value' and 'Label'
X = combined_df[['Value']]  # Features (independent variables)
y = combined_df['Label']    # Target variable (dependent variable)

# Split the data into 80% training and 20% testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train a logistic regression model
# model = LogisticRegression(max_iter=1000)
# model = svm.SVC()
model = RandomForestClassifier(random_state=42)
# model = DecisionTreeClassifier(max_depth=3)
model.fit(X_train, y_train)

# save the model 
filename = 'randfor.sav'
pickle.dump(model, open(filename, 'wb')) 
  
# load the model 
load_model = pickle.load(open(filename, 'rb')) 

# Make predictions on the test set
y_pred = model.predict(X_test)

# Calculate precision, recall, F1-score, and accuracy
precision = precision_score(y_test, y_pred, average='weighted')
recall = recall_score(y_test, y_pred, average='weighted')
f1 = f1_score(y_test, y_pred, average='weighted')
accuracy = accuracy_score(y_test, y_pred)

# Create a table to display the metrics
print("Metrics:")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1-score: {f1:.4f}")
print(f"Accuracy: {accuracy:.4f}")

# Compute Confusion Matrix
cm = confusion_matrix(y_test, y_pred)

# Plot the confusion matrix
disp = ConfusionMatrixDisplay(confusion_matrix = cm, display_labels = ['fast_swat', 'slow_swat', 'static'])
disp.plot(cmap=plt.cm.Blues)
plt.title('Confusion Matrix - Random Forest Classifier')
plt.show()

