start and upload:

docker-compose up
curl -F "file=@test.txt" -F "user=Alice" -F "password=secret123" http://localhost:5001/upload

download:
curl -O -J "http://localhost:5001/download?filename=test.txt&user=Alice&password=secret123"

delete:
curl -X DELETE "http://localhost:5001/delete?filename=test.txt&user=Alice&password=secret123"

check upload:
docker exec -it project2-storage-1 sh 
ls /storage

replace storage with metadata/backup