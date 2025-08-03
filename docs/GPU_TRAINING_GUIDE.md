# GPU Training Guide for Bitcoin LSTM Model

This guide explains how to leverage GPU acceleration for training the Bitcoin LSTM model using various cloud and local options.

## 🚀 Quick Start Options

### Option 1: Google Colab (Free GPU)
```bash
# 1. Upload your data to Google Drive
# 2. Open Google Colab and enable GPU runtime
# 3. Mount Google Drive and clone repository
!git clone https://github.com/your-username/bitcoin-quant-trading.git
%cd bitcoin-quant-trading

# 4. Install dependencies
!pip install -r requirements.txt

# 5. Run training
!python scripts/train_lstm_model.py
```

### Option 2: Kaggle Notebooks (Free GPU)
```bash
# 1. Create new Kaggle notebook
# 2. Enable GPU accelerator
# 3. Add dataset or clone repository
!git clone https://github.com/your-username/bitcoin-quant-trading.git
%cd bitcoin-quant-trading

# 4. Install and run
!pip install -r requirements.txt
!python scripts/train_lstm_model.py
```

### Option 3: AWS EC2 with GPU
```bash
# Launch p3.2xlarge or g4dn.xlarge instance
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Setup environment
sudo apt update
sudo apt install python3-pip git
git clone https://github.com/your-username/bitcoin-quant-trading.git
cd bitcoin-quant-trading

# Install CUDA and dependencies
pip3 install -r requirements.txt
python3 scripts/train_lstm_model.py
```

### Option 4: VS Code Remote Development
```bash
# 1. Install Remote-SSH extension in VS Code
# 2. Connect to cloud GPU instance
# 3. Open terminal in VS Code
# 4. Run training directly in remote environment
```

## 🔧 Hardware Configurations

### Local CPU Training (Lightweight)
- **Sequence Length**: 30 days
- **LSTM Units**: [32, 16]
- **Batch Size**: 16
- **Epochs**: 20
- **Training Time**: ~10-15 minutes

### GPU Training (Full Model)
- **Sequence Length**: 60 days
- **LSTM Units**: [128, 64, 32]
- **Batch Size**: 64
- **Epochs**: 100
- **Training Time**: ~5-10 minutes on modern GPU

## 📊 Cloud GPU Providers Comparison

| Provider | Instance Type | GPU | Cost/Hour | Free Tier |
|----------|---------------|-----|-----------|-----------|
| Google Colab | - | T4 | Free | 12h/day |
| Kaggle | - | P100/T4 | Free | 30h/week |
| AWS EC2 | g4dn.xlarge | T4 | $0.526 | No |
| AWS EC2 | p3.2xlarge | V100 | $3.06 | No |
| GCP | n1-standard-4 + T4 | T4 | $0.35 | $300 credit |
| Azure | NC6s_v3 | V100 | $3.06 | $200 credit |

## 🛠️ Setup Instructions

### 1. Google Colab Setup
```python
# In Colab notebook cell:
from google.colab import drive
drive.mount('/content/drive')

# Clone repository
!git clone https://github.com/your-username/bitcoin-quant-trading.git
%cd bitcoin-quant-trading

# Check GPU
import tensorflow as tf
print("GPU Available: ", tf.config.list_physical_devices('GPU'))

# Install requirements
!pip install -r requirements.txt

# Run training
!python scripts/train_lstm_model.py
```

### 2. AWS EC2 GPU Instance
```bash
# Launch instance with Deep Learning AMI
# Instance type: g4dn.xlarge or p3.2xlarge

# Connect via SSH
ssh -i your-key.pem ubuntu@your-instance-ip

# Activate conda environment (if using Deep Learning AMI)
source activate tensorflow2_p39

# Clone and setup
git clone https://github.com/your-username/bitcoin-quant-trading.git
cd bitcoin-quant-trading
pip install -r requirements.txt

# Run training
python scripts/train_lstm_model.py
```

