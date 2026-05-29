import os
import torch
import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader

def get_transforms():
    """
    Define the required challenge transforms.
    Use the ImageNet mean and standard deviation statistics.
    """
    # Standard ImageNet parameters (required for pretrained models)
    cln_mean = [0.485, 0.456, 0.406]
    cln_std = [0.229, 0.224, 0.225]
    
    # Training transforms (includes data augmentation)
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5), # Required data augmentation
        transforms.ColorJitter(brightness=0.2, contrast=0.2), # Lighting control
        transforms.ToTensor(),
        transforms.Normalize(mean=cln_mean, std=cln_std)
    ])
    
    # Validation and test transforms (no random augmentations)
    test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=cln_mean, std=cln_std)
    ])
    
    return train_transform, test_transform

def create_loaders(data_path, batch_size=32):
    """
    Load images from the Few-Shot folders created in Phase 1
    and return ready-to-use PyTorch DataLoaders.
    """
    train_transform, test_transform = get_transforms()
    
    # Define absolute or relative paths
    train_real_path = os.path.join(data_path, "source_real", "train")
    val_real_path = os.path.join(data_path, "source_real", "val")
    test_real_path = os.path.join(data_path, "source_real", "test")
    test_infograph_path = os.path.join(data_path, "target_infograph", "test")
    
    print("📦 Loading datasets with ImageFolder...")
    
    # Load using ImageFolder (auto-labels folders by class name)
    train_dataset = ImageFolder(root=train_real_path, transform=train_transform)
    val_dataset = ImageFolder(root=val_real_path, transform=test_transform)
    
    # The source test set may fail if 'apple' ended with 0 images in the previous step,
    # so we validate whether the folder contains class subfolders before loading.
    try:
        test_real_dataset = ImageFolder(root=test_real_path, transform=test_transform)
        loader_test_real = DataLoader(test_real_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
        print(f"   -> Source test loaded: {len(test_real_dataset)} images.")
    except RuntimeError:
        loader_test_real = None
        print("   -> ⚠️ Source test does not contain enough images to initialize (e.g. Apple limited). It will be skipped.")

    test_info_dataset = ImageFolder(root=test_infograph_path, transform=test_transform)
    
    # Create the DataLoaders
    loader_train = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    loader_val = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    loader_test_infograph = DataLoader(test_info_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    
    print(f"✅ Load complete:")
    print(f"   -> Train Source: {len(train_dataset)} images (mapped to {len(train_dataset.classes)} classes).")
    print(f"   -> Val Source: {len(val_dataset)} images.")
    print(f"   -> Test Infograph (Target): {len(test_info_dataset)} images.")
    
    return loader_train, loader_val, loader_test_real, loader_test_infograph

if __name__ == "__main__":
    # Quick loader sanity check
    PROJECT_DATA_PATH = "C:\Users\Anderson\Documents\UD\7mo\MachineLearning\Challenges\challenge-7_5\data"
    ltrain, lval, ltest_r, ltest_i = create_loaders(PROJECT_DATA_PATH)
