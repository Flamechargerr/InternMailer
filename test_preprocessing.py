from reply_classifier import get_reply_classifier

c = get_reply_classifier()

test1 = "Thanks for reaching out! I'm interested in discussing this further."
test2 = "Thank you, but I'm not interested at this time."

# Check preprocessing
processed1 = c.preprocess_text(test1)
processed2 = c.preprocess_text(test2)

print(f"Original 1: {test1}")
print(f"Processed 1: {processed1}")
print(f"Has 'interested': {'interested' in processed1}")
print(f"Has 'im interested': {'im interested' in processed1}")
print()
print(f"Original 2: {test2}")
print(f"Processed 2: {processed2}")
print(f"Has 'not interested': {'not interested' in processed2}")
print(f"Has 'im not interested': {'im not interested' in processed2}")
print()

# Check keywords
print("INTERESTED keywords:", c.keywords[list(c.keywords.keys())[0]][:5])
print("NOT_INTERESTED keywords:", c.keywords[list(c.keywords.keys())[1]][:5])
