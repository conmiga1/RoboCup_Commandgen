"""
Combined GPSR test-set generator.

Source of truth for FORMAT/SCHEMA  -> oldGPSR_testset.jsonl
Source of truth for LOGIC          -> gpsr_commands.py (CommandGenerator)

Produces exactly 300 test sets, each a chat-style JSONL row:

    {"messages": [
        {"role": "user",      "content": "Parse this robot command:\n<english text>"},
        {"role": "assistant", "content": "<compact-JSON string: [ {sequence, action, ...params}, ... ]>"}
    ]}

The assistant content is itself a JSON array of 1..N sequence objects (no extra
"command" wrapper), each carrying only the parameters that are valid for its
"action" (drawn from the 22 command templates defined in gpsr_commands.py's
CommandGenerator.templates).
"""

import json
import random
from collections import Counter

random.seed()  # non-deterministic; change/remove for reproducibility

# ---------------------------------------------------------------------------
# 1. KNOWLEDGE BASE
#    (vocabulary extracted from oldGPSR_testset.jsonl so every value we use
#     is one the reference set already considers valid)
# ---------------------------------------------------------------------------

ROOMS = [
    "bathroom", "bedroom", "dining room", "garage", "garden",
    "hallway", "kitchen", "living room", "office", "study",
]

# generic beacons / furniture used as "location" (not all of these can hold objects)
LOCATIONS = [
    "bathroom sink", "bedroom desk", "bookshelf", "cabinet", "counter",
    "dining table", "entrance door", "garden bench", "hallway shelf",
    "kitchen table", "living room couch", "nightstand", "office chair",
    "side table", "tv stand",
]

# subset of LOCATIONS that can plausibly hold objects (used for placement_location)
PLACEMENT_LOCATIONS = [
    "bedroom desk", "bookshelf", "cabinet", "counter", "dining table",
    "hallway shelf", "kitchen table", "nightstand", "side table", "tv stand",
]

NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George",
    "Hannah", "Ivan", "Julia", "Kevin", "Laura", "Michael", "Nancy", "Oliver",
]

GESTURES = [
    "waving person",
    "person raising their left arm",
    "person raising their right arm",
    "person pointing to the left",
    "person pointing to the right",
]

POSES = ["sitting person", "standing person", "lying person"]

PERSON_INFO = ["name", "pose", "gesture"]

OBJECT_COMPARATORS = [
    "biggest", "largest", "smallest", "heaviest", "lightest", "thinnest",
]

TALK_TOPICS = [
    "something about yourself", "the time", "what day is today",
    "what day is tomorrow", "your teams name", "your teams country",
    "your teams affiliation", "the day of the week", "the day of the month",
]

COLORS = ["blue", "yellow", "black", "white", "red", "orange", "gray"]
CLOTHES = ["t shirt", "shirt", "blouse", "sweater", "coat", "jacket"]
CLOTHING = [f"{c} {g}" for c in COLORS for g in CLOTHES]

OBJECTS_BY_CATEGORY = {
    "drink": ["coke", "juice", "water", "milk"],
    "snack": ["chips", "cookie", "cereal"],
    "fruit": ["banana", "orange", "apple"],
    "utensil": ["knife", "bowl", "cup"],
    "electronic": ["remote", "phone", "tablet"],
    "stationery": ["book", "pen", "notebook"],
}
OBJECT_CATEGORIES = list(OBJECTS_BY_CATEGORY.keys())


def random_object():
    """Return (object, category) picked consistently from the same category."""
    cat = random.choice(OBJECT_CATEGORIES)
    obj = random.choice(OBJECTS_BY_CATEGORY[cat])
    return obj, cat


# Verbs / prepositions lifted straight from gpsr_commands.py's verb_dict / prep_dict
VERB = {
    "take": ["take", "get", "grasp", "fetch"],
    "place": ["put", "place"],
    "deliver": ["bring", "give", "deliver"],
    "bring": ["bring", "give"],
    "go": ["go", "navigate"],
    "find": ["find", "locate", "look for"],
    "talk": ["tell", "say"],
    "meet": ["meet"],
    "tell": ["tell"],
    "greet": ["greet", "salute", "say hello to", "introduce yourself to"],
    "count": ["tell me how many"],
    "follow": ["follow"],
    "guide": ["guide", "escort", "take", "lead"],
}


