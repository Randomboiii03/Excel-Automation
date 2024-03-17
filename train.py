import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from joblib import dump

# Load the CSV data into a DataFrame
df = pd.read_csv('./source/source.csv')

# Drop rows with NaN values
df.dropna(subset=['address', 'area-muni'], inplace=True)

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['address'])
y = df['area-muni']

# Split the dataset into training and testing set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Training
model = LogisticRegression(max_iter=200)
model.fit(X_train, y_train)

# Evaluation
y_pred = model.predict(X_test)
print("Detailed Classification Report:")
print(classification_report(y_test, y_pred))

# Accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Overall Prediction Accuracy: {accuracy:.2f}")

# Prediction and Output
# Predict and output for the test set for demonstration
for i, idx in enumerate(X_test.toarray().argsort(axis=1)):
    address_features = vectorizer.inverse_transform(X_test[i])
    print(f"Address: {' '.join(address_features[0])}")
    print(f"True Area-Muni: {y_test.iloc[i]}, Predicted Area-Muni: {y_pred[i]}\n")

# Save the model and vectorizer
dump(model, '../model.joblib')
dump(vectorizer, '../vectorizer.joblib')

# import pandas as pd
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.linear_model import LogisticRegression
# from sklearn.metrics import accuracy_score, classification_report
# from joblib import dump

# # Load the CSV data into a DataFrame
# df = pd.read_csv('output_file.csv')

# # Drop rows with NaN values
# df.dropna(subset=['address', 'area-muni'], inplace=True)

# vectorizer = TfidfVectorizer()
# X = vectorizer.fit_transform(df['address'])
# y = df['area-muni']

# # Train the model
# model = LogisticRegression(max_iter=200)
# model.fit(X, y)

# # Make predictions on the 'area-muni' column itself
# predictions = model.predict(X)
# df['predictions'] = predictions

# # Evaluation
# accuracy = accuracy_score(y, predictions)
# print(f"Overall Prediction Accuracy: {accuracy:.2f}")

# # Save the model and vectorizer
# dump(model, 'model.joblib')
# dump(vectorizer, 'vectorizer.joblib')

# # Save the updated DataFrame with predictions
# df.to_csv('output_file_with_predictions.csv', index=False)
