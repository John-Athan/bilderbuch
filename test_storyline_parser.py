import json
from storyline_creator import parse_llm_output

# Test case 1: JSON with newlines in keys
test_json_1 = '''
{
  "response": [
    {
      
      "title": "Der kleine Drache im Weltall",
      "pages": [
        { "text": "Seite 1", "image_description": "Beschreibung 1" },
        { "text": "Seite 2", "image_description": "Beschreibung 2" }
      ]
    }
  ]
}
'''

# Test case 2: JSON with newline before "title" key (simulating the error)
test_json_2 = '''
[
  {
    
"title": "Der kleine Drache im Weltall",
    "pages": [
      { "text": "Seite 1", "image_description": "Beschreibung 1" },
      { "text": "Seite 2", "image_description": "Beschreibung 2" }
    ]
  }
]
'''

# Test case 3: JSON with missing title
test_json_3 = '''
[
  {
    "pages": [
      { "text": "Seite 1", "image_description": "Beschreibung 1" },
      { "text": "Seite 2", "image_description": "Beschreibung 2" }
    ]
  }
]
'''

print("Testing parse_llm_output with problematic JSON inputs...")

try:
    # Test case 1
    storylines_1 = parse_llm_output(test_json_1)
    print(f"Test 1 passed: Found {len(storylines_1)} storylines")
except Exception as e:
    print(f"Test 1 failed: {e}")

try:
    # Test case 2 (simulates the actual error)
    storylines_2 = parse_llm_output(test_json_2)
    print(f"Test 2 passed: Found {len(storylines_2)} storylines with title: {storylines_2[0].title}")
except Exception as e:
    print(f"Test 2 failed: {e}")

try:
    # Test case 3
    storylines_3 = parse_llm_output(test_json_3)
    print(f"Test 3 passed: Found {len(storylines_3)} storylines with title: {storylines_3[0].title}")
except Exception as e:
    print(f"Test 3 failed: {e}")

print("All tests completed.")