# Deployment Guide

คู่มือการ Deploy Qwen2-VL OCR Application ไปยัง Dokploy และ platform อื่นๆ

## 📋 ข้อกำหนดเบื้องต้น

- Git repository (GitHub, GitLab, หรือ Bitbucket)
- API endpoint สำหรับ Qwen2-VL model
- API Key สำหรับเข้าถึง Vision API

## 🚀 Deploy ไปยัง Dokploy

### ขั้นตอนที่ 1: เตรียม Repository

1. Push code ขึ้น Git repository:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_REPO_URL
git push -u origin main
```

### ขั้นตอนที่ 2: สร้าง Project ใน Dokploy

1. เข้าสู่ Dokploy Dashboard
2. คลิก "Create New Project"
3. เลือก "Import from Git"
4. เชื่อมต่อกับ Git repository ของคุณ

### ขั้นตอนที่ 3: ตั้งค่า Build Configuration

**Build Settings:**
- **Build Method:** Dockerfile
- **Dockerfile Path:** `./Dockerfile`
- **Port:** `8080`

### ขั้นตอนที่ 4: ตั้งค่า Environment Variables

เพิ่ม environment variables ต่อไปนี้:

```env
# API Configuration (Required)
API_URL=http://your-api-server/v1/chat/completions
API_KEY=your-api-key-here
MODEL=qwen2-vl-32b-instruct-awq

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=8080
FLASK_DEBUG=False

# File Upload Configuration
MAX_FILE_SIZE_MB=16
UPLOAD_FOLDER=uploads

# PDF Processing
DEFAULT_DPI=200
```

### ขั้นตอนที่ 5: Deploy

1. คลิก "Deploy" button
2. รอให้ build และ deployment เสร็จสมบูรณ์
3. เข้าใช้งานผ่าน URL ที่ Dokploy สร้างให้

## 🐳 Deploy ด้วย Docker Compose (Local/VPS)

### 1. Clone repository:
```bash
git clone YOUR_REPO_URL
cd qwen25-32b-ocr
```

### 2. สร้างไฟล์ .env:
```bash
cp .env.example .env
```

### 3. แก้ไข .env ตามค่าจริง:
```bash
nano .env
```

### 4. Build และ Run:
```bash
docker-compose up -d
```

### 5. ตรวจสอบ logs:
```bash
docker-compose logs -f
```

### 6. เข้าใช้งาน:
```
http://localhost:8080
```

### 7. Stop service:
```bash
docker-compose down
```

## 🔧 Deploy บน VPS (Manual Docker)

### 1. ติดตั้ง Docker:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 2. Build Docker image:
```bash
docker build -t qwen2-vl-ocr .
```

### 3. Run container:
```bash
docker run -d \
  --name ocr-app \
  -p 8080:8080 \
  -e API_URL=http://your-api/v1/chat/completions \
  -e API_KEY=your-key \
  -e MODEL=qwen2-vl-32b-instruct-awq \
  -e FLASK_DEBUG=False \
  --restart unless-stopped \
  qwen2-vl-ocr
```

### 4. ตรวจสอบ logs:
```bash
docker logs -f ocr-app
```

## 📊 Health Check

ตรวจสอบสถานะ application:

```bash
curl http://localhost:8080/api/config
```

ควรได้ response:
```json
{
  "api_url": "http://...",
  "model": "qwen2-vl-32b-instruct-awq",
  "max_file_size": "16MB",
  "allowed_extensions": ["png", "jpg", "jpeg", "gif", "bmp", "webp", "pdf"]
}
```

## 🔐 Security Best Practices

1. **API Key Security:**
   - เก็บ API Key ใน environment variables เท่านั้น
   - ห้าม commit .env file เข้า git
   - ใช้ secrets management ของ platform

2. **Network Security:**
   - ใช้ HTTPS สำหรับ production
   - ตั้งค่า firewall ให้เปิดเฉพาะ port ที่จำเป็น
   - ใช้ reverse proxy (Nginx/Caddy) ถ้าเป็นไปได้

3. **File Upload:**
   - จำกัดขนาดไฟล์ที่ MAX_FILE_SIZE_MB
   - ตรวจสอบ file type ก่อน process
   - ลบไฟล์ชั่วคราวหลัง process เสร็จ

## 🔄 Update และ Rollback

### Update ใน Dokploy:
1. Push code ใหม่ขึ้น git
2. Dokploy จะ auto-deploy (ถ้าเปิด auto-deploy)
3. หรือคลิก "Redeploy" ใน dashboard

### Rollback:
1. เข้า Dokploy dashboard
2. เลือก deployment version ก่อนหน้า
3. คลิก "Rollback"

### Update ด้วย Docker Compose:
```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📈 Monitoring

### ดู Logs:
**Dokploy:**
- เข้า dashboard > Logs tab

**Docker Compose:**
```bash
docker-compose logs -f ocr-app
```

**Docker:**
```bash
docker logs -f ocr-app
```

### Resource Usage:
```bash
docker stats ocr-app
```

## 🐛 Troubleshooting

### ปัญหา: Container ไม่ start
```bash
# ดู logs
docker logs ocr-app

# ตรวจสอบ environment variables
docker exec ocr-app env
```

### ปัญหา: API Connection Error
- ตรวจสอบ API_URL และ API_KEY
- ตรวจสอบว่า container สามารถเข้าถึง API endpoint ได้
- ทดสอบด้วย curl:
```bash
docker exec ocr-app curl -I http://your-api
```

### ปัญหา: PDF Processing ล้มเหลว
- ตรวจสอบว่า poppler-utils ถูกติดตั้งในcontainer
- เพิ่ม memory limit ถ้าจำเป็น:
```bash
docker run --memory="2g" ...
```

### ปัญหา: Upload File ใหญ่ไม่ได้
- เพิ่มค่า MAX_FILE_SIZE_MB
- ตรวจสอบ reverse proxy timeout settings
- เพิ่ม gunicorn timeout (แก้ใน Dockerfile)

## 🌐 Custom Domain (Dokploy)

1. ไปที่ Project Settings
2. เพิ่ม Custom Domain
3. ตั้งค่า DNS:
   - Type: A Record หรือ CNAME
   - Value: Dokploy server IP
4. Enable SSL/TLS (Let's Encrypt)

## 📝 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| API_URL | ✅ | - | Qwen2-VL API endpoint |
| API_KEY | ✅ | - | API authentication key |
| MODEL | ✅ | qwen2-vl-32b-instruct-awq | Model name |
| FLASK_HOST | ❌ | 0.0.0.0 | Flask bind address |
| FLASK_PORT | ❌ | 8080 | Application port |
| FLASK_DEBUG | ❌ | False | Debug mode |
| MAX_FILE_SIZE_MB | ❌ | 16 | Max upload size |
| UPLOAD_FOLDER | ❌ | uploads | Upload directory |
| DEFAULT_DPI | ❌ | 200 | PDF conversion DPI |

## 🎯 Performance Tuning

### Gunicorn Workers:
แก้ไข `Dockerfile` CMD:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:8080", \
     "--workers", "4", \  # จำนวน workers
     "--threads", "4", \  # threads per worker
     "--timeout", "300", \  # request timeout
     "app:app"]
```

**Worker Formula:** `(2 x CPU cores) + 1`

### Memory:
- Minimum: 512MB
- Recommended: 1GB
- For heavy PDF: 2GB+

## 📞 Support

หากพบปัญหาการ deploy:
1. ตรวจสอบ logs ก่อน
2. ดูที่ Troubleshooting section
3. ตรวจสอบ environment variables ให้ครบถ้วน
