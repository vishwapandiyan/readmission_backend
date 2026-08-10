"""
Hospital Readmission Prediction Model - Training Script
"""
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score

RANDOM_STATE = 42

# Load
df = pd.read_csv("patient_data_final.csv")
X = df.drop(columns=["patient_id", "readmitted_30_days", "drg_code"])
y = df["readmitted_30_days"]

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

# Preprocess
categorical = X.select_dtypes(include="object").columns.tolist()
numeric = X.select_dtypes(exclude="object").columns.tolist()
prep = ColumnTransformer([("num", StandardScaler(), numeric), ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), categorical)])

# Train
model = Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE))])
print("Training...")
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]
print(f"AUC: {roc_auc_score(y_test, y_proba):.3f}")
print(f"Accuracy: {accuracy_score(y_test, y_pred):.1%}")

# Save
with open("best_model.pkl", "wb") as f:
    pickle.dump(model, f)
feats = model.named_steps["prep"].get_feature_names_out()
coefs = model.named_steps["clf"].coef_[0]
pd.DataFrame({"feature": feats, "coefficient": coefs, "abs_coefficient": np.abs(coefs)}).sort_values("abs_coefficient", ascending=False).to_csv("best_model_feature_importance.csv", index=False)
print("✓ Saved: best_model.pkl, best_model_feature_importance.csv")
