import os
import argparse

def main(jsonl_file_path, eval_name):
    # Command to transform the CSV file into JSONL
    # command = f'openai tools fine_tunes.prepare_data -f {csv_file_path}'

    # # Execute the command
    # subprocess.run(command, shell=True)

    # # Determine the resulting JSONL file path
    # base_name = os.path.basename(csv_file_path).replace('.csv', '_prepared.jsonl')
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Transform CSV to JSONL, create eval YAML file, and save to specified paths.')
    parser.add_argument('csv_file_path', type=str, help='The path to the CSV file.')
    parser.add_argument('eval_name', type=str, help='The evaluation project name.')

    args = parser.parse_args()
    main(args.csv_file_path, args.eval_name)