def v(key):
    return random.choice(VERB[key])


def art(word):
    return "an" if word[0].lower() in "aeiou" else "a"


# ---------------------------------------------------------------------------
# 2. THE 22 ACTIONS  (== the 22 keys of CommandGenerator.templates in
#    gpsr_commands.py). Each builder returns (params_dict, sentence_text).
# ---------------------------------------------------------------------------

def gen_goToLoc():
    room = random.choice(ROOMS)
    params = {"room": room}
    text = f"{v('go')} to the {room}"
    return params, text


def gen_takeObjFromPlcmt():
    plcmt = random.choice(PLACEMENT_LOCATIONS)
    if random.random() < 0.5:
        obj, _ = random_object()
        params = {"object": obj, "placement_location": plcmt}
        text = f"{v('take')} the {obj} from the {plcmt}"
    else:
        cat = random.choice(OBJECT_CATEGORIES)
        params = {"object_category": cat, "placement_location": plcmt}
        text = f"{v('take')} a {cat} item from the {plcmt}"
    return params, text


def gen_findPrsInRoom():
    room = random.choice(ROOMS)
    if random.random() < 0.5:
        g = random.choice(GESTURES)
        params = {"gesture": g, "room": room}
        text = f"{v('find')} the {g} in the {room}"
    else:
        p = random.choice(POSES)
        params = {"pose": p, "room": room}
        text = f"{v('find')} the {p} in the {room}"
    return params, text


def gen_findObjInRoom():
    room = random.choice(ROOMS)
    if random.random() < 0.5:
        obj, _ = random_object()
        params = {"object": obj, "room": room}
        text = f"{v('find')} {art(obj)} {obj} in the {room}"
    else:
        cat = random.choice(OBJECT_CATEGORIES)
        params = {"object_category": cat, "room": room}
        text = f"{v('find')} a {cat} item in the {room}"
    return params, text


def gen_meetPrsAtBeac():
    name = random.choice(NAMES)
    loc = random.choice(LOCATIONS)
    params = {"person_name": name, "location": loc}
    text = f"{v('meet')} {name} at the {loc}"
    return params, text


def gen_countObjOnPlcmt():
    cat = random.choice(OBJECT_CATEGORIES)
    plcmt = random.choice(PLACEMENT_LOCATIONS)
    params = {"object_category": cat, "placement_location": plcmt}
    text = f"{v('count')} {cat} items there are on the {plcmt}"
    return params, text


def gen_countPrsInRoom():
    room = random.choice(ROOMS)
    if random.random() < 0.5:
        g = random.choice(GESTURES)
        params = {"gesture": g, "room": room}
        text = f"{v('count')} people are {g.split(' ', 1)[1] if g.startswith('person') else g} in the {room}"
    else:
        p = random.choice(POSES)
        params = {"pose": p, "room": room}
        text = f"{v('count')} {p}s are in the {room}"
    return params, text


def gen_tellPrsInfoInLoc():
    info = random.choice(PERSON_INFO)
    if random.random() < 0.5:
        room = random.choice(ROOMS)
        params = {"person_info": info, "room": room}
        text = f"{v('tell')} me the {info} of the person in the {room}"
    else:
        loc = random.choice(LOCATIONS)
        params = {"person_info": info, "location": loc}
        text = f"{v('tell')} me the {info} of the person at the {loc}"
    return params, text


def gen_tellObjPropOnPlcmt():
    comp = random.choice(OBJECT_COMPARATORS)
    plcmt = random.choice(PLACEMENT_LOCATIONS)
    params = {"object_comparator": comp, "placement_location": plcmt}
    text = f"{v('tell')} me what is the {comp} object on the {plcmt}"
    return params, text


def gen_talkInfoToGestPrsInRoom():
    talk = random.choice(TALK_TOPICS)
    g = random.choice(GESTURES)
    room = random.choice(ROOMS)
    params = {"talk_topic": talk, "gesture": g, "room": room}
    text = f"{v('talk')} {talk} to the {g} in the {room}"
    return params, text


