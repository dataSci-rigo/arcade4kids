"""
Train an EMNIST Letters CNN and export to ONNX.
Run once with: conda run -n omaha python fetch_model.py

Requires: torch torchvision onnx
  pip install torch torchvision onnx
"""

import os, sys
os.makedirs("models", exist_ok=True)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader
    import torchvision
    import torchvision.transforms as transforms
except ImportError:
    print("Installing torch, torchvision, onnx ...")
    os.system(f"{sys.executable} -m pip install torch torchvision onnx --quiet")
    import torch, torch.nn as nn, torch.optim as optim
    from torch.utils.data import DataLoader
    import torchvision, torchvision.transforms as transforms

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {DEVICE}")

# ── Model ───────────────────────────────────────────────────────────────────
class LetterCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.BatchNorm2d(32),
            nn.Conv2d(32, 32, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout2d(0.25),   # 14×14

            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.BatchNorm2d(64),
            nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout2d(0.25),   # 7×7

            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(), nn.BatchNorm2d(128),
            nn.MaxPool2d(2), nn.Dropout2d(0.25),   # 3×3
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 3 * 3, 256), nn.ReLU(), nn.Dropout(0.5),
            nn.Linear(256, 26),
        )

    def forward(self, x):
        return self.classifier(self.features(x))

# ── Data ─────────────────────────────────────────────────────────────────────
# EMNIST Letters: labels 1-26 (A=1 … Z=26), images transposed relative to MNIST
tf = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1722,), (0.3309,)),
])

# Patch URL to working NIST mirror (old URL redirects to HTML)
torchvision.datasets.EMNIST.url = "https://biometrics.nist.gov/cs_links/EMNIST/gzip.zip"
torchvision.datasets.EMNIST.md5 = None  # skip checksum

print("Loading EMNIST Letters dataset …")
train_ds = torchvision.datasets.EMNIST(
    root="/tmp/emnist", split="letters", train=True,  download=True, transform=tf)
test_ds  = torchvision.datasets.EMNIST(
    root="/tmp/emnist", split="letters", train=False, download=True, transform=tf)

train_loader = DataLoader(train_ds, batch_size=256, shuffle=True,  num_workers=4, pin_memory=True)
test_loader  = DataLoader(test_ds,  batch_size=256, shuffle=False, num_workers=4, pin_memory=True)

CKPT = os.path.join("models", "emnist_letters.pt")

# ── Train (skip if checkpoint exists) ────────────────────────────────────────
model = LetterCNN().to(DEVICE)
if os.path.exists(CKPT):
    print(f"Loading checkpoint {CKPT} …")
    model.load_state_dict(torch.load(CKPT, map_location=DEVICE))
else:
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=3e-3,
        steps_per_epoch=len(train_loader), epochs=12
    )
    loss_fn = nn.CrossEntropyLoss(label_smoothing=0.1)

    EPOCHS = 12
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total, correct = 0, 0
        for imgs, labels in train_loader:
            imgs = imgs.to(DEVICE)
            labels = (labels - 1).to(DEVICE)    # shift 1-26 → 0-25
            optimizer.zero_grad()
            out = model(imgs)
            loss_fn(out, labels).backward()
            optimizer.step()
            scheduler.step()
            correct += (out.argmax(1) == labels).sum().item()
            total += len(labels)
        acc = correct / total * 100

        model.eval()
        tcorrect, ttotal = 0, 0
        with torch.no_grad():
            for imgs, labels in test_loader:
                imgs = imgs.to(DEVICE)
                labels = (labels - 1).to(DEVICE)
                tcorrect += (model(imgs).argmax(1) == labels).sum().item()
                ttotal += len(labels)
        print(f"Epoch {epoch:2d}/{EPOCHS}  train {acc:.1f}%  test {tcorrect/ttotal*100:.1f}%")

    torch.save(model.state_dict(), CKPT)
    print(f"Checkpoint saved → {CKPT}")

# ── Export to ONNX ────────────────────────────────────────────────────────────
model.eval().cpu()
dummy = torch.zeros(1, 1, 28, 28)
out_path = os.path.join("models", "emnist_letters.onnx")
torch.onnx.export(
    model, dummy, out_path,
    input_names=["input"], output_names=["logits"],
    dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
    opset_version=17,
)
print(f"\nSaved → {out_path}")
print("Test with: python -c \"import onnxruntime as ort, numpy as np; "
      "s=ort.InferenceSession('models/emnist_letters.onnx'); "
      "print(s.run(None, {'input': np.zeros((1,1,28,28), dtype='float32')})[0].argmax())\"")
