import torch
import torchvision.models as tvm
from PIL import Image
from app.services.preprocessing import apply_clahe
import torchvision.transforms as T

clahe_cfg = {'clip_limit': 2.0, 'tile_grid_size': [8, 8]}
img_path = r'C:\Users\heman\Downloads\archive_extracted\Knee Osteoarthritis Classification\test\Normal\N26_aug_2.jpeg'

img = Image.open(img_path).convert('RGB')
img = apply_clahe(img, clahe_cfg)

t_imagenet = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

t_custom = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize([0.2264, 0.2264, 0.2264], [0.2769, 0.2769, 0.2769])
])

model = tvm.mobilenet_v3_large(weights=None)
model.classifier[-1] = torch.nn.Linear(model.classifier[-1].in_features, 3)
model.load_state_dict(torch.load('model_artifacts/model.pth', map_location='cpu'))
model.eval()

x1 = t_imagenet(img).unsqueeze(0)
x2 = t_custom(img).unsqueeze(0)

classes = ['Normal', 'Osteopenia', 'Osteoporosis']

with torch.no_grad():
    out1 = torch.softmax(model(x1), dim=1)[0]
    out2 = torch.softmax(model(x2), dim=1)[0]

print('--- WITH IMAGENET NORMALIZATION (EXACT MATCH WITH TRAINING) ---')
print('Probabilities:', {c: round(float(p), 4) for c, p in zip(classes, out1)})
print('Predicted class:', classes[int(out1.argmax())])

print('\n--- WITH CUSTOM STATS NORMALIZATION (SHIFTED) ---')
print('Probabilities:', {c: round(float(p), 4) for c, p in zip(classes, out2)})
print('Predicted class:', classes[int(out2.argmax())])
