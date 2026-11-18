def embed_frames(frames, model_name="clip-ViT-B-32"):
    """Create reproducible CLIP evidence for every sampled frame."""
    from PIL import Image
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    images = [Image.open(frame["path"]).convert("RGB") for frame in frames]
    vectors = model.encode(images, normalize_embeddings=True).tolist()
    for frame, vector in zip(frames, vectors):
        frame["clip_model"] = model_name
        frame["clip_embedding"] = vector
    return frames

