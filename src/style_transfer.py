import os
import random
import torch
import torch_directml
import torch.nn as nn
import torch.optim as optim
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

# 1. Strict hardware configuration (force dedicated AMD GPU with 16 GB)
if torch_directml.is_available():
    device = torch_directml.device(1)
    print(f"🚀 NST RUNNING ON DEDICATED AMD GPU (16 GB): {device}")
else:
    device = torch.device("cpu")
    print("💻 No DirectML detected, using CPU.")

# 2. Standardized preprocessing per the guide protocol
imsize = 224
loader_transform = transforms.Compose([
    transforms.Resize((imsize, imsize)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

unnormalize = transforms.Normalize(
    mean=[-0.485/0.229, -0.456/0.224, -0.406/0.225],
    std=[1/0.229, 1/0.224, 1/0.225]
)

def image_loader(image_name):
    image = Image.open(image_name).convert('RGB')
    image = loader_transform(image).unsqueeze(0)
    return image.to(device)

def gram_matrix(feat):
    b, c, h, w = feat.size()
    feat = feat.view(b, c, h * w)
    return torch.bmm(feat, feat.transpose(1, 2)) / (c * h * w)

# 3. Exact loss class integrated into the sequential flow (page 6 of the guide)
class StyleContentLoss(nn.Module):
    def __init__(self, content_layers, style_layers):
        super().__init__()
        self.content_layers = content_layers
        self.style_layers = style_layers

    def forward(self, vgg_model, x, content_target, style_targets):
        content_loss = torch.tensor(0.0, device=x.device)
        style_loss = torch.tensor(0.0, device=x.device)
        
        for name, layer in vgg_model.named_children():
            x = layer(x)
            
            if name in self.content_layers:
                content_loss = content_loss + nn.functional.mse_loss(x, content_target[name])
                
            if name in self.style_layers:
                style_loss = style_loss + nn.functional.mse_loss(gram_matrix(x), style_targets[name])
                
        return content_loss, style_loss

def extract_features(vgg, img, layers):
    features = {}
    x = img
    for name, layer in vgg.named_children():
        x = layer(x)
        if name in layers:
            features[name] = x.clone()
    return features

def generate_synthetic_image(vgg_base, content_path, style_path, num_steps=300, alpha=1.0, beta=1e4):
    content_img = image_loader(content_path)
    style_img = image_loader(style_path)
    
    # Start from the real image and enable gradients
    generated = content_img.clone().detach().requires_grad_(True)

    content_layers = ['relu4_2']
    style_layers = ['relu1_1', 'relu2_1', 'relu3_1', 'relu4_1', 'relu5_1']
    all_layers = set(content_layers + style_layers)

    # Extract fixed target activations using the mapped network
    with torch.no_grad():
        content_feats = extraer_caracteristicas(vgg_base, content_img, content_layers)
        style_feats_raw = extraer_caracteristicas(vgg_base, style_img, style_layers)
        style_grams = {k: gram_matrix(v) for k, v in style_feats_raw.items()}

    # Truncate the mapped network using internal module keys (nn.Sequential compatibility)
    capas_ordenadas = list(vgg_base._modules.keys())
    ultimo_indice = max([capas_ordenadas.index(l) for l in all_layers])
    
    vgg_truncated = nn.Sequential()
    for name in capas_ordenadas[:ultimo_indice + 1]:
        vgg_truncated.add_module(name, vgg_base._modules[name])
    vgg_truncated.eval()

    model_loss = StyleContentLoss(content_layers, style_layers)
    
    # Fast pixel-level Adam optimizer
    optimizer = optim.Adam([generated], lr=0.03)

    for step in range(1, num_steps + 1):
        optimizer.zero_grad()
        
        c_loss, s_loss = model_loss(vgg_truncated, generated, content_feats, style_grams)
        loss = (alpha * c_loss) + (beta * s_loss)
        
        loss.backward()
        optimizer.step()
        
        with torch.no_grad():
            generated.clamp_(-3, 3)
            
        if step % 50 == 0 or step == 1:
            print(f"      🔹 Step {step:03d}/{num_steps} -> Total: {loss.item():.4f} | Content: {c_loss.item():.4f} | Style: {s_loss.item():.4f}")

    return generated.detach()

if __name__ == "__main__":
    random.seed(42)
    torch.manual_seed(42)

    # Rebuild native VGG19 into readable nn.Sequential names
    vgg_raw = models.vgg19(weights=models.VGG19_Weights.DEFAULT).features.to(device).eval()
    vgg_mapped = nn.Sequential()
    
    block, conv = 1, 1
    for layer in vgg_raw.children():
        if isinstance(layer, nn.Conv2d):
            name = f'conv{block}_{conv}'
        elif isinstance(layer, nn.ReLU):
            name = f'relu{block}_{conv}'
            layer = nn.ReLU(inplace=False)
            conv += 1
        elif isinstance(layer, nn.MaxPool2d):
            name = f'pool{block}'
            block += 1
            conv = 1
        else:
            name = f'layer_{block}_{conv}'
            
        vgg_mapped.add_module(name, layer)

    # Project path definitions
    BASE_DIR = "C:\Users\Anderson\Documents\UD\7mo\MachineLearning\Challenges\challenge-7_5"
    DATA_DIR = os.path.join(BASE_DIR, "data")
    SOURCE_DIR = os.path.join(DATA_DIR, "source_real", "train")
    TARGET_DIR = os.path.join(DATA_DIR, "target_infograph", "test")
    SYNTHETIC_DIR = os.path.join(DATA_DIR, "synthetic_target")

    classes = ['apple', 'banana', 'cake', 'pizza', 'sandwich', 'strawberry']
    images_per_class = 30

    print("⚡ Starting Group 5 style transfer pipeline...")
    
    for clase in classes:
        source_class_path = os.path.join(SOURCE_DIR, clase)
        target_class_path = os.path.join(TARGET_DIR, clase)
        output_class_path = os.path.join(SYNTHETIC_DIR, clase)
        os.makedirs(output_class_path, exist_ok=True)

        list_content = os.listdir(source_class_path)
        list_style = os.listdir(target_class_path)

        limit_images = min(len(list_content), images_per_class)
        print(f"
📂 Processing class [{clase.upper()}]: Generating {limit_images} synthetic images...")

        for idx in range(limit_images):
            c_img = list_content[idx]
            s_img = random.choice(list_style)

            path_c = os.path.join(source_class_path, c_img)
            path_s = os.path.join(target_class_path, s_img)

            output_tensor = generar_image_sintetica(vgg_mapped, path_c, path_s, num_steps=300, alpha=1.0, beta=1e4)
            
            out_img = unnormalize(output_tensor.squeeze(0)).cpu().clamp(0, 1)
            out_img = transforms.ToPILImage()(out_img)
            
            output_name = f"synth_{clase}_{idx:02d}.png"
            out_img.save(os.path.join(output_class_path, output_name))
            print(f"   -> [{idx+1}/{limit_images}] Saved successfully: {output_name}")

    print("
🎉 Phase B completed successfully! The 180 synthetic images are ready in 'data/synthetic_target/'.")
