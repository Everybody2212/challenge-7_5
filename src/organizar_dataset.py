import os
import shutil
import random

# Set seed so image splitting is reproducible
random.seed(42)

# --- PATH CONFIGURATION ---
# Change these paths to the folders where you extracted the DomainNet datasets
DOMAINNET_REAL_PATH = "C:\Users\Anderson\Documents\UD\7mo\MachineLearning\Challenges\datasets\real\real" 
DOMAINNET_INFOGRAPH_PATH = "C:\Users\Anderson\Documents\UD\7mo\MachineLearning\Challenges\datasets\infograph\infograph"

# Project destination path
PROJECT_DATA_PATH = "C:\Users\Anderson\Documents\UD\7mo\MachineLearning\Challenges\challenge-7_5\data"

# The 6 classes assigned to Group 5
FOOD_CLASSES = ["apple", "banana", "cake", "pizza", "sandwich", "strawberry"]

def create_directories():
    """Create the Few-Shot folder structure in the project."""
    for clase in FOOD_CLASSES:
        os.makedirs(os.path.join(PROJECT_DATA_PATH, "source_real", "train", clase), exist_ok=True)
        os.makedirs(os.path.join(PROJECT_DATA_PATH, "source_real", "val", clase), exist_ok=True)
        os.makedirs(os.path.join(PROJECT_DATA_PATH, "source_real", "test", clase), exist_ok=True)
        os.makedirs(os.path.join(PROJECT_DATA_PATH, "target_infograph", "test", clase), exist_ok=True)

def process_real_source():
    """Filter and split the Real domain while preserving the Few-Shot budget."""
    print("Processing source domain (Real)...")
    for clase in FOOD_CLASSES:
        class_source_path = os.path.join(DOMAINNET_REAL_PATH, clase)
        if not os.path.exists(class_source_path):
            print(f"⚠️ Warning: original folder for {clase} was not found")
            continue
            
        # List and shuffle class images
        images = [img for img in os.listdir(class_source_path) if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
        random.shuffle(images)
        
        total_images = len(images)
        print(f"ℹ️ {clase} has a total of {total_images} original images.")
        
        # Case 1: ideal scenario (more than 100 images)
        if total_images >= 100:
            train_images = images[:50]
            val_images = images[50:100]
            test_images = images[100:]
        # Case 2: critical scenario (less than 100 images)
        else:
            print(f"⚠️ Critical Warning: {clase} has only {total_images} images. Adjusting adaptive split...")
            # Reserve 50 mandatory images for train if possible
            mitad = total_images // 2
            if total_images >= 60:
                # If there are at least 60, reserve 50 for train and the rest for val
                train_images = images[:50]
                val_images = images[50:]
                test_images = [] # Temporarily left empty
            else:
                # If the set is extremely small, split half and half
                train_images = images[:mitad]
                val_images = images[mitad:]
                test_images = []
                
        # Copy to respective destinations
        for img in train_images:
            shutil.copy(os.path.join(class_source_path, img), os.path.join(PROJECT_DATA_PATH, "source_real", "train", clase, img))
        for img in val_images:
            shutil.copy(os.path.join(class_source_path, img), os.path.join(PROJECT_DATA_PATH, "source_real", "val", clase, img))
        for img in test_images:
            shutil.copy(os.path.join(class_source_path, img), os.path.join(PROJECT_DATA_PATH, "source_real", "test", clase, img))
            
    print("✅ Real domain organized successfully.")

def process_infograph_target():
    """Move ALL class images to the Infograph test domain."""
    print("Processing target domain (Infograph)...")
    for clase in FOOD_CLASSES:
        class_source_path = os.path.join(DOMAINNET_INFOGRAPH_PATH, clase)
        if not os.path.exists(class_source_path):
            print(f"⚠️ Warning: original folder for {clase} was not found")
            continue
            
        images = [img for img in os.listdir(class_source_path) if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        for img in images:
            shutil.copy(os.path.join(class_source_path, img), os.path.join(PROJECT_DATA_PATH, "target_infograph", "test", clase, img))
            
    print("✅ Infograph domain organized successfully.")

if __name__ == "__main__":
    crear_directorios()
    procesar_origen_real()
    procesar_destino_infograph()
