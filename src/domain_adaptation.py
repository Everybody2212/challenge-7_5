import os
import random
import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch_directml
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from torchvision import datasets, transforms, models

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    print(f"🌱 Random seed fixed at: {seed}")

if __name__ == "__main__":
    if torch_directml.is_available():
        device = torch_directml.device(1)
        print(f"🚀 CLASSIFIER RUNNING ON AMD GPU: {device}")
    else:
        device = torch.device("cpu")
        print("💻 DirectML not available, using CPU.")

    BASE_DIR = "C:\Users\Anderson\Documents\UD\7mo\MachineLearning\Challenges\challenge-7_5"
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOG_DIR = os.path.join(BASE_DIR, "runs")
    CHECKPOINT_DIR = os.path.join(BASE_DIR, "checkpoints")
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    SEEDS = [42, 100, 2026]
    final_results = {}

    imsize = 224
    batch_size = 32  # Adjusted to the guide's suggested search space

    # Identical preprocessing required to avoid artificial bias
    transform_train = transforms.Compose([
        transforms.Resize((imsize, imsize)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    transform_val = transforms.Compose([
        transforms.Resize((imsize, imsize)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    source_train_dir = os.path.join(DATA_DIR, "source_real", "train")
    synthetic_train_dir = os.path.join(DATA_DIR, "synthetic_target")
    target_val_dir = os.path.join(DATA_DIR, "target_infograph", "test")

    dataset_val = datasets.ImageFolder(target_val_dir, transform=transform_val)
    loader_val = DataLoader(dataset_val, batch_size=batch_size, shuffle=False)

    def train_one_epoch(model, dataloader, criterion, optimizer):
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

    def evaluate_model(model, dataloader, criterion):
        model.eval()
        running_loss, corrects, total = 0.0, 0, 0
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

    def initialize_model(num_classes):
        # Load ResNet-18 (or change this to ResNet-50 if preferred)
        model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        num_ftrs = model.fc.in_features
        model.fc = nn.Linear(num_ftrs, num_classes)
        return model.to(device)

    # --- OFFICIAL MULTI-SEED LOOP ---
    for seed in SEEDS:
        print(f"
=======================================================")
        print(f"🏃 RUNNING EXPERIMENT WITH SEED {seed}")
        print(f"=======================================================")
        set_seed(seed)

        dataset_source = datasets.ImageFolder(source_train_dir, transform=transform_train)
        dataset_synthetic = datasets.ImageFolder(synthetic_train_dir, transform=transform_train)

        loader_source = DataLoader(dataset_source, batch_size=batch_size, shuffle=True)
        loader_synthetic = DataLoader(dataset_synthetic, batch_size=batch_size, shuffle=True)

        num_classes = len(dataset_source.classes)
        model = inicializar_modelo(num_classes)
        criterion = nn.CrossEntropyLoss()

        writer_st1 = SummaryWriter(os.path.join(LOG_DIR, f"seed_{seed}_stage1_source"))
        writer_st2 = SummaryWriter(os.path.join(LOG_DIR, f"seed_{seed}_stage2_synthetic"))

        # 🏁 STAGE 1: Feature Extraction / Baseline (Required: 20-30 epochs)
        epochs_st1 = 25 
        optimizer = optim.Adam(model.parameters(), lr=1e-4)
        print(f"
🔹 [Stage 1] Seed {seed} - Training on Real Source (Photos)...")
        acc_final_st1 = 0.0
        for epoch in range(1, epochs_st1 + 1):
            t0 = time.time()
            loss_t, acc_t = train_one_epoch(model, loader_source, criterion, optimizer)
            loss_v, acc_v = evaluate_model(model, loader_val, criterion)
            if epoch % 5 == 0 or epoch == 1:
                print(f"  Epoch [{epoch:02d}/{epochs_st1:02d}] ({time.time()-t0:.1f}s) -> Loss: {loss_t:.4f} | Acc: {acc_t:.4f} || Val Acc: {acc_v:.4f}")
            writer_st1.add_scalar("Loss/Train", loss_t, epoch)
            writer_st1.add_scalar("Accuracy/Train", acc_t, epoch)
            writer_st1.add_scalar("Loss/Validation", loss_v, epoch)
            writer_st1.add_scalar("Accuracy/Validation", acc_v, epoch)
            acc_final_st1 = acc_v

        if seed == 42:
            torch.save(model.state_dict(), os.path.join(CHECKPOINT_DIR, "best_part_A_model.pt"))
            print(f"💾 Part A checkpoint saved successfully (.pt)")

        # 🚀 STAGE 2: Fine-Tuning / Adaptation with NST (Required: 30-50 epochs)
        epochs_st2 = 40 
        optimizer = optim.Adam(model.parameters(), lr=1e-5, weight_decay=1e-4)
        print(f"
🔹 [Stage 2] Seed {seed} - Fine-Tuning with Synthetic Images (NST)...")
        acc_final_st2 = 0.0
        for epoch in range(1, epochs_st2 + 1):
            t0 = time.time()
            loss_t, acc_t = train_one_epoch(model, loader_synthetic, criterion, optimizer)
            loss_v, acc_v = evaluate_model(model, loader_val, criterion)
            if epoch % 5 == 0 or epoch == 1:
                print(f"  Synth Epoch [{epoch:02d}/{epochs_st2:02d}] ({time.time()-t0:.1f}s) -> Loss: {loss_t:.4f} | Acc: {acc_t:.4f} || Val Acc: {acc_v:.4f}")
            writer_st2.add_scalar("Loss/Train", loss_t, epoch)
            writer_st2.add_scalar("Accuracy/Train", acc_t, epoch)
            writer_st2.add_scalar("Loss/Validation", loss_v, epoch)
            writer_st2.add_scalar("Accuracy/Validation", acc_v, epoch)
            acc_final_st2 = acc_v

        if seed == 42:
            torch.save(model.state_dict(), os.path.join(CHECKPOINT_DIR, "best_part_C_model.pt"))
            print(f"💾 Part C checkpoint saved successfully (.pt)")

        final_results[seed] = {"Stage1_Base": acc_final_st1, "Stage2_Adapted": acc_final_st2}
        writer_st1.close()
        writer_st2.close()

    # FINAL CONSOLIDATED STATISTICS REPORT
    print("
" + "="*55)
    print("📊 FINAL CONSOLIDATED METRICS REPORT (3 SEEDS)")
    print("="*55)
    accs_st1 = [res["Stage1_Base"] for res in final_results.values()]
    accs_st2 = [res["Stage2_Adapted"] for res in final_results.values()]
    print(f"➡️ BASELINE (Stage 1): {np.mean(accs_st1)*100:.2f}% ± {np.std(accs_st1)*100:.2f}%")
    print(f"➡️ ADAPTED DOMAIN (Stage 2): {np.mean(accs_st2)*100:.2f}% ± {np.std(accs_st2)*100:.2f}%")
    print(f"🚀 NET GAIN ON INFOGRAPHICS: +{(np.mean(accs_st2) - np.mean(accs_st1))*100:.2f}%")
