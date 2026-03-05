from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch
import os


class InferencePipeline:
    def __init__(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.model_path = os.path.join(project_root, "machine_learning", "saved_model")
        self.tokenizer = RobertaTokenizer.from_pretrained(self.model_path)
        self.model = RobertaForSequenceClassification.from_pretrained(self.model_path)

    def predict(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        outputs = self.model(**inputs)
        prediction = torch.argmax(outputs.logits, dim=1).item()
        return "Suspicious" if prediction == 1 else "Not Suspicious"

if __name__ == "__main__":
    pipeline = InferencePipeline()
    print(pipeline.predict("Example text to classify"))
