# Define custom text classification logic if needed

# Cache the pipeline instance to avoid reloading the model on every call
_pipeline_instance = None


def _get_pipeline():
    global _pipeline_instance
    if _pipeline_instance is None:
        from .inference import InferencePipeline
        _pipeline_instance = InferencePipeline()
    return _pipeline_instance


def classify_text(text):
    """Classify text as suspicious or not using the cached inference pipeline."""
    pipeline = _get_pipeline()
    return pipeline.predict(text)

if __name__ == "__main__":
    result = classify_text("Example text to classify")
    print(result)
