#### Design
* Used a thin layer on top of LLM clients so that we can easily switch to different providers. 
(Maybe not necessary given most of those APIs are identical.)
* Introduced the `Plugin` concept to allow extending the engine easily. It is using 
  [function calling](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
behind the scenes and also added extra functionality to ask for clarification when the input is 
in the status of `INVALID_INPUT`. Also added a simple weather plugin to demonstrate the expandability.
* Abstracted the `Conversation` so we can use Standard input and output for real conversation and use the fake one for testing.

#### Implementation
* LLM [function calling](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) is used to pick `Plugins` and extract input from user conversation. 
* Google [google-maps-services-python](https://github.com/googlemaps/google-maps-services-python) is used to get the travel distance and clarify
locations when necessary.

#### Execution
Create a .env file under the root and put two variables as below
```
ANTHROPIC_API_KEY=<key>
GOOGLE_MAP_API_KEY=<key>
```

Setup python venv
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Execute the agent
```
python src/main.py
```

#### Areas to Improve
* Python is not my strength. Never use it in production environment. You might find coding style issue and inconsistent style.
* Use google map API to find a list of address options when the provided one is ambiguous, then ask LLM to have the user to pick one.

