import torch
import torch.nn as nn
from torchvision import transforms, models, datasets
from PIL import Image
from pathlib import Path
import os


class PredictionPipeline:
    def __init__(self,
                 filename: str,
                 device: torch.device = None):
        """
        :param filename: Path to the image to predict
        :param config: TrainingConfig instance for model construction and loading
        :param device: torch.device, optional. Automatically selects GPU/CPU if not specified
        """
        self.filename = filename
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Load class names
        # self.class_names = datasets.ImageFolder(self.config.training_data).classes
        self.class_names = ["adenocarcinoma", "normal"]
        print(f"Class index mapping: {{i: name for i, name in enumerate(self.class_names)}}")

        # Build and load model
        self.model = self._load_model()

    def _load_model(self) -> nn.Module:
        # Model architecture should match training configuration
        model = models.resnet18(weights=None)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, 2)

        # Load trained weights
        state_dict = torch.load(os.path.join("model", "model.pt"), map_location=self.device)
        model.load_state_dict(state_dict)
        model.to(self.device).eval()
        return model

    def predict(self) -> list:
        # Preprocessing pipeline
        preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                  std=[0.229, 0.224, 0.225])
        ])

        # Load and process image
        img = Image.open(self.filename).convert('RGB')
        input_tensor = preprocess(img).unsqueeze(0).to(self.device)

        # Inference
        with torch.no_grad():
            outputs = self.model(input_tensor)
            probs = torch.softmax(outputs, dim=1).squeeze(0)
            idx = int(probs.argmax())
            confidence = float(probs[idx])

        label = self.class_names[idx]
        print(f"Predicted result: index {idx} -> class '{label}', confidence {confidence:.3f}")

        # Return result
        return [{
            "index": idx,
            "label": label,
            "confidence": confidence
        }]