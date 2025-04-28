docker build -t jellyfin-library-poster . --platform linux/amd64, linux/arm64
$IMAGE_ID = docker images -q jellyfin-library-poster | Select-Object -First 1
docker tag $IMAGE_ID evanqu/jellyfin-library-poster:latest
Write-Host "成功将 $IMAGE_ID 标记为 evanqu/jellyfin-library-poster:latest"
docker push evanqu/jellyfin-library-poster:latest