import requests

url = "https://httpbin.org/ip"


def read_proxy_file(file_path):
    with open(file_path, 'r') as file:
        line = file.readline().strip()
        proxy_host, proxy_port, proxy_username, proxy_password = line.split(':')
    return proxy_host, proxy_port, proxy_username, proxy_password


file_path = "../proxy.txt"
proxy_host, proxy_port, proxy_username, proxy_password = read_proxy_file(file_path)

proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"

proxy_dict = {
    "http": proxy_url,
    "https": proxy_url
}

try:
    response = requests.get(url, proxies=proxy_dict)

    print("Response from proxy server:")
    print(response.text)

except Exception as e:
    print("Error:", e)
