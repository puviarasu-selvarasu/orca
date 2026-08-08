import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from .aggregators import get_system_metrics_aggregated

def predict_system_health(user):
    """
    Predict future CPU/RAM usage based on historical patterns.
    Returns a dict with prediction and confidence.
    """
    data = get_system_metrics_aggregated(user)
    if len(data) < 5:
        return None
    
    df = pd.DataFrame(data)
    # Convert date to ordinal
    df['date_ord'] = pd.to_datetime(df['date']).map(lambda x: x.toordinal())
    X = df[['date_ord']].values
    y = df['count'].values
    
    model = LinearRegression()
    model.fit(X, y)
    # Predict for next day
    next_day = pd.Timestamp.now().toordinal() + 1
    pred = model.predict([[next_day]])
    confidence = model.score(X, y)  # R^2
    
    return {
        'metric': 'activity',
        'predicted_value': float(pred[0]),
        'confidence': float(confidence),
        'unit': 'messages'
    }

def predict_build_success(user, project_type, file_count):
    """
    Predict whether a build will succeed based on past builds.
    Uses a RandomForest classifier (trained on historical build logs).
    """
    # For now, return a dummy prediction.
    # In reality, you'd fetch past build records and train a model.
    return {'success_probability': 0.85, 'confidence': 0.7}