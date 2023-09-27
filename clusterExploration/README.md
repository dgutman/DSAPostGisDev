### Cluster exploration analysis for Vandy Data Set

Creating a virtual environment, I typically run this from the root directory of the repo


    python -m venv .pyenv

    source .pyenv/bin/activate

    pip install -r requirements.txt


    ### Weird MAC OSX Stuff

    jupyter notebook doesn't seem to run, I am running

       jupyter nbclassic


## Dash Application
This also lives in the same directory, to start it just (once your environment is loaded!)

   python app.py



### Viewing dash app

   Go to http://localhost:8050

### # Things to note

The app will restart when you make changes, but if you break the python code, you'll have to restart the app (i.e. python app.py)