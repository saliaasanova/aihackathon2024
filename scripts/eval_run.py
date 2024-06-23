import os
import argparse
import subprocess
import yaml
import re

def main(jsonl_file_path, eval_name):
    jsonl_file_path = jsonl_file_path

    # Define the destination path for the JSONL file
    destination_path = f'evals/registry/data/{eval_name}/samples.jsonl'

    # Create destination directory if it doesn't exist
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    # Move the JSONL file to the destination
    os.rename(jsonl_file_path, destination_path)

    print(f"JSONL file saved to {destination_path}")

    # Create the YAML content
    yaml_content = f"""
{eval_name}:
  id: {eval_name}.dev.v0
  description: 
  metrics: [accuracy]
{eval_name}.dev.v0:
  class: evals.elsuite.modelgraded.classify:ModelBasedClassify
  args:
    samples_jsonl: {eval_name}/samples.jsonl
    eval_type: cot_classify
    modelgraded_spec: fact
"""

    # Define the destination path for the YAML file
    yaml_file_path = f'evals/registry/evals/{eval_name}.yaml'

    # Create destination directory if it doesn't exist
    os.makedirs(os.path.dirname(yaml_file_path), exist_ok=True)

    # Write the YAML content to the file
    with open(yaml_file_path, 'w') as yaml_file:
        yaml_file.write(yaml_content.strip())

    print(f"YAML file saved to {yaml_file_path}")

    # Path to the cot.yaml file
    cot_yaml_path = "evals/registry/completion_fns/cot.yaml"

    costs = {
        "cot/gpt-3.5-turbo-instruct": {"input": 1.5, "output": 2},
        "cot/gpt-3.5-turbo": {"input": 0.5, "output": 2},
        "cot/gpt-3.5-turbo-0125": {"input": 0.5, "output": 1.5},
        "cot/gpt-4": {"input": 30, "output": 60},
        "cot/gpt-4-0613": {"input": 60, "output": 120},
        "cot/gpt-4-turbo": {"input": 10, "output": 30},
        "cot/gpt-4-1106-preview": {"input": 10, "output": 30},
        "cot/gpt-4-0125-preview": {"input": 10, "output": 30},
        "cot/gpt-4o-2024-05-13": {"input": 5, "output": 15},
        "cot/gpt-4o": {"input": 5, "output": 15},
    }

    # Load the cot.yaml file
    with open(cot_yaml_path, "r") as file:
        cot_config = yaml.safe_load(file)

    # Extract model names from the configuration
    models = list(cot_config.keys())

    # Task to evaluate
    task = eval_name

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
        index = (counts_C * 1 + counts_B * 0.8 + counts_A * 0.7 + counts_E * 0.5 - counts_D) * 100
        totalCost = inputToken * costs[model]["input"] + outputToken * costs[model]["output"]
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
        print(f"| {i:<4} | {model:<{max_model_name_length}} | {round(index ,1):^9} | ${round(model_costs[model]/1000,1):>10} USD |")

    print(f"+------+ {'-'*(max_model_name_length+2)} +---------+ --------------- +")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Transform JSONL to eval, create eval YAML file, and save to specified paths.')
    parser.add_argument('jsonl_file_path', type=str, help='The path to the JSONL file.')
    parser.add_argument('eval_name', type=str, help='The evaluation project name.')

    args = parser.parse_args()
    main(args.jsonl_file_path, args.eval_name)
