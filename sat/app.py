import sqlite3
import pandas as pd

import streamlit as st
from streamlit_chat import message

from langchain import OpenAI, SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate
from langchain.agents import ZeroShotAgent
from langchain.agents import AgentExecutor


# from scripts.sql_connector import convert_df_to_sql, read_sql_query
import mysql.connector
from sqlalchemy.dialects.mysql import mysqlconnector
import psycopg2
from sqlalchemy import create_engine, MetaData, select, Table
from sqlalchemy import text

from langchain.agents import create_pandas_dataframe_agent

from dotenv import load_dotenv

# def create_prompt():

#     prefix = """Given an input question, first create a syntactically correct query to run, then look at the results of the query and return the answer.
#     Use the following format:
#     Question: "Question here"
#     SQLQuery: "SQL Query to run"
#     SQLResult: "Result of the SQLQuery"
#     Answer: "Final answer here"

#     Only use the following tables:

#     {tables}
    
#     Refer the chat history as well as the table information to answer the following question:
#     Question: {input}"""

#     suffix = """Begin!"""


#     prompt_template = ZeroShotAgent.create_prompt(
#         prefix=prefix, 
#         suffix=suffix,
#         tools=[],
#         input_variables=["input", "tables"]
#     )

#     return prompt_template

def df_agent_response(df):
    llm = OpenAI(temperature=0)
    response = create_pandas_dataframe_agent(llm, df, verbose=True)
    return response

def sql_agent_response(input, input_db):

    # prompt_template = create_prompt()
    llm = OpenAI(temperature=0)

    db_chain = SQLDatabaseChain(llm = llm,
                            database = input_db,
                            # prompt=prompt_template,
                            verbose=True
                            # memory=st.session_state.memory
                            )
    
    response = db_chain.run(input)
    return response



def sql_table(input,input_db, api_key):

    from langchain.chat_models import ChatOpenAI
    from langchain.chains import create_sql_query_chain
    llm = OpenAI(temperature=0, openai_api_key = api_key)
    # prom = """
    #     safety stock = max value * max val delay - avg val * avg val delay
    # """
    chain = create_sql_query_chain(llm, input_db)

    response = chain.invoke({"question":input})

    return response





def main():
    load_dotenv()

    with st.sidebar:
        db_type = st.radio("Select Database Type", ["MySQL", "PostgreSQL", "default"])
        db_host = st.text_input("Enter Database Host", placeholder="Enter Database Host")
        db_port = st.text_input("Enter Database Port", placeholder="Enter Database Port", 
                                help="Default port is 5432 for PostgreSQL and 3306 for MySQL")
        db_name = st.text_input("Enter Database Name", placeholder="Enter Database Name")
        db_user = st.text_input("Enter Database User", placeholder="Enter Database User")
        db_password = st.text_input("Enter Database Password", "", type="password")

        api_key = st.text_input("Enter open_api_key", type="password")
        connect_button = st.button("Connect")

        
        if db_type == "MySQL":
            sql_uri = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            # sql_uri = f"mysql+mysqlconnector://root:localadmin@localhost:3306/adventureworks"
            #sql_uri = "mssql+pyodbc://@CBLLAP0315\SQLEXPRESS/AdventureWorks2022?driver=ODBC+Driver+17+for+SQL+Server"
            #sql_uri = ""

        elif db_type == "PostgreSQL":
            sql_uri = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        elif db_type == 'default':
            sql_uri = f"mysql+mysqlconnector://root:localadmin@localhost:3306/adventureworks"

        # elif db_type == "SQLite":
        #     sql_uri = f"sqlite:///{db_name}.db"
 
        # else:
        #     st.sidebar.error("Invalid Database Type selected")
    # sql_uri = f"mysql+mysqlconnector://root:localadmin@localhost:3306/adventureworks"
    try:
        if connect_button:
            st.write(sql_uri)
            input_db = SQLDatabase.from_uri(sql_uri)
            st.session_state.input_db = input_db
            st.sidebar.success("Connected")
            

            engine = create_engine(sql_uri)

            connection = engine.connect()
            metadata = MetaData()
            metadata.reflect(bind=engine)
            list_of_tables = list(metadata.tables.keys())
            m = 1
            st.success("You can start your exploration now!")
    except:
        st.error("Invalid Database Credentials")
            
    try:
        if st.sidebar.checkbox("Data Preview"):
            engine = create_engine(sql_uri)

            metadata = MetaData()
            metadata.reflect(bind=engine)

            list_of_tables = list(metadata.tables.keys())
            selected_table_name = st.sidebar.selectbox("Select table", list_of_tables)
            table = Table(selected_table_name, metadata, autoload_with=engine)

            
            connection = engine.connect()
            result = connection.execute(table.select())
            rows = result.fetchall()

            st.write("Selected Table:", selected_table_name)
            df = pd.DataFrame(rows, columns=table.columns.keys())
            select_num_records = st.number_input("Select Number of Records :", min_value=5, max_value=len(df), value=5, step=5)
            st.dataframe(df.head(select_num_records))  # Displaying only the top 5 rows
            st.divider()

    except:
        st.warning("Please connect to a database first")

    # response = df_agent_response(df)
    # st.write(response)
    
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(
            memory_key="chat_history"
        )

    # Check and initialize other session state variables
    if 'generated' not in st.session_state:
        st.session_state['generated'] = []
    if 'past' not in st.session_state:
        st.session_state['past'] = []
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [
            {'role': 'system', 'content': 'You are a helpful ChatBot!'}
        ]

    # Create containers
    response_container = st.container()
    container = st.container()

    # Chat input form
    with container:
        with st.form(key='my_form', clear_on_submit=True):
            user_input = st.text_area(label='You', key='input', height=20)
            submit_button = st.form_submit_button(label='Send')
            # prompt = propmt_template()

    # Reset conversation button
    reset_button = st.button("Start New Conversation")
    if reset_button:
        st.session_state['generated'] = []
        st.session_state['past'] = []

    # Process user input
    if submit_button and user_input:
        input_db = st.session_state.get('input_db', None)
        #output = sql_agent_response(user_input, input_db)

        type12 = st.radio("Answer Type", ["Table", "Text"])

        if type12 == "Table":
            query = sql_table(user_input, input_db, api_key)
            print(query)
            engine = create_engine(sql_uri)
            connection = engine.connect()
            output = pd.read_sql(query, connection)
            st.write(output)
            print(output)
            connection.close()
        
        else :
            output = sql_table(user_input, input_db)

            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(output)

            # Display conversation
            if st.session_state['generated']:
                with response_container:
                    for i in range(len(st.session_state['generated'])):
                        # Display user message
                        message(st.session_state['past'][i], is_user=True, key=str(i) + '_user1')

                        # Display bot message
                        message(st.session_state['generated'][i], key=str(i))
                


        # output = df_agent_response(df)
        # output = user_input
        

    
