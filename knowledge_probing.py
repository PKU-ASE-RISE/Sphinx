import json
from typing import List, Dict, Tuple
import sys
import os
from Agents.utils import get_llm
from LLMs import vlm_base


def load_data(file_path: str) -> List[Dict]:
    with open(file_path, 'r') as f:
        return json.load(f)


def generate_prompt(question_data: Dict, app_name: str) -> Tuple[str, str]:
    # MCQA prompt
    mcqa_prompt = f"Given the app name {app_name} in the category '{question_data['app_cateory']}', " \
                  f"answer the following multiple-choice question:\n\n" \
                  f"{question_data['question']}\n\n" \
                  f"Options:\n"
    for option, text in question_data['options'].items():
        mcqa_prompt += f"{option}. {text}\n"
    mcqa_prompt += "\nPlease answer with only the option character (A, B, C, or D)."

    # Binary prompt
    binary_prompt = f"Given the app name {app_name} in the category '{question_data['app_cateory']}', " \
                    f"is the following statement a correct option for the question: " \
                    f"\"{question_data['question']}\"\n\n" \
                    f"Statement: "

    return mcqa_prompt, binary_prompt


def evaluate_mcqa(ground_truth: str, llm_answer: str) -> bool:
    return ground_truth.upper() == llm_answer.upper()


def evaluate_binary_questions(ground_truth: str, binary_answers: List[str]) -> Dict[str, bool]:
    ground_truth_index = ord(ground_truth.upper()) - 65
    binary_answers_bool = [ans.upper() == 'T' for ans in binary_answers]

    single_true_correct = binary_answers_bool == [
        i == ground_truth_index for i in range(4)]
    multiple_true_correct = binary_answers_bool[ground_truth_index]
    all_false = not any(binary_answers_bool)
    all_true = all(binary_answers_bool)
    multiple_true = sum(binary_answers_bool) > 1
    single_true = sum(binary_answers_bool) == 1

    return {
        'single_true_correct': single_true_correct,
        'multiple_true_correct': multiple_true_correct,
        'all_false': all_false,
        'all_true': all_true,
        'multiple_true': multiple_true,
        'single_true': single_true
    }


def process_question(question_data: Dict):
    mcqa_prompt, binary_prompt_base = generate_prompt(
        question_data, question_data['app_name'][0])
    global current_llm
    # ---------------------------------------------------------------------
    if isinstance(current_llm, vlm_base):
        llm_mcqa_answer = current_llm([{"role": "user", "content": [mcqa_prompt]}])[
            'parsed_output']
    else:
        llm_mcqa_answer = current_llm([{"role": "user", "content": mcqa_prompt}])[
            'parsed_output']
    print('==============================================')
    print(mcqa_prompt, llm_mcqa_answer)
    print('==============================================')
    # ---------------------------------------------------------------------

    mcqa_correct = evaluate_mcqa(
        question_data['ground_truth'], llm_mcqa_answer)

    binary_results = []
    for option, text in question_data['options'].items():
        binary_prompt = binary_prompt_base + text + \
            f"\nPlease answer with only 'T' for yes or 'F' for no."

        # ---------------------------------------------------------------------
        if isinstance(current_llm, vlm_base):
            binary_answer = current_llm([{"role": "user", "content": [binary_prompt]}])[
                'parsed_output']
        else:
            binary_answer = current_llm([{"role": "user", "content": binary_prompt}])[
                'parsed_output']
        print('==============================================')
        print(binary_prompt, binary_answer)
        print('==============================================')
        # ---------------------------------------------------------------------
        print(binary_answer)
        binary_results.append(binary_answer)

    binary_evaluation = evaluate_binary_questions(
        question_data['ground_truth'], binary_results)

    return {
        'mcqa_result': mcqa_correct,
        'binary_result': binary_evaluation
    }


def process_questions(data: List[Dict]):
    mcqa_correct = 0
    total_questions = len(data)

    binary_stats = {
        'single_true_case': {'correct': 0, 'total': 0},
        'multiple_true_case': {'correct': 0, 'total': 0},
        'all_false_count': 0,
        'all_true_count': 0,
        'multiple_true_count': 0,
        'single_true_count': 0
    }

    for question_data in data:
        result = process_question(question_data)

        if result['mcqa_result']:
            mcqa_correct += 1

        binary_result = result['binary_result']
        if binary_result['single_true']:
            binary_stats['single_true_count'] += 1
            binary_stats['single_true_case']['total'] += 1
            binary_stats['single_true_case']['correct'] += int(
                binary_result['single_true_correct'])
        if binary_result['multiple_true']:
            binary_stats['multiple_true_count'] += 1
            binary_stats['multiple_true_case']['total'] += 1
            binary_stats['multiple_true_case']['correct'] += int(
                binary_result['multiple_true_correct'])
        binary_stats['all_false_count'] += int(binary_result['all_false'])
        binary_stats['all_true_count'] += int(binary_result['all_true'])

    mcqa_accuracy = mcqa_correct / total_questions if total_questions > 0 else 0

    return {
        'mcqa_stats': {
            'total': total_questions,
            'correct': mcqa_correct,
            'accuracy': mcqa_accuracy
        },
        'binary_stats': binary_stats
    }

# Main execution


def evaluate_single_llm(llm_name: str):
    data = load_data('questions.json')
    results = process_questions(data)

    print("\nMCQA Results:")
    print(f"Total Questions: {results['mcqa_stats']['total']}")
    print(f"Correct Answers: {results['mcqa_stats']['correct']}")
    print(f"Accuracy: {results['mcqa_stats']['accuracy']:.2f}")

    print("\nBinary Statistics:")
    binary_stats = results['binary_stats']
    print(f"Single True Case Count: {binary_stats['single_true_count']}")
    if binary_stats['single_true_case']['total'] > 0:
        print(
            f"Single True Case Accuracy: {binary_stats['single_true_case']['correct'] / binary_stats['single_true_case']['total']:.2f}")
    else:
        print("Single True Case Accuracy: N/A (No single true cases)")

    print(f"Multiple True Case Count: {binary_stats['multiple_true_count']}")
    if binary_stats['multiple_true_case']['total'] > 0:
        print(
            f"Multiple True Case Accuracy: {binary_stats['multiple_true_case']['correct'] / binary_stats['multiple_true_case']['total']:.2f}")
        print(
            f"Multiple True Case Incorrect Count: {binary_stats['multiple_true_case']['total'] - binary_stats['multiple_true_case']['correct']}")
    else:
        print("Multiple True Case Accuracy: N/A (No multiple true cases)")
        print("Multiple True Case Incorrect Count: N/A (No multiple true cases)")

    print(f"All False Count: {binary_stats['all_false_count']}")
    print(f"All True Count: {binary_stats['all_true_count']}")
    return results


if __name__ == "__main__":
    llms = ['llama32_11b']
    current_llm = None
    os.makedirs('knowledge_probing', exist_ok=True)
    for llm in llms:
        current_llm = get_llm(llm)
        print(f"Evaluating LLM: {llm}")
        # redirect stdout to file
        sys.stdout = open(f'knowledge_probing/{llm}.txt', 'w')
        results = evaluate_single_llm(llm)
        json.dump(results, open(
            f'knowledge_probing/{llm}_results.json', 'w'), indent=4)
        sys.stdout.close()
        # reset stdout
        sys.stdout = sys.__stdout__