def gen_followNameFromBeacToRoom():
    name = random.choice(NAMES)
    frm = random.choice(LOCATIONS)
    to = random.choice(ROOMS)
    params = {"person_name": name, "from_location": frm, "to_room": to}
    text = f"{v('follow')} {name} from the {frm} to the {to}"
    return params, text


def gen_guideNameFromBeacToBeac():
    name = random.choice(NAMES)
    frm = random.choice(LOCATIONS)
    to = random.choice(LOCATIONS + ROOMS)
    params = {"person_name": name, "from_location": frm, "to_location": to}
    text = f"{v('guide')} {name} from the {frm} to the {to}"
    return params, text


def gen_guidePrsFromBeacToBeac():
    frm = random.choice(LOCATIONS)
    to = random.choice(LOCATIONS + ROOMS)
    if random.random() < 0.5:
        g = random.choice(GESTURES)
        params = {"gesture": g, "from_location": frm, "to_location": to}
        text = f"{v('guide')} the {g} from the {frm} to the {to}"
    else:
        p = random.choice(POSES)
        params = {"pose": p, "from_location": frm, "to_location": to}
        text = f"{v('guide')} the {p} from the {frm} to the {to}"
    return params, text


def gen_guideClothPrsFromBeacToBeac():
    cloth = random.choice(CLOTHING)
    frm = random.choice(LOCATIONS)
    to = random.choice(LOCATIONS + ROOMS)
    params = {"clothing": cloth, "from_location": frm, "to_location": to}
    text = f"{v('guide')} the person wearing a {cloth} from the {frm} to the {to}"
    return params, text


def gen_bringMeObjFromPlcmt():
    plcmt = random.choice(PLACEMENT_LOCATIONS)
    if random.random() < 0.5:
        obj, _ = random_object()
        params = {"object": obj, "source_location": plcmt}
        text = f"{v('bring')} me {art(obj)} {obj} from the {plcmt}"
    else:
        cat = random.choice(OBJECT_CATEGORIES)
        params = {"object_category": cat, "source_location": plcmt}
        text = f"{v('bring')} me a {cat} item from the {plcmt}"
    return params, text


def gen_tellCatPropOnPlcmt():
    cat = random.choice(OBJECT_CATEGORIES)
    comp = random.choice(OBJECT_COMPARATORS)
    plcmt = random.choice(PLACEMENT_LOCATIONS)
    params = {"object_category": cat, "object_comparator": comp, "placement_location": plcmt}
    text = f"{v('tell')} me what is the {comp} {cat} item on the {plcmt}"
    return params, text


def gen_greetClothDscInRm():
    cloth = random.choice(CLOTHING)
    room = random.choice(ROOMS)
    params = {"clothing": cloth, "room": room}
    text = f"{v('greet')} the person wearing a {cloth} in the {room}"
    return params, text


def gen_greetNameInRm():
    name = random.choice(NAMES)
    room = random.choice(ROOMS)
    params = {"person_name": name, "room": room}
    text = f"{v('greet')} {name} in the {room}"
    return params, text


def gen_meetNameAtLocThenFindInRm():
    name = random.choice(NAMES)
    meet_loc = random.choice(LOCATIONS)
    find_room = random.choice(ROOMS)
    params = {"person_name": name, "meet_location": meet_loc, "find_room": find_room}
    text = f"{v('meet')} {name} at the {meet_loc} then {v('find')} them in the {find_room}"
    return params, text


def gen_countClothPrsInRoom():
    cloth = random.choice(CLOTHING)
    room = random.choice(ROOMS)
    params = {"clothing": cloth, "room": room}
    text = f"{v('count')} people in the {room} are wearing a {cloth}"
    return params, text


def gen_tellPrsInfoAtLocToPrsAtLoc():
    info = random.choice(PERSON_INFO)
    loc1, loc2 = random.sample(LOCATIONS, 2)
    params = {"person_info": info, "from_location": loc1, "to_location": loc2}
    text = f"{v('tell')} the {info} of the person at the {loc1} to the person at the {loc2}"
    return params, text


