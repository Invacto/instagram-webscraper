# README

These scripts are meant to be run in Docker Containers with Docker Compose as the orcestration software.

Once the Docker containers are running, each container needs a ```config.json``` configured with a residential proxy, datacenter proxies, and usernames.

To generate a ```config.json``` , input the residential proxy into the ```script_inputs/proxy.txt``` file, input the datacenter proxies into the ```script_inputs/datacenter_proxy.txt``` file, and the usernames into the ```script_inputs/usernames.txt```. Then in the ```generate_json_config.py``` file, modifed the index range of the usernames to be used at the bottom of the file, and then run the script. The script will write to a file named ```config.json```.

To run the scraping script, run ```script.py``` in the background with the correct config.json in the same directory of the docker container.

To extract usernames from scraped JSONs, which requires for users to be scraped beforehand, run the ```generate_json_config.py``` and it will generate username files in 100k batches, which could be modifed in the script.
