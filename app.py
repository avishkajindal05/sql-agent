import gradio as gr
import json
import db
import pandas as pd

try:
    db.init_db()
    
except Exception as e:
    print(f"Error Initiating DB: {e}")
with open("branding.json") as f:
    brand_data = json.load()
    brand = brand_data['brand']