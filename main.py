from fastapi import FastAPI
from pydantic import BaseModel
from database_setup import db
from functions import generate_final_response


app = FastAPI()

class InputData(BaseModel):
    user_question: str
    
schema = db.get_table_info()
# Main API endpoint for generating SQL predictions and responses
@app.post("/generate")
async def generate(data: InputData):
    response = generate_final_response(data.user_question,schema=schema)
    
    return {"response": response}