import torch
import torch.nn as nn
from torchvision import models

def construir_backbone(mode="feature_extraction", num_classes=6, device="cpu"):
    """
    Build the official ResNet-18 backbone unified for Group 5's project.
    Freeze or unfreeze layers depending on the required variant.
    """
    # Strictly unified to ResNet-18 for cross-stage consistency
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    
    if mode == "feature_extraction":
        for param in model.parameters():
            param.requires_grad = False
    elif mode == "fine_tuning":
        for param in model.parameters():
            param.requires_grad = True
            
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_classes)
    return model.to(device)

def train_one_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss, corrects, total = 0.0, 0, 0
    for inputs, labels in dataloader:
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, 1)
        corrects += torch.sum(preds == labels.data)
        total += inputs.size(0)
    return running_loss / total, (corrects.double() / total).item()

def evaluate_model(model, dataloader, criterion, device):
    model.eval()
    running_loss, corrects, total = 0.0, 0, 0
    if dataloader is None:
        return 0.0, 0.0
    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            corrects += torch.sum(preds == labels.data)
            total += inputs.size(0)
    return running_loss / total, (corrects.double() / total).item()
