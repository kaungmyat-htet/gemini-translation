# Python Translation Script using Gemini


Before you begin, please make sure you have these requirements.

**Requirements**
* Python
* Gemini API Key (You can get it from [Google AI Studio](https://aistudio.google.com/))

**Steps**
1. Please download this repository
2. Get the Gemini API key
    2.1 You can either put the key in .env file (as in .env.dist) or just put it in the command when you run the script
```bash
# create a virtual environment
python -m venv env

# activate the virtual environment
# if you are using Windows
env/Scripts/activate

# if you are using Linux/MacOS
source ./env/bin/activate

# install the dependencies
pip install -r requirements.txt

# run the script
# you can also add api-key using --api-key
python3 gemini-translate.py <input_file> <output_file> --column <column_name_to_translate>
```