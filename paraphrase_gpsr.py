import requests
import re
import json
i=0

class SimpleOpenaiAPI:
    def __init__(self, server: str, key: str, model: str):
        self.model = model
        self.url = server
        self.key = key

    def chat(self, request: str, system: str, temp=0.7, max_tokens=2048) -> str:
        headers = {
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }

        json_payload = {
            "model": self.model,
            "temperature": temp,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": request}
            ]
        }

        reply = requests.post(self.url, headers=headers, json=json_payload)
        if reply.status_code != 200:
            raise Exception(f"{reply.reason}: {reply.text}")

        json_data = reply.json()
        return json_data["choices"][0]["message"]["content"].strip()

    def alternativePhrasing(self, task: str) -> list[str]:
        # --- Prompt left exactly as-is, per request ---
        system = """You are tasked with generating **one paraphrased version** of a given task command.
Your input will be a **single task command**.
Your output must be **a single Markdown list** containing **one phrasing** of that command **and nothing else**.

---

### **Guidelines**
* **Output length (strict):**
  * Output **exactly one** Markdown list item. Never output two, three, or more.
  * Do not explain your choice, do not add a preamble, do not add anything after the list item.
* **Content preservation:**
  * Keep all **entities, objects, and locations exactly the same** (e.g., “coke” must remain “coke”).
  * You may **restructure the sentence** as long as meaning and entities are preserved.
* **Tone and style:**
  * Maintain a **natural, conversational tone** write as if real people might say it.
  * Avoid robotic or overly formal phrasing unless required for the most complex version."""

        reply = self.chat(task, system)
        alternatives = []
        for line in reply.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("- "):
                alternatives.append(line.removeprefix("- ").strip())
            elif line.startswith("* "):
                alternatives.append(line.removeprefix("* ").strip())
            elif re.match(r"^[1-9]+\.", line):
                alternatives.append(re.sub(r"^[1-9]+\.\s*", '', line).strip())

        return alternatives


def extract_command_text(content: str) -> str:
    """
    Pulls out only the text that comes AFTER the
    "Parse this command:" / "Parse this robot command:" prefix.

    Example:
        "Parse this robot command:\\nMeet Charlie in the living room and say the day of the month"
        -> "Meet Charlie in the living room and say the day of the month"
    """
    match = re.search(r"Parse this (?:robot )?command:\s*(.*)", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: if the prefix isn't found, just use the whole string.
    return content.strip()


if __name__ == '__main__':
    # 1. Local Ollama endpoint (OpenAI-compatible), no billing, no internet needed
    OLLAMA_ENDPOINT = "http://localhost:11434/v1/chat/completions"

    # 2. Ollama doesn't require a real key, any placeholder works
    OLLAMA_KEY = "ollama"

    # 3. Model name must match EXACTLY what "ollama list" shows after you've pulled it
    #    (often includes a tag, e.g. "llama3.1:latest" — check with `ollama list`)
    MODEL_NAME = "llama3.1:latest"

    llm = SimpleOpenaiAPI(server=OLLAMA_ENDPOINT, key=OLLAMA_KEY, model=MODEL_NAME)

    # Path to your dataset (the file you uploaded)
    DATASET_PATH = "GPSR_testset.json"
    OUTPUT_PATH = "paraphrased_output.json"

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    results = []

    for entry in dataset:
        user_msg = next(m["content"] for m in entry["messages"] if m["role"] == "user")
        assistant_msg = next(m["content"] for m in entry["messages"] if m["role"] == "assistant")
        task_text = extract_command_text(user_msg)

        print(f"\nOriginal: '{task_text}'")
        alternatives = llm.alternativePhrasing(task_text)
        i+=1
        print(i)

        # Prompt is set up to return exactly one paraphrase; fall back to the
        # original text if the model somehow returns nothing.
        paraphrase = alternatives[0] if alternatives else task_text
        print(f"  {paraphrase}")

        results.append({
            "messages": [
                {
                    "role": "user",
                    "content": f"Parse this robot command:\n{paraphrase}"
                },
                {
                    "role": "assistant",
                    "content": assistant_msg
                }
            ]
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(results)} entries to {OUTPUT_PATH}")