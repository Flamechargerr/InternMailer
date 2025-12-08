from reply_classifier import ReplyClassifier

c = ReplyClassifier()

test = "Thanks for reaching out! I'm interested in discussing this further."
processed = c.preprocess_text(test)
content = c.extract_signature_cutoff(processed)

print(f"Original: {test}")
print(f"Processed: {processed}")
print(f"After signature removal: {content}")
print()

# Check keyword matching manually
for keyword in ['interested', 'im interested', 'interested in']:
    print(f"  '{keyword}' in content: {keyword in content}")
