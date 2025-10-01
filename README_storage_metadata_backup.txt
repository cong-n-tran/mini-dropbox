start and upload:

docker-compose up
curl -F "file=@test.txt" -F "user=Test" http://localhost:5001/upload


check upload:
docker exec -it project2-storage-1 sh 
ls /storage

replace storage with metadata/backup