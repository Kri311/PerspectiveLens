import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel

class TripletLoss(nn.Module):
    """
    Triplet Loss for Contrastive Learning.
    Forces the embeddings of articles with the same framing (Anchor & Positive) to be closer,
    while pushing away articles with different framing (Anchor & Negative).
    """
    def __init__(self, margin=1.0):
        super(TripletLoss, self).__init__()
        self.margin = margin

    def forward(self, anchor, positive, negative):
        # Calculate cosine distance
        distance_positive = 1.0 - F.cosine_similarity(anchor, positive)
        distance_negative = 1.0 - F.cosine_similarity(anchor, negative)
        
        # Triplet loss formula: max(0, dist(A, P) - dist(A, N) + margin)
        losses = F.relu(distance_positive - distance_negative + self.margin)
        return losses.mean()

class FramingDataset(Dataset):
    def __init__(self, triplets, tokenizer, max_length=512):
        self.triplets = triplets
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.triplets)

    def __getitem__(self, idx):
        anchor_text, pos_text, neg_text = self.triplets[idx]
        
        def encode(text):
            return self.tokenizer(
                text,
                padding='max_length',
                truncation=True,
                max_length=self.max_length,
                return_tensors='pt'
            )
            
        return encode(anchor_text), encode(pos_text), encode(neg_text)

def train_contrastive_framing_model(model_name="google/muril-base-cased", epochs=3):
    """
    Example training loop for fine-tuning MuRIL using Contrastive Learning.
    This teaches the model to separate articles based on 'spin' and 'framing' 
    rather than just topical keywords.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    
    # Mock data: (Anchor, Positive (same frame), Negative (different frame))
    mock_data = [
        ("Govt announces welfare scheme", "CM launches new benefits", "Opposition slams reckless spending"),
    ]
    
    dataset = FramingDataset(mock_data, tokenizer)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    criterion = TripletLoss(margin=1.0)
    
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for anchor_batch, pos_batch, neg_batch in dataloader:
            optimizer.zero_grad()
            
            # Move to device and get pooled output (CLS token)
            a_emb = model(**{k: v.squeeze(1).to(device) for k, v in anchor_batch.items()}).pooler_output
            p_emb = model(**{k: v.squeeze(1).to(device) for k, v in pos_batch.items()}).pooler_output
            n_emb = model(**{k: v.squeeze(1).to(device) for k, v in neg_batch.items()}).pooler_output
            
            loss = criterion(a_emb, p_emb, n_emb)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1} | Average Triplet Loss: {total_loss / len(dataloader)}")

    print("Contrastive fine-tuning complete. Model has learned framing differences!")
    return model
