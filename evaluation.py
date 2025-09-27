import json
import sys
import re
from collections import defaultdict

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if isinstance(data, dict):
                lists = [v for v in data.values() if isinstance(v, list)]
                if len(lists) == 1:
                    return lists[0]
            if isinstance(data, list):
                return data
            return [data]
        except json.JSONDecodeError:
            f.seek(0)
            records = []
            for raw in f:
                line = raw.strip()
                if not line or line in ('[', ']'):
                    continue
                if line.endswith(','):
                    line = line[:-1]
                if line.startswith('{') and line.endswith('}'):
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return records


def extract_answer(output_str, qtype):
    m = re.findall(r"Answer:\s*\{(.+?)\}", output_str)
    if m:
        answer = m[-1].strip()
    else:
        m = re.findall(r"Answer:\s*(.+)", output_str)
        answer = m[-1].strip() if m else ""

    if not answer:
        return ""
    if qtype == 'multiple_choice':
        return answer[0].upper()
    return answer


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <predictions_file>", file=sys.stderr)
        sys.exit(1)

    GROUND_TRUTH_PATH = "./data/muslr.json"
    PREDICTIONS_PATH = sys.argv[1]

    gt_list = load_json(GROUND_TRUTH_PATH)
    pred_list = load_json(PREDICTIONS_PATH)

    pred_by_id = {}
    for idx, rec in enumerate(pred_list):
        rec_id = rec.get("custom_id", rec.get("id", idx))
        pred_by_id[rec_id] = rec

    total = 0
    correct = 0

    for idx, gt in enumerate(gt_list):
        rec_id = gt.get("id", idx)
        pred = pred_by_id.get(rec_id)
        if not pred or not gt.get("answer"):
            continue

        raw_output = None
        if "output" in pred and isinstance(pred["output"], str):
            raw_output = pred["output"]
        elif (
            "response" in pred
            and isinstance(pred["response"], dict)
            and "body" in pred["response"]
            and "choices" in pred["response"]["body"]
            and len(pred["response"]["body"]["choices"]) > 0
            and "message" in pred["response"]["body"]["choices"][0]
            and "content" in pred["response"]["body"]["choices"][0]["message"]
        ):
            raw_output = pred["response"]["body"]["choices"][0]["message"]["content"]

        if not raw_output:
            continue

        ans = extract_answer(raw_output, gt.get("type", "")).replace(" ", "")
        if not ans:
            continue

        total += 1
        if ans.upper() == gt["answer"].upper():
            correct += 1

    accuracy = (correct / total * 100) if total else 0.0
    print(f"{accuracy:.2f}%")

if __name__ == "__main__":
    main()