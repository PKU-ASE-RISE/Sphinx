
import json
from llmtest import *
multiple = 'Please answer with only the option character (A, B, C, or D). '
truefalse = 'Please answer with only \'T\' for yes or \'F\' for no. '
def solve(file):
    print(file)
    def work(text, x, prompt):
        s = x+len(prompt)
        return text[s:text.find('==============================================',s)-1]
        
    answers = []
    last = 0
    with open(file,'r+',encoding='utf-8') as fp:
        text = ''.join(fp.readlines())
        while 1:
            x1 = text.find(multiple, last)
            x2 = text.find(truefalse, last)
            if x1==-1 and x2==-1:
                break
            if x1!=-1 and (x1<x2 or x2==-1):
                answers += [work(text,x1,multiple)]
                last = x1 +5
            else:
                answers += [work(text,x2,truefalse)]
                last = x2 +5
    if 'write_raw_output' == 0:
        answerjs = json.dumps({'answers':answers})
        with open(file.replace('.txt','_extracted.json'),'w+') as fp:
            fp.write(answerjs)

    final_answer = []
    final_data = {}
    need_gpt = 0
    with open('questions.json','r+') as fp:
        questions = json.load(fp)
        id = 0
        for question in questions:
            question['llm_multiple_choice_answer'] = answers[id*5]
            question['llm_binary_answer'] = answers[id*5+1:id*5+5]
            if answers[id*5] in ['A','B','C','D']:
                question['repaired_llm_multiple_choice_answer'] = answers[id*5]
            else:
                need_gpt += 1 
                print(f'using gpt on: {answers[id*5]}')
                ans = ask_modify_abcd(answers[id*5])
                question['repaired_llm_multiple_choice_answer'] = ans
                print(f'gpt answer: {ans}')
            question['repaired_llm_binary_answer'] = []
            for i in answers[id*5+1:id*5+5]:
                if i in ['T','F']:
                    question['repaired_llm_binary_answer'] += [i]
                else:
                    need_gpt += 1 
                    print(f'using gpt on: {i}')
                    ans = ask_modify_tf(i)
                    question['repaired_llm_binary_answer'] += [ans]
                    print(f'gpt answer: {ans}')
            final_answer += [question]
            id += 1
    def get_everything_right(abcd, tf):
        right_abcd = {'app_level':0,'intention_level':0}
        total_abcd = {'app_level':0,'intention_level':0}
        
        right_single_tf = {'app_level':0,'intention_level':0}
        total_single_tf = {'app_level':0,'intention_level':0}
        right_multiple_tf = {'app_level':0,'intention_level':0}
        total_multiple_tf = {'app_level':0,'intention_level':0}
        
        all_false_tf = {'app_level':0,'intention_level':0}
        all_true_tf = {'app_level':0,'intention_level':0}
        total_tf = {'app_level':0,'intention_level':0}
        id = 0
        for question in final_answer:   
            gt = question["ground_truth"]
            type = question['question_type']
            if question[abcd] == gt:
                right_abcd[type] += 1
            total_abcd[type] += 1
            
            tfs = question[tf]
            howmanyt = 0
            for i in tfs:
                if i == 'T':
                    howmanyt += 1
            dick = {'A':0,'B':1,'C':2,'D':3}
            if howmanyt == 1:
                if tfs[dick[gt]] == 'T':
                    right_single_tf[type] += 1
                total_single_tf[type] += 1
            elif howmanyt == 0:
                all_false_tf[type] += 1
            else:
                if howmanyt == 4:
                    all_true_tf[type] += 1
                if tfs[dick[gt]] == 'T':
                    right_multiple_tf[type] += 1
                total_multiple_tf[type] += 1
                
            total_tf[type] += 1
            id+=1            
        return right_abcd,total_abcd,right_single_tf,total_single_tf,\
            right_multiple_tf,total_multiple_tf,all_false_tf,all_true_tf,total_tf
            


    def fill_in(real_type,type,right_abcd,total_abcd,right_single_tf,total_single_tf,\
            right_multiple_tf,total_multiple_tf,all_false_tf,all_true_tf,total_tf):
        final_data[real_type] = {
            "mcqa_stats": {
                "total": total_abcd[type],
                "correct": right_abcd[type],
                "accuracy": right_abcd[type] / total_abcd[type]
            },
            "binary_stats": {
                "single_true_case": {
                    "correct": right_single_tf[type],
                    "total": total_single_tf[type]
                },
                "multiple_true_case": {
                    "correct": right_multiple_tf[type],
                    "total": total_multiple_tf[type]
                },
                "all_false_count": all_false_tf[type],
                "all_true_count": all_true_tf[type],
                "multiple_true_count": total_multiple_tf[type],
                "single_true_count": right_single_tf[type]
            }
        }
    right_abcd,total_abcd,right_single_tf,total_single_tf,\
        right_multiple_tf,total_multiple_tf,all_false_tf,all_true_tf,total_tf\
            =get_everything_right('llm_multiple_choice_answer','llm_binary_answer') 
    fill_in('app_level','app_level',right_abcd,total_abcd,right_single_tf,total_single_tf,\
            right_multiple_tf,total_multiple_tf,all_false_tf,all_true_tf,total_tf)
    fill_in('intention_level','intention_level',right_abcd,total_abcd,right_single_tf,total_single_tf,\
            right_multiple_tf,total_multiple_tf,all_false_tf,all_true_tf,total_tf)
    
    right_abcd,total_abcd,right_single_tf,total_single_tf,\
        right_multiple_tf,total_multiple_tf,all_false_tf,all_true_tf,total_tf\
            =get_everything_right('repaired_llm_multiple_choice_answer','repaired_llm_binary_answer') 
    fill_in('repaired_app_level','app_level',right_abcd,total_abcd,right_single_tf,total_single_tf,\
            right_multiple_tf,total_multiple_tf,all_false_tf,all_true_tf,total_tf)
    fill_in('repaired_intention_level','intention_level',right_abcd,total_abcd,right_single_tf,total_single_tf,\
            right_multiple_tf,total_multiple_tf,all_false_tf,all_true_tf,total_tf)
            
    if 'write_revised_question_output':
        answerjs = json.dumps(final_answer, indent =4)
        with open(file.replace('.txt','_revised_question_answer.json'),'w+') as fp:
            fp.write(answerjs)
            
    if 'write_final_output':
        final_data['gpt_repair_used'] = need_gpt
        answerjs = json.dumps(final_data, indent = 4)
        with open(file.replace('.txt','_final.json'),'w+') as fp:
            fp.write(answerjs)
            
            
