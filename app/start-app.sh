#!/usr/bin/env bash
export token="$DATAROBOT_API_TOKEN"
export endpoint="$DATAROBOT_ENDPOINT"
streamlit run --server.port 8080 app.py