def gen_followPrsAtLoc():
    room = random.choice(ROOMS)
    if random.random() < 0.5:
        g = random.choice(GESTURES)
        params = {"gesture": g, "room": room}
        text = f"{v('follow')} the {g} in the {room}"
    else:
        p = random.choice(POSES)
        params = {"pose": p, "room": room}
        text = f"{v('follow')} the {p} in the {room}"
    return params, text


# Registry: action name -> builder function. Exactly 22 entries, matching the
# 22 keys of CommandGenerator.templates in gpsr_commands.py.
ACTIONS = {
    "goToLoc": gen_goToLoc,
    "takeObjFromPlcmt": gen_takeObjFromPlcmt,
    "findPrsInRoom": gen_findPrsInRoom,
    "findObjInRoom": gen_findObjInRoom,
    "meetPrsAtBeac": gen_meetPrsAtBeac,
    "countObjOnPlcmt": gen_countObjOnPlcmt,
    "countPrsInRoom": gen_countPrsInRoom,
    "tellPrsInfoInLoc": gen_tellPrsInfoInLoc,
    "tellObjPropOnPlcmt": gen_tellObjPropOnPlcmt,
    "talkInfoToGestPrsInRoom": gen_talkInfoToGestPrsInRoom,
    "followNameFromBeacToRoom": gen_followNameFromBeacToRoom,
    "guideNameFromBeacToBeac": gen_guideNameFromBeacToBeac,
    "guidePrsFromBeacToBeac": gen_guidePrsFromBeacToBeac,
    "guideClothPrsFromBeacToBeac": gen_guideClothPrsFromBeacToBeac,
    "bringMeObjFromPlcmt": gen_bringMeObjFromPlcmt,
    "tellCatPropOnPlcmt": gen_tellCatPropOnPlcmt,
    "greetClothDscInRm": gen_greetClothDscInRm,
    "greetNameInRm": gen_greetNameInRm,
    "meetNameAtLocThenFindInRm": gen_meetNameAtLocThenFindInRm,
    "countClothPrsInRoom": gen_countClothPrsInRoom,
    "tellPrsInfoAtLocToPrsAtLoc": gen_tellPrsInfoAtLocToPrsAtLoc,
    "followPrsAtLoc": gen_followPrsAtLoc,
}

ACTION_NAMES = list(ACTIONS.keys())
assert len(ACTION_NAMES) == 22, f"expected 22 actions, got {len(ACTION_NAMES)}"

# Allowed parameter keys per action (used by the validator)
ALLOWED_PARAMS = {
    "goToLoc": {"room"},
    "takeObjFromPlcmt": {"object", "object_category", "placement_location"},
    "findPrsInRoom": {"gesture", "pose", "room"},
    "findObjInRoom": {"object", "object_category", "room"},
    "meetPrsAtBeac": {"person_name", "location"},
    "countObjOnPlcmt": {"object_category", "placement_location"},
    "countPrsInRoom": {"gesture", "pose", "room"},
    "tellPrsInfoInLoc": {"person_info", "room", "location"},
    "tellObjPropOnPlcmt": {"object_comparator", "placement_location"},
    "talkInfoToGestPrsInRoom": {"talk_topic", "gesture", "room"},
    "followNameFromBeacToRoom": {"person_name", "from_location", "to_room"},
    "guideNameFromBeacToBeac": {"person_name", "from_location", "to_location"},
    "guidePrsFromBeacToBeac": {"gesture", "pose", "from_location", "to_location"},
    "guideClothPrsFromBeacToBeac": {"clothing", "from_location", "to_location"},
    "bringMeObjFromPlcmt": {"object", "object_category", "source_location"},
    "tellCatPropOnPlcmt": {"object_category", "object_comparator", "placement_location"},
    "greetClothDscInRm": {"clothing", "room"},
    "greetNameInRm": {"person_name", "room"},
    "meetNameAtLocThenFindInRm": {"person_name", "meet_location", "find_room"},
    "countClothPrsInRoom": {"clothing", "room"},
    "tellPrsInfoAtLocToPrsAtLoc": {"person_info", "from_location", "to_location"},
    "followPrsAtLoc": {"gesture", "pose", "room"},
}


