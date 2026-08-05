import psutil

for service in psutil.win_service_iter():
    print(service.name())