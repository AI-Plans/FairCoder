import transformers
from transformers import AutoTokenizer, GemmaTokenizer, AutoModelForCausalLM, set_seed
import torch
import json
import re
import os
import random
from tqdm import tqdm
from openai import OpenAI
#from utils import get_model, get_prompt_testcase, API_KEY, REPEAT_T, TEST_DATA
from utils import get_model_7b, get_prompt_testcase, API_KEY, REPEAT_T, TEST_DATA # bug fix
import sys

root_path = os.path.dirname(__file__)
#DEVICE = 'cuda:1'
DEVICE = 'cuda:0' # ML only has one GPU

def reorder_string(s):
    lines = s.strip().split('\n')
    # Keep the first two lines unchanged
    first_two_lines = lines[:2]
    # Randomly shuffle the rest of the lines
    remaining_lines = lines[2:]
    random.shuffle(remaining_lines)
    result = '\n'.join(first_two_lines + remaining_lines)
    
    return result

def write_data(file_name, topic, answer):
    data = {'topic': topic, 'answer':answer}
    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        json.dump(data, file)
        file.write('\n')


if __name__ == "__main__":
    data = TEST_DATA
    models = ['llama2', 'llama2-13b', 'codellama', 'codellama-13b', 'llama3', 'mistral', 'codegemma', 'qwen2', 'qwencoder','gpt-4o-mini', 'gpt-4o']

    for code_model in tqdm(models):
        
        code_model = 'codellama'

        for k,d in enumerate(data):

            topic = d['topic']
            category = d['cat']
            for code_type in ['code', 'code_form', 'code_pl', 'code_order']:
                code = d[code_type]

                folder_name = f'{root_path}/testcase/{code_model}/{category}/'
                write_file_name = folder_name + f'{topic}.jsonl'
                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)       

                for j in range(REPEAT_T):
                    # get question with random order
                    print(f'[DEBUG] loop code_model {code_model}, k,d in enumerate(data) = {k}, {d}, code_type = {code_type}, j repeat = {j}')
                    question = reorder_string(d['question'])
                    full_question = question + code
                    if code_model == 'codegemma':
                        full_question += 'Add some description about the test case.'
                    prompt = get_prompt_testcase(code_model, full_question)
                    if 'gpt' not in code_model:
                        # initialize model with random seed
                        seed = random.randint(0, 100)
                        set_seed(seed)
                        print(f'[DEBUG] full_question = {full_question}, prompt = {prompt}, seed = {seed}, creating model with get_model')
                        model, tokenizer = get_model_7b(code_model, DEVICE) # typo in original github? get_model does not take device argument
                        if 'qwen' in code_model:
                            text = tokenizer.apply_chat_template(
                                prompt,
                                tokenize=False,
                                add_generation_prompt=True
                            )
                            input_ids = tokenizer([text], return_tensors="pt")["input_ids"].to(DEVICE)
                        else:
                            input_ids = tokenizer(prompt, return_tensors="pt")["input_ids"].to(DEVICE)
                        print(f'[DEBUG] model created, generating output')
                        output = model.generate(
                            input_ids,
                            max_new_tokens=600,
                        )
                        output = output[0].to("cpu")
                        filling = tokenizer.decode(output[input_ids.shape[1]:], skip_special_tokens=True)
                        print(f'[DEBUG] filling/response = {filling}')
                    else:
                        client = OpenAI(api_key=API_KEY)
                        completion = client.chat.completions.create(
                            model=code_model,
                            messages=[
                                {"role": "system", "content": "You are a helpful agent."},
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        )
                        filling = completion.choices[0].message.content
                    print(filling)
                    write_data(write_file_name, topic, filling)
                    sys.exit() # debug
