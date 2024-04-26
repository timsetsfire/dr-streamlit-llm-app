import sys
import json
import requests
import uuid
import datetime as dt
import pandas as pd
import streamlit as st
import yaml
import logging
import os 

import datarobot as dr 

try: 
    from dotenv import load_dotenv 
    load_dotenv(override = True) 
except Exception as e:
    print(e)

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(
                format="{} - %(levelname)s - %(asctime)s - %(message)s".format("debug-loggers"),
        )
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

DATAROBOT_API_TOKEN = os.environ['DATAROBOT_API_TOKEN']
DATAROBOT_ENDPOINT = os.environ.get("DATAROBOT_ENDPOINT","https://app.datarobot.com/api/v2")

def set_init_session_state():
    st.session_state["APP_NAME"] = "Generic App Name"
    st.session_state["LLM_DEPLOYMENT"] = None
    st.session_state["API_URL"] = None
    st.session_state["LLM_QUERY_DONE"] = False
    st.session_state["FILE_TO_URL"] = {}
    st.session_state["ALL_LLM_DEPLOYMENTS"] = {}

if "LLM_QUERY_DONE" not in st.session_state:
    set_init_session_state()

class DataRobotPredictionError(Exception):
    """Raised if there are issues getting predictions from DataRobot"""

def render_cite_area(think_area, state_key, answer_lang="python"):
    try:
        resp = st.session_state[state_key]
    except KeyError:
        raise ValueError('No response generated to your query. Please try again.')
    with think_area:
        ct = st.container()
        ct.header("**Answer:**")
        ct.markdown(resp)


        try: 
            file_to_url = st.session_state["FILE_TO_URL"]
            ct.header("**Citations:**")
            citations = st.session_state["citations"]
            num_citations = st.session_state["num_citations"]
            for i in range( int(num_citations)):
                filename = citations[f"CITATION_SOURCE_{i}"]
                url = file_to_url.get(filename, filename)
                # title = doc['metadata']['file_path'].split('.', 1)[0]
                title = filename
                with ct.expander(f"Citation {i+1}"):
                    st.markdown('**Source:** {}'.format(url))
                    st.markdown('**Content:**')
                    st.markdown( citations[f"CITATION_CONTENT_{i}"])
        except Exception as e:
            st.markdown("*** No Citations Available ***")
            st.markdown(e)
    return 0


def run_prompt(cite_response=None):
    DATAROBOT_KEY = st.session_state["LLM_DEPLOYMENT"].default_prediction_server["datarobot-key"]
    prompt = st.session_state.latest_prompt
    try:
        headers = {
            'Content-Type': 'text/plain; charset=UTF-8',
            'Authorization': 'Bearer {}'.format(DATAROBOT_API_TOKEN),
            'DataRobot-Key': DATAROBOT_KEY,
        }
        url = st.session_state["API_URL"]

        def llm_query(prompt): 
            data = pd.DataFrame([dict(promptText = prompt)])
            predictions_response = requests.post(
                url,
                data=data.to_csv(index = False),
                headers=headers
            )
            return predictions_response

        prediction_results = llm_query(prompt).json()
        output = prediction_results["data"][0]["prediction"]
        num_citations = (len(prediction_results["data"][0]["extraModelOutput"])-1) / 3
        citations = prediction_results["data"][0]["extraModelOutput"]
    except Exception as e:
        print(e)
        return 1
    
    if 'error' in prediction_results.keys():
        print('Request errored. Error message: {}'.format(prediction_results['error']))
        raise ValueError('Response errored. Please try again. Error message: {}'.format(prediction_results['error']))
        return 1

    st.session_state['response'] = output
    st.session_state['citations'] = citations
    st.session_state["num_citations"] = num_citations
    return 0


def main():

    if "LLM_QUERY_DONE" not in st.session_state:
        set_init_session_state()
    if not st.session_state["LLM_QUERY_DONE"] :
        with st.spinner("Grabbing available LLM Deployments from DataRobot MLOps ..."):
            st.session_state["LLM_QUERY_DONE"] = True
            llm_deployments = dict([ (d.label, d) for d in dr.Deployment.list() if d.model["target_type"] == "TextGeneration"])
            st.session_state["ALL_LLM_DEPLOYMENTS"] = llm_deployments
    llm_deployments = st.session_state["ALL_LLM_DEPLOYMENTS"]
    deployment_name = st.sidebar.selectbox("Pick your LLM Deployment", [d[0] for d in llm_deployments.items()])
    deployment = llm_deployments[deployment_name]   
    st.session_state["LLM_DEPLOYMENT"] = deployment
    API_URL = os.path.join(deployment.prediction_environment["name"], f'predApi/v1.0/deployments/{deployment.id}/predictions')
    st.session_state["API_URL"] = API_URL

    app_title = st.sidebar.text_input("Name your applicatoin", value = "Chat with your DataRobot Proxied LLMs!!")
    st.session_state["APP_NAME"] = app_title


    uploaded_file = st.sidebar.file_uploader("Upload file to url mapper.  This will be used to take Documents returned in citations and provide URLs", type="yaml", )
    # if st.sidebar.button("upload file mapper"):
    if uploaded_file is not None:
        file_to_url = yaml.load(uploaded_file, Loader = yaml.SafeLoader) 
        st.session_state["FILE_TO_URL"] = file_to_url
        st.session_state["UPLOADED_FILE_NAME"] = uploaded_file
    else:
        st.session_state["FILE_TO_URL"] = {}
    
    if st.session_state["API_URL"] is not None:
        with st.sidebar.expander(f"Chat Bot Details"):
            try:
                creds = os.environ["DATAROBOT_API_TOKEN"], os.environ["DATAROBOT_API_TOKEN"], os.environ["DATAROBOT_API_TOKEN"]
                st.markdown("DR Credentials are set!")
            except Exception as e:
                st.markdown(f"DR credentials are not available: {e}")
            st.markdown(st.session_state["LLM_DEPLOYMENT"])
            st.markdown(st.session_state["LLM_DEPLOYMENT"].description)
            st.markdown(st.session_state["API_URL"])

    st.title(st.session_state["APP_NAME"])
    st.markdown("This chatbot app will ONLY work with Deployments that originated from within the DataRobot Playground")
    prompt_area = st.container()
    if 'prompt_sent' not in st.session_state:
        st.session_state['prompt_sent'] = False
    if 'docs_source' not in st.session_state:
        st.session_state['docs_source'] = 'All'

    send, _ = st.columns([1, 4])
    do_send = send.button(label='Send', key='send')

    cite_area = st.container()
    cite_response = cite_area.empty()

    if do_send:
        submit_time = dt.datetime.now()
        _id = uuid.uuid4().hex
        association_id = '{}_{}'.format(_id, submit_time)
        st.session_state['prompt_sent'] = True
        st.session_state['association_id'] = association_id
        run_prompt(cite_response)
    
    if st.session_state['prompt_sent'] == True:
        render_cite_area(cite_response, 'response', answer_lang='markdown')

    prompt_area.text_area(
        label='Prompt',
        key='latest_prompt',
        kwargs={
            'cite_area': cite_response,
        }, value = "Start prompting!!"
    )

if __name__ == "__main__":
    main()
