import requests

url = "https://dark-sky.p.rapidapi.com/37.774929,-122.419418,2019-02-20"

headers = {
    'x-rapidapi-key': "7953924927mshd08331263c55184p14b3c7jsn9975f5ed4b2f",
    'x-rapidapi-host': "dark-sky.p.rapidapi.com"
    }

response = requests.request("GET", url, headers=headers)

print(response.text)
