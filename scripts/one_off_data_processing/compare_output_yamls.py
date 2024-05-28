"""
This is useful for plotting data from outputs from running a model. It can take in a number of yaml files in
yaml_paths (key = name to label in the plot, value = path to yaml) and plot the outputs.
The resulting figure is saved to output_path (as a png).
"""

import yaml
import matplotlib.pyplot as plt

# Function to read YAML files
def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Function to extract overall scores from the YAML data
def extract_overall_scores(yaml_data):
    scores = yaml_data['overall_scores']
    return scores

# Function to plot the overall scores
def plot_overall_scores(score_dicts, labels, output_path):
    behaviors = ['FEED', 'KILL', 'KILL_PHASE2', 'STALK', 'WALK']
    metrics = ['classification_f1', 'classification_precision', 'classification_recall']

    fig, axes = plt.subplots(len(metrics), 1, figsize=(10, 15), sharex=True)
    fig.suptitle('Model Outputs Comparison')

    for i, metric in enumerate(metrics):
        ax = axes[i]
        for label, scores in zip(labels, score_dicts):
            values = [scores[metric][behavior] for behavior in behaviors]
            ax.plot(behaviors, values, marker='o', label=label)
        ax.set_title(metric.replace('_', ' ').capitalize())
        ax.set_ylabel('Score')
        # Set xticks before setting xticklabels within the loop
        ax.set_xticks(range(len(behaviors)))  # This line is moved before setting labels
        ax.set_xticklabels(behaviors)
        ax.legend()

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_path)
    plt.show()
    print("Saved figure to {}".format(output_path))

# Main function
def main(yaml_paths, output_path):
    score_dicts = []
    labels = []

    for label, path in yaml_paths.items():
        yaml_data = read_yaml(path)
        overall_scores = extract_overall_scores(yaml_data)
        score_dicts.append(overall_scores)
        labels.append(label)  # Use the provided label

    plot_overall_scores(score_dicts, labels, output_path)

# Example dictionary with labels and paths
yaml_paths = {
    'CRNN': '/home/matthew/AI_Capstone/ai-capstone/BEBE_results-phase2/CRNN/F202_15sample_8hz_1hr_WALK/F202_15sample_8hz_1hr_WALK_CRNN/fold_1/test_eval.yaml',
    'RF': '/home/matthew/AI_Capstone/ai-capstone/BEBE_results-phase2/rf/F202_15sample_8hz_1hr_WALK/F202_15sample_8hz_1hr_WALK_rf/fold_1/test_eval.yaml'
}

output_path = 'model_comparison.png'

if __name__ == '__main__':
    main(yaml_paths, output_path)