# ---------------------------------------------------------------------------
# 3. BALANCED ACTION SELECTION
# ---------------------------------------------------------------------------

class ActionBalancer:
    """Tracks how many times each of the 22 actions has been used and always
    proposes one of the currently least-used actions (ties broken randomly),
    so the distribution stays roughly flat across the whole run."""

    def __init__(self, action_names):
        self.counts = Counter({a: 0 for a in action_names})

    def pick(self):
        min_count = min(self.counts.values())
        least_used = [a for a, c in self.counts.items() if c == min_count]
        action = random.choice(least_used)
        self.counts[action] += 1
        return action


# ---------------------------------------------------------------------------
# 4. TEST-SET GENERATION
# ---------------------------------------------------------------------------

def build_test_set(balancer):
    """Builds one test set: 1-3 sequences, correctly numbered, no 'command'
    wrapper -- just a JSON array of sequence objects, exactly like
    oldGPSR_testset.jsonl."""
    n_seq = random.choices([1, 2, 3], weights=[45, 35, 20])[0]

    sequences = []
    sentences = []
    for i in range(1, n_seq + 1):
        action = balancer.pick()
        params, text = ACTIONS[action]()
        seq_obj = {"sequence": i, "action": action}
        seq_obj.update(params)
        sequences.append(seq_obj)
        sentences.append(text)

    # Join the per-sequence sentences into one natural-language command.
    joiners = [", then ", ", and ", ", and then ", ". Then ", ", "]
    full_text = sentences[0]
    for s in sentences[1:]:
        full_text += random.choice(joiners) + s
    full_text = full_text[0].upper() + full_text[1:]

    row = {
        "messages": [
            {"role": "user", "content": f"Parse this robot command:\n{full_text}"},
            {"role": "assistant", "content": json.dumps(sequences, separators=(",", ":"))},
        ]
    }
    return row, sequences


def build_test_set_fixed(balancer, n_seq):
    """Same as build_test_set, but the number of sequences is fixed instead
    of randomly sampled -- used to build exactly-sized step groups."""
    sequences = []
    sentences = []
    for i in range(1, n_seq + 1):
        action = balancer.pick()
        params, text = ACTIONS[action]()
        seq_obj = {"sequence": i, "action": action}
        seq_obj.update(params)
        sequences.append(seq_obj)
        sentences.append(text)

    joiners = [", then ", ", and ", ", and then ", ". Then ", ", "]
    full_text = sentences[0]
    for s in sentences[1:]:
        full_text += random.choice(joiners) + s
    full_text = full_text[0].upper() + full_text[1:]

    row = {
        "messages": [
            {"role": "user", "content": f"Parse this robot command:\n{full_text}"},
            {"role": "assistant", "content": json.dumps(sequences, separators=(",", ":"))},
        ]
    }
    return row


def generate_dataset(n_per_step=100):
    """Builds an exactly-balanced dataset:
      - Step 1 (1 sequence/test set):  n_per_step test sets  -> n_per_step action occurrences
      - Step 2 (2 sequences/test set): n_per_step test sets  -> 2*n_per_step action occurrences
      - Step 3 (3 sequences/test set): n_per_step test sets  -> 3*n_per_step action occurrences

    Each step gets its OWN ActionBalancer, so the 22 actions are spread as
    evenly as possible *within each step* (as requested), not just overall.
    """
    all_rows = []
    step_counts = {}

    for n_seq in (1, 2, 3):
        balancer = ActionBalancer(ACTION_NAMES)
        seen_texts = set()
        step_rows = []
        for _ in range(n_per_step):
            for _attempt in range(10):
                row = build_test_set_fixed(balancer, n_seq)
                text = row["messages"][0]["content"]
                if text not in seen_texts:
                    seen_texts.add(text)
                    break
                for seq in json.loads(row["messages"][1]["content"]):
                    balancer.counts[seq["action"]] -= 1
            step_rows.append(row)
        all_rows.extend(step_rows)
        step_counts[n_seq] = dict(balancer.counts)

    random.shuffle(all_rows)
    return all_rows, step_counts