from pathlib import Path
        
def calc_final(model_name):
    path = Path(model_name + "_revised_question_answer.json")
    with open(path) as fp:
        res = json.load(fp)
    original_correct_goal = 0
    original_correct_app = 0
    original_total_goal = 0
    original_total_app = 0
    revised_correct_goal = 0
    revised_correct_app = 0
    revised_total_goal = 0
    revised_total_app = 0
    for x in res:
        gt = x["ground_truth"]
        bin_gt = ["F", "F", "F", "F"]
        bin_gt[ord(gt) - ord("A")] = "T"
        q_type = x["question_type"]
        original_mut_answer = x["llm_multiple_choice_answer"]
        original_bin_answers = x["llm_binary_answer"]
        revised_mut_answer = x["repaired_llm_multiple_choice_answer"]
        revised_bin_answers = x["repaired_llm_binary_answer"]
        original_total = 5
        revised_total = 5
        original_correct = int(gt == original_mut_answer) + sum([int(a == b) for a, b in zip(bin_gt, original_bin_answers)])
        revised_correct = int(gt == revised_mut_answer) + sum([int(a == b) for a, b in zip(bin_gt, revised_bin_answers)])
        if q_type == "app_level":
            original_correct_app += original_correct
            revised_correct_app += revised_correct
            original_total_app += original_total
            revised_total_app += revised_total
        else:
            original_correct_goal += original_correct
            revised_correct_goal += revised_correct
            original_total_goal += original_total
            revised_total_goal += revised_total
    
    print("=" * 20)
    print(f"Model: {model_name}")
    print(f"Original goal-level accuracy: {original_correct_goal / original_total_goal}")
    print(f"Revised goal-level accuracy: {revised_correct_goal / revised_total_goal}")
    print(f"Original app-level accuracy: {original_correct_app / original_total_app}")
    print(f"Revised app-level accuracy: {revised_correct_app / revised_total_app}")
        
    
if __name__ == "__main__":
    calc_final("gpt4")
    calc_final("gpt4o")
    calc_final("gpt4omini")
    calc_final("qwen_vl_plus")
    calc_final("qwen_vl_max")
    calc_final("deepseek")
    calc_final("llama3")
    calc_final("llama3_70b")
    calc_final("llama32_11b")
    # solve("llama32_11b.txt")
    # solve('qwen_vl_plus.txt')
    # import glob
    # for i in glob.glob('*.txt'):
    #     solve(i)