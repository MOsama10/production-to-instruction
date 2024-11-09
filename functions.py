# functions.py
from human_model import *
from sqlcoder_model import *
from database_setup import * 
from imports import *

def generate_response(user_question: str, query_result: str, error_message = None):
    prompt = f"""
Given an sql query result {str(query_result)} in a list and a user question {user_question} show them in a regular human readable way and expalian the output.
make the final answer in a summary,

### Final Output
"""
    messages = [
        {"role": "system", "content": "You are a professional presenter"},
        {"role": "user", "content": prompt}
    ]
    text = human_tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    model_inputs = human_tokenizer([text], return_tensors="pt").to(model.device)

    generated_ids = human_model.generate(
        **model_inputs,
        streamer = human_streamer,
        max_new_tokens=1024,
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = human_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    #print(response)
    return response


def generate_text(prompt: str, max_length: int = 500) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, temperature=0,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
        max_new_tokens=max_length,
        streamer=streamer,)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def generate_sql(user_question: str, schema: str, error_message=None, query=None) -> str:
    try:
        if error_message:
            prompt = f"""
            ### Task
Correct the SQL query provided based on the [ERROR]{error_message}[/ERROR].

### Instructions
- Use the provided database schema for reference.
- Correct the SQL query based on the error and ensure it returns the intended result.
- If the error cannot be corrected with the given database schema, return 'I do not know.'

### Input
- **Database Schema:** {schema}
- **Original Query:** [SQL]{query}[/SQL]

### Answer
Given the schema and the error, here is the corrected SQL query:
[SQL]
            """
            generated_sql = generate_text(prompt, 1500)
        else:
            prompt = f"""
### Task
Generate a SQL query to answer [QUESTION]{user_question}[/QUESTION]

### Instructions
- Analyze the user's question carefully and map it to the database schema.
- Check the sample rows of the data to know the data patterns and which records appear in which columns.
- YOU MUST WRITE ALL COLUMN NAMES in double quotes (e.g., "Material Description").
- Pay close attention to the structure of the schema to infer relationships between columns.
- Ensure that any JOIN or WHERE clauses are correctly formulated based on table relationships in the schema.
- If the question cannot be answered using the given schema, respond with 'I do not know'
- Avoid assumptions that aren't clearly supported by the schema or user question.

### Database Schema
This query will run on a database whose schema is represented in this string:
{schema}

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{user_question}[/QUESTION]
```sql
            """
            generated_sql = generate_text(prompt, 1500)
        
        # Ensure that the SQL generation worked
        if not generated_sql:
            raise ValueError("The model did not return a valid SQL query.")

        sql_start = generated_sql.find("```sql") + 6
        sql_end = generated_sql.find("```", sql_start)
        return generated_sql[sql_start:sql_end].strip()
    
    except Exception as e:
        # Return error details for debugging
        return f"Error generating SQL: {str(e)}"

def execute_query(query: str) -> str:
    try:
        result = db.run(query)
        if not result:
            raise ValueError("No result was returned from the query execution.")
        return result
    except Exception as e:
        error_message = f"An error occurred while executing the query: {str(e)}"
        return error_message

def generate_user_response(user_question: str, query_result: str, error_message=None) -> str:
    try:
        prompt = f"""As a professional representative of a manufacturing and logistics company,
        provide a clear and concise response to the following user query based on the database result.
        Make sure the response is easy for a regular user to understand.

        ### User Query
        {user_question}

        ### Database Result
        {query_result}

        ### Final Output
        Please provide a detailed readable human response without annotations or anything below based on this information:
        """

        # Generate the response text from the model
        generated_response = generate_text(prompt, 1500)
        
        # Regular expression to match the response text after the "Final Output" section
        response_start = generated_response.find('### Final Output')
        response = generated_response[response_start:].strip()
        if not response:
            raise ValueError("Generated response is empty.")
        return response

    except Exception as e:
        return f"Error generating response: {str(e)}"


def generate_final_response(user_question: str, schema: str):
    max_retries = 3
    iter = 0

    sql_query = generate_sql(user_question, schema)
    # SQL adjustments based on specific conditions
    adjusted_query = sql_query.replace("ILIKE", "LIKE").replace("TRUE", "1").replace("FALSE", "0")
    sql_query = adjusted_query

    query_result = execute_query(sql_query)

    while iter < max_retries:
        if query_result.startswith("An error"):
            # Regenerate the SQL query based on the error message
            sql_query = generate_sql(user_question, schema, query_result, sql_query)
            query_result = execute_query(sql_query)
            iter += 1
        else:
            break

    # Display result or error if max retries reached
    if iter >= max_retries:
        print(f"Query could not be corrected after {max_retries} attempts.")
    else:
        print("Query Result:")
        display(query_result)

    # Generate user response
    response = generate_user_response(user_question, query_result)
    return response