### 3. VS Code Remote Development
```bash
# 1. Install Remote-SSH extension
# 2. Add SSH configuration in VS Code
Host gpu-server
    HostName your-instance-ip
    User ubuntu
    IdentityFile ~/.ssh/your-key.pem

# 3. Connect to remote host
# 4. Open integrated terminal
# 5. Run training commands
```

## 📈 Performance Optimization

### Memory Management
```python
# Add to training script for large datasets
import tensorflow as tf

# Enable mixed precision training
policy = tf.keras.mixed_precision.Policy('mixed_float16')
tf.keras.mixed_precision.set_global_policy(policy)

# Configure GPU memory growth
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
```

### Batch Size Optimization
```python
# Auto-detect optimal batch size
def find_optimal_batch_size(model, X_sample):
    batch_sizes = [16, 32, 64, 128, 256]
    for batch_size in batch_sizes:
        try:
            model.fit(X_sample[:batch_size], epochs=1, verbose=0)
            print(f"Batch size {batch_size}: OK")
        except tf.errors.ResourceExhaustedError:
            print(f"Batch size {batch_size}: Too large")
            return batch_sizes[batch_sizes.index(batch_size) - 1]
    return batch_sizes[-1]
```

## 🔄 Data Transfer Strategies

### For Cloud Training
```bash
# Option 1: Direct upload to cloud storage
aws s3 cp data/ s3://your-bucket/bitcoin-data/ --recursive

# Option 2: Use git-lfs for large files
git lfs track "*.csv"
git add .gitattributes
git add data/
git commit -m "Add training data"
git push

# Option 3: Download data directly in cloud
# Add data download script to training pipeline
```

### Sync Results Back
```bash
# Download trained models
scp -i your-key.pem ubuntu@your-instance-ip:~/bitcoin-quant-trading/results/* ./results/

# Or use cloud storage
aws s3 sync results/ s3://your-bucket/results/
```

## 🎯 Training Monitoring

### TensorBoard Integration
```python
# Add to training script
import tensorflow as tf
from datetime import datetime

# Setup TensorBoard logging
log_dir = f"logs/fit/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
tensorboard_callback = tf.keras.callbacks.TensorBoard(
    log_dir=log_dir, 
    histogram_freq=1,
    write_graph=True,
    write_images=True
)

# Add to model.fit callbacks
callbacks.append(tensorboard_callback)
```

### Remote Monitoring
```bash
# Start TensorBoard on remote server
tensorboard --logdir=logs/fit --host=0.0.0.0 --port=6006

# Access via SSH tunnel
ssh -L 6006:localhost:6006 -i your-key.pem ubuntu@your-instance-ip

# Open http://localhost:6006 in local browser
```

## 💡 Cost Optimization Tips

1. **Use Spot Instances**: Save up to 90% on AWS/GCP
2. **Auto-shutdown**: Set up automatic instance termination
3. **Preemptible Instances**: Use GCP preemptible VMs
4. **Free Tiers**: Start with Colab/Kaggle for experimentation
5. **Model Checkpointing**: Save progress to resume interrupted training

## 🚨 Best Practices

1. **Always backup data** before cloud training
2. **Use version control** for code synchronization
3. **Monitor costs** with cloud billing alerts
4. **Test locally first** with small datasets
5. **Use mixed precision** for faster training
6. **Implement early stopping** to avoid overfitting
7. **Save model checkpoints** regularly

## 📞 Troubleshooting

### Common Issues
- **CUDA out of memory**: Reduce batch size or model complexity
- **Slow data loading**: Use tf.data.Dataset with prefetching
- **Connection timeouts**: Use screen/tmux for long training sessions
- **Version conflicts**: Use Docker containers for consistency

### Quick Fixes
```bash
# Check GPU utilization
nvidia-smi

# Monitor training in background
nohup python scripts/train_lstm_model.py > training.log 2>&1 &

# Resume interrupted training
python scripts/train_lstm_model.py --resume --checkpoint=path/to/checkpoint
```
