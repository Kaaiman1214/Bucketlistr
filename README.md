# Bucketlistr
A self-hosted open source Bucketlist solution

### Using Docker
**Run the container:** Replace `/path/to/host/data` and `/path/to/host/config`:
   ```bash
  docker run -d \
    --name Bucketlistr \
    --restart unless-stopped \
    -v /path/to/host/bucketlist.db:/app/bucketlist.db \
    -v /path/to/host/uploads:/app/static/uploads \
    -p 8000:8000 \
    -e TZ=Europe/Amsterdam \
     kds1215/bucketlistr
   ```
