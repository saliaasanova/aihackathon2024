import subprocess
import yaml
import re

# Path to the cot.yaml file
cot_yaml_path = "evals/registry/completion_fns/cot.yaml"

costs = {
    "cot/gpt-3.5-turbo-instruct":{"input":1.5,"output":2},
    "cot/gpt-3.5-turbo" :{"input": 0.5,"output": 2},
    "cot/gpt-3.5-turbo-0125" :{"input" : 0.5,"output" : 1.5},
    "cot/gpt-4" :{"input": 30,"output":60},
    "cot/gpt-4-0613" :{"input": 60,"output":120},
    "cot/gpt-4-turbo" :{"input": 10,"output":30},
    "cot/gpt-4-1106-preview" :{"input": 10,"output":30},
    "cot/gpt-4-0125-preview" :{"input": 10,"output":30},
    "cot/gpt-4o-2024-05-13" :{"input": 5,"output":15},
    "cot/gpt-4o" :{"input": 5,"output":15},    
}

# Load the cot.yaml file
with open(cot_yaml_path, "r") as file:
    cot_config = yaml.safe_load(file)

# Extract model names from the configuration
models = list(cot_config.keys())

# Task to evaluate
task = "ab"

# Dictionary to store final report data
final_reports = {}

# Regular expression to match the final report lines
final_report_pattern = re.compile(r"\[oaieval.py:\d+\] ([\w/_]+): (\d+)")

# Iterate through each model and run the evaluation command
for model in models:
    command = ["oaieval", model, task]
    print(f"Evaluating: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Extract final report data
    final_report_data = {}
    for line in result.stderr.splitlines():
        match = final_report_pattern.search(line)
        if match:
            key, value = match.groups()
            final_report_data[key] = int(value)
    
    # Store the final report data by model name
    final_reports[model] = final_report_data

# Calculate the index and sort the models
model_indices = {}
model_costs = {}
for model, report in final_reports.items():
    counts_A = report.get("counts/A", 0)
    counts_B = report.get("counts/B", 0)
    counts_C = report.get("counts/C", 0)
    counts_D = report.get("counts/D", 0)
    counts_E = report.get("counts/E", 0)
    inputToken = report.get("usage_prompt_tokens", 0)
    outputToken = report.get("usage_completion_tokens", 0)
    index = (counts_C * 1 + counts_B*0.8 + counts_A * 0.7 + counts_E*0.5 - counts_D)*100
    totalCost = inputToken*costs[model]["input"] + outputToken*costs[model]["output"]
    model_indices[model] = index
    model_costs[model] = totalCost

# Sort models by the calculated index in descending order
sorted_models = sorted(model_indices.items(), key=lambda x: x[1], reverse=True)
max_model_name_length = 30

print(f"+------+ {'-'*(max_model_name_length+2)} +---------+ --------------- +")
print(f"| No.  | Model{' '*(max_model_name_length-5)} | Metascore| Average Cost    |")
print(f"+------+ {'-'*(max_model_name_length+2)} +---------+ --------------- +")

i = 0

for model, index in sorted_models:
    i += 1
    print(f"| {i:<4} | {model:<{max_model_name_length}} | {round(index ,1):^7} | ${round(model_costs[model]/1000,1):>10} USD |")

print(f"+------+ {'-'*(max_model_name_length+2)} +---------+ --------------- +")