# ---------------------------------------------------------------------------
# 5. VALIDATION
# ---------------------------------------------------------------------------

def validate(rows, expected_n=300):
    errors = []

    if len(rows) != expected_n:
        errors.append(f"Expected {expected_n} test sets, found {len(rows)}")

    seen_user_msgs = Counter()
    action_occurrences = Counter()

    for idx, row in enumerate(rows):
        try:
            msgs = row["messages"]
            assert len(msgs) == 2
            assert msgs[0]["role"] == "user"
            assert msgs[1]["role"] == "assistant"
            assert msgs[0]["content"].startswith("Parse this robot command:\n")
            seen_user_msgs[msgs[0]["content"]] += 1

            sequences = json.loads(msgs[1]["content"])  # must be valid JSON
            assert isinstance(sequences, list) and len(sequences) >= 1

            if isinstance(sequences, dict) or "command" in (sequences[0] if sequences else {}):
                errors.append(f"[row {idx}] unexpected 'command' wrapper")

            for expected_seq_num, seq in enumerate(sequences, start=1):
                assert isinstance(seq, dict), f"[row {idx}] sequence not an object"
                assert "command" not in seq, f"[row {idx}] 'command' key found in sequence"
                assert seq.get("sequence") == expected_seq_num, (
                    f"[row {idx}] bad sequence numbering: "
                    f"expected {expected_seq_num}, got {seq.get('sequence')}"
                )
                action = seq.get("action")
                assert action in ACTIONS, f"[row {idx}] unknown action '{action}'"
                action_occurrences[action] += 1

                param_keys = set(seq.keys()) - {"sequence", "action"}
                allowed = ALLOWED_PARAMS[action]
                invalid = param_keys - allowed
                assert not invalid, f"[row {idx}] invalid params {invalid} for action '{action}'"
                assert param_keys, f"[row {idx}] action '{action}' has no parameters at all"

        except AssertionError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"[row {idx}] {type(e).__name__}: {e}")

    dupes = {k: v for k, v in seen_user_msgs.items() if v > 1}

    report = {
        "n_rows": len(rows),
        "n_errors": len(errors),
        "errors": errors[:50],
        "action_occurrences": dict(action_occurrences),
        "n_duplicate_user_messages": len(dupes),
    }
    return report


# ---------------------------------------------------------------------------
# 6. MAIN
# ---------------------------------------------------------------------------

def step_size(row):
    return len(json.loads(row["messages"][1]["content"]))


if __name__ == "__main__":
    rows, step_counts = generate_dataset(n_per_step=100)

    out_path = "/mnt/user-data/outputs/gpsr_testset_improved.jsonl"
    with open(out_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    report = validate(rows, expected_n=300)

    sizes = Counter(step_size(r) for r in rows)
    print("=== TEST SETS PER STEP ===")
    for k in (1, 2, 3):
        print(f"Step {k} (n_sequences={k}): {sizes[k]} test sets")

    print("\n=== ACTION DISTRIBUTION PER STEP ===")
    for k in (1, 2, 3):
        counts = step_counts[k]
        total = sum(counts.values())
        print(f"\n-- Step {k}: {total} total action occurrences across 22 actions --")
        for a in ACTION_NAMES:
            print(f"  {a:32s} {counts[a]}")

    overall = Counter()
    for k in (1, 2, 3):
        overall.update(step_counts[k])
    print(f"\n=== OVERALL ACTION DISTRIBUTION (all steps combined) ===")
    for a in ACTION_NAMES:
        print(f"{a:32s} {overall[a]}")
    print(f"\nTotal action occurrences overall: {sum(overall.values())}")

    print("\n=== VALIDATION REPORT ===")
    print(f"rows: {report['n_rows']}")
    print(f"errors: {report['n_errors']}")
    if report["errors"]:
        for e in report["errors"]:
            print(" -", e)
    print(f"duplicate user messages: {report['n_duplicate_user_messages']}")
    print(f"\nWrote {out_path}")
