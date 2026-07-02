"""Train a resume category classifier using TF-IDF + Logistic Regression.

Trained directly on your labeled Resume.csv (Resume_str -> Category).
This gives you a real baseline fast; swap in a stronger model later if needed.
"""
import joblib
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline

MODEL_PATH = Path(__file__).parent.parent / "models" / "category_classifier.joblib"


def train_classifier(csv_path: str, test_size: float = 0.2, random_state: int = 42):
    df = pd.read_csv(csv_path)
    X_train, X_test, y_train, y_test = train_test_split(
        df["Resume_str"], df["Category"],
        test_size=test_size, random_state=random_state, stratify=df["Category"]
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=5000, stop_words="english", ngram_range=(1, 2)
        )),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    report = classification_report(y_test, y_pred, zero_division=0)
    print(report)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

    return pipeline, report


def predict_category(text: str, model_path: str = None) -> str:
    path = model_path or MODEL_PATH
    pipeline = joblib.load(path)
    return pipeline.predict([text])[0]


if __name__ == "__main__":
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/Resume.csv"
    train_classifier(csv_path)
