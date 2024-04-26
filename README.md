
## DR Rag Bot Accelerator

The purpose of this repo is to quickly and easily get you a streamlit app deployed to datarobot.  The purpose of the app is to provide an interface for folks to interact with llm blueprints that have been deployed from the datarobot llm playground to datarobot mlops / console.  

## run the app 

Before pushing the app to DataRobot, give it a spin locally via

`streamlit run app/app.py`

This will require the following environment variables:
* `DATAROBOT_API_TOKEN`
* `DATAROBOT_ENDPOINT`

## push the app to datarobot 

install [dr-apps](https://github.com/datarobot/dr-apps) 

run the following 

`drapps create --path ./app --base-env 6542cd582a9d3d51bf4ac71e 'Connect to any LLM Proxied by DR'`

This will create an app in datarobot nammed `Connect to any LLM Proxied by DR`.  

If you don't already have `DATAROBOT_API_TOKEN` and `DATAROBOT_ENDPOINT` set and environment variables, either set them, or pass them to the `drapps create` command via `-t` and `-E` arguments as follows 

`drapps create -t <datarobot-api-token> -E <datarobot-endpoint> --path ./app --base-env 6542cd582a9d3d51bf4ac71e 'Connect to any LLM Proxied by DR'`